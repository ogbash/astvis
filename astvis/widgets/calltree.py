#!/usr/bin/env python

import logging
LOG = logging.getLogger("calltree")
from astvis.common import FINE, FINER, FINEST

from astvis.common import INFO_TEXT, INFO_OBJECT_PATH
from astvis.model import ast
from astvis import core, event
from astvis.event import ADDED_TO_DIAGRAM, REMOVED_FROM_DIAGRAM
from astvis.widgets.base import BaseWidget

import gtk
import pickle

class RowFactory:
    thumbnailFilenames = {ast.File: "data/thumbnails/file.png",
            ast.ProgramUnit: lambda obj: obj.type=='module' and "data/thumbnails/module.png"
                    or "data/thumbnails/program.png",
            ast.Subprogram: "data/thumbnails/subroutine.png",
            ast.Statement: lambda obj: obj.type=='call' and 'data/thumbnails/call.png' or None,
            ast.Call: "data/thumbnails/call.png"}
            
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

class CallTree(BaseWidget):
    def __init__(self, root, astTree=None):
        BaseWidget.__init__(self, 'call_tree', 'call_tree_outer')
        self.root = root
        self.view = self.widget
        self.hide()
        
        column = gtk.TreeViewColumn("Name")
        cell = gtk.CellRendererPixbuf()
        column.pack_start(cell, False)
        column.add_attribute(cell, "pixbuf", 2)
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 0)
        column.add_attribute(cell, "foreground-gdk", 3)

        self.view.append_column(column)

        # register events
        self.view.connect("key-press-event", self._keyPress, None)
        self.view.connect("button-press-event", self._buttonPress)        
        self.view.connect("drag-data-get", self._dragDataGet)
        self.view.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, 
                [(INFO_TEXT.name, 0, INFO_TEXT.number),
                 (INFO_OBJECT_PATH.name, 0, INFO_OBJECT_PATH.number)],
                gtk.gdk.ACTION_COPY)        

        self.model = gtk.TreeStore(str, object, gtk.gdk.Pixbuf, gtk.gdk.Color)
        self.view.set_model(self.model)
        #self.view.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        
        event.manager.subscribeClass(self._objectChanged, ast.ASTObject)
        
        if astTree!=None:
            astTree.view.get_selection().connect('changed', self._astTreeChanged)
            self._astTreeChanged(astTree.view.get_selection())
        
    def _keyPress(self, widget, event, data):
        print event
        
    def _buttonPress(self, widget, event):
        if event.type==gtk.gdk._2BUTTON_PRESS:
            model, iRow = self.view.get_selection().get_selected()
            obj = model[iRow][1]
            if obj:
                self.showObject(obj)
                return True
        return False
        
    def _astTreeChanged(self, selection):
        _model, iRow = selection.get_selected()
        if iRow!=None:
            astObj = _model[iRow][1]
            self.showObject(astObj)     

    def hide(self):
        #self.view.get_parent().hide() # scrolled window
        pass

    def show(self):
        self.view.get_parent().show() # scrolled window

    def _clearModel(self):
        def free(model, path, iRow):
            obj = model[iRow][1]
    
        self.model.foreach(free)
    
        self.model.clear()

    def showObject(self, obj):
        self._clearModel()
    
        black = gtk.gdk.color_parse("black")
        green = gtk.gdk.color_parse("darkgreen")
        
        data = factory.getRow(obj)
        data[3] = self.root.diagram.hasObject(obj) and green or black
        iObj = self.model.append(None, data)
        
        resolver = core.getService('ASTTreeWalker')
        references = resolver.getReferencesFrom(obj)
        LOG.log(FINE, "Number of references for %s: %d" %(obj, len(references)))
        for ref in references:
            # generate row for subprograms only
            if not (isinstance(ref, ast.Statement) and ref.type=='call'\
                    or isinstance(ref, ast.Call)):
                continue
            
            astModel = ref.getModel()
            astScope = astModel.getScope(ref)
            basicModel = astModel.basicModel
            scope = basicModel.getObjectByASTObject(astScope)
            callee = basicModel.getObjectByName(ref.name.lower(), scope)
          
            if callee is not None:
                callObj = callee.astObject
                data = factory.getRow(callObj)
                color = self.root.diagram.hasObject(callObj) and green or black
                data[3] = color
            else:
                data = (ref.name, None, None, black)
            self.model.append(iObj, data)

        self.view.expand_row(self.model.get_path(iObj), False)        
        self.show()
        
    def _dragDataGet(self, widget, context, selection_data, info, timestamp):
        "GTK DnD protocol"
        LOG.debug("GTK DnD dragDataGet with info=%d",info)
        model, iRow = self.view.get_selection().get_selected()
        obj = model[iRow][1]
        if obj:
            path = obj.model.getPath(obj)
            data = (obj.__class__,path)
        else:
            data = (None, model[iRow][0])
        selection_data.set(INFO_OBJECT_PATH.name, 0, pickle.dumps(data))
        
    def _findInTree(self, obj):    
        def each(model, path, iObj, data):
            childObj = self.model[iObj][1]
            if obj is childObj:
                data.append(iObj)
        
        data = []
        self.model.foreach(each, data)
        return data
        
    def _objectChanged(self, obj, event, args):
        if not self.model:
            return
        if event==ADDED_TO_DIAGRAM:
            diagram, = args
            iObjects = self._findInTree(obj)
            for iObject in iObjects:
                self.model[iObject][3] = gtk.gdk.color_parse("darkgreen")
        if event==REMOVED_FROM_DIAGRAM:
            diagram, = args
            iObjects = self._findInTree(obj)
            for iObject in iObjects:
                self.model[iObject][3] = gtk.gdk.color_parse("black")
        

