
"Control flow model."

import ast        
from astvis.hgraph import HierarchicalGraph
import pynalyze.controlflow as cf
from pynalyze.controlflow import Block, BasicBlock, StartBlock, EndBlock, ConditionBlock

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

class ControlFlowModel(cf.ControlFlowModel):

    "Model allows to navigate through AST tree of a subroutine or a program."

    def __init__(self, astObj):
        assert isinstance(astObj, ast.Code)

        cf.ControlFlowModel.__init__(self, astObj,list(astObj.statementBlock.statements))

    CLASS_MAP = {ast.IfStatement: IfBlock,
                 ast.IfConstruct: IfConstructBlock,
                 ast.DoStatement: DoBlock}
    
    JUMP_STATEMENT_CLASSES = (ast.Exit,)

    def _resolveJumpStatements(self):
        "For each Fortran 'exit' statement find 'do' block."
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
        if isinstance(self.block, (StartBlock, EndBlock)):
            return self.block.model.code.declarationBlock.statements[self.index]
        else:
            return self.block.executions[self.index]

    def __str__(self):
        return "flow.ASTLocation(in %s at %d)" % (self.block, self.index)

    
    def __repr__(self):
        return self.__str__()+"<%0x>"%id(self)

class ASTLocation(Location):

    def __init__(self, block, index, astObject):
        super(ASTLocation, self).__init__(block, index)
        self.astObject = astObject

    def __eq__(self, obj):
        return super(ASTLocation, self).__eq__(obj) and self.astObject==obj.astObject

    def __hash__(self):
        return hash((super(ASTLocation,self).__hash__(), self.astObject))
