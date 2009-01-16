
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

class ItemFactory(diagram.ItemFactory):
    def getDiagramItem(self, obj):
        if isinstance(obj, flow.Block):
            return RectangleItem(obj.astObjects and str(astObjects[-1]) or ' ')

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
                item = self.add(self.flowModel.codeBlock, cx,cy)
                context.drop_finish(True, timestamp)
            else:
                context.drop_finish(False, timestamp)                
        else:
            context.drop_finish(False, timestamp)


class BlockItem(RectangleItem):
    pass
