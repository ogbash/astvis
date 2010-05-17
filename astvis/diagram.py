#! /usr/bin/env python

import logging
LOG=logging.getLogger(__name__)
from astvis.common import FINE, FINER, FINEST

import gaphas
from event import ADDED_TO_DIAGRAM, REMOVED_FROM_DIAGRAM
from astvis import event, action
from astvis.misc.list import ObservableList
import gtkx
from astvis import gaphasx

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
        assert isinstance(factory, ItemFactory)
        
        self._factory = factory
        self._canvas = gaphas.canvas.Canvas()
        self._canvas.diagram = self
        self._items = {}
        self._connectors = {} # connection -> connector

    def add(self, obj, x=0, y=0, item=None):
        if self._items.has_key(obj):
            return False

        if not item:    
            item = self._factory.getDiagramItem(obj)
        if item:
            
            LOG.debug("Adding %s to diagram", item)
            self._items[obj] = item
            self._addItem(item, x, y)

            if hasattr(item, 'children'):
                LOG.log(FINER, "Adding %d children of %s", len(item.children), item)
                for child in item.children:
                    self._canvas.add(child,parent=item)
            
            event.manager.notifyObservers(obj, ADDED_TO_DIAGRAM, (self,))
            return True
        return False

    def _addItem(self, item, x, y):
        self._canvas.add(item)
        item.matrix.translate(x,y)            
        self._canvas.update_matrix(item)

    def getItem(self, obj):
        return self._items.get(obj, None)
    
    def remove(self, obj):
        if self._items.has_key(obj):
            LOG.debug("Removing %s (%s) from diagram", obj, self._items[obj])
            self._removeItem(self._items[obj])
            del self._items[obj]
            event.manager.notifyObservers(obj, REMOVED_FROM_DIAGRAM, (self,))    
            return True
        return False
    
    def _removeItem(self, item):
        self._canvas.remove(item)
    
    def hasObject(self, obj):
        return self._items.has_key(obj)
        
    def addConnector(self, connection, connector):
        if self._connectors.has_key(connection):
            return False
        LOG.debug("Adding connector %s to diagram", connector)
        self._connectors[connection] = connector
        connector.setup_diagram()
        return True
        
    def removeConnector(self, connection):
        if not self._connectors.has_key(connection):
            return None
        connector = self._connectors[connection]
        LOG.debug("Removing connector %s from diagram", connector)
        connector.teardown_diagram()
        del self._connectors[connection]
        return connector
        
    def getCanvas(self):
        return self._canvas

    def setupView(self, view):
        view.connect('focus-in-event', self._focusIn)
        
    def _focusIn(self, widget, ev):
        if self.gtkActionGroup!=None:
            action.manager.bringToFront(self.gtkActionGroup)
        

    def getDefaultTool(self):
        return gaphasx.DefaultTool()

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
