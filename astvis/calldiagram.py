#! /usr/bin/env python

import logging
LOG=logging.getLogger(__name__)
from common import FINE, FINER, FINEST

from model import ast, basic
from model.ast import ACTIVE_CHANGED
from common import *
from gaphasx import EllipseItem, RectangleItem, MorphConstraint
import diagram
import event
from event import ADDED_TO_DIAGRAM, REMOVED_FROM_DIAGRAM
from astvis import core
from astvis import gtkx

import gaphas

class DisconnectHandle(object):

    def __init__(self, canvas, items, handle):
        self.canvas = canvas
        self.items = items
        self.handle = handle

    def __call__(self):
        self.handle_disconnect()

    def handle_disconnect(self):
        canvas = self.canvas
        items = self.items
        handle = self.handle
        try:
            canvas.solver.remove_constraint(handle.connection_data)
        except KeyError:
            print 'constraint was already removed for', items, handle
            pass # constraint was alreasy removed
        handle.connection_data = None
        handle.connected_to = None
        # Remove disconnect handler:
        handle.disconnect = None


class ItemFactory(diagram.ItemFactory):
    def getDiagramItem(self, obj):
        if isinstance(obj, ast.ProgramUnit):
            item = RectangleItem(obj.name)
            item.object = obj
            return item
        elif isinstance(obj, ast.Subprogram):
            item= SubprogramItem(obj)
            item.object = obj
            return item

class CallDiagram(diagram.Diagram):

    __gtkmodel__ = gtkx.GtkModel()

    def _setName(self, name): self._name = name
    name = property(lambda self: self._name, _setName)
    name = event.Property(name,'name')
    __gtkmodel__.appendAttribute('name')


    def __init__(self, name, project):
        diagram.Diagram.__init__(self, ItemFactory())
        self.project = project
        self._name = name
        event.manager.subscribeClass(self._notify, ast.ASTObject)        
                
    def _connectItems(self, items, connector):
        LOG.debug('connect %s', items)
        handles = connector.handles()[-1], connector.handles()[0] # tail --> head

        for i in xrange(2):
            constraint = MorphConstraint(
                gaphas.canvas.CanvasProjection(handles[i], connector),
                items[i],
                gaphas.canvas.CanvasProjection(items[1-i].center, items[1-i]))
            handles[i].connection_data = constraint
            handles[i].connected_to = items[i]
            handles[i].disconnect = DisconnectHandle(self._canvas, items, handles[i])
            
            self._canvas.solver.add_constraint(constraint)
        
    def _notify(self, obj, event, args, dargs):
        """Notified when objects are added to or removed from diagram.

        @todo: reimplement calle[er]Names with ReferenceResolver"""
        
        LOG.debug('%s', obj)
        if event==ADDED_TO_DIAGRAM and args[0]==self:
            # add container connector
            if self.hasObject(obj.parent):
                self.addConnector(ContainerConnector(obj.parent, obj, self))
            for child in obj.getChildren():
                if self.hasObject(child):
                    self.addConnector(ContainerConnector(obj, child, self))
            # get all calls/callers for obj and add connectors
            resolver = core.getService('ReferenceResolver')

            refObjs = resolver.getReferencedObjects(obj)            
            for refObj in refObjs:
                if not isinstance(refObj, (basic.ProgramUnit, basic.Subprogram)):
                    continue
                callee = refObj.astObject
                if callee and self.hasObject(callee):
                    self.addConnector(CallConnector(obj, callee, self))            

            basicObj = obj.model.basicModel.getObjectByASTObject(obj)
            refObjs = resolver.getReferringObjects(basicObj).keys()
            for refObj in refObjs:
                caller = refObj
                if caller and self.hasObject(caller):
                    self.addConnector(CallConnector(caller, obj, self))
                    
    def __setstate__(self, state):
        self.__dict__.update(state)
        event.manager.subscribeClass(self._notify, ast.ASTObject)        

def _draw_head(context):
    cr = context.cairo
    cr.move_to(0,0)
    cr.line_to(5,5)
    cr.line_to(5,-5)
    cr.line_to(0,0)
    cr.move_to(5,0)

### diagram items

class SubprogramItem(EllipseItem):
    def __init__(self, obj):
        EllipseItem.__init__(self, obj.name)
        self.object = obj
        self.color = obj.getActive() and (0,0,0,1) or (.5,.5,.5,0)

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

    def _objectChanged(self, obj, event, args, dargs):
        if event==ACTIVE_CHANGED:
            self.color = self.object.getActive() and (0,0,0,1) or (.6,.6,.6,1)
            self.canvas.request_update(self)

# connectors

class ContainerConnector(diagram.Connector, event.Observer):
    "Parent-child relation for modules, subprograms"
    
    def __init__(self, parent, child, _diagram):
        diagram.Connector.__init__(self)
        self._diagram = _diagram
        self._parent = parent
        self._child = child
        self._line = gaphas.item.Line()
        self._line.handles()[0].connectable=False
        self._line.handles()[-1].connectable=False
        event.manager.subscribe(self, self._parent)
        event.manager.subscribe(self, self._child)

    def setup_diagram(self):
        self._diagram._canvas.add(self._line)
        self._diagram._connectItems((self._diagram._items[self._parent], self._diagram._items[self._child]), self._line)
        
    def teardown_diagram(self):
        self._diagram._canvas.remove(self._line)        
        
    def notify(self, obj, event, args, dargs):
        if event==REMOVED_FROM_DIAGRAM:
            diagram, = args
            if not diagram==self._diagram or not obj in (self._parent, self._child):
                return
            self._diagram.removeConnector(self)

    def __setstate__(self, state):
        self.__dict__.update(state)
        event.manager.subscribe(self, self._parent)
        event.manager.subscribe(self, self._child)        

class CallConnector(diagram.Connector, event.Observer):
    "Calls relation for modules, subprograms"
    
    def __init__(self, caller, callee, diagram):
        self._diagram = diagram
        self._caller = caller
        self._callee = callee        
        self._line = gaphas.item.Line()
        self._line.handles()[0].connectable=False
        self._line.handles()[-1].connectable=False
        self._line.draw_head = _draw_head
        event.manager.subscribe(self, self._caller)
        event.manager.subscribe(self, self._callee)

    def setup_diagram(self):
        self._diagram._canvas.add(self._line)
        self._diagram._connectItems((self._diagram._items[self._caller], self._diagram._items[self._callee]), self._line)
        
    def teardown_diagram(self):
        self._diagram._canvas.remove(self._line)

    def notify(self, obj, _event, args, dargs):
        if _event==REMOVED_FROM_DIAGRAM:
            diagram, = args
            if not diagram==self._diagram:
                return            
            diagram.removeConnector(self)
            #event.manager.unsubscribe(self, self._caller)
            #event.manager.unsubscribe(self, self._callee)


    def __setstate__(self, state):
        self.__dict__.update(state)
        event.manager.subscribe(self, self._caller)
        event.manager.subscribe(self, self._callee)        
