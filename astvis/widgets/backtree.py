#! /usr/bin/env python

import logging
LOG = logging.getLogger("backtree")
from astvis.common import FINE, FINER, FINEST

from astvis.model import basic, ast
from astvis import core, action
from astvis.widgets.base import BaseWidget

import gtk

class RowFactory:
    thumbnailFilenames = {basic.ProgramUnit: lambda obj: obj.type=='module' and "data/thumbnails/module.png"
                    or "data/thumbnails/program.png",
            basic.Subprogram: "data/thumbnails/subroutine.png",
            basic.Variable: "data/thumbnails/variable.png"}
            
    def __init__(self):
        self.thumbnails = {}    

    def getRow(self, data):
        obj,refs = data
        name = hasattr(obj,"name") and obj.name or str(obj)

        if refs!=None:
            s = "%s (%d refs)" % (name, len(refs))
        else:
            s = name
        return [s, (obj,refs) , self._getThumbnail(obj), gtk.gdk.color_parse("black")]

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

class BackCallTree(BaseWidget):
    UI_DESCRIPTION='''
    <popup name="backtree-popup">
      <menuitem action="show-ast-object-by-basic"/>
    </popup>
    '''

    @classmethod
    def getActionGroup(cls):
        if not hasattr(cls, 'ACTION_GROUP'):
            cls.ACTION_GROUP = action.ActionGroup(action.manager,
                                                  'back-tree',
                                                  contextAdapter=cls.getSelected,
                                                  contextClass=BackCallTree,
                                                  targetClasses=[basic.BasicObject],
                                                  categories=['show'])
        return cls.ACTION_GROUP

    def __init__(self, root, astTree=None):
        BaseWidget.__init__(self, 'back_call_tree', outerWidgetName='back_call_tree_outer',
                            menuName='backtree-popup')

        self.root = root
        self.view = self.widget
        self._object = None

        column = gtk.TreeViewColumn("Name")
        cell = gtk.CellRendererPixbuf()
        column.pack_start(cell, False)
        column.add_attribute(cell, "pixbuf", 2)
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 0)
        column.add_attribute(cell, "foreground-gdk", 3)
        
        self.view.append_column(column)

        self.model = gtk.TreeStore(str, object, gtk.gdk.Pixbuf, gtk.gdk.Color)
        self.view.set_model(self.model)

        # create refs list
        self.refsList = ReferencesList(self, self.wTree)
        self.view.get_selection().connect('changed', self.__selectionChanged)
                
    def __selectionChanged(self, selection):
        model, iRow = selection.get_selected()
        
        if iRow!=None:
            obj,refs = model[iRow][1]
            self.refsList.setReferences(refs)
        else:
            self.refsList.setReferences(None)

    def _clearModel(self):
        self._object = None
        
        def free(model, path, iRow):
            obj = model[iRow][1]
    
        self.model.foreach(free)
        self.model.clear()

    def showObject(self, obj):
        "@type: BasicObject"
        self._clearModel()
        self._object = obj
        self._addObject(obj, None, None, set())

    def _getSelected(self, selection):
        model, iRow = selection.get_selected()
        if iRow==None:
            return None
        return model[iRow][1][0]

    def _addObject(self, obj, refs, iParent, shown):
        
        data = factory.getRow((obj, refs))
        iObj = self.model.append(iParent, data)

        if obj in shown:
            return
        else:
            shown.add(obj)
        
        resolver = core.getService('ReferenceResolver')
        references = resolver.getReferringObjects(obj)

        if LOG.isEnabledFor(FINER):
            LOG.log(FINER, "Number of referring objects for %s: %d", obj, len(references.keys()))
        for refScope, refs in references.items():
            basicObj = refScope.model.basicModel.getObjectByASTObject(refScope)
            self._addObject(basicObj, refs, iObj, shown)

        self.view.expand_row(self.model.get_path(iObj), False)

    def getState(self):
        return self._object

    def setState(self, state):
        self.showObject(state)

class ReferencesList(BaseWidget):
    @classmethod
    def getActionGroup(cls):
        if not hasattr(cls, 'ACTION_GROUP'):
            cls.ACTION_GROUP = action.ActionGroup(action.manager,
                                                  'back-tree-refs',
                                                  contextClass=cls,
                                                  categories=['refs'])
        return cls.ACTION_GROUP

    def __init__(self, backCallTree, wTree):
        BaseWidget.__init__(self, 'back_call_tree_refs', outerWidgetName='back_call_tree_outer',
                            wTree=wTree)

        self.parent = backCallTree
        self.view = self.widget

        self.widget.hide()
        self.widget.connect("button-press-event", self.__buttonPress)

        column = gtk.TreeViewColumn("Location")
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 2)
        self.view.append_column(column)

        self.model = gtk.ListStore(str, object, str)
        self.view.set_model(self.model)

    def setReferences(self, refs):
        self.model.clear()

        if refs:
            # sort references
            sortedRefs = list(refs)
            def compare(x,y):
                return cmp(x.getFile(), y.getFile()) or \
                       cmp(x.location.begin.line, y.location.begin.line) or \
                       cmp(x.location.begin.column, y.location.begin.column)
            sortedRefs.sort(compare)
            
            # add to model
            for ref in sortedRefs:
                if ref.location!=None:
                    loc = "%s:%d,%d" % (ref.getFile().name,
                                        ref.location.begin.line,
                                        ref.location.begin.column)
                else:
                    loc = "%s" % ref.getFile().name
                self.model.append((str(ref),ref,loc))

            self.widget.show()
        else:
            self.widget.hide()

    def __buttonPress(self, widget, event):
        if event.type==gtk.gdk._2BUTTON_PRESS and event.button==1:
            _model, iRow = self.view.get_selection().get_selected()
            if iRow==None:
                return False
            obj = _model[iRow][1]
            if hasattr(obj, 'location'):
                self.parent.root.showFile(obj.model.project, obj.getFile(), obj.location)
                return True
        return False
