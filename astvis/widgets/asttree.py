#!/usr/bin/env python

"""Abstract syntax tree module."""

import logging
LOG = logging.getLogger("asttree")
from astvis.common import FINE, FINER, FINEST

from astvis.common import INFO_TEXT, INFO_OBJECT_PATH
from astvis.model import ast
from astvis import event, project, gtkx
from astvis import action
from astvis.widgets.base import BaseWidget
import gtk
import pickle

class RowFactory:
    thumbnailFilenames = {ast.File: "data/thumbnails/file.png",
            ast.ProgramUnit: lambda obj: obj.type=='module' and "data/thumbnails/module.png"
                    or "data/thumbnails/program.png",
            ast.Subprogram: "data/thumbnails/subroutine.png",
            ast.Statement: lambda obj: obj.type=='call' and 'data/thumbnails/call.png' or None,
            ast.Call: "data/thumbnails/call.png",
            ast.Use: "data/thumbnails/use.png"}
            
    def __init__(self):
        self.thumbnails = {}

    def getRow(self, obj):
        name = hasattr(obj,"name") and obj.name or str(obj)
        
        return [name, obj, self._getThumbnail(obj), gtk.gdk.color_parse("black")]

    def _getThumbnail(self, obj):
        "Thumbnail to be shown in GtkTreeView for the C{obj} element"
        filename = RowFactory.thumbnailFilenames.get(obj.__class__, None)
        if callable(filename):
            filename = filename(obj)

        if not filename:
            return None
        if not self.thumbnails.has_key(filename):
            import gtk.gdk
            thumbnail = gtk.gdk.pixbuf_new_from_file_at_size(filename, 16, 16)
            self.thumbnails[filename] = thumbnail
        return self.thumbnails.get(filename, None)

factory = RowFactory()

class FilterRule:
    def __init__(self, action, path, type_, value):
        self.action = action
        self.path = path
        self.type = type_
        self.value = value
        
    def __str__(self):
        return 'action=%s, path=%s, type=%s, value=%s' % (self.action, self.path, self.type, self.value)

    def __repr__(self):
        return str(self)
        
class Filter:
    ALLOW = 'ALLOW'
    HIDE = 'HIDE'
    DENY = 'DENY'

    TYPES_FILTER = lambda obj, value: isinstance(obj, value)
    EQ_FILTER = lambda obj, value: obj == value
    FILTERS = {'type':TYPES_FILTER, 'eq': EQ_FILTER, 'true': lambda obj, value: True}

    PREDEFINED_FILTERS = {}
    
    def __init__(self, rules = []):
        self.rules = rules #: list of filter rules
        
    def apply(self, obj):
        for rule in self.rules:
            filter_ = Filter.FILTERS[rule.type]
            filterObj = self.resolvePath(obj, rule.path)
            res = apply(filter_, (filterObj, rule.value))
            if res:
                return rule.action
        return None

    def resolvePath(self, obj, path):
        if not path:
            return obj
        elements = path.split('.')
        for elem in elements:
            obj = getattr(obj, elem)
        return obj

Filter.PREDEFINED_FILTERS['hide files'] = Filter([FilterRule(Filter.HIDE, None, 'type', ast.File)])
Filter.PREDEFINED_FILTERS['show globals'] = Filter([
        FilterRule(Filter.HIDE, None, 'type', ast.File),
        FilterRule(Filter.ALLOW, None, 'type', ast.ProgramUnit),
        FilterRule(Filter.HIDE, None, 'type', ast.TypeDeclaration),
        FilterRule(Filter.ALLOW, None, 'type', ast.Entity),
        FilterRule(Filter.HIDE, None, 'type', ast.Block),
        FilterRule(Filter.DENY, None, 'true', None)
        ])


