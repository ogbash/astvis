#! /usr/bin/env python

from astvis import action, core
from astvis.model import ast, flow

__all__=['DataflowService']

class DataflowService(core.Service):

    @action.Action('ast-reaching-definitions',"Reaching defs",targetClass=ast.ASTObject)
    def getReachingDefinitions(self, astNode, context=None):
        "@todo: This is just filler code, reimplement the function."
        
        localEntities = [] 
        
        for decl in astNode.declarationBlock.statements:
            localEntities.extend(decl.entities)

        localNames = map(lambda e:e.name, localEntities)

        return localNames

    def getActiveDefinitionsByBlock(self, block):
        """Return all references and calls in the control flow block.

        @type block: L{astvis.model.flow.Block}
        """
        
        # collect AST objects
        objs = []
        def cb(block):
            if isinstance(block, flow.BasicBlock):
                objs.extend(block.executions)

        block.itertree(cb)

        # find references in every AST object
        unknown = set()
        written = set()
        read = set()
        called = set()
        service = core.getService('ASTTreeWalker')
        for obj in objs:
            refs = service.getReferencesFrom(obj)
            for ref in refs:
                if isinstance(ref, ast.Statement) and ref.type=='call' \
                       or isinstance(ref, ast.Call):
                    called.add(ref.name.lower())
                else:
                    isA = ref.isAssignment()
                    if isA is None:
                        unknown.add(ref.name.lower())
                    elif isA:
                        written.add(ref.name.lower())
                    else:
                        read.add(ref.name.lower())
        print 'called = ', called
        print 'unknown = ', unknown
        print 'written = ', written
        print 'read = ', read
