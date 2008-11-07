#! /usr/bin/env python

from astvis import action, core
from astvis.model import ast

__all__=['DataflowService']

class DataflowService(core.Service):

    @action.Action('ast-reaching-definitions',"Reaching defs",targetClass=ast.ASTObject)
    def getReachingDefinitions(self, astNode, context=None):
        print "reaching definitions"
