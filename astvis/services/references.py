#! /usr/bin/env python

import logging
LOG = logging.getLogger('references')

from astvis.model import ast
from astvis import core

class ReferenceResolver(core.Service):

    def __init__(self):
        self._caches = {} #: basic model -> reference cache

    def getReferencedObjects(self, astScope):
        model = astScope.model.basicModel
        if not self._caches.has_key(model):
            cache = self._collectReferences(model)
            self._caches[model] = cache
            #model._cache=cache
        cache = self._caches[model]
        return cache.references.get(astScope, ())
        
    def getReferringObjects(self, obj):
        """@type obj: L{BasicObject}
        @param obj: object to find references to"""
        model = obj.model
        if not self._caches.has_key(model):
            cache = self._collectReferences(model)
            self._caches[model] = cache
            #model._cache=cache
        cache = self._caches[model]
        return cache.backReferences.get(obj, {})

    def _collectReferences(self, astModel):
        cache = ReferenceResolver._ReferenceCache(astModel)
        return cache
                
    class _ReferenceCache(object):
        def __init__(self, model):
            self.model = model #: basic model where references are resolved
            self.astModel = model.astModel #: AST model where references are resolved
            self.references = {} #: program/subprogram (AST) object -> set[referenced module/subprogram/variable (Basic) object]
            self.backReferences = {} #: referenced module/subprogram/variable (Basic) object -> set[program/subprogram (AST) object]
            self._fill()
            
        def _fill(self):
            "Parse AST tree and fill cache."
            LOG.info("Generating references cache for %s" % self.model)
            self.astModel.itertree(self.callback)
            LOG.debug("%d calling module/subprogram AST objects in reference cache" % len(self.references))
            LOG.debug("%d referenced module/subprogram/variable objects in back reference cache" % len(self.backReferences))

        def callback(self, astObj):
            if isinstance(astObj, ast.Statement) and astObj.type=='call' or\
                    isinstance(astObj, ast.Reference) or\
                    isinstance(astObj, ast.Call):
                astScope = self.astModel.getScope(astObj)
                chain = self.model.getReferenceChainByASTObject(astObj)
                if chain!=None:
                    self._addReference(astObj, astScope, chain[-1])
                
        def _addReference(self, astObj, astScope, referencedObj):
            if not self.references.has_key(astScope):
                self.references[astScope] = set()
            self.references[astScope].add(referencedObj)

            if not self.backReferences.has_key(referencedObj):
                self.backReferences[referencedObj] = {}
            if not self.backReferences[referencedObj].has_key(astScope):
                self.backReferences[referencedObj][astScope] = set()
            self.backReferences[referencedObj][astScope].add(astObj)
            
class ASTTreeWalker(core.Service):
    def __init__(self):
        self._caches = {}

    def getReferencesFrom(self, astObj):
        "Get references from the given program or subprogram"
        references = []
        def add(child):
            if isinstance(child, ast.Statement) and child.type=='call':
                references.append(child)
            elif isinstance(child, ast.Reference) and child.base is None:
                references.append(child)
            elif isinstance(child, ast.Call):
                references.append(child)
        
        if isinstance(astObj, (ast.ProgramUnit, ast.Subprogram)): # skip subprograms
            if astObj.declarationBlock is not None:
                astObj.declarationBlock.itertree(add)
            if astObj.statementBlock is not None:
                astObj.statementBlock.itertree(add)
        else:
            astObj.itertree(add)
            
        return references

