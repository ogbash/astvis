#! /usr/bin/env python

"""AST model  classes for the application."""

from astvis.common import OPTIONS
import itertools

ACTIVE_CHANGED = "active"

class ASTModel(object):
    def __init__(self):
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


# basic model classes

class ASTObject(object):
    """Base class for all AST objects."""

    _xmlChildren = {'location': 'location'}

    def _setModel(self, model):
        self._model = model

    model = property(lambda self: self._model, _setModel,
            doc="AST model where this AST object belongs to.")

    def __init__(self, model):
        self.model = model
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
    _xmlTags = [("file",None)]
    _xmlAttributes = {"name": "name"}
    _xmlChildren = {"units": ("module", "program") }
    _xmlChildren.update(ASTObject._xmlChildren)

    def __init__(self, model):
        ASTObject.__init__(self, model)
        self.name = '<unknown>'
        self.units = []

    def getChildren(self):
        return self.units
        
    def __str__(self):
        return "<File %s>" % self.name

class ProgramUnit(ASTObject):
    def _setBlock(self, value):
        if value.type=='declarations':
            self.declarationBlock = value
        else:
            self.statementBlock = value            

    _xmlTags = [("module", None), ("program", None)]
    _xmlAttributes = {"name": "id"}
    _xmlChildren = {"subprograms": ("subroutine", "function"),
            _setBlock: ("block",),
            'uses': ('use',)}
    _xmlChildren.update(ASTObject._xmlChildren)
    
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
    def _setBlock(self, value):
        if value.type=='declarations':
            self.declarationBlock = value
        else:
            self.statementBlock = value            

    _xmlTags = [("subroutine", None), ("function", None)]
    _xmlAttributes = {"name": "id"}
    _xmlChildren = {"subprograms": ('subroutine', 'function'),
            _setBlock: ("block",),
            'uses': ('use',) }
    _xmlChildren.update(ASTObject._xmlChildren)
    
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
    _xmlTags = [("block", None)]
    _xmlAttributes = {'type': 'type'}
    _xmlChildren = {'statements': ('statement','declaration') }
    _xmlChildren.update(ASTObject._xmlChildren)

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
    _xmlTags = [("statement", None)]
    _xmlAttributes = {"type": "type", 'name': 'name'}
    _xmlChildren = {"blocks": ("block",)}
    _xmlChildren.update(ASTObject._xmlChildren)
    
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
    _xmlTags = [("statement", lambda args: args['type']=='assignment')]
    _xmlAttributes = {"type": "type"}
    _xmlChildren = {"target": ("target",),
            "value": ("value",) }
    #_xmlChildren.update(Statement._xmlChildren)

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
    _xmlTags = [('type',None)]
    _xmlAttributes = {}
    _xmlChildren = {'name': ('name',)}
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
    _xmlTags = [('entity',None)]
    _xmlAttributes = {}
    _xmlChildren = {'name': ('name',)}
    def _xmlContent(self, childName, value):
        if childName=='name':
            self.name = value.strip()
        
    def __init__(self, model):
        self.name = '<entity>'

    def __str__(self):
        return self.name

class TypeDeclaration(Declaration):
    _xmlTags = [("declaration", lambda args: args['type']=='type')]
    _xmlAttributes = {'decltype': 'type'}
    _xmlChildren = {'type': ('type',),
            'entities': ('entities',)}
    
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
    _xmlTags = [("call", None)]
    _xmlAttributes = {"type": 'type', "name": "name"}
    _xmlChildren = {}
        
    def __init__(self, model, parent = None):
        Expression.__init__(self, model, parent)
        self.name = '<unknown call>'
        
class Operator(Expression):
    _xmlTags = [("operator", None)]
    _xmlAttributes = {"type": "type"}
    _xmlChildren = {'right': ('left',),
            'right': ('right',)}
    
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

    _xmlTags = [("constant", None)]
    _xmlAttributes = {"type": "type"}
    _xmlChildren = {}
    _xmlContent = _setContent

    def __init__(self, model, parent = None):
        Expression.__init__(self, model)
        self.parent = parent
        self.type = None
        self.value = None

    def __str__(self):
        return self.value or '<constant>'

class Reference(Expression):
    _xmlTags = [("reference", None)]
    _xmlAttributes = {"name": "name"}
    _xmlChildren = {"base": ("base",)}

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
    _xmlTags = [('use', None)]
    _xmlAttributes = {'name': 'id'}
    _xmlChildren = {}

    def __init__(self, model, parent = None):
        ASTObject.__init__(self, model)
        self.parent = parent
        self.name = None

    def __str__(self):
        return "<use %s>" % self.name
        
class Location(dict):
    _xmlTags = [("location", None)]
    _xmlAttributes = {}
    _xmlChildren = {'begin': ("begin",),
            'end': ("end",)}
            
    def __init__(self, model):
        super(Location, self).__init__()
        self.begin = None
        self.end = None
        
class Point(object):
    def _setLine(self, line):
        self.line = int(line)
    def _setColumn(self, column):
        self.column = int(column)
    
    _xmlTags = [('begin',None), ('end',None)]
    _xmlAttributes = {_setLine: 'line',
            _setColumn: 'column'}
    _xmlChildren = {}

    def __init__(self, model):
        pass

