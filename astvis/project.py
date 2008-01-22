#!/usr/bin/env python

import logging
LOG=logging.getLogger('project')
from common import FINE, FINER, FINEST

import gtk
import xmlmap
from astvis import event, gtkx
from model import ast, basic

def readASTModel(filename):
    """load xml file
    @todo: move this function to other module?"""
    LOG.debug('Loading AST file %s' % filename)
    try:
        astModel = ast.ASTModel()
        loader = xmlmap.XMLLoader(astModel, Project.classes, "/ASTCollection")
        astModel.filename = filename
        astModel.files = loader.loadFile(filename)
        LOG.debug('Finished loading AST file %s' % filename)
    except Exception, e:
        LOG.debug('Failed loading AST file %s' % filename)
        raise e
    return astModel

class Project(object):
    def _setName(self, name):
        self._name = name
    def _setASTModel(self, astModel):
        self._astModel = astModel
    def _setBasicModel(self, basicModel):
        self._basicModel = basicModel

    objClasses = [ast.File, ast.ProgramUnit, ast.Subprogram]
    classes = list(objClasses)
    classes.extend([ast.Block, ast.Use,
            ast.Assignment, ast.Call, ast.Statement,
            ast.TypeDeclaration, ast.Type, ast.Entity,
            ast.Constant, ast.Reference, ast.Operator,
            ast.Location, ast.Point])
            
    __gtkmodel__ = gtkx.GtkModel()

    name = property(lambda self: self._name, _setName)
    name = event.Property(name,'name')
    __gtkmodel__.appendAttribute('name')    

    "AST model"
    astModel = property(lambda self: self._astModel, _setASTModel)
    astModel = event.Property(astModel,'astModel')
    __gtkmodel__.appendChild('astModel')

    "Basic model"
    model = property(lambda self: self._basicModel, _setBasicModel)
    model = event.Property(model,'basicModel')
    __gtkmodel__.appendChild('basicModel', 'model')
    
    "Diagrams"
    diagrams = property(lambda self: self._diagrams)
    __gtkmodel__.appendChild('diagrams')

    def __init__(self, projectFileName=None):
        self._name = "(unnamed)"
        self.sourceDir = None
        self._astModel = None #: ast model
        self._basicModel = None #: basic model
        self._diagrams = []

    def addDiagram(self, diagram):
        self._diagrams.append(diagram)
        event.manager.notifyObservers(self._diagrams, event.PROPERTY_CHANGED,
                                      (None,event.PC_ADDED,diagram,None), {'index':len(self._diagrams)-1})
