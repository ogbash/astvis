
"Control flow diagram."

import logging
LOG=logging.getLogger(__name__)
from astvis.common import FINE, FINER, FINEST

from astvis.common import *
from astvis import diagram
from astvis.model import ast

import gtk
import pickle
import cairo

class ItemFactory(diagram.ItemFactory):
    def getDiagramItem(self, obj):
        pass

class ControlFlowDiagram (diagram.Diagram):

    def __init__(self, name, project):
        diagram.Diagram.__init__(self, ItemFactory())
        self.project = project
        self.name = name

    def setupView(self, view):
        view.drag_dest_set(gtk.DEST_DEFAULT_MOTION|gtk.DEST_DEFAULT_DROP,
                [(INFO_OBJECT_PATH.name,0,INFO_OBJECT_PATH.number)],
                gtk.gdk.ACTION_COPY)
        view.connect("drag-data-received", self._dragDataRecv)

    def _dragDataRecv(self, widget, context, x, y, data, info, timestamp):
        LOG.debug("GTK DnD data_recv with info=%d"%info)
        if info==INFO_OBJECT_PATH.number:
            clazz, path = pickle.loads(data.data)
            if clazz==ast.ProgramUnit or clazz==ast.Subprogram:
                # get canvas coordinates
                m = cairo.Matrix(*widget.matrix)
                m.invert()
                cx, cy = m.transform_point(x,y)
                # add item
                obj = self.project.astModel.getObjectByPath(path)
                item = self.add(obj, cx,cy)
                context.drop_finish(True, timestamp)
            else:
                context.drop_finish(False, timestamp)                
        else:
            context.drop_finish(False, timestamp)

