#! /usr/bin/env python

import logging as _logging
from astvis.common import FINE, FINER, FINEST
LOG = _logging.getLogger(__name__)

from astvis import action, core
from astvis import widgets

class CodeService(core.Service):

    @action.Action('find-in-ast-tree', 'Find in AST', contextClass=widgets.CodeView)
    def findInASTTree(self, location, context):
        file_, line, column = location
        astModel = file_.model
                    
        astViews = filter(lambda x: x.__class__.__name__=="AstTree", context.root.views.keys())
        if astViews:
            astView = astViews[0]

            obj = self._findObjectByLocation(file_, (line, column))
            if obj!=None:
                astView.selectObject(obj)

    def _findObjectByLocation(self, obj, loc):
        line, column = loc
        
        for child in  obj.getChildren():
            if child.location != None:
                begin = child.location.begin
                end = child.location.end
                if (begin.line<line or begin.line==line and begin.column<=column) and \
                   (end.line>line or end.line==line and end.column>column):
                    return self._findObjectByLocation(child, loc)
        else:
            return obj
