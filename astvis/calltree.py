#!/usr/bin/env python

import logging
LOG = logging.getLogger("calltree")

import gtk
import pickle

from common import INFO_TEXT, INFO_OBJECT_NAME
from event import ADDED_TO_DIAGRAM, REMOVED_FROM_DIAGRAM

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
    
        black = gtk.gdk.color_parse("black")
        green = gtk.gdk.color_parse("darkgreen")
        
        iObj = self.model.append(None, (obj.name, obj, obj.getThumbnail(), 
                self.root.diagram.hasObject(obj) and green or black )) # color
        
        if not hasattr(obj,"callNames"):
            return
        
        for name in obj.callNames:
            if self.root.project.objects.has_key(name.lower()):
                callObj = self.root.project.objects[name.lower()]
                thumb = callObj.getThumbnail()
                color = self.root.diagram.hasObject(callObj) and green or black
            else:
                callObj = None
                thumb = None
                color = black
            self.model.append(iObj, (name, callObj, thumb, color))        

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
        
    def _objectChanged(self, event, args):
        if not self.model:
            return
        if event==ADDED_TO_DIAGRAM:
            obj, diagram = args
            iObjects = self._findInTree(obj)
            for iObject in iObjects:
                self.model[iObject][3] = gtk.gdk.color_parse("darkgreen")
        if event==REMOVED_FROM_DIAGRAM:
            obj, diagram = args
            iObjects = self._findInTree(obj)
            for iObject in iObjects:
                self.model[iObject][3] = gtk.gdk.color_parse("black")
        

