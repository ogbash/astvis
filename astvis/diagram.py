#! /usr/bin/env python

import gaphas
from event import ADDED_TO_DIAGRAM, REMOVED_FROM_DIAGRAM
import event

class ItemFactory:
    def getDiagramItem(self, obj):
        raise NotImplementedError("Must implement in subclass")
            
    def getDiagramConnector(self, relation):
        raise NotImplementedError("Must implement in subclass")

class Diagram(object):
    "Functions required for diagrams"
    
    def __init__(self, factory):
        self._factory = factory
        self._canvas = gaphas.canvas.Canvas()
        self._items = {}
        self._connectors = {}

    def add(self, obj, x=0, y=0):
        if self._items.has_key(obj):
            return False
    
        item = self._factory.getDiagramItem(obj)
        if item:
            self._items[obj] = item
            self._canvas.add(item)
            item.matrix.translate(x,y)            
            self._canvas.update_matrix(item)
        
            event.manager.notifyObservers(obj, ADDED_TO_DIAGRAM, (self,))
            return True
        return False
    
    def remove(self, obj):
        if self._items.has_key(obj):
            self._canvas.remove(self._items[obj])
            del self._items[obj]
            event.manager.notifyObservers(obj, REMOVED_FROM_DIAGRAM, (self,))
            return True
        return False
        
    def hasObject(self, obj):
        return self._items.has_key(obj)
        
    def addRelation(self, relation):
        if self._connectors.has_key(relation):
            return False

        items = map(lambda obj: self._items.get(obj, None), relation.getObjects())
        if None in items:
            return False
        
        connector = self._factory.getDiagramConnector(relation)
        self._connectors[relation] = connector
        self._canvas.add(connector)
        self._connectItems(items, connector)
        
    def removeRelation(self, relation):
        if self._connectors.has_key(relation):
            self._canvas.remove(self._connectors[relation])
            del self._connectors[relation]
            return True
        return False
        
    def getCanvas(self):
        return self._canvas

# exports

from calldiagram import *

