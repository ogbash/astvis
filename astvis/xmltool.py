#! /usr/bin/env python

import xml.sax
from model import File, ProgramUnit, Subprogram, Block, Statement

class XMLLoader(xml.sax.handler.ContentHandler):
    def __init__(self, project):
        self.project = project
        self.files = []
        self.contexts = []
        self.blocks = []
        self.statements = []
        
    def startElement(self, name, attrs):
        if name=="file":
            self.startFile(attrs)
        elif name in ("program", "module"):
            self.startProgramUnit(attrs)
        elif name in ("subroutine", "function"):
            self.startSubprogram(attrs)
        elif name in ("block"):
            self.startBlock(attrs)
        elif name in ("statement"):
            self.startStatement(attrs)
        elif name in ("call"):
            self.startCall(attrs)
        
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
        elif name in ("call"):
            self.endCall()
            
    def loadFile(self, filename):
        f = open(filename, "r")
        try:
            xmlTree = xml.sax.parse(f, self)
        finally:
            f.close()
        return self.files
        
    def startFile(self, attrs):
        self.file = File(self.project)
        self.file.name = attrs["name"]
        self.contexts.append(self.file)

    def endFile(self):
        del self.contexts[-1]
        self.files.append(self.file)

    def startProgramUnit(self, attrs):
        parent = len(self.contexts)>0 and self.contexts[-1] or None
        pr = ProgramUnit(self.project, parent)
        pr.name = attrs["id"]
        self.file.units.append(pr)
        self.contexts.append(pr)
        self.project.objects[pr.getName().lower()] = pr
        
    def endProgramUnit(self):
        del self.contexts[-1]

    def startSubprogram(self, attrs):
        parent = len(self.contexts)>0 and self.contexts[-1] or None
        sub = Subprogram(self.project, parent)
        sub.name = attrs["id"]
        parent.subprograms.append(sub)
        self.contexts.append(sub)
        self.project.objects[sub.getName().lower()] = sub
        
    def endSubprogram(self):
        del self.contexts[-1]
        
    def startBlock(self, attrs):
        if len(self.statements)>0:
            block = Block(self.project, self.statements[-1])
            self.statements[-1].addBlock(block)
        else:
            block = Block(self.project, self.contexts[-1])
            self.contexts[-1].addBlock(block)
        self.blocks.append(block)
        
    def endBlock(self):
        del self.blocks[-1]
        
    def startStatement(self, attrs):
        block = len(self.blocks)>0 and self.blocks[-1] or self.contexts[-1]
        st = Statement(self.project, block)
        st.type = attrs["type"]
        
        if st.type=="call":
            self.project.addCall(self.contexts[-1].getName(), attrs['name'])        
        
        block.addStatement(st)
        self.statements.append(st)

    def endStatement(self):
        del self.statements[-1]
        
    def startCall(self, attrs):
        self.project.addCall(self.contexts[-1].getName(), attrs['name'])
        
    def endCall(self):
        pass

