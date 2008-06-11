#! /usr/bin/env python

"""AST model  classes for the application."""

from astvis.common import OPTIONS
from astvis.xmlmap import XMLTag, XMLAttribute, ObjectProperty
import itertools

ACTIVE_CHANGED = "active"

class ASTModel(object):
    def __init__(self):
        self.project = None
        self.files = None
        self.basicModel = None
        
    def itertree(self, callback):
        for f in self.files:
            f.itertree(callback)

    def getScope(self, astObj):
        if isinstance(astObj, (Subprogram, ProgramUnit)):
            return astObj
        return astObj.parent and self.getScope(astObj.parent) or None

    def getStatement(self, astObj):
        if isinstance(astObj, Statement):
            return astObj
        return astObj.parent and self.getStatement(astObj.parent) or None
        
    def getPath(self, astObj):
        if astObj is None:
            return []
        
        path = self.getPath(astObj.parent)

        if isinstance(astObj, (File,ProgramUnit,Subprogram)):
            path.append(astObj.name)
        else:
            # unnamed object
            path.append('*')
        return path
        
    def getObjectByPath(self, path):
        for f in self.files:
            if f.name == path[0]:
                obj = f
                break
        else:
            return None

        i = 1
        while i<len(path):
            if path[i]=='*' or path[i]=='**': # can't get when unnamed objects in the path
                return None
            if isinstance(obj, File):
                for subObj in itertools.chain(obj.units, obj.subprograms):
                    if subObj.name==path[i]:
                        obj = subObj
                        i = i+1
                        break
                else:
                    return None
            elif isinstance(obj, (ProgramUnit, Subprogram)):
                for subObj in obj.subprograms:
                    if subObj.name==path[i]:
                        obj = subObj
                        i = i+1
                        break
                else:
                    return None
            else:
                return None
        return obj
        
    def __str__(self):
        return "ASTModel(nFiles=%d)" % len(self.files)

# basic model classes

class ASTObject(object):
    """Base class for all AST objects."""

    _xmlChildren = [(XMLTag('location'), ObjectProperty('location'))]

    def _setModel(self, model):
        self._model = model
    def _getModel(self):
        if hasattr(self,'_model'):
            return self._model
        return self.parent is not None and self.parent.model or None
        
    model = property(_getModel, _setModel,
            doc="AST model where this AST object belongs to.")

    def __init__(self, model):
        self.model = model
        self.parent = None        
        self.location = None
        self.__active = True
        self.tags = set()
        
    def setActive(self, active):
        prevActive = self.__active
        self.__active = active
        if not prevActive==active and isinstance(self, Observable):
            self.notifyObservers(ACTIVE_CHANGED, (active,))
    
    def getFile(self):
        if isinstance(self, File):
            return self
        if hasattr(self, 'parent'):
            return self.parent.getFile()
        return None
        
    def getModel(self):
        return self.model
    
    def getActive(self):
        return self.__active

    def getChildren(self):
        "List of element children"
        return []
        
    def itertree(self, callback):
        for f in self.getChildren():
            f.itertree(callback)
        callback(self)

class File(ASTObject):
    _xmlTags = [XMLTag('file')]
    _xmlAttributes = [(XMLAttribute('name'), ObjectProperty('name'))]
    _xmlChildren = [(XMLTag('module'), ObjectProperty('units', list)),
            (XMLTag('program'), ObjectProperty('units', list))]
    _xmlChildren.extend(ASTObject._xmlChildren)

    def __init__(self, model):
        ASTObject.__init__(self, model)
        self.name = '<unknown>'
        self.units = []
        self.subprograms = []

    def getChildren(self):
        return self.units
        
    def __str__(self):
        return "<File %s>" % self.name

class Code(ASTObject):
    _xmlChildren = [(XMLTag('subroutine'), ObjectProperty('subprograms', list)),
            (XMLTag('function'), ObjectProperty('subroutine')),
            (XMLTag('block', {'type': 'declarations'}), ObjectProperty('declarationBlock')),
            (XMLTag('block', {'type': 'statements'}), ObjectProperty('statementBlock')),
            (XMLTag('use'), ObjectProperty('uses', list))]    
    _xmlChildren.extend(ASTObject._xmlChildren)

