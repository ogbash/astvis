
"Control flow model."

import ast

class Block(object):

    def __init__(self, statements):
        self.statements = statements
        self._subBlocks = None


    _getSubBlocks(self):
        if self._subBlocks==None:
            self._subBlocks = calculateSubBlocks()
        return self._subBlocks
    subBlocks = property(_getSubBlocks)

    def getNextBlocks(self):
        pass

    def calculateSubBlocks(self):
        subBlocks = []
        subBlockStmts = []
        for stmt in self.statements:
            subBlockStmts.append(stmt)
            if isinstance(stmt, ast.IfConstruct):
                pass

class ControlFlowModel(object):

    "Model allows to navigate through AST tree of a subroutine or program."

    def __init__(self, astObj):
        assert isinstance(astObj, ast.Code)
        
        self.code = astObj

