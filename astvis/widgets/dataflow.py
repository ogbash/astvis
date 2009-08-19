import logging
LOG = logging.getLogger("widgets.dataflow")
from astvis.common import FINE, FINER, FINEST

from astvis.widgets.base import BaseWidget
from astvis import action
from astvis.model import ast

import gtk

class UsedDefinitionsList(BaseWidget):
    @classmethod
    def getActionGroup(cls):
        if not hasattr(cls, 'ACTION_GROUP'):
            cls.ACTION_GROUP = action.ActionGroup(action.manager,
                                                  'usedef-list',
                                                  contextClass=UsedDefinitionsList,
                                                  contextAdapter=None,
                                                  targetClasses=[ast.ASTObject],
                                                  categories=['usedef','show'])
        return cls.ACTION_GROUP

    def __init__(self, root):
        super(UsedDefinitionsList, self).__init__('usedef_list')

        self.root = root
        self.diagram = None
        self.block = None
        self.usedDefs = None

        self.view = self.widget

        column = gtk.TreeViewColumn("")
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 0)

        self.view.append_column(column)

        self.model = gtk.TreeStore(str, object)
        self.view.set_model(self.model)

        self.view.get_selection().connect('changed', self._selectionChanged)

    def showData(self, diagram, block, usedDefs):
        self.diagram = diagram
        self.block = block
        self.usedDefs = usedDefs

        self.model.clear()
        names = list(usedDefs.keys())
        names.sort()
        for name in names:
            iName = self.model.append(None, (name, (name, usedDefs[name])))
            for key in usedDefs[name].keys():
                definition, defBlock, defIndex = key
                iDef = self.model.append(iName, (str(definition), \
                                                 (definition, (defBlock, defIndex, usedDefs[name][key]))))
                for reference in usedDefs[name][key]:
                    self.model.append(iDef, (str(reference), reference))

    def _selectionChanged(self, selection):
        _model, iRow = selection.get_selected()
        if iRow!=None:
            obj, values = _model[iRow][1]
            if isinstance(obj, ast.ASTObject):
                defBlock, defIndex, references = values
                self.diagram.selectBlocksByObject(obj)