class ProgramUnit(Code):

    _xmlTags = [XMLTag("module"), XMLTag("program")]
    _xmlAttributes = [(XMLAttribute('id'), ObjectProperty('name'))]
    _xmlChildren = list(Code._xmlChildren)
    
    def _xmlPreProcess(self, name, attrs):
        self.type = name

    def __init__(self, model, parent = None):
        ASTObject.__init__(self, model)
        self.parent = parent
        self.type = None
        self.name = '<unknown>'
        self.uses = []
        self.declarationBlock = None
        self.statementBlock = None
        self.subprograms = []

    def getChildren(self):
        children = []
        children.extend(self.uses)
        if self.declarationBlock:
            children.append(self.declarationBlock)
        if self.statementBlock:
            children.append(self.statementBlock)
        children.extend(self.subprograms)
        return children
        
    def __str__(self):
        return "<%s %s>" % (self.type or 'ProgramUnit', self.name)

class Subprogram(ASTObject):

    _xmlTags = [XMLTag("subroutine"), XMLTag("function")]
    _xmlAttributes = [(XMLAttribute('id'), ObjectProperty('name'))]
    _xmlChildren = list(Code._xmlChildren)
    
    def __init__(self, model, parent = None):
        " - parent: program unit or subroutine where this sub belongs"
        ASTObject.__init__(self, model)
        self.parent = parent
        self.name = '<unknown>'
        self.uses = []
        self.declarationBlock = None
        self.statementBlock = None
        self.subprograms = []

    def getChildren(self):
        children = []
        children.extend(self.uses)
        if self.declarationBlock:
            children.append(self.declarationBlock)
        if self.statementBlock:
            children.append(self.statementBlock)
        children.extend(self.subprograms)
        return children
        
    def __str__(self):
        return "<Subprogram %s>" % self.name

class Block(ASTObject):
    _xmlTags = [XMLTag("block")]
    _xmlAttributes = [(XMLAttribute('type'), ObjectProperty('type'))]
    _xmlChildren = [(XMLTag('statement'), ObjectProperty('statements', list)),
        (XMLTag('declaration'), ObjectProperty('statements', list))]
    _xmlChildren.extend(ASTObject._xmlChildren)

    def __init__(self, model, parent = None):
        ASTObject.__init__(self, model)
        self.parent = parent
        self.statements = []
        self.type = None
        
    def getChildren(self):
        return self.statements  

    def addStatement(self, statement):
        self.statements.append(statement)

    def __str__(self):
        return "{%s}"%(self.type or '')
        
class Statement(ASTObject):
    _xmlTags = [XMLTag("statement")]
    _xmlAttributes = [(XMLAttribute('type'), ObjectProperty('type')), 
            (XMLAttribute('name'), ObjectProperty('name'))]
    _xmlChildren = [(XMLTag('block'), ObjectProperty('blocks', list))]
    _xmlChildren.extend(ASTObject._xmlChildren)
    
    def __init__(self, model, parent = None):
        ASTObject.__init__(self, model)
        self.parent = parent
        self.type = "<unknown>"
        self.blocks = []
        self.name = None
        
    def __str__(self):
        return "<%s>"%(self.type or 'statement')

    def getChildren(self):
        return self.blocks

class Assignment(Statement):
    _xmlTags = [XMLTag("statement", {'type': 'assignment'})]
    _xmlAttributes = [(XMLAttribute('type'), ObjectProperty('type'))]
    _xmlChildren = [(XMLTag('target'), ObjectProperty('target')),
            (XMLTag('value'), ObjectProperty('value'))]
    #_xmlChildren.extend(Statement._xmlChildren)

    def __init__(self, model, parent = None):
        Statement.__init__(self, model, parent)
        self.target = None
        self.value = None
        
    def getChildren(self):
        children = []
        if self.target: children.append(self.target)
        if self.value: children.append(self.value)
        return children

    def __str__(self):
        return "<assignment>"


class Declaration(ASTObject):
    pass

class Type(ASTObject):
    _xmlTags = [XMLTag('type')]
    _xmlAttributes = []
    _xmlChildren = [(XMLTag('name'), ObjectProperty('name'))]
    def _xmlContent(self, childName, value):
        if childName=='name':
            self.name = value.strip()
        elif childName=='kind':
            self.kind = value.strip()
        
    def __init__(self, model):
        self.name = '<unknown type>'
        self.kind = None

    def __str__(self):
        return self.name

