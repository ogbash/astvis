#!/usr/bin/env python

import logging
LOG=logging.getLogger('project')
from common import FINE, FINER, FINEST

import gtk
import xmlmap
from astvis import event
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
    objClasses = [ast.File, ast.ProgramUnit, ast.Subprogram]
    classes = list(objClasses)
    classes.extend([ast.Block, ast.Use,
            ast.Assignment, ast.Call, ast.Statement,
            ast.TypeDeclaration, ast.Type, ast.Entity,
            ast.Constant, ast.Reference, ast.Operator,
            ast.Location, ast.Point])

    def _setName(self, name):
        self._name = name
    def _setASTModel(self, astModel):
        self._astModel = astModel
        self.model = basic.BasicModel(astModel)
        event.manager.notifyObservers(self, event.ASTMODEL_CHANGED, None)

    name = property(lambda self: self._name, _setName)
    name = event.Property(name,'name')

    astModel = property(lambda self: self._astModel, _setASTModel)

    def __init__(self, projectFileName=None):
        self._name = "(unnamed)"
        self.sourceDir = None
        self._astModel = None #: ast model
        self.model = None #: basic model

