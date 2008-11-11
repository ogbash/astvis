#! /usr/bin/env python

from astvis import action, core
from astvis.model import ast

__all__=['DataflowService']

class DataflowService(core.Service):

    @action.Action('ast-reaching-definitions',"Reaching defs",targetClass=ast.ASTObject)
    def getReachingDefinitions(self, astNode, context=None):
        
        localEntities = [] 
        
        for decl in astNode.declarationBlock.statements:
            localEntities.extend(decl.entities)

        localNames = map(lambda e:e.name, localEntities)

        return localNames
