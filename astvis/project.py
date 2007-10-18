#!/usr/bin/env python

import gtk
import xmltool
from event import ADDED_TO_DIAGRAM, REMOVED_FROM_DIAGRAM
import event
from model import BaseObject, Subprogram, File, ProgramUnit

class Project:

    def __init__(self, projectFileName=None, astFileName=None):
        self.name = "{unnamed}"
        self.objects = {}
        self.relations = set()
        self.astModel = gtk.TreeStore(str, object, gtk.gdk.Pixbuf, gtk.gdk.Color)
        
        if astFileName:
            self._loadAstFile(astFileName)
            
        event.manager.subscribeClass(self._objectChanged, BaseObject)
            

    def _loadAstFile(self, fileName):
        # load xml file
        self.files = xmltool.loadFile(fileName)

        # generate object map
        self._generateObjectMap(self.files)

        # generate sidebar tree
        self._generateSidebarTree(None, self.files)

        # generate relations
        #self._createRelations(self.files)

    def _generateObjectMap(self, objects):
        for obj in objects:
            self.objects[obj.getName().lower()] = obj
            self._generateObjectMap(obj.getChildren())

    def _generateSidebarTree(self, parent, objects):
        for obj in objects:
            data=[obj.getName(), obj, obj.getThumbnail(), gtk.gdk.color_parse("black")]
            row = self.astModel.append(parent,data)
            self._generateSidebarTree(row, obj.getChildren())
            
    def _createRelations(self, objects):
        for obj in objects:
            if isinstance(obj, (ProgramUnit,Subprogram)):
                for child in obj.getChildren():
                    self.relations.add(ContainerRelation(obj,child))
                for calleeName in set(obj.callNames):
                    if self.objects.has_key(calleeName.lower()):
                        self.relations.add(CallRelation(obj,self.objects[calleeName.lower()]))
            self._createRelations(obj.getChildren())

    def _findInTree(self, obj):
        if hasattr(obj, "parent"):
            iParent = self._findInTree(obj.parent)
            if not iParent:
                return None
        else:
            iParent = None        
        iChild = self.astModel.iter_children(iParent)
        while iChild:
            childObj, = self.astModel.get(iChild, 1)
            if obj is childObj:
                break
            iChild = self.astModel.iter_next(iChild)
        return iChild
        
    def _objectChanged(self, obj, event, args):
        if event==ADDED_TO_DIAGRAM:
            diagram, = args
            iObject = self._findInTree(obj)
            self.astModel[iObject][3] = gtk.gdk.color_parse("darkgreen")
        if event==REMOVED_FROM_DIAGRAM:
            diagram, = args
            iObject = self._findInTree(obj)
            self.astModel[iObject][3] = gtk.gdk.color_parse("black")

# relations
# TODO remove or refactor all relations
class Relation:
    def getObjects(self):
        raise NotImplementedError("Must implement in subclass")

class ContainerRelation(Relation):
    "Parent-child relation for modules, subprograms"
    
    def __init__(self, parent, child):
        self._parent = parent
        self._child = child
        self.line = gaphas.item.Line()
        self.line.handles()[0].connectable=False
        self.line.handles()[-1].connectable=False
        
        parent.addObserver(self)
        child.addObserver(self)

    def notify(self, event, args):
        if event==ADDED_TO_DIAGRAM:
            obj, diagram = args
            diagram.addRelation(self)

        if event==REMOVED_FROM_DIAGRAM:
            obj, diagram = args
            diagram.removeRelation(self)
            
    def getObjects(self):
        return self._parent, self._child

class CallRelation(Relation):
    "Calls relation for modules, subprograms"
    
    def __init__(self, caller, callee):
        self._caller = caller
        self._callee = callee        
        caller.addObserver(self)
        callee.addObserver(self)

    def notify(self, event, args):
        if event==ADDED_TO_DIAGRAM:
            obj, diagram = args
            diagram.addRelation(self)

        if event==REMOVED_FROM_DIAGRAM:
            obj, diagram = args
            diagram.removeRelation(self)

    def getObjects(self):
        return self._caller, self._callee



