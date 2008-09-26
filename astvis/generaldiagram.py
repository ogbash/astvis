import logging
LOG=logging.getLogger(__name__)
from common import FINE, FINER, FINEST

from common import INFO_PROJECTS_ATTRPATH
from astvis import diagram
from astvis import gtkx
from astvis import event
from astvis.model import concept
from gaphasx import EllipseItem, RectangleItem
from astvis.transfer import internalize

import gtk
import pickle

class ItemFactory(diagram.ItemFactory):
    def getDiagramItem(self, obj):
        if isinstance(obj, concept.Activity):
            item = ActivityItem(obj.name)
            item.object = obj
            return item
        elif isinstance(obj, concept.Data):
            item= RectangleItem(obj.name)
            item.object = obj
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
            print obj



class ActivityItem(EllipseItem):
    def __init__(self, obj):
        EllipseItem.__init__(self, obj.name)
        self.object = obj

    def draw(self, context):
        super(SubprogramItem, self).draw(context)
