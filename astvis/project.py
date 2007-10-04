#!/usr/bin/env python

import gtk
import xmltool
from common import ADDED_TO_DIAGRAM, REMOVED_FROM_DIAGRAM
from model import Observable
from model import Subprogram, File, ProgramUnit
from model import ContainerRelation, CallRelation

class Project:

    def __init__(self, projectFileName=None, astFileName=None):
        self.name = "{unnamed}"
        self.objects = {}
        self.relations = set()
        self.astModel = gtk.TreeStore(str, object, gtk.gdk.Pixbuf, gtk.gdk.Color)
        
        if astFileName:
            self._loadAstFile(astFileName)
            

    def _loadAstFile(self, fileName):
        # load xml file
        self.files = xmltool.loadFile(fileName)

        # generate object map
        self._generateObjectMap(self.files)

        # generate sidebar tree
        self._generateSidebarTree(None, self.files)

        # generate relations
        self._createRelations(self.files)

    def _generateObjectMap(self, objects):
        for obj in objects:
            self.objects[obj.name.lower()] = obj
            self._generateObjectMap(obj.getChildren())

    def _generateSidebarTree(self, parent, objects):
        for obj in objects:
            data=[obj.getName(), obj, obj.getThumbnail(), gtk.gdk.color_parse("black")]
            row = self.astModel.append(parent,data)
            if isinstance(obj,Observable):
                obj.addObserver(self._objectChanged)
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
        
    def _objectChanged(self, event, args):
        if event==ADDED_TO_DIAGRAM:
            obj, diagram = args
            iObject = self._findInTree(obj)
            self.astModel[iObject][3] = gtk.gdk.color_parse("darkgreen")
        if event==REMOVED_FROM_DIAGRAM:
            obj, diagram = args
            iObject = self._findInTree(obj)
            self.astModel[iObject][3] = gtk.gdk.color_parse("black")


