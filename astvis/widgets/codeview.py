#! /usr/bin/env python

import logging as _logging
from astvis.common import FINE, FINER, FINEST
LOG = _logging.getLogger(__name__)

import gtk
import pango
from astvis import action

class CodeView(gtk.TextView):

    def __init__(self, root, file_, *args, **kvargs):
        gtk.TextView.__init__(self, *args, **kvargs)

        self.root = root
        self.file = file_
        self.set_editable(False)
        font = pango.FontDescription("Courier 12")
        self.modify_font(font)

        self.connect('populate-popup', self._populatePopup)

        self.actionGroup = action.manager.createActionGroup('codeview', self, self.getSelected)

    def _populatePopup(self, textview, menu):
        self.actionGroup.updateActions(self.getSelected())
        action.generateMenu(self.actionGroup, menu=menu)

    def getSelected(self, context=None):
        it = self.get_buffer().get_iter_at_mark(self.get_buffer().get_insert())
        loc = self.file, it.get_line()+1, it.get_line_offset()
        return loc
        
