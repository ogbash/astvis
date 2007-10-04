#! /usr/bin/env python

from model import Observer, _DiagramItemSource
from model import ADDED_TO_CANVAS, REMOVED_FROM_CANVAS
import gaphasx
import gaphas

class ContainerRelation(Observer):
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
        if event==ADDED_TO_CANVAS:
            obj, canvas = args
            if obj is self._parent and self._child.getDiagramItem().canvas or \
                    obj is self._child and self._parent.getDiagramItem().canvas:
                canvas.add(self.line)
                self._connectItems(self._child.getDiagramItem(),
                        self._parent.getDiagramItem(),
                        self.line,
                        canvas)

        if event==REMOVED_FROM_CANVAS:
            obj, canvas = args
            if self.line.canvas:
                canvas.remove(self.line)
                
    
    def _connectItems(self, item1, item2, line, canvas):            
        handle1, handle2 = line.handles()[0], line.handles()[-1]
        constraint1 = gaphasx.MorphConstraint(gaphas.canvas.CanvasProjection(handle1, line), item1, 
                gaphas.canvas.CanvasProjection(item2.center, item2))
        constraint2 = gaphasx.MorphConstraint(gaphas.canvas.CanvasProjection(handle2, line), item2, 
                gaphas.canvas.CanvasProjection(item1.center, item1))
        
        def disconnect1():
            canvas.solver.remove_constraint(constraint1)
            handle1._connect_constraint = None
            handle1.connected_to = None            
            handle1.disconnect = None        
        handle1._connect_constraint = constraint1
        handle1.connected_to = item1
        handle1.disconnect = disconnect1
        canvas.solver.add_constraint(constraint1)

        def disconnect2():
            canvas.solver.remove_constraint(constraint2)
            handle2._connect_constraint = None
            handle2.connected_to = None            
            handle2.disconnect = None
        handle2._connect_constraint = constraint2
        handle2.connected_to = item2
        handle2.disconnect = disconnect2
        canvas.solver.add_constraint(constraint2)
    

def draw_head(context):
    cr = context.cairo
    cr.move_to(0,0)
    cr.line_to(5,5)
    cr.line_to(5,-5)
    cr.line_to(0,0)
    cr.move_to(5,0)

class CallRelation(Observer):
    "Calls relation for modules, subprograms"
    
    def __init__(self, caller, callee):
        self._caller = caller
        self._callee = callee
        self.line = gaphas.item.Line()
        self.line.handles()[0].connectable=False
        self.line.handles()[-1].connectable=False        
        self.line.draw_head = draw_head
        
        caller.addObserver(self)
        callee.addObserver(self)

    def notify(self, event, args):
        if event==ADDED_TO_CANVAS:
            obj, canvas = args
            if obj is self._caller and self._callee.getDiagramItem().canvas or \
                    obj is self._callee and self._caller.getDiagramItem().canvas:
                canvas.add(self.line)
                self._connectItems(self._callee.getDiagramItem(),
                        self._caller.getDiagramItem(),
                        self.line,
                        canvas)

        if event==REMOVED_FROM_CANVAS:
            obj, canvas = args
            if self.line.canvas:
                canvas.remove(self.line)


    def _connectItems(self, item1, item2, line, canvas):
        handle1, handle2 = line.handles()[0], line.handles()[-1]
        
        constraint1 = gaphasx.MorphConstraint(gaphas.canvas.CanvasProjection(handle1, line), item1, 
                gaphas.canvas.CanvasProjection(item2.center, item2))
        def disconnect1():
            canvas.solver.remove_constraint(constraint1)
            handle1._connect_constraint = None
            handle1.connected_to = None            
            handle1.disconnect = None                
        handle1._connect_constraint = constraint1
        handle1.connected_to = item1
        handle1.disconnect = disconnect1
        canvas.solver.add_constraint(constraint1)

        constraint2 = gaphasx.MorphConstraint(gaphas.canvas.CanvasProjection(handle2, line), item2, 
                gaphas.canvas.CanvasProjection(item1.center, item1))
        def disconnect2():
            canvas.solver.remove_constraint(constraint2)
            handle2._connect_constraint = None
            handle2.connected_to = None            
            handle2.disconnect = None                
        handle2._connect_constraint = constraint2
        handle2.connected_to = item2
        handle2.disconnect = disconnect2
        canvas.solver.add_constraint(constraint2)

