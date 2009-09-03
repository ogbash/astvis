#! /usr/bin/env python

from astvis import action, core
from astvis.model import ast, flow

__all__=['DataflowService']

class DataflowService(core.Service):

    def __init__(self):
        core.Service.__init__(self)

        self._reachingDefinitions = {} # astScope -> (ins, outs)
        self._liveVariables = {} # astScope -> (ins, outs)

    @action.Action('ast-reaching-definitions',"Reaching defs",targetClass=ast.ASTObject)
    def getReachingDefinitions(self, astNode, context=None):
        """For each basic block calculates (variable) definitions that reach this code location.
        
        @return: (ins, outs) - definitions on enter/leave of each basic block
        @rtype: (d, d) where d = {block: {name: set((block, indexInBlock))}}
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

        astWalkerService = core.getService('ASTTreeWalker')

        outDefs = dict(inDefs)
        
        for i,execution in enumerate(block.executions):
            refs = astWalkerService.getReferencesFrom(execution)
            for ref in refs:
                if isinstance(ref, ast.Statement) and ref.type=='call' \
                       or isinstance(ref, ast.Call):
                    pass # ignore calls
                else:
                    isA = ref.isAssignment()
                    if isA is None or isA: # consider unknown as write
                        # replace the previous definition
                        assignName = ref.name.lower()
                        outDefs[assignName] = set([flow.ASTLocation(block,i,ref)])

        return outDefs

    def _update(self, toData, fromData):
        "Update IN definitions/OUT uses from OUT definitions/IN uses."
        for name in fromData.keys():
            if not toData.has_key(name):
                toData[name] = set()
            toData[name].update(fromData[name])

    def _backTransform(self, outUses, block):
        """Transform function for the 'live variables' algorithm.
        """

        astWalkerService = core.getService('ASTTreeWalker')

        inUses = dict(outUses)

        executions = list(block.executions)
        n = len(executions)
        executions.reverse()
        for i,execution in enumerate(executions):
            refs = astWalkerService.getReferencesFrom(execution)
            for ref in refs:
                if isinstance(ref, ast.Statement) and ref.type=='call' \
                       or isinstance(ref, ast.Call):
                    pass # ignore calls
                else:
                    isA = ref.isAssignment()
                    if isA is None or isA==False: # consider unknown as read
                        # replace the previous use
                        name = ref.name.lower()
                        inUses[name] = set([flow.ASTLocation(block,n-1-i,ref)])

        return inUses


    def getLiveVariables(self, astNode, context=None):
        """For each basic block calculates (variable) uses that are reached from this code location.
        
        @return: (ins, outs) - uses on enter/leave of each basic block
        @rtype: (d, d) where d = {block: {name: set((block, indexInBlock))}}
        """
        
        astScope = astNode.model.getScope(astNode, False)
        # check for cached version
        if self._liveVariables.has_key(astScope):
            return self._liveVariables[astScope]

        # else calculate
        localEntities = []
        for decl in astScope.declarationBlock.statements:
            localEntities.extend(decl.entities)

        localNames = map(lambda e:e.name.lower(), localEntities)
        cfservice = core.getService('ControlflowService')
        flowModel = cfservice.getModel(astScope)

        ins = {} # { block: {name: set((block,indexInBlock,astNode))}}
        outs = {} # { block: {name: set((block,indexInBlock,astNode))}}

        # some help functions
        def IN(block, createNew=True):
            if not ins.has_key(block):
                if not createNew:
                    return None
                ins[block] = {}
            return ins[block]

        def OUT(block):
            if not outs.has_key(block):
                outs[block] = {}
            return outs[block]

        # start main loop which works until converging of IN/OUT states
        
        working = [] # blocks that have their OUT redefined
        working.append(flowModel._endBlock)

        while working:
            block = working.pop()
            outUses = OUT(block)
            oldInUses = IN(block, False)
            inUses = self._backTransform(outUses, block)
            changed = (inUses != oldInUses)
            if changed:
                ins[block] = inUses
                # OUT has changed since the last try
                #  add following basic blocks to the working set as their INs change
                for prevBlock in block.getPreviousBasicBlocks():
                    prevOutUses = OUT(prevBlock)
                    self._update(prevOutUses, inUses)
                    working.append(prevBlock)

        self._liveVariables[astScope] = (ins, outs)
        return ins, outs

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

        usedDefs = {} # use (e.g. Reference) -> set(Definitions)

        defsInBlock = set()
        class Data:
            pass
        data = Data() # solve problem with closures
        data.block = None
        data.index = None
        
        def matchReference(node):
            if isinstance(node, ast.Reference) and node.base==None \
                   and not node.isAssignment():
                name = node.name.lower()

                if name in defsInBlock:
                    return # the variable is defined in our basic block
                
                if ins[data.block].has_key(name):
                    for defLoc in ins[data.block][name]:
                        # check that definition is outside of our initial block
                        if not block.hasInside(defLoc.block):
                            if not usedDefs.has_key(name):
                                usedDefs[name] = {}
                            if not usedDefs[name].has_key(defLoc):
                                usedDefs[name][defLoc] = set()
                            usedDefs[name][defLoc].add(flow.ASTLocation(data.block, data.index, node))

            elif isinstance(node, ast.Assignment):
                name = node.target.getPrimaryBase().name.lower()
                defsInBlock.add(name)
                
                
        def iterExecutions(block):
            if isinstance(block, flow.BasicBlock):
                if not ins.has_key(block):
                    return
                data.block = block
                data.index = 0
                defsInBlock.clear()
                for execution in block.executions:
                    execution.itertree(matchReference)
                    data.index += 1

        block.itertree(iterExecutions)

        return usedDefs


    def getDefinedUses(self, block):
        "For every definition in the block calculate potential uses."

        defdUses = {} # use (e.g. Reference) -> set(Definitions)

        code = block.model.code
        rdIns, rdOuts = self.getReachingDefinitions(code)
        lvIns, lvOuts = self.getLiveVariables(code)

        # create block graph to get edges leaving the block
        mainBlock = block.model.block
        blockGraph = flow.BlockGraph(set([mainBlock]), block.model.getConnections())
        if block.parentBlock != None:
            blockGraph.unfold(block.parentBlock)

        # for each edge leaving the block match
        #  reaching definitions and live variables
        for edge in blockGraph.outEdges[block]:
            for fromBlock, toBlock in blockGraph.edges[edge]: # for each edge
                for name in lvOuts[fromBlock].keys(): # for each live variable on the edge
                    if name in rdOuts[fromBlock].keys():
                        # for each reaching definition of the variable
                        for defLoc in rdOuts[fromBlock][name]:
                            if block.hasInside(defLoc.block):
                                if not defdUses.has_key(name):
                                    defdUses[name] = {}
                                if not defdUses[name].has_key(defLoc):
                                    defdUses[name][defLoc] = set()
                                # for each use of live variable
                                defdUses[name][defLoc].update(lvOuts[fromBlock][name])

        return defdUses

    def getBlockDefinitions(self, block):
        code = block.model.code
        ins, outs = self.getReachingDefinitions(code)

        def updateSum(dict1, dict2, sumf=set.union):
            "Update dict1 by adding (not replacing) values from dict2."
            for key in dict2.keys():
                if not dict1.has_key(key):
                    dict1[key] = dict2[key]
                else:
                    dict1[key] = sumf(dict1[key], dict2[key])

        mainBlock = block.model.block
        blockGraph = flow.BlockGraph(set([mainBlock]), block.model.getConnections())
        if block.parentBlock != None:
            blockGraph.unfold(block.parentBlock)
        
        # calculate all in definitions
        inDefs = {}
        for edge in blockGraph.inEdges[block]:
            for fromBlock, toBlock in blockGraph.edges[edge]:
                updateSum(inDefs, ins[toBlock])        
        # calculate all out definitions
        outDefs = {}
        for edge in blockGraph.outEdges[block]:
            for fromBlock, toBlock in blockGraph.edges[edge]:
                updateSum(outDefs, outs[fromBlock])

        # block definitions are those which in outDefs but not in inDefs
        blockDefs = {}
        for name in outDefs.keys():
            defs = outDefs[name]-inDefs.get(name, set())
            if defs:
                blockDefs[name] = defs

        return blockDefs
