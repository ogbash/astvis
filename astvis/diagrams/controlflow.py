
"Control flow diagram."

import logging
LOG=logging.getLogger('diagrams.controlflow')
from astvis.common import FINE, FINER, FINEST

from astvis.common import *
from astvis import diagram
from astvis.model import ast, flow
from astvis.gaphasx import RectangleItem, DiamondItem, MorphBoundaryPort
from astvis import event
from astvis.event import REMOVED_FROM_DIAGRAM

import gtk
import pickle
import cairo
import gaphas
import gaphas.tool
from gaphas.connector import PointPort, VariablePoint

class ItemFactory(diagram.ItemFactory):
    def getDiagramItem(self, obj):
        if isinstance(obj, (flow.StartBlock, flow.EndBlock)):
            return EntryExitItem(obj)
        elif isinstance(obj, flow.ConditionBlock):
            return ConditionBlockItem(obj, obj.astObjects and str(obj.astObjects[-1]) or '')            
        elif isinstance(obj, flow.Block):
            return BlockItem(obj, obj.astObjects and str(obj.astObjects[-1]) or '')

class ControlFlowDiagram (diagram.Diagram):

    def __init__(self, name, project):
        diagram.Diagram.__init__(self, ItemFactory())
        self.project = project
        self.name = name
        self.flowModel = None
        self._unboundConnections = set()
        self._connectTool = gaphas.tool.ConnectHandleTool()

    def setupView(self, view):
        view.drag_dest_set(gtk.DEST_DEFAULT_MOTION|gtk.DEST_DEFAULT_DROP,
                [(INFO_OBJECT_PATH.name,0,INFO_OBJECT_PATH.number)],
                gtk.gdk.ACTION_COPY)
        view.connect("drag-data-received", self._dragDataRecv)

    def _dragDataRecv(self, widget, context, x, y, data, info, timestamp):
        if self.flowModel != None:
            return
        
        LOG.debug("GTK DnD data_recv with info=%d"%info)
        if info==INFO_OBJECT_PATH.number:
            clazz, path = pickle.loads(data.data)
            if issubclass(clazz, ast.Code):
                # get canvas coordinates
                m = cairo.Matrix(*widget.matrix)
                m.invert()
                cx, cy = m.transform_point(x,y)
                # add item
                obj = self.project.astModel.getObjectByPath(path)
                self.flowModel = flow.ControlFlowModel(obj)
                self.add(self.flowModel.block, cx,cy)
                self._unboundConnections = self.flowModel.getConnections()
                self.bindConnections()

                context.drop_finish(True, timestamp)
            else:
                context.drop_finish(False, timestamp)                
        else:
            context.drop_finish(False, timestamp)

    def bindConnections(self):
        clConnections = self.flowModel.classifyConnectionsBy(self._unboundConnections, self._items.keys())
        if LOG.isEnabledFor(FINER):
            LOG.log(FINER, "%d unbound connections, %d classified connections",
                    len(self._unboundConnections), len(clConnections))

        newUnboundConnections = set()
        for key in clConnections.keys():
            fromBlock, toBlock = key
            if fromBlock is toBlock:
                self._items[fromBlock].connections.update(clConnections[key])
                if LOG.isEnabledFor(FINEST):
                    LOG.log(FINEST, "Internal block connection: %s", fromBlock)
            elif fromBlock!=None and toBlock!=None:
                self.addConnector(ControlFlowConnector(fromBlock, toBlock, self, clConnections[key]))
            else:
                if LOG.isEnabledFor(FINEST):
                    LOG.log(FINEST, "Missing block(s) for the connection: %s, %s; basic connections: %s",
                            fromBlock,
                            toBlock,
                            map(lambda cs: (str(cs[0]), str(cs[1])), clConnections[key]))
                newUnboundConnections.update(clConnections[key])
                
        self._unboundConnections = newUnboundConnections

    def removeConnector(self, connector):
        res = super(ControlFlowDiagram, self).removeConnector(connector)
        if res:
            if LOG.isEnabledFor(FINEST):
                LOG.log(FINEST, "Updating unbound connections with %s", connector.connections)
            self._unboundConnections.update(connector.connections)

    def getDefaultTool(self):
        tool = gaphas.tool.ToolChain()
        tool.append(gaphas.tool.HoverTool())
        tool.append(OpenCloseBlockTool())
        tool.append(gaphas.tool.ItemTool())
        tool.append(gaphas.tool.RubberbandTool())
        return tool

    def remove(self, obj):
        item = self.getItem(obj)
        res = super(ControlFlowDiagram, self).remove(obj)
        if res:
            self._unboundConnections.update(item.connections)
        return res


    def _connectItems(self, items, connectorItem):
        LOG.debug('connect %s', items)
        handles = connectorItem.handles()[-1], connectorItem.handles()[0] # tail --> head

        self._connectTool.connect_handle(connectorItem, handles[0], items[0], items[0].port)
        self._connectTool.connect_handle(connectorItem, handles[1], items[1], items[1].port)
        
