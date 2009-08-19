#! /usr/bin/env python

from astvis import action, core
from astvis.model import ast, flow

__all__=['DataflowService']

class DataflowService(core.Service):

    def __init__(self):
        core.Service.__init__(self)

        self._reachingDefinitions = {} # astScope -> (ins, outs)

    @action.Action('ast-reaching-definitions',"Reaching defs",targetClass=ast.ASTObject)
    def getReachingDefinitions(self, astNode, context=None):
        """For each basic block calculates (variable) definitions that reach this code location.
        
        @return: (ins, outs) - definitions on enter/leave of each basic block
        @rtype: (d, d) where d = {block: set((block, indexInBlock))}
        """
        
        astScope = astNode.model.getScope(astNode, False)
        # check for cached version
        if self._reachingDefinitions.has_key(astScope):
            return self._reachingDefinitions[astScope]

        # else calculate
        localEntities = [] 
        
        for decl in astScope.declarationBlock.statements:
            localEntities.extend(decl.entities)

        localNames = map(lambda e:e.name.lower(), localEntities)
        cfservice = core.getService('ControlflowService')
        flowModel = cfservice.getModel(astScope)

        ins = {} # { block: {name: set((block,indexInBlock))}}
        outs = {} # { block: {name: set((block,indexInBlock))]}}

        # some help functions
        def IN(block):
            if not ins.has_key(block):
                ins[block] = {}
            return ins[block]

        def OUT(block, createNew=True):
            if not outs.has_key(block):
                if not createNew:
                    return None
                outs[block] = {}
            return outs[block]

        # start main loop which works until converging of IN/OUT states
        
        working = [] # blocks that have their IN redefined
        working.append(flowModel.block.getFirstBasicBlock())

        while working:
            block = working.pop()
            inDefs = IN(block)
            oldOutDefs = OUT(block, False)
            outDefs = self._transform(inDefs, block)
            changed = (outDefs != oldOutDefs)
            if changed:
                outs[block] = outDefs
                # OUT has changed since the last try
                #  add following basic blocks to the working set as their INs change
                for nextBlock in block.getNextBasicBlocks():
                    if nextBlock==None:
                        # @todo: fix parser (handle "read" statement)
                        # this is only necessary, because fortran parser is not complete
                        #  i.e. there may exist empty block
                        continue 
                    nextInDefs = IN(nextBlock)
                    self._update(nextInDefs, outDefs)
                    working.append(nextBlock)

        self._reachingDefinitions[astScope] = (ins, outs)
        return ins, outs

    def _transform(self, inDefs, block):
        """Transform function for the 'reaching definitions' algorithm.

        @todo: for arrays - add the new, not replace the previous, definition
        """

        outDefs = dict(inDefs)
        for i,execution in enumerate(block.executions):
            if isinstance(execution, ast.Assignment):
                # replace the previous definition
                assignName = execution.target.name.lower()
                outDefs[assignName] = set([(block,i)])

        return outDefs

    def _update(self, toDefs, fromDefs):
        "Update IN definitions from OUT definitions."
        for name in fromDefs.keys():
            if not toDefs.has_key(name):
                toDefs[name] = set()
            toDefs[name].update(fromDefs[name])

    def getActiveDefinitionsByBlock(self, block):
        """Return all references and calls in the control flow block.

        @type block: L{astvis.model.flow.Block}
        """
        
        # collect AST objects
        objs = []
        def cb(block):
            if isinstance(block, flow.BasicBlock):
                objs.extend(block.executions)

        block.itertree(cb)

        # find references in every AST object
        unknown = set()
        written = set()
        read = set()
        called = set()
        service = core.getService('ASTTreeWalker')
        for obj in objs:
            refs = service.getReferencesFrom(obj)
            for ref in refs:
                if isinstance(ref, ast.Statement) and ref.type=='call' \
                       or isinstance(ref, ast.Call):
                    called.add(ref.name.lower())
                else:
                    isA = ref.isAssignment()
                    if isA is None:
                        unknown.add(ref.name.lower())
                    elif isA:
                        written.add(ref.name.lower())
                    else:
                        read.add(ref.name.lower())
        print 'called = ', called
        print 'unknown = ', unknown
        print 'written = ', written
        print 'read = ', read


    def getUsedDefinitions(self, block):
        "For every use of variable in the block calculate potential definitions."

        ins, outs = self.getReachingDefinitions(block.model.code)

        #blockGraph = flow.BlockGraph(set([block.model.block]), block.model.getConnections())
        #if block.parentBlock!=None:
        #    blockGraph.unfold(block.parentBlock)
        #insDefs = {}
        #for edge in blockGraph.inEdges[block]:
        #    for fromBlock, toBlock in blockGraph.edges[edge]:
        #        for name in ins[toBlock].keys():
        #            if not insDefs.has_key(name):
        #                insDefs[name]=set()
        #            insDefs[name].update(ins[toBlock][name])

        usedDefs = {} # use (e.g. Reference) -> set(Definitions)

        defsInBlock = set()
        class Data:
            pass
        data = Data() # solve problem with closures
        data.block = None

        def isInside(defBlock):
            if defBlock==block:
                return True
            if defBlock.parentBlock!=None:
                return isInside(defBlock.parentBlock)
            return False
        
        def matchReference(node):
            if isinstance(node, ast.Reference) and node.base==None \
                   and not node.isAssignment():
                name = node.name.lower()

                if name in defsInBlock:
                    return # the variable is defined in our basic block
                
                if ins[data.block].has_key(name):
                    for defBlock, defIndex in ins[data.block][name]:
                        # check that definition is outside of our initial block
                        if not isInside(defBlock):
                            if not usedDefs.has_key(name):
                                usedDefs[name] = set()
                            usedDefs[name].add(defBlock.executions[defIndex])

            elif isinstance(node, ast.Assignment):
                name = node.target.getPrimaryBase().name.lower()
                defsInBlock.add(name)
                
                
        def iterExecutions(block):
            if isinstance(block, flow.BasicBlock):
                if not ins.has_key(block):
                    return
                data.block = block
                defsInBlock.clear()
                for execution in block.executions:
                    execution.itertree(matchReference)

        block.itertree(iterExecutions)

        print usedDefs

        return usedDefs
