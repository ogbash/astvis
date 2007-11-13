#! /usr/bin/env python

from astvis.model import ast

class ReferenceResolver(object):

    def __init__(self):
        self._caches = {}

    def getReferences(self, obj, model):
        if not self._caches.has_key(model):
            cache = self._collectReferences(model)
            self._caches[model] = cache
        cache = self._caches[model]
        return cache[obj]
        
    def _collectReferences(self, astModel):
        cache = _ReferenceCache()
        astModel.itertree(cache.callback)
        return cache
                
class _ReferenceCache(object):
    def __init__(self, astModel):
        self.astModel = astModel
        self.references = {}

    def callback(self, obj):
        if isinstance(obj, ast.Statement) and obj.type=='call':
            self.references[obj.name]
