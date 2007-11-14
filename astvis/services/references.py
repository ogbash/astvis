#! /usr/bin/env python

from astvis.model import ast

class ReferenceResolver(object):

    def __init__(self):
        self._caches = {}

    def getReferencedObject(self, scope, name):
        if not self._caches.has_key(model):
            cache = self._collectReferences(model.astModel)
            self._caches[model] = cache
        cache = self._caches[model]
        return cache[obj]
        
    def _collectReferences(self, astModel):
        cache = ReferenceResolver._ReferenceCache(astModel)
        return cache
                
    class _ReferenceCache(object):
        def __init__(self, astModel):
            self.astModel = astModel
            self.references = {}
            astModel.itertree(cache.callback)

        def callback(self, obj):
            if isinstance(obj, ast.Statement) and obj.type=='call':
                self.references[obj.name]
            
class ASTTreeWalker(object):
    def __init__(self):
        self._caches = {}

    def getReferencesFrom(self, astObj):
        references = []
        def add(child):
            if isinstance(child, ast.Statement) and child.type=='call':
                references.append(child)
            elif isinstance(child, ast.Reference) and child.base is None:
                references.append(child)
            elif isinstance(child, ast.Call):
                references.append(child)
        astObj.itertree(add)
            
        return references

