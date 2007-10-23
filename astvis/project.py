#!/usr/bin/env python

import gtk
import xmltool
from event import ADDED_TO_DIAGRAM, REMOVED_FROM_DIAGRAM
import event
from model import BaseObject, Subprogram, File, ProgramUnit

class Project:

    def __init__(self, projectFileName=None, astFileName=None):
        self.name = "{unnamed}"
        self.objects = {} # id -> obj
        self.calleeNames = {} # caller id -> callee id
        self.callerNames = {} # callee id -> id caller
        self.astModel = gtk.TreeStore(str, object, gtk.gdk.Pixbuf, gtk.gdk.Color)
        
        if astFileName:
            self._loadAstFile(astFileName)
            
        event.manager.subscribeClass(self._objectChanged, BaseObject)
            

    def _loadAstFile(self, fileName):
        # load xml file
        loader = xmltool.XMLLoader(self)
        self.files = loader.loadFile(fileName)

        # generate sidebar tree
        self._generateSidebarTree(None, self.files)

    def _generateSidebarTree(self, parent, objects):
        for obj in objects:
            data=[obj.getName(), obj, obj.getThumbnail(), gtk.gdk.color_parse("black")]
            row = self.astModel.append(parent,data)
            self._generateSidebarTree(row, obj.getChildren())

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
            
    def addCall(self, callerName, calleeName):
        callerName = callerName.lower()
        calleeName = calleeName.lower()
        
        if not calleeName in self.callerNames:
            self.callerNames[calleeName] = list()
        self.callerNames[calleeName].append(callerName)

        if not callerName in self.calleeNames:
            self.calleeNames[callerName] = list()
        self.calleeNames[callerName].append(calleeName)

