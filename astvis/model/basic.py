#! /usr/bin/env python

import logging
LOG = logging.getLogger('model.basic')
from astvis.common import FINE, FINER, FINEST

"""Basic model classes for the application."""

class BasicObject(object):
    pass
    
class Scope(BasicObject):
    def __init__(self):
        self.uses = {} # name ->obj
        self.variables = {}

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
        self.subprograms = {} # name->obj
        
    def __str__(self):
        return "<ProgramUnit %s>" % self.name

class Subprogram(Scope):
    def __init__(self):
        Scope.__init__(self)
        self.astObject = None
        self.parent = None
        self.name = None
        self.subprograms = {} # name->obj
        
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
        self.name
        self.module = None # Subprogram
        self.only = {} # name->name
    def __str__(self):
        return "<Use %s>" % self.name


