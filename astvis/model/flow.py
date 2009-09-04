
"Control flow model."

import ast        
from astvis.hgraph import HierarchicalGraph

class Block(object):
    """
    Abstract base class for blocks in Control/Data Flow analysis.

    This class is a common base class for basic blocks and composite
    types of blocks (If, Do, Case, and other blocks). It defines
    interface of methods and common implementation which can be
    redefined in subclasses.

    @ivar model: control flow model that this block belongs to
    @type model: L{ControlFlowModel}
    """

    def __init__(self, model, parentBlock, subBlocks = []):
        self.model = model # control flow model
        self.parentBlock = parentBlock
        self.subBlocks = list(subBlocks)
        self.firstBlock = self.subBlocks and self.subBlocks[0] or None
        self.endBlock = None

        self._nextBasicBlocks = None
        self._previousBasicBlocks = None

        self.astObjects = []

    def getFirstBasicBlock(self):
        """The first basic block that is run when entering this block.
        @rtype: L{BasicBlock}
        """
        if self.firstBlock==None:
            return None

        if isinstance(self.firstBlock, BasicBlock):
            return self.firstBlock
        else:
            return self.firstBlock.getFirstBasicBlock()

    def getEndBlock(self):
        """The following block after exiting this block.
        @rtype: L{Block}
        """
        if self.endBlock==None and self.parentBlock!=None:
            return self.parentBlock.getEndBlock()
        return self.endBlock

    def getNextBasicBlocks(self):
        """Basic blocks that may be executed after exiting this block.
        @return: list of basic blocks
        @rtype: list of L{BasicBlock}s
        """
        if self._nextBasicBlocks==None:
            nextBlock = self.getEndBlock().getFirstBasicBlock()
            if nextBlock is not None:
                self._nextBasicBlocks = [nextBlock]
            else:
                self._nextBasicBlocks = []
        return self._nextBasicBlocks

    def getPreviousBasicBlocks(self):
        if self._previousBasicBlocks == None:
            self.model._calculatePreviousBasicBlocks()
        return self._previousBasicBlocks

    def __str__(self):
        return "<%s(%s)>" % (self.__class__.__name__,
                             (self.astObjects and self.astObjects[-1] or ''))

    def addSubBlocks(self, blocks):
        self.subBlocks.extend(blocks)
        if self.subBlocks:
            self.firstBlock = self.subBlocks[0]

    def itertree(self, callback):
        for b in self.subBlocks:
            b.itertree(callback)
        callback(self)

    def hasInside(self, block):
        if block==self:
            return True
        if block.parentBlock!=None:
            return self.hasInside(block.parentBlock)
        return False

class BasicBlock(Block):

    def __init__(self, model, parentBlock, executions):
        Block.__init__(self, model, parentBlock)
        self.executions = executions

        self.astObjects.extend(executions)

    def getFirstBasicBlock(self):
        return self


class StartBlock(BasicBlock):
    def __init__(self, model, parentBlock):
        BasicBlock.__init__(self, model, parentBlock, [])

class EndBlock(BasicBlock):
    def __init__(self, model, parentBlock):
        BasicBlock.__init__(self, model, parentBlock, [])

    def getNextBasicBlocks(self):
        return []

class ConditionBlock(BasicBlock):

    def __init__(self, model, parentBlock, executions):
        BasicBlock.__init__(self, model, parentBlock, executions)
        self.branchBlocks = []

    def getNextBasicBlocks(self):
        if self._nextBasicBlocks==None:
            blocks = []
            for branchBlock in self.branchBlocks:
                nextBlock = branchBlock.getFirstBasicBlock()
                if nextBlock is not None:
                    blocks.append(nextBlock)
            nextBlocks = super(ConditionBlock,self).getNextBasicBlocks()
            blocks.extend(nextBlocks)
            self._nextBasicBlocks = blocks
        return self._nextBasicBlocks


class IfBlock(Block):

    def __init__(self, model, parentBlock, ifStatement):
        Block.__init__(self, model, parentBlock)
        self.astObjects.append(ifStatement)

        condBlock = None
        if ifStatement.condition!=None:
            condBlock = ConditionBlock(self.model, self, [ifStatement.condition])
            self.subBlocks.append(condBlock)

        thenBlock = Block(self.model, self)
        thenBlocks = self.model.generateBlocks(thenBlock, list(ifStatement.blocks[0].statements))
        thenBlock.addSubBlocks(thenBlocks)
        self.subBlocks.append(thenBlock)
        
        if condBlock!=None:
            condBlock.branchBlocks.append(thenBlock)            
            self.firstBlock = condBlock
        else:
            self.firstBlock = thenBlock

