#! /usr/bin/env python

import logging as _logging
from astvis.common import FINE, FINER, FINEST
LOG = _logging.getLogger(__name__)

import gtk
import pango
from astvis import action

class CodeView(gtk.TextView):

    @classmethod
    def getActionGroup(cls):
        if not hasattr(cls, 'ACTION_GROUP'):
            cls.ACTION_GROUP = action.ActionGroup(action.manager,
                                                  'codeview',
                                                  CodeView.getSelected,
                                                  contextClass=CodeView,
                                                  categories=['find'])
                                                  
        return cls.ACTION_GROUP        

    def __init__(self, root, file_, *args, **kvargs):
        gtk.TextView.__init__(self, *args, **kvargs)

        self.root = root
        self.file = file_
        self.set_editable(False)
        font = pango.FontDescription("Courier 12")
        self.modify_font(font)

        self.connect('populate-popup', self._populatePopup)

        self.gtkActionGroup = self.getActionGroup().createGtkActionGroup(self)

    def _populatePopup(self, textview, menu):
        print "Populate popup"
        self.getActionGroup().updateActions(self.gtkActionGroup, self.getSelected())
        action.generateMenu(self.gtkActionGroup, menu=menu)

    def getSelected(self):
        it = self.get_buffer().get_iter_at_mark(self.get_buffer().get_insert())
        loc = self.file, it.get_line()+1, it.get_line_offset()
        return loc
        
