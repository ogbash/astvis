
"Control flow model."

import ast        

class Block(object):

    def __init__(self, parentBlock, subBlocks = []):
        self.parentBlock = parentBlock
        self.subBlocks = list(subBlocks)
        self.firstBlock = self.subBlocks and self.subBlocks[0] or None
        self.endBlock = None

        self._nextBasicBlocks = None

        self.astObjects = []

    def getFirstBasicBlock(self):
        if self.firstBlock==None:
            return None

        if isinstance(self.firstBlock, BasicBlock):
            return self.firstBlock
        else:
            return self.firstBlock.getFirstBasicBlock()

    def getEndBlock(self):
        if self.endBlock==None and self.parentBlock!=None:
            return self.parentBlock.getEndBlock()
        return self.endBlock

    def getNextBasicBlocks(self):
        if self._nextBasicBlocks==None:
            self._nextBasicBlocks = [self.getEndBlock().getFirstBasicBlock()]
        return self._nextBasicBlocks

    def __str__(self):
        return "<%s(%s)>" % (self.__class__.__name__,
                             (self.astObjects and self.astObjects[-1] or ''))

    def addSubBlocks(self, blocks):
        self.subBlocks.extend(blocks)
        if self.subBlocks:
            self.firstBlock = self.subBlocks[0]

    classMap = {}

    @staticmethod
    def generateBlocks(parentBlock, statements):        
        blocks = []
        
        simpleStatements = []
        while len(statements)>0:
            stmt = statements[0]
            if stmt.__class__ in Block.classMap.keys():
                BlockClass = Block.classMap[stmt.__class__]
                if simpleStatements:
                   blocks.append(BasicBlock(parentBlock, simpleStatements))
                   simpleStatements = []
    
                subBlock = BlockClass(parentBlock, stmt)
                blocks.append(subBlock)

            else:
                simpleStatements.append(stmt)

            del statements[0]
            
        if simpleStatements:
            blocks.append(BasicBlock(parentBlock, simpleStatements))
            simpleStatements = []

        for i in xrange(len(blocks)-1):
            blocks[i].endBlock = blocks[i+1]

        return blocks


class BasicBlock(Block):

    def __init__(self, parentBlock, executions):
        Block.__init__(self, parentBlock)
        self.executions = executions

        self.astObjects.extend(executions)

    def getFirstBasicBlock(self):
        return self


class StartBlock(BasicBlock):
    def __init__(self, parentBlock):
        BasicBlock.__init__(self, parentBlock, [])

class EndBlock(BasicBlock):
    def __init__(self, parentBlock):
        BasicBlock.__init__(self, parentBlock, [])

    def getNextBasicBlocks(self):
        return []

class ConditionBlock(BasicBlock):

    def __init__(self, parentBlock, executions):
        BasicBlock.__init__(self, parentBlock, executions)
        self.branchBlocks = []

    def getNextBasicBlocks(self):
        if self._nextBasicBlocks==None:
            blocks = []
            for branchBlock in self.branchBlocks:
                blocks.append(branchBlock.getFirstBasicBlock())
            blocks.append(self.getEndBlock().getFirstBasicBlock())
            self._nextBasicBlocks = blocks
        return self._nextBasicBlocks


class IfBlock(Block):

    def __init__(self, parentBlock, ifStatement):
        Block.__init__(self, parentBlock)
        self.astObjects.append(ifStatement)

        condBlock = None
        if ifStatement.condition!=None:
            condBlock = ConditionBlock(self, [ifStatement.condition])
            self.subBlocks.append(condBlock)

        thenBlock = Block(self)
        thenBlocks = Block.generateBlocks(thenBlock, ifStatement.blocks[0].statements)
        thenBlock.addSubBlocks(thenBlocks)
        self.subBlocks.append(thenBlock)
        
        if condBlock!=None:
            condBlock.branchBlocks.append(thenBlock)            
            self.firstBlock = condBlock
        else:
            self.firstBlock = thenBlock

class IfConstructBlock(Block):

    def __init__(self, parentBlock, ifConstruct):
        Block.__init__(self, parentBlock)
        self.astObjects.append(ifConstruct)

        for stmt in ifConstruct.statements:
            ifBlock = IfBlock(self, stmt)
            self.subBlocks.append(ifBlock)
            if len(self.subBlocks)>1:
                self.subBlocks[-2].subBlocks[0].endBlock = self.subBlocks[-1] # elseif/else branch

        self.firstBlock = self.subBlocks[0]

Block.classMap = {ast.IfStatement: IfBlock,
                  ast.IfConstruct: IfConstructBlock}


class ControlFlowModel(object):

    "Model allows to navigate through AST tree of a subroutine or a program."

    def __init__(self, astObj):
        assert isinstance(astObj, ast.Code)
        
        self.code = astObj
        self.block = Block(None)

        self._startBlock = StartBlock(self.block)
        self._endBlock = EndBlock(self.block)
        self._codeBlock = Block(self.block)
        blocks = Block.generateBlocks(self._codeBlock, astObj.statementBlock.statements)
        self._codeBlock.subBlocks = blocks
        
        self.block.subBlocks = [self._startBlock,self._codeBlock,self._endBlock]
        self.block.firstBlock = self._startBlock
        self._codeBlock.firstBlock = blocks[0]
        self._startBlock.endBlock = self._codeBlock
        self._codeBlock.endBlock = self._endBlock

        self._connections = None

    def getConnections(self):
        if self._connections==None:
            connections = set()
            processed = set()
            blocks = set()
            blocks.add(self.block.getFirstBasicBlock())
            while blocks:
                block = blocks.pop()
                processed.add(block)
                nextBlocks = block.getNextBasicBlocks()
                for nextBlock in nextBlocks:
                    connections.add((block, nextBlock))
                    if nextBlock!=None and not nextBlock in processed:
                        blocks.add(nextBlock)
            self._connections = connections
        return self._connections

    def classifyConnectionsBy(self, connections, blocks):
        """Takes list of tuples and divides them into classes, where
        each class is some connection for I{blocks} and its elements
        are all connections of the subBlocks of I{blocks}.
        """
        blockSet = set(blocks)

        def find(block):
            while not block in blockSet and block!=None:
                block = block.parentBlock
            return block

        clConnections = {}
        for blockFrom, blockTo in connections:
            clBlockFrom = find(blockFrom)
            clBlockTo = find(blockTo)
            if not clConnections.has_key((clBlockFrom,clBlockTo)):
                clConnections[(clBlockFrom,clBlockTo)] = []
            clConnections[(clBlockFrom,clBlockTo)].append((blockFrom,blockTo))

        return clConnections