class AstTree(BaseWidget):
    
    def __init__(self, root, astModel):
        LOG.debug('Generating AstTree with %s' % astModel)
        BaseWidget.__init__(self, 'ast_tree', 'ast_tree_outer', 
                actionFilters=[{'targetClasses': (ast.ASTObject,)}, {'category':'show-'}], menuName='object_menu')
        self.root = root
        self.astModel = astModel
        self.model = None #: GTK tree model for the AST tree  
        self.view = self.widget #: GTK tree view
        self.filters = {} #: enabled filters, name->filter
        
        column = gtk.TreeViewColumn("Name")
        cell = gtk.CellRendererPixbuf()
        column.pack_start(cell, False)
        column.add_attribute(cell, "pixbuf", 2)
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 0)
        column.add_attribute(cell, "foreground-gdk", 3)
        self.view.append_column(column)

        column = gtk.TreeViewColumn("Tags")
        cell = TagCellRenderer()
        column.pack_start(cell, False)
        column.set_cell_data_func(cell, cell.setCellData)
        self.view.append_column(column)

        self.view.connect("key-press-event", self._keyPress, None)
        self.view.connect("button-press-event", self._buttonPress)
        self.view.get_selection().connect("changed", self._selectionChanged, None)        
        self.view.connect("drag-data-get", self._dragDataGet)
        self.view.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, 
                [(INFO_TEXT.name, 0, INFO_TEXT.number),
                 (INFO_OBJECT_PATH.name, 0, INFO_OBJECT_PATH.number)],
                gtk.gdk.ACTION_COPY)
        self.model = gtk.TreeStore(str, object, gtk.gdk.Pixbuf, gtk.gdk.Color)
        self.view.set_model(self.model)
                
        event.manager.subscribeClass(self._objectChanged, ast.ASTObject)                
        event.manager.subscribeClass(self._objectChanged, project.Project)
        event.manager.subscribeClass(self._tagChanged, project.TagDict)
        event.manager.subscribeClass(self._tagTypeChanged, project.TagType)
        
        self.regenerateSidebarTree()
        
    def _selectionChanged(self, selection, param):
        model, iRow = selection.get_selected()
        if not model or not iRow:
            return
        obj = model[iRow][1]
        
    def regenerateSidebarTree(self):
        LOG.debug("Regenerating sidebar tree")
        self.model.clear()
        astModel = self.astModel
        self._generateSidebarTree(None, astModel and astModel.files or ())
        
    def _generateSidebarTree(self, iParent, astObjects):            
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "Generating for %s %d children" % \
                    (iParent and self.model[iParent][1] or '', len(astObjects)))
        for obj in astObjects:
            action = None
            for filterName, filter_ in self.filters.iteritems():
                action = filter_.apply(obj)
                # @todo: this must be OR operation, resolve several DENY, HIDE filters
                if action is not None: break
            if LOG.isEnabledFor(FINER):
                LOG.log(FINER, "Filter result for %s is %s" % (obj, action))
            if action==Filter.ALLOW or action is None:
                #data=[obj.getName(), obj, obj.getThumbnail(), gtk.gdk.color_parse("black")]
                data = factory.getRow(obj)
                iRow = self.model.append(iParent,data)
                self._generateSidebarTree(iRow, obj.getChildren())
            elif action==Filter.HIDE:
                self._generateSidebarTree(iParent, obj.getChildren())
        
    def _findInTree(self, obj):
        if hasattr(obj, "parent"):
            iParent = self._findInTree(obj.parent)
        else:
            iParent = None        
        iChild = self.model.iter_children(iParent)
        while iChild:
            childObj, = self.model.get(iChild, 1)
            if obj is childObj:
                return iChild
            iChild = self.model.iter_next(iChild)
        return iParent
        
    def _objectChanged(self, obj, _event, args, dargs):
        if _event==event.ADDED_TO_DIAGRAM:
            diagram, = args
            iObject = self._findInTree(obj)
            self.model[iObject][3] = gtk.gdk.color_parse("darkgreen")
        elif _event==event.REMOVED_FROM_DIAGRAM:
            diagram, = args
            iObject = self._findInTree(obj)
            self.model[iObject][3] = gtk.gdk.color_parse("black")
        elif _event==event.PROPERTY_CHANGED and obj==self.astModel.project:
            propertyName = args[0]
            if propertyName == 'astModel':
                # generate sidebar tree
                self.regenerateSidebarTree()
        
    def _tagChanged(self, tagDict, _event, args, dargs):
        obj = dargs['key']
        if tagDict.project==self.astModel.project:
            iter_ = self._findInTree(obj)
            path = self.model.get_path(iter_)
            self.model.row_changed(path, iter_)

    def _tagTypeChanged(self, tagType, _event, args, dargs):
        def changed(path, iter_):
            self.model.row_changed(path, iter_)
        gtkx.foreach_visible(self.view, self.model, changed)

    def selectObject(self, obj):
        iObject = self._findInTree(obj)
        if iObject:
            path = self.model.get_path(iObject)
            self.view.expand_to_path(path)
            self.view.get_selection().select_path(path)
            self.view.scroll_to_cell(path)    

    def _keyPress(self, widget, event, data):
        pass

    def _buttonPress(self, widget, event):
        if event.type==gtk.gdk._2BUTTON_PRESS:
            _model, iRow = self.view.get_selection().get_selected()
            obj = _model[iRow][1]
            if isinstance(obj, ast.File):
                self.root.showFile(self.astModel.project, obj)
                return True
            if hasattr(obj, 'location'):
                self.root.showFile(self.astModel.project, obj.getFile(), obj.location)
                return True
        return False
     
    def _dragDataGet(self, widget, context, data, info, timestamp):
        "Returns data for the GTK DnD protocol."
        model, iRow = self.view.get_selection().get_selected()
        obj = model[iRow][1]
        path = obj.model.getPath(obj)
        data.set(INFO_OBJECT_PATH.name, 0, pickle.dumps((obj.__class__,path)) )
        LOG.debug("GTK DnD dragDataGet with info=%d, path=%s"%(info, path))
        
    def filter_clicked(self, button):
        dialog = FilterDialog(self.filters)
        # show dialog
        result = dialog.run()
        if result > 0:
            self.filters = dialog.filters
            self.regenerateSidebarTree()
        dialog.destroy()

    @action.Action('follow-call', label='Follow call', sensitivePredicate=
                   lambda x,c: isinstance(x,ast.Call) or isinstance(x,ast.Statement) and x.type=='call')
    def _onFollowCall(self, astObj, context=None):
        astScope = astObj.model.getScope(astObj, original=True)
        model = astObj.model.basicModel
        scope = model.getObjectByASTObject(astScope)
        obj = model.getObjectByName(astObj.name.lower(), scope)
        if obj!=None and obj.astObjects:
            self.selectObject(obj.astObjects[0])
            self.updateHistory()
        
    def findLocationInTree(self, location):
        file_, line, column = location
        print location

    def getState(self):
        "Return selected AST object or None."
        model, iRow = self.view.get_selection().get_selected()
        if iRow==None:
            return None
        else:
            return model[iRow][1]

    def setState(self, state):
        self.selectObject(state)


