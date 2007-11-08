#!/usr/bin/env python

import logging
LOG = logging.getLogger("calltree")
from common import FINE, FINER, FINEST

import gtk
import pickle

from common import INFO_TEXT, INFO_OBJECT_NAME
from event import ADDED_TO_DIAGRAM, REMOVED_FROM_DIAGRAM
import event
from model import ast

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

class CallTree:
    def __init__(self, root, view):
        self.root = root
        self.view = view
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
                [(INFO_TEXT[0], 0, INFO_TEXT[1]),
                 (INFO_OBJECT_NAME[0], 0, INFO_OBJECT_NAME[1])],
                gtk.gdk.ACTION_COPY)        

        self.model = gtk.TreeStore(str, object, gtk.gdk.Pixbuf, gtk.gdk.Color)
        self.view.set_model(self.model)
        #self.view.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        
        event.manager.subscribeClass(self._objectChanged, ast.ASTObject)
        
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
        project = obj.project
    
        black = gtk.gdk.color_parse("black")
        green = gtk.gdk.color_parse("darkgreen")
        
        data = factory.getRow(obj)
        data[3] = self.root.diagram.hasObject(obj) and green or black
        iObj = self.model.append(None, data)
        
        name = hasattr(obj, 'name') and obj.name.lower() or None
        if not name:
            return
        
        calleeNames = project.calleeNames.get(name, ())
        LOG.log(FINE, "Number of callees for %s: %d" %(obj, len(calleeNames)))
        for name in calleeNames:
            if project.astObjects.has_key(name.lower()):
                callObj = project.astObjects[name.lower()]
                data = factory.getRow(callObj)
                color = self.root.diagram.hasObject(callObj) and green or black
                data[3] = color
            else:
                data = (name, None, None, black)
            self.model.append(iObj, data)

        self.view.expand_row(self.model.get_path(iObj), False)        
        self.show()
        
    def _dragDataGet(self, widget, context, selection_data, info, timestamp):
        model, iRow = self.view.get_selection().get_selected()
        obj = model[iRow][1]
        if obj:
            data = (obj.__class__,obj.name)
        else:
            data = (None, model[iRow][0])
        selection_data.set(INFO_OBJECT_NAME[0], 0, pickle.dumps(data))
        
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
        

