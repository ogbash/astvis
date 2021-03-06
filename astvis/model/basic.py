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
        astModel._basicModel = self # be more careful? only one basic model per ast model is allowed
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
            for astObj in file_.subprograms:
                obj = self._createObject(None, astObj)
                self.globalObjects[obj.name] = obj
                _generateSubroutines(astObj, obj)
            for astObj in file_.units:
                obj = self._createObject(None, astObj)
                self.globalObjects[obj.name] = obj
                _generateSubroutines(astObj, obj)
                        
        # generate variables, uses
        for n, astObj in enumerate(astFiles):
            event.manager.notifyObservers(self, event.TASK_PROGRESSED, (0.5+0.5*n/len(astFiles),))
            self._fillObject(astObj)

    def _createObject(self, parentObj, astObj):
        "Creates basic object from given C{astObj} and its parent basic object"
        if isinstance(astObj, ast.ProgramUnit):
            obj = ProgramUnit(self)
            obj.parent = parentObj
            obj.astObject = astObj
            obj.type = astObj.type
            obj.name = astObj.name.lower()

        elif isinstance(astObj, ast.Subprogram):
            obj = Subprogram(self)
            obj.parent = parentObj
            obj.astObject = astObj
            obj.name = astObj.name.lower()

        self.objectsMap[astObj] = obj
        return obj
        
    def _fillObject(self, astObj):
        "Parse data from AST model and initialize this model."
        if isinstance(astObj, ast.TypeDeclaration):
            astScope = self.astModel.getScope(astObj)
            scope = self.getObjectByASTObject(astScope)
            if scope!=None:
                scope.scanDeclaration(astObj)
            else:
                LOG.debug('No object for %s', astScope)
        elif isinstance(astObj, ast.Use):
            astScope = self.astModel.getScope(astObj)
            scope = self.getObjectByASTObject(astScope)
            use = Use(self)
            use.name = astObj.name.lower()
            use.module = self.globalObjects.get(use.name, None)
            scope.uses[use.name] = use
        elif isinstance(astObj, ast.Typedef):
            astScope = self.astModel.getScope(astObj)
            scope = self.getObjectByASTObject(astScope)
            typedef = Typedef(self)
            typedef.name = astObj.name.lower()
            scope.typedefs[typedef.name] = typedef
        
        # recurse for children
        for childAstObj in astObj.getChildren():
            self._fillObject(childAstObj)

    def getObjectByASTObject(self, astObj):
        """Returns object for any AST object."""
        if not hasattr(astObj, 'name'):
            raise Exception("AST object %s must have name to find corresponding object" % astObj)
            
        # index
        if self.objectsMap.has_key(astObj):
            return self.objectsMap[astObj]

        # find (super)parent with name (scope)
        parentAstObj = astObj.model.getScope(astObj)
        
        # no parent with name found, but we expect global level to have File parent
        if parentAstObj is None:
            raise Exception("AST object %s must have scope" % astObj)

        if isinstance(parentAstObj, ast.File):
            # this is global object, ie module/program or global subprogram
            return self.globalObjects.get(astObj.name.lower())
        else:
            parentObj = self.getObjectByASTObject(parentAstObj)
            obj = parentObj[astObj.name.lower()]
            return obj


    def getReferenceChainByASTObject(self, astObj):
        """Return the list of basic objects that correspond to each part in
        astObj data or subroutine reference."""
    
        if isinstance(astObj, ast.Reference) and astObj.base!=None:
            chain = self.getReferenceChainByASTObject(astObj.base)
            if chain==None:
                return None
            #obj = self.getObjectByName(chain[-1].type.name, chain[-1])
            baseVar = chain[-1]
            baseType = self.getObjectByName(baseVar.typename, baseVar.parent)
            if baseType!=None:
                var = baseType[astObj.name.lower()]
                chain.append(var)
                return chain
            else:
                return None
        else:
            astScope = self.astModel.getScope(astObj)
            scope = self.getObjectByASTObject(astScope)
            referencedObj = self.getObjectByName(astObj.name.lower(), scope)
            if referencedObj!=None:
                return [referencedObj]
            else:
                return None

    def getObjectByName(self, name, scope):
        "Find the object that the name refers to in the given scope."
        if scope.variables.has_key(name):
            return scope.variables[name]
        if scope.subprograms.has_key(name):
            return scope.subprograms[name];
        # at the moment derived types namespace is in proc and var namespace
        if scope.typedefs.has_key(name):
            return scope.typedefs[name]
            
        # @todo handle renamed 'use'
        for use in scope.uses.itervalues():
            if use.module is not None:
                v = self.getObjectByName(name, use.module)
                if v: return v
            else:
                LOG.log(FINER, 'No module named %s'%use.name)
            
        # recurse to upper scopes
        if scope.parent is not None and isinstance(scope.parent, Scope):
            return self.getObjectByName(name, scope.parent)
        else:
            #try global objects
            return self.globalObjects.get(name, None)

class BasicObject(object):
    def __init__(self, model):
        self.model = model
        self.astObjects = []

    astObject = property(lambda self: self.astObjects and self.astObjects[0],
            lambda self, obj: self.astObjects.append(obj))
        
    def __getitem__(self, key):
        return None
        
    
class Scope(BasicObject):
    def __init__(self, model):
        BasicObject.__init__(self, model)
        self.uses = {} #: name ->obj
        self.variables = {}
        self.subprograms = {} #: name->obj
        self.typedefs = {} #: name->obj
        
    def scanDeclaration(self, astDecl):
        'Scan AST declaration and extend scope variables.'
        for entity in astDecl.entities:
            variable = self.variables.get(entity.name.lower())
            if variable==None:
                variable = Variable(self.model)
                variable.name = entity.name.lower()
                variable.parent = self
                if astDecl.type!=None:
                    variable.astObject = entity
                self.variables[variable.name] = variable
                if LOG.isEnabledFor(FINER):
                    LOG.log(FINER, "Add %s to %s", variable, self)
            variable.scanDeclaration(astDecl)
            
    def __getitem__(self, key):
        if self.variables.has_key(key):
            return self.variables[key]
        elif self.typedefs.has_key(key):
            return self.typedefs[key]
        return None


class ProgramUnit(Scope):
    def __init__(self, model):
        Scope.__init__(self, model)
        self.parent = None
        self.name = None
        self.type = None
        
    def __str__(self):
        return "<ProgramUnit %s>" % self.name

class Subprogram(Scope):
    def __init__(self, model):
        Scope.__init__(self, model)
        self.parent = None
        self.name = None
        
    def __str__(self):
        return "<Subprogram %s>" % self.name
    
class Variable(BasicObject):
    def __init__(self, model):
        BasicObject.__init__(self, model)
        self.parent = None
        self.name = None
        self.intent = None
        
    def scanDeclaration(self, astDecl):
        self.typename = astDecl.type.name.lower()
        for attr in astDecl.attributes:
            if attr.type=='intent':
                self.intent = attr.intent
        self.astObjects.append(astDecl)

    def __str__(self):
        return "<Variable %s>" % self.name

    __repr__=__str__

class Use(BasicObject):
    def __init__(self, model):
        BasicObject.__init__(self, model)
        self.name = None
        self.module = None # Subprogram
        self.only = {} # name->name
    def __str__(self):
        return "<Use %s>" % self.name

class Typedef(Scope):

    def __init__(self, model):
        Scope.__init__(self, model)
        self.name = None
        self.parent = None

    def scanDeclarations(self, astTypedef):
        self.astObject = astTypedef
        
    