class FilterDialog:
    FILTER_VALUES = {
        'eq': [lambda value: int(value), lambda value: float(value), lambda value: str(value)],
        'type': {'file': ast.File, 'program': ast.ProgramUnit, 'subprogram': ast.Subprogram}
        }
    
    def __init__(self, selectedFilters):
        self.filters = {} #! Filter objects by name
    
        wTree = gtk.glade.XML("astvisualizer.glade", 'astfilter_dialog')
        wTree.signal_autoconnect(self)
        self.wTree = wTree
        self.widget = wTree.get_widget('astfilter_dialog')
        
        # initialize dialog
        self.actionModel = gtk.ListStore(str) #: GTK tree model of the filter action combo box
        self.actionModel = wTree.get_widget('filter_action').get_model()

        self.typeModel = gtk.ListStore(str)
        wTree.get_widget('filter_type').set_model(self.typeModel)
        for type_ in Filter.FILTERS.keys():
            wTree.get_widget('filter_type').append_text(type_)

        self.pathModel = gtk.ListStore(str)
        wTree.get_widget('filter_object_path').set_model(self.pathModel)        
        map(wTree.get_widget('filter_object_path').append_text, ['parent'])
        
        self.valueModel = gtk.ListStore(str)
        wTree.get_widget('filter_value').set_model(self.valueModel)

        # initialize rules and filters view
        def createColumn(header, prop, cnum, view, ctype=None):
            column = gtk.TreeViewColumn(header)
            if ctype==bool:
                cell = gtk.CellRendererToggle()
                cell.set_property('activatable', True)
            else:            
                cell = gtk.CellRendererText()
            column.pack_start(cell, True)
            column.add_attribute(cell, prop, cnum)
            view.append_column(column)
            return cell, column

        self.rulesModel = gtk.ListStore(str,str,str,str,object) #: GTK list model for the rules of selected filter
        rulesView = wTree.get_widget('rules_view')
        rulesView.set_model(self.rulesModel)
        createColumn("Action", "text", 0, rulesView)
        createColumn("Object path", "text", 1, rulesView)
        createColumn("Filter type", "text", 2, rulesView)
        createColumn("Value", "text", 3, rulesView)
        
        self.filtersModel = gtk.ListStore(str, object, bool) #: GTK list model for the filters
        filtersView = wTree.get_widget('filters_view')
        filtersView.get_selection().connect('changed', self._filterRowSelected)
        filtersView.set_model(self.filtersModel)
        def toggled(button, path):
            state = self.filtersModel[path][2]
            self.filtersModel[path][2] = not state
        cell, column = createColumn(" ", "active", 2, filtersView, bool)
        cell.connect('toggled', toggled)
        createColumn("Name", "text", 0, filtersView)
        for filterName, filter_ in Filter.PREDEFINED_FILTERS.iteritems():
            self.filters[filterName] = filter_
            self.filtersModel.append((filterName, filter_, selectedFilters.has_key(filterName)))
                    
    def _showFilterRules(self, filter_):
        self.rulesModel.clear()
        if filter_ is not None:
            for rule in filter_.rules:
                row = (rule.action, rule.path, rule.type, str(rule.value), rule.value)
                self.rulesModel.append(row)
        
    def run(self):
        res = self.widget.run()
        if res > 0:
            self._createFilters()
            LOG.log(FINE, 'Found %d filters' % len(self.filters))
        return res
            
    def _createFilters(self):
        "After we exit dialog take the GUI filter list and create filters"
        filters = {}
        for row in iter(self.filtersModel):
            filterName, filter_, selected = row
            if selected:
                filters[filterName] = filter_
        self.filters = filters
    
    def destroy(self):
        return self.widget.destroy()

    def add_filter(self, button):
        "Add filter to the list"
        i = self.wTree.get_widget('filter_action').get_active()
        if i==-1:
            return # report error
        action = self.actionModel[i][0]

        path = self.wTree.get_widget('filter_object_path').get_active_text()

        i = self.wTree.get_widget('filter_type').get_active()
        if i==-1:
            return # report error
        type_ = self.typeModel[i][0]
        
        value = self.wTree.get_widget('filter_value').get_active_text()
        obj = self._getValue(type_, value)
        row = (action, path, type_, str(obj), obj)
        LOG.debug('Adding filter %s' % (row,))
        self.filtersModel.append(row)

    def _getValue(self, type_, key):
        "Cast value received from the UI"
        valFuns = FilterDialog.FILTER_VALUES[type_]
        if isinstance(valFuns, dict):
            # the value is just in the dictionary
            return valFuns[key]
        elif isinstance(valFuns, list):
            # the value is a list of lambdas
            for fun in valFuns:
                try:
                    value = fun(key)
                    return value
                except:
                    pass
                    
    def _filterRowSelected(self, obj):
        model, iRow = obj.get_selected()
        if iRow is None:
            self._showFilterRules(None)
        else:
            filterName = model[iRow][0]
            self._showFilterRules(self.filters[filterName])

