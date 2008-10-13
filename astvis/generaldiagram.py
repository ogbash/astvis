import logging
LOG=logging.getLogger(__name__)
from common import FINE, FINER, FINEST

from common import INFO_PROJECTS_ATTRPATH
from astvis import diagram
from astvis import gtkx
from astvis import event
from astvis.model import concept
from gaphasx import RoundedRectangleItem, RectangleItem
from astvis.transfer import internalize
from gaphas.item import Line
from gaphas.connector import PointPort, LinePort, Handle

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

class ActivityItem(RoundedRectangleItem):
    def __init__(self, obj):
        RoundedRectangleItem.__init__(self, obj.name)
        self.object = obj

        for hname in ['left','right','top','bottom']:
            h_from = Handle(movable=False)
            h_from.x=-10
            self._handles.append(h_from)
            setattr(self,'_%s_from'%hname,h_from)
            h_to = Handle(movable=False)
            self._handles.append(h_to)
            setattr(self,'_%s_to'%hname,h_to)
            self._ports.append(LinePort(h_from, h_to))

    def draw(self, context):
        super(ActivityItem, self).draw(context)

    def pre_update(self, context):
        super(ActivityItem, self).pre_update(context)
        for hname, fx, fy, tx, ty in \
            [('left', -1, -1, -1, 1),
             ('right', 1, -1, 1, 1),
             ('top', -1, -1, 1, -1),
             ('bottom', -1, 1, 1, 1)]:
            getattr(self, '_%s_from'%hname).x = fx*(self.w+self.PADX)/2.0
            getattr(self, '_%s_from'%hname).y = fy*(self.h+self.PADY)/2.0
            getattr(self, '_%s_to'%hname).x = tx*(self.w+self.PADX)/2.0
            getattr(self, '_%s_to'%hname).y = ty*(self.h+self.PADY)/2.0

class DataItem(RectangleItem):

    def __init__(self, label):
        RectangleItem.__init__(self, label)

        for hname in ['left','right','top','bottom']:
            h = Handle()
            h.movable=False
            self._handles.append(h)
            setattr(self,'_%s'%hname,h)
            self._ports.append(PointPort(h))

    def pre_update(self, context):
        super(DataItem, self).pre_update(context)
        self._left.x = -(self.w+self.PADX)/2.0
        self._right.x = (self.w+self.PADX)/2.0
        self._top.y = -(self.h+self.PADY)/2.0
        self._bottom.y = (self.h+self.PADY)/2.0

class FlowLine(Line):

    def draw_head(self, context):
        cr = context.cairo
        cr.move_to(0,0)
        cr.line_to(8,5)
        cr.move_to(8,-5)
        cr.line_to(0,0)

