#! /usr/bin/env python

"""AST model  classes for the application."""

from astvis.common import OPTIONS
from astvis.xmlmap import XMLTag, XMLAttribute, PythonObject, Chain, Link
import itertools
from StringIO import StringIO

ACTIVE_CHANGED = "active"

class ASTModel(object):
    def __init__(self):
        self.project = None
        self.files = []
        self.basicModel = None
        
    def itertree(self, callback):
        for f in self.files:
            f.itertree(callback)

    def getScope(self, astObj):
        if isinstance(astObj, (Subprogram, ProgramUnit)):
            return astObj
        return astObj.parent!=None and self.getScope(astObj.parent) or None

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

    _xmlChildren = [Chain([(XMLTag('location'), PythonObject(ref='location'))])]

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
    _xmlAttributes = [(XMLAttribute('name'), PythonObject(ref='name'))]
    _xmlChildren = [[(None, PythonObject(list, ref='units')),
                     (XMLTag('module'), None)],
                    [(None, PythonObject(list, ref='units')),
                     (XMLTag('program'), None)]
                    ]
    _xmlChildren.extend(ASTObject._xmlChildren)

    def __init__(self, model):
        ASTObject.__init__(self, model)
        self.name = '<unknown>'
        self.units = []
        self.subprograms = []

    def getChildren(self):
        c = []
        c.extend(self.subprograms)
        c.extend(self.units)
        return c
        
    def __str__(self):
        return "<File %s>" % self.name

class Code(ASTObject):
    _xmlChildren = [[(None, PythonObject(list, ref='subprograms')),
                     (XMLTag('subroutine'), None)],
                    [(None, PythonObject(list, ref='subprograms')),
                     (XMLTag('function'), None)],
                    [(XMLTag('block', {'type': 'declarations'}), PythonObject(None,ref='declarationBlock'))],
                    [(XMLTag('block', {'type': 'executions'}), PythonObject(None,ref='statementBlock'))],
                    [(None, PythonObject(list, ref='uses')),
                     (XMLTag('use'), None)]
                    ]
    _xmlChildren.extend(ASTObject._xmlChildren)

    def addBlock(self, block, attrs):
        if attrs['type']=='declarations':
            self.declarationBlock=block
        elif attrs['type']=='executions':
            self.statementBlock=block

class ProgramUnit(Code):

    _xmlTags = [XMLTag("module"), XMLTag("program")]
    _xmlAttributes = [(XMLAttribute('id'), PythonObject(ref='name')),
                      (XMLAttribute('tag',special=True), PythonObject(ref='type'))]
    _xmlChildren =  list(Code._xmlChildren)
    
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
    __repr__=__str__

class Subprogram(Code):

    _xmlTags = [XMLTag("subroutine"), XMLTag("function")]
    _xmlAttributes = [(XMLAttribute('id'), PythonObject(ref='name'))]
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
    __repr__=__str__

class Block(ASTObject):
    _xmlTags = [XMLTag("block")]
    _xmlAttributes = [(XMLAttribute('type'), PythonObject(ref='type'))]
    _xmlChildren =  [[(None, PythonObject(list, ref='statements')),
                      (XMLTag('statement'), None)],
                     [(None, PythonObject(list, ref='statements')),
                      (XMLTag('declaration'), None)]
                     ]
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
    _xmlTags = [XMLTag("statement", priority=0)]
    _xmlAttributes = [(XMLAttribute('type'), PythonObject(ref='type')), 
            (XMLAttribute('name'), PythonObject(ref='name'))]
    _xmlChildren =  [[(None, PythonObject(list, ref='blocks')),
                      (XMLTag('block'), None)]
                     ]
    _xmlChildren.extend(ASTObject._xmlChildren)
    
    def __init__(self, model, parent = None):
        ASTObject.__init__(self, model)
        self.parent = parent
        self.type = "<unknown>"
        self.blocks = []
        self.name = None

    def addBlock(self, block, attrs):
        self.blocks.append(block)
        
    def __str__(self):
        return "<%s>"%(self.type or 'statement')

    def getChildren(self):
        if hasattr(self, 'arguments'):
            return self.arguments
        else:
            return self.blocks

class SelectCase(Statement):
    def __init__(self, model,parent=None):
        ASTObject.__init__(self, model)
        self.parent = parent
        self.value = None    
        self.cases = []

    def getChildren(self):
        c = []
        c.append(self.value)
        c.extend(self.cases)
        return c

class Case(ASTObject):
    def __init__(self, model,parent=None):
        ASTObject.__init__(self, model)
        self.parent = parent
        self.sections = []
        self.block = None

    def addBlock(self, block, attrs):
        self.block = block

    def getChildren(self):
        c = []
        c.extend(self.sections)
        c.append(self.block)
        return c

class Assignment(Statement):
    _xmlTags = [XMLTag("statement", {'type': 'assignment'})]
    _xmlAttributes = [(XMLAttribute('type'), PythonObject(ref='type'))]
    _xmlChildren =  [[(XMLTag('target'), None), (XMLTag(), PythonObject(ref='target'))],
                     [(XMLTag('value'), None), (XMLTag(), PythonObject(ref='value'))]
                     ]
    _xmlChildren.extend(Statement._xmlChildren)

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
        return "<%s = >" % self.target


class Declaration(ASTObject):
    pass

class Type(ASTObject):
    _xmlTags = [XMLTag('type')]
    _xmlAttributes = []
    _xmlChildren =  [[(XMLTag('name'), PythonObject(ref='name'))]
                     ]
    #def _xmlContent(self, childName, value):
    #    if childName=='name':
    #        self.name = value.strip()
    #    elif childName=='kind':
    #        self.kind = value.strip()
        
    def __init__(self, model):
        self.name = '<unknown type>'
        self.kind = None

    def __str__(self):
        return self.name

