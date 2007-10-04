#! /usr/bin/env python

import logging

import gaphas
from common import OPTIONS
from common import ADDED_TO_DIAGRAM, REMOVED_FROM_DIAGRAM

ACTIVE_CHANGED = "active"
SHOW = "show" # object,

# help classes and interfaces

class _TreeRow:
    "Helper functions for GtkTreeModel"

    def __init__(self, imageFile=None):
        if imageFile:
            import gtk.gdk
            self._thumbnail = gtk.gdk.pixbuf_new_from_file_at_size(imageFile, 16, 16)            

    def getName(self):
        return hasattr(self,"name") and self.name or "{noname}"

    def getChildren(self):
        "List of element children"
        return []

    def getThumbnail(self):
        "Thumbnail to be shown in GtkTreeView for this element"
        return hasattr(self,"_thumbnail") and self._thumbnail or None


# observer

class Observable:
    LOG = logging.getLogger("Observable")

    "Observable object"
    def __init__(self):
        self.__observers = set()

    def notifyObservers(self, event, args):
        for observer in self.__observers:
            try:
                if isinstance(observer,Observer):
                    observer.notify(event, args)
                else:
                    observer(event,args)
            except(Exception), e:
                Observable.LOG.warn("Exception during notify, %s", e, exc_info=True)
                
    def addObserver(self, observer):
        self.__observers.add(observer)
        
    def removeObserver(self, observer):
        if observer in self.__observers:
            self.__observers.remove(observer)
    
class Observer:
    "Interface for observers"
    def notify(self, event, args):
        pass

# basic model classes

class _BaseObject:
    def __init__(self):
        self.__active = True
        self.tags = set()
        
    def setActive(self, active):
        prevActive = self.__active
        self.__active = active
        if not prevActive==active and isinstance(self, Observable):
            self.notifyObservers(ACTIVE_CHANGED, (active,))
        
    def getActive(self):
        return self.__active


class File(_BaseObject, _TreeRow):
    def __init__(self, xmlNode=None):
        _BaseObject.__init__(self)
        _TreeRow.__init__(self, "data/thumbnails/file.png")
        self.units = []

    def getChildren(self):
        return self.units
        
    def __str__(self):
        return "<File %s>" % self.name

class ProgramUnit(_BaseObject, _TreeRow, Observable):
    def __init__(self, parent = None):
        _BaseObject.__init__(self)
        Observable.__init__(self)
        _TreeRow.__init__(self, "data/thumbnails/module.png")
        self.parent = parent
        self.subprograms = []
        self.callNames = []

    def getChildren(self):
        return self.subprograms

    def __str__(self):
        return "<ProgramUnit %s>" % self.name

class Subprogram(_BaseObject, _TreeRow, Observable):
    def __init__(self, parent = None):
        " - parent: program unit or subroutine where this sub belongs"
        _BaseObject.__init__(self)
        Observable.__init__(self)
        _TreeRow.__init__(self, "data/thumbnails/subroutine.png")
        self.parent = parent
        self.subprograms = []
        self.callNames = []

    def getChildren(self):
        return self.subprograms

    def __str__(self):
        return "<Subprogram %s>" % self.name

# relations

class Relation(Observer):
    def getObjects(self):
        raise NotImplementedError("Must implement in subclass")

class ContainerRelation(Relation):
    "Parent-child relation for modules, subprograms"
    
    def __init__(self, parent, child):
        self._parent = parent
        self._child = child
        self.line = gaphas.item.Line()
        self.line.handles()[0].connectable=False
        self.line.handles()[-1].connectable=False
        
        parent.addObserver(self)
        child.addObserver(self)

    def notify(self, event, args):
        if event==ADDED_TO_DIAGRAM:
            obj, diagram = args
            diagram.addRelation(self)

        if event==REMOVED_FROM_DIAGRAM:
            obj, diagram = args
            diagram.removeRelation(self)
            
    def getObjects(self):
        return self._parent, self._child

class CallRelation(Relation):
    "Calls relation for modules, subprograms"
    
    def __init__(self, caller, callee):
        self._caller = caller
        self._callee = callee        
        caller.addObserver(self)
        callee.addObserver(self)

    def notify(self, event, args):
        if event==ADDED_TO_DIAGRAM:
            obj, diagram = args
            diagram.addRelation(self)

        if event==REMOVED_FROM_DIAGRAM:
            obj, diagram = args
            diagram.removeRelation(self)

    def getObjects(self):
        return self._caller, self._callee

