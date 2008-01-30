#!/usr/bin/env python

import logging
LOG=logging.getLogger('project')
from common import FINE, FINER, FINEST

import gtk
import xmlmap
from astvis import event, gtkx, action
from model import ast, basic
from astvis.misc.list import ObservableList

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

class TagType(object):
    __gtkmodel__ = gtkx.GtkModel()

    def _setName(self, name): self._name = name
    name = property(lambda self: self._name, _setName)
    name = event.Property(name,'name')
    __gtkmodel__.appendAttribute('name')

    def _setColor(self, color): self._color = color
    color = property(lambda self: self._color, _setColor)
    color = event.Property(color,'color')

    def __init__(self, name):
        self._name = name
        self._color = gtk.gdk.Color(0,0xffff,0)

class TagTypeList(ObservableList):
    __gtkmodel__ = gtkx.GtkModel()

    name = "Tag types"
    __gtkmodel__.appendAttribute('name')    

    def __init__(self, project):
        list.__init__(self)
        self.project = project

    def __hash__(self,obj):
        return object.__hash__(self,obj)

    def __eq__(self, obj):
        return self is obj
        
    def __str__(self):
        return "<TagTypeList size=%s, project=%s>" % (len(self), self.project)

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

    __thumbnail__ = gtk.gdk.pixbuf_new_from_file_at_size('data/thumbnails/project.png', 16, 16)
    __gtkmodel__.appendAttribute('__thumbnail__')

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

    "Tag types"
    tagTypes = property(lambda self: self._tagTypes)
    __gtkmodel__.appendChild('tagTypes')

    "Tags"
    tags = property(lambda self: self._tags)

    def __init__(self, projectFileName=None):
        self._name = "(unnamed)"
        self.sourceDir = None
        self._astModel = None #: ast model
        self._basicModel = None #: basic model
        self._diagrams = []
        self._tagTypes = TagTypeList(self)
        self._tags = {}

    def addDiagram(self, diagram):
        self._diagrams.append(diagram)
        event.manager.notifyObservers(self._diagrams, event.PROPERTY_CHANGED,
                                      (None,event.PC_ADDED,diagram,None), {'index':len(self._diagrams)-1})

class ProjectService(object):
    @action.Action('new-tag-type', 'New tag', targetClass=TagTypeList)
    def newTagType(self, target, context):
        target.append(TagType('(unnamed)'))

