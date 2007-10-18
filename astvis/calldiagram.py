#! /usr/bin/env python

from model import ProgramUnit, Subprogram
from model import ACTIVE_CHANGED
from gaphasx import EllipseItem, RectangleItem, MorphConstraint
import diagram
from common import OPTIONS

import gaphas

class CallDiagram(diagram.Diagram):

    def __init__(self):
        diagram.Diagram.__init__(self, CallDiagram.ItemFactory())

    class ItemFactory(diagram.ItemFactory):
        def getDiagramItem(self, obj):
            if isinstance(obj, ProgramUnit):
                item = RectangleItem(obj.name)
                item.object = obj
                return item
            elif isinstance(obj, Subprogram):
                item= SubprogramItem(obj)
                item.object = obj
                return item
                
#        def getDiagramConnector(self, relation):
#            if isinstance(relation, CallRelation):
#                connector = gaphas.item.Line()
#                connector.handles()[0].connectable=False
#                connector.handles()[-1].connectable=False        
#                connector.draw_head = _draw_head                
#                return connector
#            elif isinstance(relation, ContainerRelation):
#                connector = gaphas.item.Line()
#                connector.handles()[0].connectable=False
#                connector.handles()[-1].connectable=False        
#                return connector
                

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
        
    def add(self, obj, x, y):
        super(CallDiagram, self).add(obj, x, y)
        # TODO get all calls for obj and add connectors
        # TODO get all callers for obj and add connectors
        
    def remove(self, obj):
        # TODO get all calls for obj and remove connectors
        # TODO get all callers for obj and remove connectors
        super(CallDiagram, self).remove(obj)

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



