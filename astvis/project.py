#!/usr/bin/env python

import logging
LOG=logging.getLogger('project')
from common import FINE, FINER, FINEST

import gtk
import xmltool
import xmlmap
import event
import model

class Project:
    objClasses = [model.File, model.ProgramUnit, model.Subprogram]
    classes = list(objClasses)
    classes.extend([model.Block, 
            model.Assignment, model.Call, model.Statement,
            model.Constant, model.Reference, model.Operator,
            model.Location, model.Point])

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
        # add to ad-hoc "index"
        isinst = map(lambda x: isinstance(obj, x), self.objClasses)
        if True in isinst:
            self.objects[obj.name.lower()] = obj

        if isinstance(obj, model.Statement) and obj.type=='call':
            if LOG.isEnabledFor(FINEST):
                LOG.log(FINEST, "Found call %s" % obj)
            caller = obj
            while caller!=None and not caller.__class__ in (model.ProgramUnit, model.Subprogram):
                if LOG.isEnabledFor(FINEST):
                    LOG.log(FINEST, "potential caller is %s" % caller)
                caller = caller.parent

            if LOG.isEnabledFor(FINEST):
                LOG.log(FINEST, "Caller is %s" % caller)
        
            if caller!=None:
                self.addCall(caller.name, obj.name)

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
        LOG.log(FINER, 'Adding call %s -> %s' % (callerName, calleeName))
        
        if not calleeName in self.callerNames:
            self.callerNames[calleeName] = list()
        self.callerNames[calleeName].append(callerName)

        if not callerName in self.calleeNames:
            self.calleeNames[callerName] = list()
        self.calleeNames[callerName].append(calleeName)

