
import logging
LOG = logging.getLogger("concepttree")
from astvis.common import FINE, FINER, FINEST

from astvis.common import INFO_TEXT, INFO_PROJECTS_ATTRPATH

from astvis.model import concept
from astvis.widgets.base import BaseWidget
from astvis import event
from astvis.transfer import externalize, internalize

import gtk
import pickle

class ConceptTree(BaseWidget):
    
    def __init__(self, root, concepts):
        BaseWidget.__init__(self, 'concept_tree', 'concept_tree_outer',
                            categories=['concept', 'project-new-concept'],
                            targetClasses=[concept.Concept])
        self.root = root
        self.view = self.widget
        self.concepts = concepts

        self.treeModel = gtk.TreeStore(str,object)
        self.__fillTree()
        
        column = gtk.TreeViewColumn()
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, 'text', 0)
        self.view.append_column(column)

        self.view.set_model(self.treeModel)
        event.manager.subscribe(self._conceptsChanged, concepts)

        self.view.connect("drag-data-get", self._dragDataGet)
        self.view.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, 
                [(INFO_TEXT.name, 0, INFO_TEXT.number),
                 (INFO_PROJECTS_ATTRPATH.name, 0, INFO_PROJECTS_ATTRPATH.number)],
                gtk.gdk.ACTION_COPY)

        event.manager.subscribeClass(self._notify, concept.Concept)

    def _notify(self, obj, ev, args, dargs):
        if ev is event.PROPERTY_CHANGED and isinstance(obj, concept.Concept):
            #prop, detail, newval, oldval = args
            self.__fillTree()

    def _dragDataGet(self, widget, context, data, info, timestamp):
        "Returns data for the GTK DnD protocol."
        LOG.debug("GTK DnD dragDataGet with info=%d"%(info,))
        model, iRow = self.view.get_selection().get_selected()
        obj = model[iRow][1]
        if isinstance(obj, concept.Concept):
            extdata = externalize(obj)
            data.set(INFO_PROJECTS_ATTRPATH.name, 0, pickle.dumps(extdata))

    def _conceptsChanged(self, concepts, event_, args, dargs):
        self.__fillTree()

    def __fillTree(self):
        self.treeModel.clear()
        for concept in self.concepts:
            self.treeModel.append(None, (concept.name, concept))
        
