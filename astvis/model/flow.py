
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

class StartBlock(Block):
    pass

class EndBlock(Block):
    pass

class BasicBlock(Block):

    def __init__(self, parentBlock, executions):
        Block.__init__(self, parentBlock)
        self.executions = executions

        self.astObjects.extend(executions)


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

        thenBlocks = Block.generateBlocks(self, ifStatement.blocks[0].statements)
        thenBlock = Block(self, thenBlocks)
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
        self.startBlock = StartBlock(None)
        self.endBlock = EndBlock(None)
        self.codeBlock = Block(None)
        blocks = Block.generateBlocks(self.codeBlock, astObj.statementBlock.statements)
        self.codeBlock.subBlocks = blocks
        
        self.codeBlock.firstBlock = blocks[0]
        self.startBlock.endBlock = self.codeBlock
        self.codeBlock.endBlock = self.endBlock
