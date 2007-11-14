#!/usr/bin/env python

import logging
LOG=logging.getLogger('project')
from common import FINE, FINER, FINEST

import gtk
import xmlmap
import event
from model import ast, basic

class Project:
    objClasses = [ast.File, ast.ProgramUnit, ast.Subprogram]
    classes = list(objClasses)
    classes.extend([ast.Block, ast.Use,
            ast.Assignment, ast.Call, ast.Statement,
            ast.TypeDeclaration, ast.Type, ast.Entity,
            ast.Constant, ast.Reference, ast.Operator,
            ast.Location, ast.Point])

    def __init__(self, projectFileName=None, astFileName=None):
        self.name = "{unnamed}"
        self.sourceDir = None
        #deprecated self.calleeNames = {} # caller name -> callee name
        #deprecated self.callerNames = {} # callee name -> name caller
        self.astModel = None
        self.model = None
        
        if astFileName:
            self._loadAstFile(astFileName)

    def _loadAstFile(self, fileName):
        # load xml file
        LOG.debug('Loading AST file in %s' % self)
        astModel = ast.ASTModel()
        loader = xmlmap.XMLLoader(astModel, Project.classes, "/ASTCollection")
        astModel.files = loader.loadFile(fileName)
        self.astModel = astModel        
        self.model = basic.BasicModel(astModel)

        event.manager.notifyObservers(self, event.ASTMODEL_CHANGED, None)
        
        LOG.debug('Finished loading AST file in %s' % self)