class DoHeaderBlock(Block):

    def __init__(self, model, parentBlock, doStatement):
        Block.__init__(self, model, parentBlock)
        self.astObjects.append(doStatement)

        
        if doStatement.type=='for':
            self._initForBlocks(doStatement)
        elif doStatement.type=='while':
            self._initWhileBlocks(doStatement)
            
    def _initWhileBlocks(self, doStatement):
        self.conditionBlock = ConditionBlock(self.model, self, [doStatement.condition])
        self.initBlock = None
        self.stepBlock = None
        self.firstBlock = self.conditionBlock
        self.subBlocks.append(self.conditionBlock)

    def _initForBlocks(self, doStatement):
        astModel = doStatement.model
        self.initBlock = BasicBlock(self.model,
                                    self, [ast.Assignment(astModel,
                                                          target=ast.Reference(astModel,
                                                                               name=doStatement.variable),
                                                          value=doStatement.first)])
        self.conditionBlock = ConditionBlock(self.model,
                                             self, [ast.Operator(doStatement.model,
                                                                 type='.NEQ.',
                                                                 left=ast.Reference(astModel,
                                                                                    name=doStatement.variable),
                                                                 right=doStatement.last)])
        # @todo: use step from doStatement
        statements = [ast.Assignment(astModel,
                                     target=ast.Reference(astModel,
                                                          name=doStatement.variable),
                                     value=ast.Operator(astModel,
                                                        type='+',
                                                        left=ast.Reference(astModel,
                                                                           name=doStatement.variable),
                                                        right=ast.Constant(astModel,
                                                                           value=1)))
                      ]
        self.stepBlock = BasicBlock(self.model, self, statements)

        self.firstBlock = self.initBlock

        self.subBlocks.append(self.initBlock)
        self.subBlocks.append(self.conditionBlock)
        self.subBlocks.append(self.stepBlock)

        self.initBlock.endBlock = self.conditionBlock
        self.stepBlock.endBlock = self.conditionBlock

class IfConstructBlock(Block):

    def __init__(self, model, parentBlock, ifConstruct):
        Block.__init__(self, model, parentBlock)
        self.astObjects.append(ifConstruct)

        for stmt in ifConstruct.statements:
            ifBlock = IfBlock(self.model, self, stmt)
            self.subBlocks.append(ifBlock)
            if len(self.subBlocks)>1:
                self.subBlocks[-2].subBlocks[0].endBlock = self.subBlocks[-1] # elseif/else branch

        self.firstBlock = self.subBlocks[0]

class DoBlock(Block):

    def __init__(self, model, parentBlock, doStatement):
        Block.__init__(self, model, parentBlock)
        self.doId = doStatement.doId
        self.astObjects.append(doStatement)

        headerBlock = DoHeaderBlock(self.model, self, doStatement)
        self.subBlocks.append(headerBlock)

        block = Block(self.model, self)
        blocks = self.model.generateBlocks(block, list(doStatement.blocks[0].statements))
        block.addSubBlocks(blocks)
        if headerBlock.stepBlock!=None: # for
            block.endBlock = headerBlock.stepBlock
        else: # while
            block.endBlock = headerBlock.conditionBlock
        self.subBlocks.append(block)
        
        headerBlock.conditionBlock.branchBlocks.append(block)            
        self.firstBlock = headerBlock

Block.classMap = {ast.IfStatement: IfBlock,
                  ast.IfConstruct: IfConstructBlock,
                  ast.DoStatement: DoBlock}


