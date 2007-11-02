#! /usr/bin/env python

import gaphas
from common import OPTIONS

ACTIVE_CHANGED = "active"

# help classes and interfaces

class _TreeRow:
    "Helper functions for GtkTreeModel"

    def __init__(self, imageFile=None):
        if imageFile:
            import gtk.gdk
            self._thumbnail = gtk.gdk.pixbuf_new_from_file_at_size(imageFile, 16, 16)            

    def getName(self):
        return hasattr(self,"name") and self.name or str(self)

    def getChildren(self):
        "List of element children"
        return []

    def getThumbnail(self):
        "Thumbnail to be shown in GtkTreeView for this element"
        return hasattr(self,"_thumbnail") and self._thumbnail or None

# basic model classes

class BaseObject(object):
    _xmlChildren = {'location': 'location'}

    def __init__(self, project):
        self.project = project
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
    
    def getActive(self):
        return self.__active
        
    def addBlock(self, block):
        pass

    def addStatement(self, statement):
        pass

class File(BaseObject, _TreeRow):
    _xmlTags = [("file",None)]
    _xmlAttributes = {"name": "name"}
    _xmlChildren = {"units": ("module", "program") }
    _xmlChildren.update(BaseObject._xmlChildren)

    def __init__(self, project = None):
        BaseObject.__init__(self, project = None)
        _TreeRow.__init__(self, "data/thumbnails/file.png")
        self.name = '<unknown>'
        self.units = []

    def getChildren(self):
        return self.units
        
    def __str__(self):
        return "<File %s>" % self.name

class ProgramUnit(BaseObject, _TreeRow):
    def _setBlock(self, value):
        if value.type=='declarations':
            self.declarationBlock = value
        else:
            self.statementBlock = value            

    _xmlTags = [("module", None), ("program", None)]
    _xmlAttributes = {"name": "id"}
    _xmlChildren = {"subprograms": ("subroutine", "function"),
            _setBlock: ("block",)}
    _xmlChildren.update(BaseObject._xmlChildren)

    def __init__(self, project = None, parent = None):
        BaseObject.__init__(self, project)
        _TreeRow.__init__(self, "data/thumbnails/module.png")
        self.parent = parent
        self.name = '<unknown>'
        self.declarationBlock = None
        self.statementBlock = None
        self.subprograms = []

    def getChildren(self):
        children = []
        if self.declarationBlock:
            children.append(self.declarationBlock)
        if self.statementBlock:
            children.append(self.statementBlock)
        children.extend(self.subprograms)
        return children
        
    def addBlock(self, block):
        self.statementBlock = block        

    def __str__(self):
        return "<ProgramUnit %s>" % self.name

class Subprogram(BaseObject, _TreeRow):
    def _setBlock(self, value):
        if value.type=='declarations':
            self.declarationBlock = value
        else:
            self.statementBlock = value            

    _xmlTags = [("subroutine", None), ("function", None)]
    _xmlAttributes = {"name": "id"}
    _xmlChildren = {"subprograms": ("subprogram",),
            "statementBlock": ("block",) }
    _xmlChildren.update(BaseObject._xmlChildren)
    
    def __init__(self, project, parent = None):
        " - parent: program unit or subroutine where this sub belongs"
        BaseObject.__init__(self, project)
        _TreeRow.__init__(self, "data/thumbnails/subroutine.png")
        self.parent = parent
        self.name = '<unknown>'
        self.declarationBlock = None
        self.statementBlock = None
        self.subprograms = []

    def getChildren(self):
        children = []
        if self.declarationBlock:
            children.append(self.declarationBlock)
        if self.statementBlock:
            children.append(self.statementBlock)
        children.extend(self.subprograms)
        return children
        
    def addBlock(self, block):
        self.statementBlock = block        

    def __str__(self):
        return "<Subprogram %s>" % self.name

class Block(BaseObject, _TreeRow):
    _xmlTags = [("block", None)]
    _xmlAttributes = {'type': 'type'}
    _xmlChildren = {'statements': ('statement','declaration') }
    _xmlChildren.update(BaseObject._xmlChildren)

    def __init__(self, project, parent = None):
        BaseObject.__init__(self, project)
        self.parent = parent
        self.statements = []
        self.type = None
        
    def getChildren(self):
        return self.statements  

    def addStatement(self, statement):
        self.statements.append(statement)

    def __str__(self):
        return "{%s}" % self.type
        
