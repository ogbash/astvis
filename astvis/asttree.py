#!/usr/bin/env python

"""Abstract syntax tree module."""

import logging
LOG = logging.getLogger("asttree")
from common import FINE, FINER, FINEST

from common import *
import gtk
import pickle
from model import ast
import event
import project

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
        
class Filter:
    ALLOW = 'ALLOW'
    HIDE = 'HIDE'
    DENY = 'DENY'

    TYPES_FILTER = lambda obj, value: isinstance(obj, value)
    EQ_FILTER = lambda obj, value: obj == value
    FILTERS = {'type':TYPES_FILTER, 'eq': EQ_FILTER}

    hideFilesRule = FilterRule(DENY, None, 'type', ast.File)
    
    def __init__(self):
        self.filters = [Filter.hideFilesRule] #
        
    def apply(self, obj):
        for rule in self.filters:
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

class AstTree:
    
    def __init__(self, root, view):
        self.root = root
        self.project = None
        self.model = None    
        self.view = view
        self.filter = Filter()
        
        column = gtk.TreeViewColumn("Name")
        cell = gtk.CellRendererPixbuf()
        column.pack_start(cell, False)
        column.add_attribute(cell, "pixbuf", 2)
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 0)
        column.add_attribute(cell, "foreground-gdk", 3)
        self.view.append_column(column)

        self.view.connect("key-press-event", self._keyPress, None)
        self.view.connect("button-press-event", self._buttonPress)
        self.view.connect_after("popup-menu", self._popupMenu)
        self.view.get_selection().connect("changed", self._selectionChanged, None)        
        self.view.connect("drag-data-get", self._dragDataGet)
        self.view.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, 
                [(INFO_TEXT.name, 0, INFO_TEXT.number),
                 (INFO_OBJECT_PATH.name, 0, INFO_OBJECT_PATH.number)],
                gtk.gdk.ACTION_COPY)
        self.model = gtk.TreeStore(str, object, gtk.gdk.Pixbuf, gtk.gdk.Color)
                
        event.manager.subscribeClass(self._objectChanged, ast.ASTObject)                
        event.manager.subscribeClass(self._objectChanged, project.Project)
        
    def _selectionChanged(self, selection, param):
        model, iRow = selection.get_selected()
        if not model or not iRow:
            return

        obj = model[iRow][1]
        self.root.callTree.showObject(obj)
        basicObj = obj.model.basicModel.getObjectByASTObject(obj)
        self.root.backCallTree.showObject(basicObj)

    def setProject(self, project):
        self.project = project
        self.view.set_model(self.model)
        
        # generate sidebar tree
        astModel = self.project.astModel
        self._generateSidebarTree(None, astModel and astModel.files or ())
        
    def _generateSidebarTree(self, iParent, astObjects):            
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "Generating for %s %d children" % \
                    (iParent and self.model[iParent][1] or '', len(astObjects)))
        for obj in astObjects:
            action = self.filter.apply(obj)
            if LOG.isEnabledFor(FINER):
                LOG.log(FINER, "Filter result for %s is %s" % (obj, action))
            if action is Filter.ALLOW or action is None:
                #data=[obj.getName(), obj, obj.getThumbnail(), gtk.gdk.color_parse("black")]
                data = factory.getRow(obj)
                iRow = self.model.append(iParent,data)
                self._generateSidebarTree(iRow, obj.getChildren())
            else:
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
        
    def _objectChanged(self, obj, _event, args):
        if _event==event.ADDED_TO_DIAGRAM:
            diagram, = args
            iObject = self._findInTree(obj)
            self.model[iObject][3] = gtk.gdk.color_parse("darkgreen")
        elif _event==event.REMOVED_FROM_DIAGRAM:
            diagram, = args
            iObject = self._findInTree(obj)
            self.model[iObject][3] = gtk.gdk.color_parse("black")
        elif _event==event.ASTMODEL_CHANGED and obj==self.project:
            # generate sidebar tree
            self.model.clear()
            astModel = self.project.astModel
            self._generateSidebarTree(None, astModel and astModel.files or ())
        

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
                self.root.showFile(obj)
                return True
            if hasattr(obj, 'location'):
                self.root.showFile(obj.getFile(), obj.location)
                return True

        if event.type==gtk.gdk.BUTTON_PRESS and event.button==3:
            self._popupMenu(widget, event.get_time())
            return True
        
        return False

    def _popupMenu(self, widget, time=0):
        _model, iRow = self.view.get_selection().get_selected()
        obj = _model[iRow][1]
        if obj is not None:
            self.menu.popup(None, None, None, 3, time)
     
    def _dragDataGet(self, widget, context, data, info, timestamp):
        "Returns data for the GTK DnD protocol."
        model, iRow = self.view.get_selection().get_selected()
        obj = model[iRow][1]
        path = obj.model.getPath(obj)
        data.set(INFO_OBJECT_PATH.name, 0, pickle.dumps((obj.__class__,path)) )
        LOG.debug("GTK DnD dragDataGet with info=%d, path=%s"%(info, path))
        
    def filter_clicked(self, button):
        dialog = FilterDialog(self.filter.filters)
        # show dialog
        result = dialog.run()
        dialog.destroy()
        print result
        
class FilterDialog:
    FILTER_VALUES = {
        'eq': [lambda value: int(value), lambda value: float(value), lambda value: str(value)],
        'type': {'file': ast.File, 'program': ast.ProgramUnit, 'subprogram': ast.Subprogram}
        }
    
    def __init__(self, filters):
        wTree = gtk.glade.XML("astvisualizer.glade", 'astfilter_dialog')
        wTree.signal_autoconnect(self)
        self.wTree = wTree
        self.widget = wTree.get_widget('astfilter_dialog')
        
        # initialize dialog
        self.actionModel = gtk.ListStore(str)
        self.actionModel = wTree.get_widget('filter_action').get_model()

        self.typeModel = gtk.ListStore(str)
        wTree.get_widget('filter_type').set_model(self.typeModel)
        for type_ in Filter.FILTERS.keys():
            wTree.get_widget('filter_type').append_text(type_)

        self.pathModel = gtk.ListStore(str)
        wTree.get_widget('filter_object_path').set_model(self.pathModel)        
        wTree.get_widget('filter_object_path').append_text('')
        wTree.get_widget('filter_object_path').append_text('parent')
        
        self.valueModel = gtk.ListStore(str)
        wTree.get_widget('filter_value').set_model(self.valueModel)

        # initialize filters view
        filtersView = wTree.get_widget('filters')

        column = gtk.TreeViewColumn("Action")
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 0)
        filtersView.append_column(column)
        column = gtk.TreeViewColumn("Object path")
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 1)
        filtersView.append_column(column)
        column = gtk.TreeViewColumn("Filter type")
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 2)
        filtersView.append_column(column)
        column = gtk.TreeViewColumn("Value")
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 3)
        filtersView.append_column(column)
        
        self.filtersModel = gtk.ListStore(str,str,str,str)
        for filter_ in filters:
            row = (filter_.action, filter_.path, filter_.type, filter_.value)
            self.filtersModel.append(row)
        filtersView.set_model(self.filtersModel)
        filtersView.show()
        
    def run(self):
        self.widget.run()
    
    def destroy(self):
        self.widget.destroy()

    def add_filter(self, button):
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
        #value = FilterDialog.FILTER_VALUES[type_][value]
    
        row = (action, path, type_, value)
        LOG.debug('Adding filter %s' % (row,))
        self.filtersModel.append(row)

