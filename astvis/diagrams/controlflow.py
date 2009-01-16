
"Control flow diagram."

import logging
LOG=logging.getLogger(__name__)
from astvis.common import FINE, FINER, FINEST

from astvis.common import *
from astvis import diagram
from astvis.model import ast, flow
from astvis.gaphasx import RectangleItem

import gtk
import pickle
import cairo
import gaphas.tool

class ItemFactory(diagram.ItemFactory):
    def getDiagramItem(self, obj):
        if isinstance(obj, flow.Block):
            return BlockItem(obj, obj.astObjects and str(obj.astObjects[-1]) or '')

class ControlFlowDiagram (diagram.Diagram):

    def __init__(self, name, project):
        diagram.Diagram.__init__(self, ItemFactory())
        self.project = project
        self.name = name
        self.flowModel = None

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
                self.add(self.flowModel.codeBlock, cx,cy)

                context.drop_finish(True, timestamp)
            else:
                context.drop_finish(False, timestamp)                
        else:
            context.drop_finish(False, timestamp)

    def getDefaultTool(self):
        tool = gaphas.tool.ToolChain()
        tool.append(gaphas.tool.HoverTool())
        tool.append(OpenCloseBlockTool())
        tool.append(gaphas.tool.ItemTool())
        tool.append(gaphas.tool.RubberbandTool())
        return tool

class BlockItem(RectangleItem):

    MIN_WIDTH=30
    MIN_HEIGHT=30

    def __init__(self, block, text):
        RectangleItem.__init__(self, text)
        self.block = block
        if block.subBlocks:
            self.children = [OpenCloseItem(self)]

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
                y += 20
            return True

