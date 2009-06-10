#! /usr/bin/env python

from astvis import action, core
from astvis.model import ast, flow

class ControlflowService(core.Service):

    def __init__(self):
        core.Service.__init__(self)
        self._models = {}

    def getModel(self, astObj, context=None):
        if not self._models.has_key(astObj):
            flowModel = flow.ControlFlowModel(astObj)
            self._models[astObj] = flowModel
            
        return self._models[astObj]