class Entity(ASTObject):
    _xmlTags = [XMLTag('entity')]
    _xmlAttributes = []
    _xmlChildren =  [[(XMLTag('name'), PythonObject(ref='name'))]
                     ]
    #def _xmlContent(self, childName, value):
    #    if childName=='name':
    #        self.name = value.strip()
        
    def __init__(self, model):
        ASTObject.__init__(self, model)
        self.name = '<entity>'

    def __str__(self):
        return self.name

class TypeDeclaration(Declaration):
    _xmlTags = [XMLTag("declaration", {'type': 'type'})]
    _xmlAttributes = [(XMLAttribute('type'), PythonObject(ref='decltype'))]
    _xmlChildren =  [[(XMLTag('type'), PythonObject(ref='type'))],
                     [(XMLTag('entities'), PythonObject(list, ref='entities')),
                      (XMLTag(), None)]
                     ]
    
    def __init__(self, model):
        Declaration.__init__(self, model)
        self.decltype = '<unknown>'
        self.type = None
        self.entities = []

    def __str__(self):
        return "<typedecl '%s'>" % self.type
        
    def getChildren(self):
        return self.entities

class Type(ASTObject):
    def __init__(self, model):
        ASTObject.__init__(self, model)
        self.name = '<none>'

    def __str__(self):
        return str(self.name)

class Expression(ASTObject):
    def __init__(self, model, parent = None):
        ASTObject.__init__(self, model)
        self.parent = parent

class Call(Expression):
    _xmlTags = [XMLTag("call")]
    _xmlAttributes = [(XMLAttribute('type'), PythonObject(ref='type')),
            (XMLAttribute('name'), PythonObject(ref='name'))]
    _xmlChildren = []
        
    def __init__(self, model, parent = None):
        Expression.__init__(self, model, parent)
        self.name = '<unknown call>'
        self.arguments = []

    def getChildren(self):
        "List of element children"
        return self.arguments

    def __str__(self):
        return "<callexpr>{name=%s}" % self.name
    __repr__=__str__
        
class Operator(Expression):
    _xmlTags = [XMLTag("operator")]
    _xmlAttributes = [(XMLAttribute('type'), PythonObject(ref='type'))]
    _xmlChildren =  [[(XMLTag('left'), None), (XMLTag(), PythonObject(ref='left'))],
                     [(XMLTag('right'), None), (XMLTag(), PythonObject(ref='right'))]
                     ]
    
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

    _xmlTags = [XMLTag("constant")]
    _xmlAttributes = [(XMLAttribute('type'), PythonObject(ref='type'))]
    _xmlChildren = [[(XMLTag('__content__'), PythonObject(str,ref='value'))]]

    def __init__(self, model, parent = None):
        Expression.__init__(self, model)
        self.parent = parent
        self.type = None
        self.value = None

    def __str__(self):
        return self.value!=None and str(self.value) or '<constant>'

class Reference(Expression):
    _xmlTags = [XMLTag("reference")]
    _xmlAttributes = [(XMLAttribute('name'), PythonObject(str,ref='name'))]
    _xmlChildren =  [[(XMLTag('base'), None), (XMLTag(), PythonObject(str,ref='base'))]
                     ]

    def __init__(self, model, parent = None):
        Expression.__init__(self, model)
        self.parent = parent
        self.name = None
        self.base = None
        self.sections = None
        
    def getChildren(self):
        children = []
        if self.base: children.append(self.base)
        if self.sections: children.extend(self.sections)
        return children

    def __str__(self):
        return "%s.%s" % ((self.base or ''), self.name)

class Section(ASTObject):

    def __init__(self, model):
        ASTObject.__init__(self, model)
        self.first = None
        self.last = None
        self.stride = None

    def getChildren(self):
        c = []
        for name in ("first", "last", "stride"):
            v = getattr(self, name)
            if v!=None:
                c.append(v)
        return c

    def __str__(self):
        s=StringIO()
        if self.first!=None:
            s.write(str(self.first))
        s.write(":")
        if self.last!=None:
            s.write(str(self.last))
        s.write(":")
        if self.stride!=None:
            s.write(str(self.stride))
        return s.getvalue()

class Entity(ASTObject):
    def __init__(self, model):
        ASTObject.__init__(self, model)
        self.name = None

    def __str__(self):
        return "%s" % self.name


class Use(ASTObject):
    _xmlTags = [XMLTag('use')]
    _xmlAttributes = [(XMLAttribute('id'), PythonObject(str,ref='name'))]
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
    _xmlChildren =  [[(XMLTag('begin'), PythonObject(ref='begin'))],
                     [(XMLTag('end'), PythonObject(ref='end'))]
                     ]
            
    def __init__(self, model):
        super(Location, self).__init__()
        self.begin = None
        self.end = None
        
    def __str__(self):
        b = self.begin
        e = self.end
        return "<Location %d.%d to %d.%d>" % \
               (b and b.line or -1, b and b.column or -1,
                e and e.line or -1, e and e.column or -1)
        
class Point(object):    
    _xmlTags = [XMLTag('begin'), XMLTag('end')]
    _xmlAttributes = [(XMLAttribute('line'), PythonObject(int, ref='line')),
            (XMLAttribute('column'), PythonObject(int, ref='column'))]
    _xmlChildren = []

    def __init__(self, model):
        self.line = -1
        self.column = -1