class Statement(BaseObject, _TreeRow):
    _xmlTags = [("statement", None)]
    _xmlAttributes = {"type": "type", 'name': 'name'}
    _xmlChildren = {"blocks": ("block",)}
    _xmlChildren.update(BaseObject._xmlChildren)
    
    def __init__(self, project, parent = None):
        BaseObject.__init__(self, project)
        self.parent = parent
        self.type = "<unknown>"
        self.blocks = []
        self.name = None
        
    def __str__(self):
        return "<%s>"%self.type

    def addBlock(self, block):
        self.blocks.append(block)
        
    def getChildren(self):
        return self.blocks

class Assignment(Statement):
    _xmlTags = [("statement", lambda args: args['type']=='assignment')]
    _xmlAttributes = {"type": "type"}
    _xmlChildren = {"target": ("target",),
            "value": ("value",) }
    #_xmlChildren.update(Statement._xmlChildren)

    def __init__(self, project, parent = None):
        Statement.__init__(self, project, parent)
        self.target = None
        self.value = None
        
    def getChildren(self):
        children = []
        if self.target: children.append(self.target)
        if self.value: children.append(self.value)
        return children

    def __str__(self):
        return " = "


class Declaration(BaseObject, _TreeRow):
    pass

class Type(object):
    _xmlTags = [('type',None)]
    _xmlAttributes = {}
    _xmlChildren = {'name': ('name',)}
    def _xmlContent(self, childName, value):
        if childName=='name':
            self.name = value.strip()
        elif childName=='kind':
            self.kind = value.strip()
        
    def __init__(self, project):
        self.name = '<unknown type>'
        self.kind = None

    def __str__(self):
        return self.name

class Entity(object, _TreeRow):
    _xmlTags = [('entity',None)]
    _xmlAttributes = {}
    _xmlChildren = {'name': ('name',)}
    def _xmlContent(self, childName, value):
        if childName=='name':
            self.name = value.strip()
        
    def __init__(self, project):
        self.name = '<entity>'

    def __str__(self):
        return self.name

class TypeDeclaration(Declaration):
    _xmlTags = [("declaration", lambda args: args['type']=='type')]
    _xmlAttributes = {'decltype': 'type'}
    _xmlChildren = {'type': ('type',),
            'entities': ('entities',)}
    
    def __init__(self, project):
        Declaration.__init__(self, project)
        self.decltype = '<unknown>'
        self.type = None
        self.entities = []

    def __str__(self):
        return "<typedecl '%s'>" % self.type
        
    def getChildren(self):
        return self.entities

class Expression(BaseObject):
    def __init__(self, project, parent = None):
        BaseObject.__init__(self, project)

class Call(Expression, _TreeRow):
    _xmlTags = [("call", None)]
    _xmlAttributes = {"type": 'type', "name": "name"}
    _xmlChildren = {}
        
    def __init__(self, project, parent = None):
        Expression.__init__(self, project, parent)
        _TreeRow.__init__(self, "data/thumbnails/subroutine.png")
        self.name = '<unknown call>'
        
    def getName(self):
        return self.name

class Operator(Expression, _TreeRow):
    _xmlTags = [("operator", None)]
    _xmlAttributes = {"type": "type"}
    _xmlChildren = {'right': ('left',),
            'right': ('right',)}
    
    def __init__(self, project, parent = None):
        Expression.__init__(self, project)
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

class Constant(Expression, _TreeRow):
    def _setContent(self, childName, value):
        self.value = value.strip()

    _xmlTags = [("constant", None)]
    _xmlAttributes = {"type": "type"}
    _xmlChildren = {}
    _xmlContent = _setContent

    def __init__(self, project, parent = None):
        Expression.__init__(self, project)
        self.parent = parent
        self.type = None
        self.value = None

    def __str__(self):
        return self.value or '<constant>'

class Reference(Expression, _TreeRow):
    _xmlTags = [("reference", None)]
    _xmlAttributes = {"name": "name"}
    _xmlChildren = {"base": ("base",)}

    def __init__(self, project, parent = None):
        Expression.__init__(self, project)
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
        
class Location(dict):
    _xmlTags = [("location", None)]
    _xmlAttributes = {}
    _xmlChildren = {'begin': ("begin",),
            'end': ("end",)}
            
    def __init__(self, project):
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

    def __init__(self, project):
        pass

