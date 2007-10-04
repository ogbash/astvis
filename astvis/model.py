#! /usr/bin/env python

import logging

from gaphasx import EllipseItem, RectangleItem
import gaphas
from common import OPTIONS

ADDED_TO_CANVAS = "added" # object, canvas
REMOVED_FROM_CANVAS = "removed" # object, canvas
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

class _DiagramItemSource:
    "Functions required for diagram drawing"

    def getDiagramItem(self):
        "item to be added"
        return None
        
    def addToCanvas(self, canvas):
        item = self.getDiagramItem()
        canvas.add(item)
        canvas.update_matrix(item)
        
        if isinstance(self,Observable):
            self.notifyObservers(ADDED_TO_CANVAS, (self, canvas,))
    
    def removeFromCanvas(self, canvas):
        item = self.getDiagramItem()
        canvas.remove(item)
        
        if isinstance(self,Observable):
            self.notifyObservers(REMOVED_FROM_CANVAS, (self, canvas,))
        
        
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
                Observable.LOG.warn("Exception during notify, %s", e)
                
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


class File(_BaseObject, _TreeRow, _DiagramItemSource):
    def __init__(self, xmlNode=None):
        _BaseObject.__init__(self)
        _TreeRow.__init__(self, "data/thumbnails/file.png")
        self.units = []

    def getChildren(self):
        return self.units
        
    def __str__(self):
        return "<File %s>" % self.name

class ProgramUnit(_BaseObject, _TreeRow, _DiagramItemSource, Observable):
    def __init__(self, parent = None):
        _BaseObject.__init__(self)
        Observable.__init__(self)
        _TreeRow.__init__(self, "data/thumbnails/module.png")
        self.parent = parent
        self.subprograms = []
        self.callNames = []

    def getChildren(self):
        return self.subprograms

    def getDiagramItem(self):
        if not hasattr(self, "_item"):
            self._item = RectangleItem(self.name)
            self._item.object = self
        return self._item

    def __str__(self):
        return "<ProgramUnit %s>" % self.name

class Subprogram(_BaseObject, _TreeRow, _DiagramItemSource, Observable):
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

    def getDiagramItem(self):
        if not hasattr(self, "_item"):
            self._item= SubprogramItem(self)
            self._item.object = self
        return self._item

    def __str__(self):
        return "<Subprogram %s>" % self.name
        
        
### diagram items

class SubprogramItem(EllipseItem):
    def __init__(self, obj):
        EllipseItem.__init__(self, obj.name)
        self.object = obj
        self.color = obj.getActive() and (0,0,0,1) or (.5,.5,.5,0)
        obj.addObserver(self._objectChanged)

    def draw(self, context):
        if OPTIONS["view MPI tags"] and \
                ("MPI caller" in self.object.tags or "indirect MPI caller" in self.object.tags):
            cr = context.cairo
            cr.save()
            if "MPI caller" in self.object.tags:
                cr.set_source_rgba(1,0.5,0,0.5)
            else:
                cr.set_source_rgba(1,1,0,0.5)
            gaphas.util.path_ellipse(cr, 0, 0, self.w, self.h)
            cr.fill()
            cr.restore()
        super(SubprogramItem, self).draw(context)

    def _objectChanged(self, event, args):
        if event==ACTIVE_CHANGED:
            self.color = self.object.getActive() and (0,0,0,1) or (.6,.6,.6,1)
            self.canvas.request_update(self)


