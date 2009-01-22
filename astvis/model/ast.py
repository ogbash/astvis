#! /usr/bin/env python

"""AST model  classes for the application."""

from astvis.common import OPTIONS
import itertools
from StringIO import StringIO

ACTIVE_CHANGED = "active"

class ASTModel(object):
    """Model that contains AST tree of a code.

    @see: L{basic.BasicModel}
    """
    
    def __init__(self):
        self.project = None
        self.files = []
        self.basicModel = None
        
    def itertree(self, callback):
        for f in self.files:
            f.itertree(callback)

    def getScope(self, astObj, original = True):
        """Return the scope(module,subprogram,type definition) of AST object where it is located.
        @param astObj: AST object which scope is required
        @param original: Whether to ignore the I{astObj} in case it is a scope. This is useful
              to get scope of scopes (e.g. the module where a function is located).
        @rtype: L{ProgramUnit}, L{Subprogram} or L{Typedef}
        @return: scope of the I{astObj} or None
        """
        if not original and isinstance(astObj, (Subprogram, ProgramUnit, Typedef)):
            return astObj
        return astObj.parent!=None and self.getScope(astObj.parent, False) or None

    def getStatement(self, astObj):
        """Return the outer statement where AST object (expression, statement) is located.
        For statements it returns self, otherwise returns the first parent AST object
        which is of type ast.Statement."""
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
    """Base class for all AST objects.

    @ivar model: L{ASTModel} that this objects belongs.
    @ivar parent: parent L{ASTObject}.
    @ivar location: code L{Location} of the object.

    @see: L{ASTModel}
    """

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
    """AST object class that corresponds to fortran source file.

    @ivar name: Name of the file.
    @ivar units: Fortran program units and modules (see L{ProgramUnit}) that
        are defined in the file.
    @ivar subprograms: Fortran global function and procedures (see L{Subprogram}) that
        are defined in the file.
    """
    
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
    """Base class that serves as a base class for L{ProgramUnit} and L{Subprogram}.
    It contains declaration block and statement block.

    @ivar declarationBlock: L{Block} of code declarations
    @ivar statementBlock: L{Block} of code statements
    """

    def __init__(self, model):
        ASTObject.__init__(self, model)
        self.uses = []
        self.declarationBlock = None
        self.statementBlock = None
        self.subprograms = []

    def addBlock(self, block, attrs):
        if attrs['type']=='declarations':
            self.declarationBlock=block
        elif attrs['type']=='executions':
            self.statementBlock=block

class ProgramUnit(Code):
    """AST class that represents fortran program unit or module.

    Program unit and module are distinguished by L{type} variable.

    @type type: string
    @ivar type: 'program' or 'module'
    @ivar name: program unit or module name

    @note: Fortran 2008 specs I{11. Program Units}
    @see: L{Subprogram}
    """
    
    def __init__(self, model, parent = None):
        Code.__init__(self, model)
        self.parent = parent
        self.type = None
        self.name = '<unknown>'

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
        return "<%s %s>" % (self.type or 'program', self.name)
    __repr__=__str__

class Subprogram(Code):
    """Class that represents fortran subroutine or function.

    @ivar name: function or subroutine name

    @note: Fortran 2008 specs I{12. Procedures}
    @see: L{ProgramUnit}
    """

    def __init__(self, model, parent = None):
        " - parent: program unit or subroutine where this sub belongs"
        Code.__init__(self, model)
        self.parent = parent
        self.name = '<unknown>'

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

class PrintStatement(Statement):
    def _addValue(self, value): self.values.append(value)
    value = property(fget=lambda self: None, fset=_addValue)
    
    def __init__(self, model,parent=None):
        Statement.__init__(self, model, parent)
        self.format = None
        self.values = []
    
    def getChildren(self):
        c = []
        if self.format!=None:
            c.append(self.format)
        c.extend(self.values)
        return c

