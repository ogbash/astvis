#! /usr/bin/env python

import gtk
from astvis import core

__all__ = ['ObjectList']

class ObjectList(gtk.ScrolledWindow):
    def __init__(self):
        gtk.ScrolledWindow.__init__(self)
                
        self.model = gtk.ListStore(str)
        self.view = gtk.TreeView(self.model)
        self.view.show()
        
        column = gtk.TreeViewColumn("Name")
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 0)
        self.view.append_column(column)
        
        self.add(self.view)
        
    def showObject(self, obj):
        self.model.clear()
        resolver = core.getService('ReferenceResolver')
        refs = resolver.getReferringObjects(obj)
        for ref in refs:
            print ref
            self.model.append((str(ref),))

