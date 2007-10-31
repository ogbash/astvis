#!/usr/bin/env python

import gtk
import xmltool
import event

class Project:

    def __init__(self, projectFileName=None, astFileName=None):
        self.name = "{unnamed}"
        self.sourceDir = None
        self.objects = {} # id -> obj
        self.calleeNames = {} # caller id -> callee id
        self.callerNames = {} # callee id -> id caller
        self.files = {}
        
        if astFileName:
            self._loadAstFile(astFileName)       

    def _loadAstFile(self, fileName):
        # load xml file
        loader = xmltool.XMLLoader(self)
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

