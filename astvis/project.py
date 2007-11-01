#!/usr/bin/env python

import gtk
import xmltool
import xmlmap
import event
import model

class Project:
    classes = [model.File, model.ProgramUnit, model.Subprogram]

    def __init__(self, projectFileName=None, astFileName=None):
        self.name = "{unnamed}"
        self.sourceDir = None
        self.objects = {} # id -> obj
        self.calleeNames = {} # caller id -> callee id
        self.callerNames = {} # callee id -> id caller
        self.files = {}
        
        if astFileName:
            self._loadAstFile(astFileName)
            
    def _newObjectCallback(self, obj):
        isinst = map(lambda x: isinstance(obj, x), self.classes)
        if True in isinst:
            self.objects[obj.name.lower()] = obj

    def _loadAstFile(self, fileName):
        # load xml file
        #loader = xmltool.XMLLoader(self)
        loader = xmlmap.XMLLoader(self, Project.classes, "/ASTCollection")
        loader.callback = self._newObjectCallback
        self.files = loader.loadFile(fileName)
        event.manager.notifyObservers(self, event.FILES_CHANGED, None)
            
    def addCall(self, callerName, calleeName):
        callerName = callerName.lower()
        calleeName = calleeName.lower()
        
        if not calleeName in self.callerNames:
            self.callerNames[calleeName] = list()
        self.callerNames[calleeName].append(callerName)

        if not callerName in self.calleeNames:
            self.calleeNames[callerName] = list()
        self.calleeNames[callerName].append(calleeName)

