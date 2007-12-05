#! /usr/bin/env python

from model import ast, basic
from model.ast import ACTIVE_CHANGED
from common import *
from gaphasx import EllipseItem, RectangleItem, MorphConstraint
import diagram
import event
from event import ADDED_TO_DIAGRAM, REMOVED_FROM_DIAGRAM
from astvis import core

import gaphas

class CallDiagram(diagram.Diagram):

    def __init__(self, project = None):
        self.project = project
        diagram.Diagram.__init__(self, CallDiagram.ItemFactory())
        event.manager.subscribeClass(self._notify, ast.ASTObject)

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
                
    def _connectItems(self, items, connector):
        handles = connector.handles()[-1], connector.handles()[0] # tail --> head
        constraints = [None, None]
        
        constraints[0] = MorphConstraint(
                gaphas.canvas.CanvasProjection(handles[0], connector), items[0],
                gaphas.canvas.CanvasProjection(items[1].center, items[1]))
        def disconnect0():
            self._canvas.solver.remove_constraint(constraints[0])
            handles[0]._connect_constraint = None
            handles[0].connected_to = None            
            handles[0].disconnect = None                
        handles[0]._connect_constraint = constraints[0]
        handles[0].connected_to = items[0]
        handles[0].disconnect = disconnect0
        self._canvas.solver.add_constraint(constraints[0])

        constraints[1] = MorphConstraint(gaphas.canvas.CanvasProjection(handles[1], connector), items[1],
                gaphas.canvas.CanvasProjection(items[0].center, items[0]))
        def disconnect1():
            self._canvas.solver.remove_constraint(constraints[1])
            handles[1]._connect_constraint = None
            handles[1].connected_to = None            
            handles[1].disconnect = None                
        handles[1]._connect_constraint = constraints[1]
        handles[1].connected_to = items[1]
        handles[1].disconnect = disconnect1
        self._canvas.solver.add_constraint(constraints[1])
        
    def _notify(self, obj, event, args):
        """Notified when objects are added to or removed from diagram.
        
        @todo: reimplement calle[er]Names with ReferenceResolver"""
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
            refObjs = resolver.getReferringObjects(basicObj)
            for refObj in refObjs:
                caller = refObj
                if caller and self.hasObject(caller):
                    self.addConnector(CallConnector(caller, obj, self))            

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

    def _objectChanged(self, event, args):
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
        
    def notify(self, obj, event, args):
        if event==REMOVED_FROM_DIAGRAM:
            diagram, = args
            if not diagram==self._diagram or not obj in (self._parent, self._child):
                return
            self._diagram.removeConnector(self)

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

    def notify(self, obj, _event, args):
        if _event==REMOVED_FROM_DIAGRAM:
            diagram, = args
            if not diagram==self._diagram:
                return            
            diagram.removeConnector(self)
            #event.manager.unsubscribe(self, self._caller)
            #event.manager.unsubscribe(self, self._callee)