class IfConstruct(Statement):
    
    def __init__(self, model,parent=None):
        Statement.__init__(self, model, parent)
        self.statements = []

    def getChildren(self):
        return self.statements

class IfStatement(Statement):
    def __init__(self, model,parent=None):
        Statement.__init__(self, model, parent)
        self.condition = None

    def getChildren(self):
        c = []
        if self.condition!=None:
            c.append(self.condition)
        c.extend(self.blocks)
        return c

class DoStatement(Statement):
    def __init__(self, model,parent=None):
        Statement.__init__(self, model, parent)
        self.variable = None
        self.doId = None
        self.type = None # 'for' or 'while'
        self.first = None
        self.last = None
        self.step = None
        self.condition = None

    def getChildren(self):
        c = []
        if self.first!=None: c.append(self.first)
        if self.last!=None: c.append(self.last)
        if self.step!=None: c.append(self.step)
        if self.condition!=None: c.append(self.condition)
        c.extend(self.blocks)
        return c

class SelectCase(Statement):
    def __init__(self, model,parent=None):
        Statement.__init__(self, model, parent)
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

    def __init__(self, model, parent = None, target=None, value=None):
        Statement.__init__(self, model, parent)
        self.target = target
        self.value = value
        
    def getChildren(self):
        children = []
        if self.target: children.append(self.target)
        if self.value: children.append(self.value)
        return children

    def __str__(self):
        return "<%s = >" % self.target


class Allocate(Statement):

    def __init__(self, model, parent = None):
        Statement.__init__(self, model, parent)
        self.type = None # 'allocate', 'deallocate'
        self.designators = []

    def getChildren(self):
        return self.designators


class Exit(Statement):

    def __init__(self, model, parent = None):
        Statement.__init__(self, model, parent)
        self.exitId = None
        
class Declaration(ASTObject):
    pass

class Type(ASTObject):
        
    def __init__(self, model):
        self.name = '<unknown type>'
        self.kind = None

    def __str__(self):
        return self.name

class Typedef(ASTObject):
    def __init__(self, model, parent=None):
        ASTObject.__init__(self, model)
        self.parent = parent
        self.name = '<none>'
        self.blocks = []

    def addBlock(self, block, attrs):
        self.blocks.append(block)

    def getChildren(self):
        return self.blocks

class Entity(ASTObject):
        
    def __init__(self, model):
        ASTObject.__init__(self, model)
        self.name = '<entity>'

    def __str__(self):
        return self.name

class TypeDeclaration(Declaration):
    
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
        self.parent = parent

class Call(Expression):
        
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
    
    def __init__(self, model, parent = None, type="(op)", left=None, right=None):
        Expression.__init__(self, model)
        self.parent = parent
        self.type = type
        self.left = left
        self.right = right
        
    def getChildren(self):
        children = []
        if self.left: children.append(self.left)
        if self.right: children.append(self.right)
        return children

    def __str__(self):
        return "(%s)"%self.type

class Constant(Expression):

    def __init__(self, model, parent = None, type=None, value=None):
        Expression.__init__(self, model)
        self.parent = parent
        self.type = type
        self.value = value

    def __str__(self):
        return self.value!=None and str(self.value) or '<constant>'

class Reference(Expression):

    def __init__(self, model, parent = None, name=None):
        Expression.__init__(self, model)
        self.parent = parent
        self.name = name
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

    def __init__(self, model, parent = None):
        ASTObject.__init__(self, model)
        self.parent = parent
        self.name = None

    def __str__(self):
        return "<use %s>" % self.name
        
class Location(object):
            
    def __init__(self, model):
        super(Location, self).__init__()
        self.begin = Point()
        self.end = Point()
        
    def __str__(self):
        b = self.begin
        e = self.end
        return "<Location %d.%d to %d.%d>" % \
               (b and b.line or -1, b and b.column or -1,
                e and e.line or -1, e and e.column or -1)

    __repr__=__str__
        
class Point(object):    

    def __init__(self):
        self.line = -1
        self.column = -1

