import logging
LOG=logging.getLogger(__name__)
from common import FINE, FINER, FINEST

from astvis import diagram
from astvis import gtkx
from astvis import event
from astvis.model import concept
from gaphasx import EllipseItem, RectangleItem

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

class ActivityItem(EllipseItem):
    def __init__(self, obj):
        EllipseItem.__init__(self, obj.name)
        self.object = obj

    def draw(self, context):
        super(SubprogramItem, self).draw(context)
