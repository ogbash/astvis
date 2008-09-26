#! /usr/bin/env python

import gaphas
from event import ADDED_TO_DIAGRAM, REMOVED_FROM_DIAGRAM
import event
from astvis.misc.list import ObservableList
import gtkx

# ItemFactory is excesive?
class ItemFactory:
    def getDiagramItem(self, obj):
        raise NotImplementedError("Must implement in subclass")

class Connector(object):
    def setup_diagram(self):
        raise NotImplementedError("Must implement in subclass")
    def teardown_diagram(self):
        raise NotImplementedError("Must implement in subclass")
    
class Diagram(object):
    "Functions required for diagrams"
    
    def __init__(self, factory):
        self._factory = factory
        self._canvas = gaphas.canvas.Canvas()
        self._items = {}
        self._connectors = set()

    def add(self, obj, x=0, y=0, item=None):
        if self._items.has_key(obj):
            return False

        if not item:    
            item = self._factory.getDiagramItem(obj)
        if item:
            self._items[obj] = item
            self._addItem(item, x, y)
            event.manager.notifyObservers(obj, ADDED_TO_DIAGRAM, (self,))
            return True
        return False

    def _addItem(self, item, x, y):
        self._canvas.add(item)
        item.matrix.translate(x,y)            
        self._canvas.update_matrix(item)
    
    def remove(self, obj):
        if self._items.has_key(obj):
            self._removeItem(self._items[obj])
            del self._items[obj]
            event.manager.notifyObservers(obj, REMOVED_FROM_DIAGRAM, (self,))    
            return True
        return False
    
    def _removeItem(self, item):
        self._canvas.remove(item)
    
    def hasObject(self, obj):
        return self._items.has_key(obj)
        
    def addConnector(self, connector):
        if connector in self._connectors:
            return False
        self._connectors.add(connector)
        connector.setup_diagram()
        return True
        
    def removeConnector(self, connector):
        if not connector in self._connectors:
            return False
        connector.teardown_diagram()
        self._connectors.remove(connector)
        return True
        
    def getCanvas(self):
        return self._canvas

    def setupView(self, view):
        pass

class DiagramList(ObservableList):
    __gtkmodel__ = gtkx.GtkModel()

    name = "Diagrams"
    __gtkmodel__.appendAttribute('name')    

    def __init__(self, project):
        list.__init__(self)
        self.project = project

    def __hash__(self,obj):
        return object.__hash__(self,obj)

    def __eq__(self, obj):
        return self is obj
        
    def __str__(self):
        return "<DiagramList size=%s, project=%s>" % (len(self), self.project)