class BlockItem(RectangleItem):

    MIN_WIDTH=30
    MIN_HEIGHT=30

    def __init__(self, block, text):
        RectangleItem.__init__(self, text)
        self.block = block
        if block.subBlocks:
            self.children = [OpenCloseItem(self)]
        self.connections = set()

        self.port = MorphBoundaryPort(VariablePoint((0.,0.)))
        self.port.connectable = False


class ConditionBlockItem(DiamondItem):

    def __init__(self, block, text):
        DiamondItem.__init__(self, text)
        self.block = block
        if block.subBlocks:
            self.children = [OpenCloseItem(self)]
        self.connections = set()

        self.port = MorphBoundaryPort(VariablePoint((0.,0.)))
        self.port.connectable = False

class EntryExitItem(RectangleItem):

    def __init__(self, block):
        RectangleItem.__init__(self, "")
        self.block = block
        if block.subBlocks:
            self.children = [OpenCloseItem(self)]
        self.connections = set()

        self.port = MorphBoundaryPort(VariablePoint((0.,0.)))
        self.port.connectable = False

    def draw(self, context):
        super(EntryExitItem, self).draw(context)
        cr = context.cairo
        w = max((self.w+self.PADX*2), self.MIN_WIDTH)
        h = max((self.h+self.PADY*2), self.MIN_HEIGHT)
        cr.move_to(-w/2, h/4)
        cr.line_to(-w/4, h/2)
        cr.move_to(w/4, h/2)
        cr.line_to(w/2, h/4)
        cr.move_to(w/2, -h/4)
        cr.line_to(w/4, -h/2)
        cr.move_to(-w/4, -h/2)
        cr.line_to(-w/2, -h/4)
        cr.stroke()

class OpenCloseItem(gaphas.item.Item):

    def __init__(self, openCloseItem):
        gaphas.item.Item.__init__(self)
        self.item = openCloseItem
    
    def draw(self, context):
        item = self.item
        cr = context.cairo
        w,h = max((item.w+item.PADX*2),item.MIN_WIDTH), \
              max((item.h+item.PADY*2),item.MIN_HEIGHT)
        x,y = -w/2, -h/2-10
        cr.move_to(x+5, y+1)
        cr.line_to(x+5, y+9)
        cr.stroke()
        cr.move_to(x+1, y+5)
        cr.line_to(x+9, y+5)
        cr.stroke()

class OpenCloseBlockTool(gaphas.tool.Tool):

    def on_button_press(self, context, event):
        ocItem = context.view.hovered_item
        if isinstance(ocItem, OpenCloseItem):
            diagram = ocItem.canvas.diagram
            matrix = ocItem.item.matrix
            x,y = matrix[4], matrix[5]
            subBlocks = ocItem.item.block.subBlocks
            diagram.remove(ocItem.item.block)
            for subBlock in subBlocks:
                diagram.add(subBlock, x, y)
                y += 50
            diagram.bindConnections()
            return True

class ControlFlowConnector(diagram.Connector, event.Observer):

    def __init__(self, fromBlock, toBlock, diagram, connections):
        self._fromBlock = fromBlock
        self._toBlock = toBlock
        self._diagram = diagram
        self._line = ControlFlowLine()
        self._line.handles()[0].connectable=False
        self._line.handles()[-1].connectable=False
        self.connections = set(connections)
        event.manager.subscribe(self, self._toBlock)
        event.manager.subscribe(self, self._fromBlock)
        
    def setup_diagram(self):
        self._diagram._canvas.add(self._line)
        self._diagram._connectItems((self._diagram._items[self._fromBlock],
                                     self._diagram._items[self._toBlock]),
                                    self._line)
        
    def teardown_diagram(self):
        self._diagram._canvas.remove(self._line)        

    def notify(self, obj, event, args, dargs):
        if event==REMOVED_FROM_DIAGRAM:
            diagram, = args
            if not diagram==self._diagram or not obj in (self._toBlock, self._fromBlock):
                return
            self._diagram.removeConnector(self)

    def __setstate__(self, state):
        self.__dict__.update(state)
        event.manager.subscribe(self, self._toBlock)
        event.manager.subscribe(self, self._fromBlock)        

class ControlFlowLine(gaphas.item.Line):
    def draw_head(self, context):
        super(ControlFlowLine, self).draw_head(context)
        cr = context.cairo
        cr.line_to(6,3)
        cr.move_to(6,-3)
        cr.line_to(0,0)