class Entity(ASTObject):
    _xmlTags = [XMLTag('entity')]
    _xmlAttributes = []
    _xmlChildren = [(XMLTag('name'), ObjectProperty('name'))]
    def _xmlContent(self, childName, value):
        if childName=='name':
            self.name = value.strip()
        
    def __init__(self, model):
        self.name = '<entity>'

    def __str__(self):
        return self.name

class TypeDeclaration(Declaration):
    _xmlTags = [XMLTag("declaration", {'type': 'type'})]
    _xmlAttributes = [(XMLAttribute('type'), ObjectProperty('decltype'))]
    _xmlChildren = [(XMLTag('type'), ObjectProperty('type')),
            (XMLTag('entities'), ObjectProperty('entities'))]
    
    def __init__(self, model):
        Declaration.__init__(self, model)
        self.decltype = '<unknown>'
        self.type = None
        self.entities = []

    def __str__(self):
        return "<typedecl '%s'>" % self.type
        
    def getChildren(self):
        return self.entities

class Expression(ASTObject):
    def __init__(self, model, parent = None):
        ASTObject.__init__(self, model)

class Call(Expression):
    _xmlTags = [XMLTag("call")]
    _xmlAttributes = [(XMLAttribute('type'), ObjectProperty('type')),
            (XMLAttribute('name'), ObjectProperty('name'))]
    _xmlChildren = []
        
    def __init__(self, model, parent = None):
        Expression.__init__(self, model, parent)
        self.name = '<unknown call>'
        
class Operator(Expression):
    _xmlTags = [XMLTag("operator")]
    _xmlAttributes = [(XMLAttribute('type'), ObjectProperty('type'))]
    _xmlChildren = [(XMLTag('left'), ObjectProperty ('left')),
            (XMLTag('right'), ObjectProperty('right'))]
    
    def __init__(self, model, parent = None):
        Expression.__init__(self, model)
        self.parent = parent
        self.type = "(op)"
        self.left = None
        self.right = None
        
    def getChildren(self):
        children = []
        if self.left: children.append(self.left)
        if self.right: children.append(self.right)
        return children

    def __str__(self):
        return "(%s)"%self.type

class Constant(Expression):
    def _setContent(self, childName, value):
        self.value = value.strip()

    _xmlTags = [XMLTag("constant")]
    _xmlAttributes = [(XMLAttribute('type'), ObjectProperty('type'))]
    _xmlChildren = []
    _xmlContent = _setContent

    def __init__(self, model, parent = None):
        Expression.__init__(self, model)
        self.parent = parent
        self.type = None
        self.value = None

    def __str__(self):
        return self.value or '<constant>'

class Reference(Expression):
    _xmlTags = [XMLTag("reference")]
    _xmlAttributes = [(XMLAttribute('name'), ObjectProperty('name'))]
    _xmlChildren = [(XMLTag('base'), ObjectProperty('base'))]

    def __init__(self, model, parent = None):
        Expression.__init__(self, model)
        self.parent = parent
        self.name = None
        self.base = None
        self.sections = None
        
    def getChildren(self):
        children = []
        if self.base: children.append(self.base)
        if self.sections: children.append(self.sections)
        return children

    def __str__(self):
        return "%s.%s" % ((self.base or ''), self.name)

class Use(ASTObject):
    _xmlTags = [XMLTag('use')]
    _xmlAttributes = [(XMLAttribute('id'), ObjectProperty('name'))]
    _xmlChildren = []

    def __init__(self, model, parent = None):
        ASTObject.__init__(self, model)
        self.parent = parent
        self.name = None

    def __str__(self):
        return "<use %s>" % self.name
        
class Location(object):
    _xmlTags = [XMLTag("location")]
    _xmlAttributes = []
    _xmlChildren = [(XMLTag('begin'), ObjectProperty('begin')),
            (XMLTag('end'), ObjectProperty('end'))]
            
    def __init__(self, model):
        super(Location, self).__init__()
        self.begin = None
        self.end = None
        
    def __str__(self):
        return "<Location %d.%d to %d.%d>" % (self.begin.line, self.begin.column,
                self.end.line, self.end.column)
        
class Point(object):
    def _setLine(self, line):
        self.line = int(line)
    def _setColumn(self, column):
        self.column = int(column)
    
    _xmlTags = [XMLTag('begin'), XMLTag('end')]
    _xmlAttributes = [(XMLAttribute('line'), ObjectProperty('line',int)),
            (XMLAttribute('column'), ObjectProperty('column',int))]
    _xmlChildren = []

    def __init__(self, model):
        pass

