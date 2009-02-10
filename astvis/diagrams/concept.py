import logging
LOG=logging.getLogger(__name__)
from astvis.common import FINE, FINER, FINEST

from astvis.common import INFO_PROJECTS_ATTRPATH
from astvis import diagram
from astvis import gtkx
from astvis import event
from astvis.model import concept
from astvis.gaphasx import RoundedRectangleItem, RectangleItem, MorphBoundaryPort
from astvis.transfer import internalize
from gaphas.item import Line
from gaphas.connector import PointPort, LinePort, Handle, VariablePoint

import gtk
import pickle
import cairo

class ItemFactory(diagram.ItemFactory):
    def getDiagramItem(self, obj):
        if isinstance(obj, concept.Activity):
            item = ActivityItem(obj)
            item.object = obj
            return item
        elif isinstance(obj, concept.Data):
            item= DataItem(obj.name)
            item.object = obj
            return item
        elif isinstance(obj, concept.Flow):
            item = FlowLine()
            return item

class GeneralDiagram(diagram.Diagram):

    __gtkmodel__ = gtkx.GtkModel()

    def _setName(self, name): self._name = name
    name = property(lambda self: self._name, _setName)
    name = event.Property(name,'name')
    __gtkmodel__.appendAttribute('name')


    def __init__(self, name, project):
        diagram.Diagram.__init__(self, ItemFactory())
        self.project = project
        self._name = name

        event.manager.subscribeClass(self._notify, concept.Concept)

    def setupView(self, view):
        view.drag_dest_set(gtk.DEST_DEFAULT_MOTION|gtk.DEST_DEFAULT_DROP,
                           [(INFO_PROJECTS_ATTRPATH.name,0,INFO_PROJECTS_ATTRPATH.number)],
                           gtk.gdk.ACTION_COPY)
        view.connect("drag-data-received", self._dragDataRecv)

    def _dragDataRecv(self, widget, context, x, y, data, info, timestamp):
        LOG.debug("GTK DnD data_recv with info=%d"%info)
        if info==INFO_PROJECTS_ATTRPATH.number:
            attrpath = pickle.loads(data.data)
            obj = internalize(attrpath)
            if obj!=None:
                # get canvas coordinates
                m = cairo.Matrix(*widget.matrix)
                m.invert()
                cx, cy = m.transform_point(x,y)
                # add item
                item = self.add(obj, cx,cy)
                context.drop_finish(True, timestamp)
            else:
                context.drop_finish(False, timestamp)                
        else:
            context.drop_finish(False, timestamp)

    def _notify(self, obj, ev, args, dargs):
        if ev is event.PROPERTY_CHANGED and isinstance(obj, concept.Concept):
            if self._items.has_key(obj):
                item = self._items[obj]
                item.name = obj.name
                self._canvas.request_update(item)
            

class ActivityItem(RoundedRectangleItem):
    def __init__(self, obj):
        RoundedRectangleItem.__init__(self, obj.name)
        self.object = obj

        self.port = MorphBoundaryPort(VariablePoint((0.,0.)), self)
        self._ports.append(self.port)

    def draw(self, context):
        super(ActivityItem, self).draw(context)

class DataItem(RectangleItem):

    def __init__(self, label):
        RectangleItem.__init__(self, label)

        self.port = MorphBoundaryPort(VariablePoint((0.,0.)), self)
        self._ports.append(self.port)

class FlowLine(Line):

    def draw_head(self, context):
        cr = context.cairo
        cr.move_to(0,0)
        cr.line_to(8,5)
        cr.move_to(8,-5)
        cr.line_to(0,0)

