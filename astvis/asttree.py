#!/usr/bin/env python

import logging
LOG = logging.getLogger("asttree")

from common import *
import gtk
import pickle

class AstTree:
    def __init__(self, root, view):
        self.root = root
        self.project = None
        self.model = None    
        self.view = view
        
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
        self.view.get_selection().connect("changed", self._selectionChanged, None)        
        self.view.connect("drag-data-get", self._dragDataGet)
        self.view.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, 
                [(INFO_TEXT[0], 0, INFO_TEXT[1]),
                 (INFO_OBJECT_NAME[0], 0, INFO_OBJECT_NAME[1])],
                gtk.gdk.ACTION_COPY)
        
    def _selectionChanged(self, selection, param):
        model, iRow = selection.get_selected()
        if not model or not iRow:
            return

        obj = model[iRow][1]
        self.root.callTree.showObject(obj)

    def setProject(self, project):
        self.project = project
        self.model = project.astModel
        self.view.set_model(self.model)
        
    def _keyPress(self, widget, event, data):
        pass
                            
    def _dragDataGet(self, widget, context, data, info, timestamp):
        model, iRow = self.view.get_selection().get_selected()
        obj = model[iRow][1]
        data.set(INFO_OBJECT_NAME[0], 0, pickle.dumps((obj.__class__,obj.name)) )