class TagCellRenderer(gtk.GenericCellRenderer):

    def __init__(self, *args, **kvargs):
        gtk.GenericCellRenderer.__init__(self, *args, **kvargs)
        self._pixmaps = {}
        
    def _getPixmap(self, name, window):
        if not self._pixmaps.has_key(name):
            create_xpm = gtk.gdk.pixmap_create_from_xpm
            self._pixmaps[name] = create_xpm(window, None, 'data/thumbnails/%s' % name)

        return self._pixmaps[name][1]
        
    
    def on_get_size(self, widget, cell_area):
        tags = self.project.tags.get(self.obj, set())
        subTags = self.project.tags._subTags.get(self.obj, set())
        callTags = self.project.tags._callTags.get(self.obj, set())
        callSubTags = self.project.tags._callSubTags.get(self.obj, set())
        if not tags and not subTags and not callTags and not callSubTags:
            return 0,0,0,0
        return 0,0,16*(len(tags)+len(subTags)+len(callTags)+len(callSubTags)),5
        
    def on_render(self, window, widget, background_area, cell_area, expose_area, flags):
        tags = self.project.tags.get(self.obj, set())
        subTags = self.project.tags._subTags.get(self.obj, set())
        callTags = self.project.tags._callTags.get(self.obj, set())
        callSubTags = self.project.tags._callSubTags.get(self.obj, set())

        if not tags and not subTags and not callTags and not callSubTags:
            return

        gc = window.new_gc()
        
        gc.set_fill(gtk.gdk.SOLID)
        x,y,w,h = cell_area.x, cell_area.y, cell_area.width, cell_area.height
        #window.clear_area(*tuple(expose_area))

        for i,tag in enumerate(tags):
            color = tag.color
            gc.set_foreground(gc.get_colormap().alloc_color(color))
            window.draw_rectangle(gc, True, x+16*i,y,15,h)

        n = len(tags)
        #gc.set_fill(gtk.gdk.TILED)
        for i,tag in enumerate(subTags):
            color = tag.color
            gc.set_foreground(gc.get_colormap().alloc_color(color))
            window.draw_rectangle(gc, False, x+16*(n+i),y,15,h)

        # draw call tags
        gc.set_rgb_fg_color(gtk.gdk.Color())
        n = len(tags) + len(subTags)
        for i,tag in enumerate(callTags):
            color = tag.color
            gc.set_foreground(gc.get_colormap().alloc_color(color))
            gc.set_clip_mask(self._getPixmap('call_arrow.xpm', window=window))
            gc.set_clip_origin(x+16*(n+i),y)
            window.draw_rectangle(gc, True, x+16*(n+i),y,15,h)

        n = len(tags) + len(subTags) + len(callTags)
        for i,tag in enumerate(callSubTags):
            color = tag.color
            gc.set_foreground(gc.get_colormap().alloc_color(color))
            gc.set_clip_mask(self._getPixmap('call_arrow_hollow.xpm', window=window))
            gc.set_clip_origin(x+16*(n+i),y)
            window.draw_rectangle(gc, True, x+16*(n+i),y,15,h)

    def setCellData(self, column, cell, model, iter_):
        self.obj = model[iter_][1]
        self.project = self.obj.model.project

