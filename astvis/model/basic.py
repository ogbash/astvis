#! /usr/bin/env python

import logging
LOG = logging.getLogger('model.basic')

from astvis import event
from astvis.model import ast
from astvis.common import FINE, FINER, FINEST

"""Basic model classes for the application."""

class BasicModel(object):
    def __init__(self, astModel):
        self.astModel = astModel
        self.globalObjects = {} #  name (of top level program unit or subroutine) -> obj
        self.objectsMap = {} # ast object -> object

        try:
            event.manager.notifyObservers(self, event.TASK_STARTED, \
                    ('Generating basic objects',))
            self._generateObjects(astModel.files)
        finally:
            event.manager.notifyObservers(self, event.TASK_ENDED, None)            
        
    def _generateObjects(self, astFiles):
        def _generateSubroutines(astObj, obj):
            # *::**::subroutines
            for astSubObj in astObj.subprograms:
                subObj = self._createObject(obj, astSubObj)
                obj.subprograms[subObj.name] = subObj
                _generateSubroutines(astSubObj, subObj)

        LOG.debug("Generating basic objects from %d files" % len(astFiles))
    
        # first lets create core tree
        for n, file_ in enumerate(astFiles):
            event.manager.notifyObservers(self, event.TASK_PROGRESSED, (0.5*n/len(astFiles),))
            # subroutine, module::subroutine, module::variable
            for astObj in file_.units:
                obj = self._createObject(None, astObj)
                self.globalObjects[obj.name] = obj
                _generateSubroutines(astObj, obj)
                        
        # generate variables
        for n, astObj in enumerate(astFiles):
            event.manager.notifyObservers(self, event.TASK_PROGRESSED, (0.5+0.5*n/len(astFiles),))
            self._fillObject(astObj)

    def _createObject(self, parentObj, astObj):
        "Creates basic object from given C{astObj} and its parent basic object"
        if isinstance(astObj, ast.ProgramUnit):
            obj = ProgramUnit()
            obj.parent = parentObj
            obj.astObject = astObj
            obj.name = astObj.name.lower()

        elif isinstance(astObj, ast.Subprogram):
            obj = Subprogram()
            obj.parent = parentObj
            obj.astObject = astObj
            obj.name = astObj.name.lower()

        self.objectsMap[astObj] = obj
        return obj
        
    def _fillObject(self, astObj):
        if isinstance(astObj, ast.TypeDeclaration):
            astScope = ast.getScope(astObj)
            scope = self.getObjectByASTObject(astScope)
            scope.scanDeclaration(astObj)
        elif isinstance(astObj, ast.Use):
            astScope = ast.getScope(astObj)
            scope = self.getObjectByASTObject(astScope)
            use = Use()
            use.name = astObj.name.lower()
            use.module = self.globalObjects.get(use.name, None)
        
        # recurse for children
        for childAstObj in astObj.getChildren():
            self._fillObject(childAstObj)

    def getObjectByASTObject(self, astObj):
        """Returns object for any AST object.
        
        @todo: complete implementation for all possible AST objects"""
    
        if not hasattr(astObj, 'name'):
            raise Exception("AST object %s must have name to find corresponding object" % astObj)
            
        # index
        if self.objectsMap.has_key(astObj):
            return self.objectsMap[astObj]
    
        # find (super)parent with name
        parentAstObj = astObj.parent
        while parentAstObj and not hasattr(parentAstObj, 'name'):
            parentAstObj = parentAstObj.parent
            
        # no parent with name found, but we expect global level to have File parent
        if parentAstObj is None:
            raise Exception("AST object %s must have (super)parent with name defined" % astObj)
        
        if isinstance(parentAstObj, ast.File):
            # this is global object, ie module/program or global subprogram
            return self.globalObjects.get(astObj.name)
        else:
            parentObj = self.getObjectByASTObject(parentAstObj)
            return parentObj[astObj.name]

class BasicObject(object):
    pass
    
class Scope(BasicObject):
    def __init__(self):
        self.uses = {} # name ->obj
        self.variables = {}
        self.subprograms = {} # name->obj

    def getByName(self, name):
        if self.variables.has_key(name):
            return self.variables[name]
        if self.subprograms.has_key(name):
            return self.subprograms[name];
            
        # @todo handle renamed 'use'
        for use in self.uses:
            v = use.module.getByName(name)
            if v: return v


    def getVariables(self):
        """Get all variables declared in the scope.
        
        @return: list of L{Variable} objects
        """
        raise NotImplementedError('Should implement in subclass')
        
    def scanDeclaration(self, astDecl):
        'Scan AST declaration and extend scope variables.'
        for entity in astDecl.entities:
            variable = self.variables.get(entity.name.lower())
            if variable==None:
                variable = Variable()
                variable.name = entity.name.lower()
                self.variables[variable.name] = variable
                if LOG.isEnabledFor(FINER):
                    LOG.log(FINER, "Add %s to %s", variable, self)
            variable.scanDeclaration(astDecl)

class ProgramUnit(Scope):
    def __init__(self):
        Scope.__init__(self)
        self.astObject = None
        self.parent = None
        self.name = None
        
    def __str__(self):
        return "<ProgramUnit %s>" % self.name

class Subprogram(Scope):
    def __init__(self):
        Scope.__init__(self)
        self.astObject = None
        self.parent = None
        self.name = None
        
    def __str__(self):
        return "<Subprogram %s>" % self.name
    
class Variable(BasicObject):
    def __init__(self):
        self.astDeclarations = []
        self.parent = None
        self.name = None
        
    def scanDeclaration(self, astDecl):
        self.astDeclarations.append(astDecl)

    def __str__(self):
        return "<Variable %s>" % self.name

class Use(BasicObject):
    def __init__(self):
        self.name = None
        self.module = None # Subprogram
        self.only = {} # name->name
    def __str__(self):
        return "<Use %s>" % self.name


