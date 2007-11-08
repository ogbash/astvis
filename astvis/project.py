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
    classes.extend([ast.Block, 
            ast.Assignment, ast.Call, ast.Statement,
            ast.TypeDeclaration, ast.Type, ast.Entity,
            ast.Constant, ast.Reference, ast.Operator,
            ast.Location, ast.Point])

    def __init__(self, projectFileName=None, astFileName=None):
        self.name = "{unnamed}"
        self.sourceDir = None
        self.globalObjects = {} #  name (of top level program unit or subroutine) -> obj
        self.objectsMap = {} # ast object -> object
        self.astObjects = {} # name (of program unit or subroutine) -> astobj
        self.calleeNames = {} # caller name -> callee name
        self.callerNames = {} # callee name -> name caller
        self.files = {}
        
        if astFileName:
            self._loadAstFile(astFileName)
            
    def _newObjectCallback(self, obj):
        # add to ad-hoc "index"
        isinst = map(lambda x: isinstance(obj, x), self.objClasses)
        if True in isinst:
            self.astObjects[obj.name.lower()] = obj

        if isinstance(obj, ast.Statement) and obj.type=='call':
            if LOG.isEnabledFor(FINEST):
                LOG.log(FINEST, "Found call %s" % obj)
            caller = obj
            while caller!=None and not caller.__class__ in (ast.ProgramUnit, ast.Subprogram):
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
        LOG.debug("len(calleNames)=%d, len(callerNames)=%d" % (len(self.calleeNames), len(self.callerNames)))
        event.manager.notifyObservers(self, event.FILES_CHANGED, None)
        
        self._generateObjects(self.files)
            
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
        
    def _generateObjects(self, astFiles):
        LOG.debug("Generating basic objects from %d files" % len(astFiles))
    
        # first lets create core tree
        for file_ in astFiles:
            # subroutine, module->subroutine, module->variable
            for astObj in file_.units:
                obj = self._createObject(None, astObj)
                self.globalObjects[obj.name] = obj
            
                if isinstance(astObj, ast.ProgramUnit):
                    for astSubObj in astObj.subprograms:
                        subObj = self._createObject(obj, astSubObj)
                        obj.subprograms[subObj.name] = subObj
                        
        # generate variables
        for astObj in astFiles:
            self._fillObject(astObj)
    
    def getObjectByASTObject(self, astObj):
        """Returns object for any AST object.
        
        @todo: complete implementation for all possible AST objects"""
    
        if not hasattr(astObj, 'name'):
            raise Exception("AST object %s must have name to find corresponding object" % astObj)
            
        # index
        if self.objectsMap.has_key(astObj):
            return self.objectsMap[astObj]
    
        # find (super)parent with name
        parentAstObj = astObj.parent
        while parentAstObj and not hasattr(parentAstObj, 'name'):
            parentAstObj = parentAstObj.parent
            
        # no parent with name found, but we expect global level to have File parent
        if parentAstObj is None:
            raise Exception("AST object %s must have (super)parent with name defined" % astObj)
        
        if isinstance(parentAstObj, ast.File):
            # this is global object, ie module/program or global subprogram
            return self.globalObjects.get(astObj.name)
        else:
            parentObj = self.getObjectByASTObject(parentAstObj)
            return parentObj[astObj.name]
    
    def _fillObject(self, astObj):
        if isinstance(astObj, ast.TypeDeclaration):
            astScope = ast.getScope(astObj)
            scope = self.getObjectByASTObject(astScope)
            scope.scanDeclaration(astObj)

        for childAstObj in astObj.getChildren():
            self._fillObject(childAstObj)

    def _createObject(self, parentObj, astObj):
        "Creates basic object from given C{astObj} and its parent basic object"
        if isinstance(astObj, ast.ProgramUnit):
            obj = basic.ProgramUnit()
            obj.parent = parentObj
            obj.astObject = astObj
            obj.name = astObj.name.lower()

        elif isinstance(astObj, ast.Subprogram):
            obj = basic.Subprogram()
            obj.parent = parentObj
            obj.astObject = astObj
            obj.name = astObj.name.lower()

        self.objectsMap[astObj] = obj
        return obj

