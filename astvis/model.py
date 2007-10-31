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
    def __init__(self, project):
        self.project = project
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
    def __init__(self, project):
        BaseObject.__init__(self, project)
        _TreeRow.__init__(self, "data/thumbnails/file.png")
        self.units = []

    def getChildren(self):
        return self.units
        
    def __str__(self):
        return "<File %s>" % self.name

class ProgramUnit(BaseObject, _TreeRow):
    def __init__(self, project, parent = None):
        BaseObject.__init__(self, project)
        _TreeRow.__init__(self, "data/thumbnails/module.png")
        self.parent = parent
        self.statementBlock = None
        self.subprograms = []

    def getChildren(self):
        children = []
        if self.statementBlock:
            children.append(self.statementBlock)
        children.extend(self.subprograms)
        return children
        
    def addBlock(self, block):
        self.statementBlock = block        

    def __str__(self):
        return "<ProgramUnit %s>" % self.name

class Subprogram(BaseObject, _TreeRow):
    def __init__(self, project, parent = None):
        " - parent: program unit or subroutine where this sub belongs"
        BaseObject.__init__(self, project)
        _TreeRow.__init__(self, "data/thumbnails/subroutine.png")
        self.parent = parent
        self.statementBlock = None
        self.subprograms = []

    def getChildren(self):
        children = []
        if self.statementBlock:
            children.append(self.statementBlock)
        children.extend(self.subprograms)
        return children
        
    def addBlock(self, block):
        self.statementBlock = block        

    def __str__(self):
        return "<Subprogram %s>" % self.name

class Block(BaseObject, _TreeRow):
    def __init__(self, project, parent = None):
        BaseObject.__init__(self, project)
        self.parent = parent
        self.statements = []
        
    def getChildren(self):
        return self.statements  

    def addStatement(self, statement):
        self.statements.append(statement)

    def __str__(self):
        return "{}"
        
class Statement(BaseObject, _TreeRow):
    def __init__(self, project, parent = None):
        BaseObject.__init__(self, project)
        self.parent = parent
        self.type = "<unknown>"
        self.blocks = []
        
    def __str__(self):
        return "<%s>"%self.type

    def addBlock(self, block):
        self.blocks.append(block)
        
    def getChildren(self):
        return self.blocks
        
class Assignment(Statement):

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
        return " = "%(self.target or '')

class Expression(BaseObject):
    def __init__(self, project, parent = None):
        BaseObject.__init__(self, project)

class Operator(Expression, _TreeRow):
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
    def __init__(self, project, parent = None):
        Expression.__init__(self, project)
        self.parent = parent
        self.type = None
        self.value = None

    def __str__(self):
        return self.value or ''

class Reference(Expression, _TreeRow):
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