class ControlFlowModel(object):

    "Model allows to navigate through AST tree of a subroutine or a program."

    def __init__(self, astObj):
        assert isinstance(astObj, ast.Code)
        
        self.code = astObj
        self.block = Block(self, None)

        self._startBlock = StartBlock(self, self.block)
        self._endBlock = EndBlock(self, self.block)
        self._codeBlock = Block(self, self.block)
        blocks = self.generateBlocks(self._codeBlock, list(astObj.statementBlock.statements))
        self._codeBlock.subBlocks = blocks
        
        self.block.subBlocks = [self._startBlock,self._codeBlock,self._endBlock]
        self.block.firstBlock = self._startBlock
        self._codeBlock.firstBlock = blocks[0]
        self._startBlock.endBlock = self._codeBlock
        self._codeBlock.endBlock = self._endBlock

        self._connections = None

        self._resolveJumpStatements()
        self._allBasicBlocks = None


    classMap = {}
    JUMP_STATEMENT_CLASSES = (ast.Exit,)

    def generateBlocks(self, parentBlock, statements):        
        blocks = []
        
        simpleStatements = []
        while len(statements)>0:
            stmt = statements[0]
            if stmt.__class__ in Block.classMap.keys():
                BlockClass = Block.classMap[stmt.__class__]
                if simpleStatements:
                   blocks.append(BasicBlock(self, parentBlock, simpleStatements))
                   simpleStatements = []
    
                subBlock = BlockClass(self, parentBlock, stmt)
                blocks.append(subBlock)
                del statements[0]

            else:
                simpleStatements.append(stmt)
                del statements[0]
                if isinstance(stmt, self.JUMP_STATEMENT_CLASSES):
                    break

        if simpleStatements:
            blocks.append(BasicBlock(self, parentBlock, simpleStatements))
            simpleStatements = []

        for i in xrange(len(blocks)-1):
            blocks[i].endBlock = blocks[i+1]

        return blocks

    def _resolveJumpStatements(self):
        def resolve(block):
            if isinstance(block, BasicBlock) and \
                   isinstance(block.executions[-1], self.JUMP_STATEMENT_CLASSES):
                stmt = block.executions[-1]

                if isinstance(stmt, ast.Exit):
                    # find do block for exit statement
                    exitId = stmt.exitId
                    jumpBlock = block.parentBlock
                    while jumpBlock!=None:
                        if isinstance(jumpBlock,DoBlock) and jumpBlock.doId==exitId:
                            # found
                            block.endBlock = jumpBlock.getEndBlock()
                            break
                        jumpBlock = jumpBlock.parentBlock
                          
        self._codeBlock.itertree(resolve)

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

    def collectASTObjects(self):
        """Returns dictionary containing a set of AST objects for each block,
        including those in subblocks for the block."""

        astObjects = {} # block -> astObjects

        def collect(block):
            # add all AST objects of the subblocks
            astObjsForSubBlocks = map(lambda b: astObjects[b], block.subBlocks)
            #  plus the objects of the block itself
            objs = reduce(set.union, astObjsForSubBlocks, set(block.astObjects))
            astObjects[block] = objs

        self.block.itertree(collect)

        return astObjects

    def getAllBasicBlocks(self):
        if self._allBasicBlocks==None:            
            blocks = set()

            def collect(block):
                if isinstance(block, BasicBlock):
                    blocks.add(block)

            self.block.itertree(collect)
            self._allBasicBlocks = blocks

        return self._allBasicBlocks
        

    def findBlocksByObject(self, astObj, onlyBlocks=None):
        """Find basic blocks (limited by onlyBlocks) that contain the given astObj.

        @todo: may be inefficient, better to use information about astObj while searching
        """
        blocks = set()

        if onlyBlocks==None:
            onlyBlocks = self.getAllBasicBlocks()
        
        objPath = astObj.model.getObjectPath(astObj)
        for block in onlyBlocks:
            # for each block
            for blockObj in block.astObjects:
                blockObjPath = blockObj.model.getObjectPath(blockObj)
                # if provided object is within block object or vv
                if len(objPath) <= len(blockObjPath) and objPath==blockObjPath[:len(objPath)] or \
                       len(objPath) > len(blockObjPath) and blockObjPath==objPath[:len(blockObjPath)]:
                    # remember this block as having AST object that contains or is contained
                    #  within the provided AST object
                    blocks.add(block)
                    break

        return blocks

    def _calculatePreviousBasicBlocks(self):
        allBlocks = self.getAllBasicBlocks()
        for block in allBlocks:
            block._previousBasicBlocks = []

        for block in allBlocks:
            for nextBlock in block.getNextBasicBlocks():
                nextBlock._previousBasicBlocks.append(block)

class BlockGraph(HierarchicalGraph):
    
    def _getParent(self, block):
        return block.parentBlock

    def _getChildren(self, block):
        return block.subBlocks

class Location(object):
    def __init__(self, block, index):
        self.block = block
        self.index = index

    def __eq__(self, obj):
        return self.block==obj.block and self.index==obj.index

    def __hash__(self):
        return hash((self.block, self.index))

    def getStatement(self):
        if isinstance(self.block, StartBlock):
            return self.block.model.code.declarationBlock.statements[self.index]
        else:
            return self.block.executions[self.index]

class ASTLocation(Location):

    def __init__(self, block, index, astObject):
        super(ASTLocation, self).__init__(block, index)
        self.astObject = astObject

    def __eq__(self, obj):
        return super(ASTLocation, self).__eq__(obj) and self.astObject==obj.astObject

    def __hash__(self):
        return hash((super(ASTLocation,self).__hash__(), self.astObject))
