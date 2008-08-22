#! /usr/bin/env python

import xml.sax
from astvis.model.ast import File, ProgramUnit, Subprogram, Block, Statement, Assignment, \
    Operator, Reference, Constant, Call, Use

class XMLLoader(xml.sax.handler.ContentHandler):
    def __init__(self, astModel):
        self.astModel = astModel
        self.files = []
        self.contexts = []
        self.blocks = []
        self.statements = []
        self.expressions = []
        self.setters = [] # setters
        
        
    def characters(self, content):
        if len(self.expressions)>0 and isinstance(self.expressions[-1], Constant):
            self.expressions[-1].value = content.strip()
        
    def startElement(self, name, attrs):
        if name=="file":
            self.startFile(attrs)
        elif name in ("program", "module"):
            self.startProgramUnit(name, attrs)
        elif name in ("subroutine", "function"):
            self.startSubprogram(attrs)
        elif name in ("block"):
            self.startBlock(attrs)
        elif name in ("statement"):
            self.startStatement(attrs)
        elif name in ("use"):
            self.startUse(attrs)
        elif name in ("location"):
            self.startLocation(attrs)
        elif name in ("begin"):
            self.startBegin(attrs)
        elif name in ("end"):
            self.startEnd(attrs)
        elif name in ("target", "value", "base", "left", "right"):
            if len(self.expressions)>0 and hasattr(self.expressions[-1], name):
                expr = self.expressions[-1]
                self.startSetter(lambda v: setattr(expr, name, v))
            elif hasattr(self.statements[-1], name):
                stmt = self.statements[-1]
                self.startSetter(lambda v: setattr(stmt, name, v))
        elif name in ("operator", "reference", "constant", "call"):
            self.startExpression(name, attrs)
        
    def endElement(self, name):
        if name=="file":
            self.endFile()
        elif name in ("program", "module"):
            self.endProgramUnit()
        elif name in ("subroutine", "function"):
            self.endSubprogram()
        elif name in ("block"):
            self.endBlock()
        elif name in ("statement"):
            self.endStatement()
        elif name in ("use"):
            self.endUse()
        elif name in ("location"):
            self.endLocation()
        elif name in ("target", "value", "base", "left", "right"):
            if len(self.expressions)>0 and hasattr(self.expressions[-1], name):
                self.endSetter()
            elif hasattr(self.statements[-1], name):
                self.endSetter()
        elif name in ("operator", "reference", "constant", "call"):
            self.endExpression(name)
            
    def loadFile(self, filename):
        f = open(filename, "r")
        try:
            xmlTree = xml.sax.parse(f, self)
        finally:
            f.close()
        return self.files
        
    def startFile(self, attrs):
        self.file = File(self.astModel)
        self.file.name = attrs["name"]
        self.contexts.append(self.file)

    def endFile(self):
        del self.contexts[-1]
        self.files.append(self.file)

    def startProgramUnit(self, name, attrs):
        parent = len(self.contexts)>0 and self.contexts[-1] or None
        pr = ProgramUnit(self.astModel, parent)
        pr.type = name
        pr.name = attrs["id"]
        self.file.units.append(pr)
        self.contexts.append(pr)
        #self.project.objects[pr.getName().lower()] = pr
        
    def endProgramUnit(self):
        del self.contexts[-1]

    def startSubprogram(self, attrs):
        parent = len(self.contexts)>0 and self.contexts[-1] or None
        sub = Subprogram(self.astModel, parent)
        sub.name = attrs["id"]
        parent.subprograms.append(sub)
        self.contexts.append(sub)
        #self.project.objects[sub.getName().lower()] = sub
        
    def endSubprogram(self):
        del self.contexts[-1]
        
    def startBlock(self, attrs):
        if len(self.statements)>0:
            block = Block(self.astModel, self.statements[-1])
            self.statements[-1].addBlock(block, attrs)
        else:
            block = Block(self.astModel, self.contexts[-1])
            self.contexts[-1].addBlock(block, attrs)
        self.blocks.append(block)
        
    def endBlock(self):
        del self.blocks[-1]
        
    def startStatement(self, attrs):
        block = len(self.blocks)>0 and self.blocks[-1] or self.contexts[-1]
        _type = attrs["type"]
        if _type=="assignment":
            st = Assignment(self.astModel, block)
        else:
            st = Statement(self.astModel, block)
        st.type = _type
        if attrs.has_key('name'):
            st.name = attrs['name']
        
        #if st.type=="call":
        #    self.project.addCall(self.contexts[-1].getName(), attrs['name'])        
        
        block.addStatement(st)
        self.statements.append(st)

    def endStatement(self):
        del self.statements[-1]
        
    def startUse(self, attrs):
        parent = len(self.contexts)>0 and self.contexts[-1] or None
        use = Use(self.astModel, parent)
        use.name = attrs["id"]
        parent.uses.append(use)
        
    def endUse(self):
        pass

    def startLocation(self, attrs):
        self.location = {}
        if len(self.statements)>0:
            self.statements[-1].location = self.location
        elif len(self.contexts)>0:
            self.contexts[-1].location = self.location
        
    def endLocation(self):
        self.location = None

    def startBegin(self, attrs):
        if attrs.has_key('line'):
            self.location['begin'] = int(attrs['line'])

    def startEnd(self, attrs):
        if attrs.has_key('line'):
            self.location['end'] = int(attrs['line'])

    def startExpression(self, name, attrs):
        parent = len(self.expressions)>0 and self.expressions[-1] \
            or len(self.statements)>0 and self.statements[-1]
        if name=="operator":
            expr = Operator(self.astModel, parent)
            expr.type = attrs.get('type', 'op')
        elif name=="reference":
            expr = Reference(self.astModel, parent)
            expr.name = attrs['name']
        elif name=="constant":
            expr = Constant(self.astModel, parent)
            expr.type = attrs['type']
        elif name=="call":
            expr = Call(self.astModel, parent)
            expr.name = attrs['name']
        else:
            expr = None
        self.expressions.append(expr)
        
    def endExpression(self, name):
        if len(self.setters)>0:
            self.setters[-1](self.expressions[-1])
        del self.expressions[-1]

    def startSetter(self, setter):
        self.setters.append(setter)
        
    def endSetter(self):
        del self.setters[-1]

