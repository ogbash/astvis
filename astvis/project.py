#!/usr/bin/env python

import logging
LOG=logging.getLogger('project')
from common import FINE, FINER, FINEST

import gtk
import xmltool
from astvis import event, gtkx, action, core
from model import ast, basic
from astvis.misc.list import ObservableList, ObservableDict
from astvis.diagram import DiagramList
from astvis.calldiagram import CallDiagram

def readASTModel(filename):
    """load xml file
    @todo: move this function to other module?"""
    LOG.debug('Loading AST file %s' % filename)
    try:
        astModel = ast.ASTModel()
        astModel.filename = filename
        loader = xmltool.XMLLoader(astModel)
        astModel.files = loader.loadFile(filename)
        LOG.debug('Finished loading AST file %s' % filename)
    except Exception, e:
        LOG.debug('Failed loading AST file %s' % filename)
        raise
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

    def __getstate__(self):
        d = dict(self.__dict__)
        d['_color'] = d['_color'].to_string()
        return d

    def __setstate__(self, d):
        self.__dict__ = dict(d)
        self.__dict__['_color'] = gtk.gdk.color_parse(d['_color'])

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
        
class TagDict(ObservableDict):
    def __init__(self, project):
        dict.__init__(self)
        self.project = project
        self._subTags = {}
        self._callTags = {} # obj -> (tag -> caller)
        self._callSubTags = {}

    def __setitem__(self, obj, tags):
        oldTags = self.get(obj, set())
        ObservableDict.__setitem__(self, obj, tags)
        
        # track added and removed tags
        if hasattr(obj, 'parent'):
            added = tags.difference(oldTags)
            added = added.difference(self._subTags.get(obj,{}).keys())
            removed = oldTags.difference(tags)
            removed = removed.difference(self._subTags.get(obj,{}).keys())
            self._modifySubTags(obj, None, added, removed, isSource=True)

    def _modifySubTags(self, obj, child, added, removed, isSource=False):

        if not isSource:
            # handle subtags
            subTags = self._subTags.get(obj, {})

            # added and removed contain tags that were changed in child

            for tag in added.copy():
                if not subTags.has_key(tag):
                    subTags[tag] = set()
                # add object as a child that contains the tag
                if not child in subTags[tag]:
                    if subTags[tag]:
                        added.remove(tag)
                    subTags[tag].add(child)
                else:
                    added.remove(tag)

            for tag in removed.copy():
                if subTags.has_key(tag):
                    # remove object as containing the tag
                    if child in subTags[tag]:
                        subTags[tag].remove(child)
                        if not subTags[tag]: # subtags empty
                            del subTags[tag]
                            if tag in self.get(obj, set()): # but tag is present
                                removed.remove(tag)
                        else:
                            removed.remove(tag)

            # now added and removed contain tags that were changed in obj (ie parent)
            #  and subTags are new obj sub-tags
            self._subTags[obj] = subTags

        # if it is callable follow call tags
        if isinstance(obj,ast.Subprogram):
            service = core.getService('ReferenceResolver')

            basicObj = obj.model.basicModel.getObjectByASTObject(obj)
            callers = service.getReferringObjects(basicObj)

            for caller,stmts in callers.items():
                for stmt in stmts:
                    self._modifyCallTags(stmt, obj, added, removed, isSource=True)

        # notify widgets
        event.manager.notifyObservers(self, event.PROPERTY_CHANGED,
                (None,event.PC_CHANGED,None,None), dargs={'key':obj})

        # handle parent
        if added or removed:
            if hasattr(obj,'parent') and obj.parent!=None:
                self._modifySubTags(obj.parent, obj, added, removed)


    def _modifyCallTags(self, obj, child, added, removed, isSource=False):

        tags = self._callTags.get(obj, {})

        if isSource:
            # handle call tags
            
            for tag in added.copy():
                if not tags.has_key(tag):
                    tags[tag] = set()
                if tags[tag]:
                    added.remove(tag)
                tags[tag].add(child)

            for tag in removed.copy():
                if tags.has_key(tag):
                    # remove object as containing the tag
                    if child in tags[tag]:
                        tags[tag].remove(child)
                        if not tags[tag]: # subtags empty
                            del tags[tag]
                        else:
                            removed.remove(tag)
            self._callTags[obj] = tags

        else:
            # handle call subtags
            subTags = self._callSubTags.get(obj, {})
            
            for tag in added.copy():
                if not subTags.has_key(tag):
                    subTags[tag] = set()
                # add object as a child that contains the tag
                if not child in subTags[tag]:
                    if subTags[tag]:
                        added.remove(tag)
                    subTags[tag].add(child)
                else:
                    added.remove(tag)

            for tag in removed.copy():
                if subTags.has_key(tag):
                    # remove object as containing the tag
                    if child in subTags[tag]:
                        subTags[tag].remove(child)
                        if not subTags[tag]: # subtags empty
                            del subTags[tag]
                            if tag in tags.get(obj, set()): # but tag is present
                                removed.remove(tag)
                        else:
                            removed.remove(tag)

            # now added and removed contain tags that were changed in obj (ie parent)
            #  and subTags are new obj sub-tags
            self._callSubTags[obj] = subTags

        # notify widgets
        event.manager.notifyObservers(self, event.PROPERTY_CHANGED,
                (None,event.PC_CHANGED,None,None), dargs={'key':obj})

        # handle parent
        if added or removed:
            if hasattr(obj,'parent') and obj.parent!=None:
                self._modifyCallTags(obj.parent, obj, added, removed)

class Project(object):
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

    def _setName(self, name): self._name = name
    name = property(lambda self: self._name, _setName)
    name = event.Property(name,'name')
    __gtkmodel__.appendAttribute('name')

    "AST model"
    def _setASTModel(self, astModel): self._astModel = astModel
    astModel = property(lambda self: self._astModel, _setASTModel)
    astModel = event.Property(astModel,'astModel')
    __gtkmodel__.appendChild('astModel')

    "Basic model"
    def _setBasicModel(self, basicModel): self._basicModel = basicModel
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
        self._diagrams = DiagramList(self) #: diagrams
        self._tagTypes = TagTypeList(self) #: tag types
        self._tags = TagDict(self) #: object -> set<tagType>()

class ProjectService(object):
    @action.Action('new-tag-type', 'New tag', targetClass=TagTypeList)
    def newTagType(self, target, context):
        target.append(TagType('(unnamed)'))

    @action.Action('new-diagram', 'New diagram', targetClass=DiagramList)
    def newDiagram(self, diagrams, context):
        diagram = CallDiagram('(call diagram)', diagrams.project)
        diagrams.append(diagram)
