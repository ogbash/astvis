#! /usr/bin/env python

from astvis import action, core
from astvis.model import ast, flow
from astvis.model.dataflow import LiveVariableDict, ReachingDefinitionDict

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
        cfservice = core.getService('ControlflowService')
        flowModel = cfservice.getModel(astScope)
        ins = {} # { block: {name: set(flow.ASTLocation)}}
        outs = {} # { block: {name: set(flow.ASTLocation)}}

        # some help functions
        def IN(block):
            if not ins.has_key(block):
                ins[block] = ReachingDefinitionDict()
            return ins[block]

        def OUT(block, createNew=True):
            if not outs.has_key(block):
                if not createNew:
                    return None
                outs[block] = ReachingDefinitionDict()
            return outs[block]

        # start main loop which works until converging of IN/OUT states
        
        working = [] # blocks that have their IN redefined
        working.append(flowModel._startBlock)

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
                    nextInDefs.update(outDefs)
                    working.append(nextBlock)

        self._reachingDefinitions[astScope] = (ins, outs)
        return ins, outs

    def _transform(self, inDefs, block):
        """Transform function for the 'reaching definitions' algorithm.

        @todo: for arrays - add the new, not replace the previous, definition
        """

        if isinstance(block, flow.StartBlock):
            return self._transformWithStartBlock(inDefs, block)
        
        astWalkerService = core.getService('ASTTreeWalker')

        outDefs = ReachingDefinitionDict(inDefs)
        
        for i,execution in enumerate(block.executions):
            refs = astWalkerService.getReferencesFrom(execution)
            for ref in refs:
                if isinstance(ref, ast.Statement) and ref.type=='call' \
                       or isinstance(ref, ast.Call):
                    pass # ignore calls
                elif isinstance(ref, ast.Reference) and ref.isFinalComponent():
                    isA = ref.getPrimaryBase().isAssignment()
                    if isA is None or isA: # consider unknown as write
                        # replace the previous definition
                        names = []
                        workRef = ref
                        while workRef!=None:
                            names.append(workRef.name.lower())
                            workRef = workRef.base
                        names.reverse()
                        assignName = tuple(names)
                        loc = flow.ASTLocation(block,i,ref)
                        outDefs[assignName] = set([loc])

        return outDefs

    def _transformWithStartBlock(self, inDefs, block):
        outDefs = ReachingDefinitionDict(inDefs)

        code = block.model.code
        if isinstance(code, ast.Subprogram):
            # set out definitions
            basicModel = code.model.basicModel
            basicObj = basicModel.getObjectByASTObject(code)
            for name in code.parameters:
                var = basicObj.variables[name.lower()]
                if var.intent=='out':
                    continue
                astObj = var.astObject
                index = code.declarationBlock.statements.index(astObj.parent)
                outDefs[(name.lower(),)] = set([flow.ASTLocation(block,index,astObj)])

        return outDefs

    def _update(self, toData, fromData):
        "Update IN definitions/OUT uses from OUT definitions/IN uses."
        for name in fromData.keys():
            if not toData.has_key(name):
                toData[name] = set()
            toData[name].update(fromData[name])

    def _getFullName(self, ref):        
        names = []
        workRef = ref
        while workRef!=None:
            names.append(workRef.name.lower())
            workRef = workRef.base
        names.reverse()
        name = tuple(names)
        return name

    def _backTransform(self, outUses, block):
        """Transform function for the 'live variables' algorithm.
        """

        if isinstance(block, flow.EndBlock):
            return self._backTransformWithEndBlock(outUses, block)

        astWalkerService = core.getService('ASTTreeWalker')

        inUses = LiveVariableDict(outUses)

        executions = list(block.executions)
        n = len(executions)
        executions.reverse()
        for i,execution in enumerate(executions):
            refs = astWalkerService.getReferencesFrom(execution)
            for ref in refs:
                if isinstance(ref, ast.Statement) and ref.type=='call' \
                       or isinstance(ref, ast.Call):
                    pass # ignore calls
                elif isinstance(ref, ast.Reference) and ref.isFinalComponent():
                    isA = ref.isAssignment()
                    name = self._getFullName(ref)
                    
                    # if assignment, remove all uses that match
                    if isA is None or isA==True: # consider unknown as write
                        if not ref.isPartial():
                            inUses.remove(name)

                    # if not assignment, add this use
                    if isA is None or isA==False: # consider unknown as read
                        # replace the previous use
                        loc = flow.ASTLocation(block,n-1-i,ref)
                        inUses.add(name,loc)


        return inUses

    def _backTransformWithEndBlock(self, outUses, block):
        inUses = LiveVariableDict(outUses)

        code = block.model.code
        if isinstance(code, ast.Subprogram):
            # set out definitions
            basicModel = code.model.basicModel
            basicObj = basicModel.getObjectByASTObject(code)
            for name in code.parameters:
                var = basicObj.variables[name.lower()]
                if var.intent=='in':
                    continue
                astObj = var.astObject
                index = code.declarationBlock.statements.index(astObj.parent)
                inUses[(name.lower(),)] = set([flow.ASTLocation(block,index,astObj)])

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
                ins[block] = LiveVariableDict()
            return ins[block]

        def OUT(block):
            if not outs.has_key(block):
                outs[block] = LiveVariableDict()
            return outs[block]

        # start main loop which works until converging of IN/OUT states
        
        working = [] # blocks that have their IN redefined
        working.append(flowModel._endBlock)

        while working:
            block = working.pop()
            outUses = OUT(block)
            oldInUses = IN(block, False)
            inUses = self._backTransform(outUses, block)
            changed = (inUses != oldInUses)
            if changed:
                ins[block] = inUses
                # IN has changed since the last try
                #  add following basic blocks to the working set as their OUTs change
                for prevBlock in block.getPreviousBasicBlocks():
                    prevOutUses = OUT(prevBlock)
                    prevOutUses.update(inUses)
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
                elif ref.base==None:
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
                pairs = rdIns[fromBlock].intersection(lvIns[fromBlock])

                for defLoc,refLoc in pairs:
                    if block.hasInside(refLoc.block):
                        name = self._getFullName(defLoc.astObject)
                        if not usedDefs.has_key(name):
                            usedDefs[name] = {}
                        if not usedDefs[name].has_key(defLoc):
                            usedDefs[name][defLoc] = set()
                        usedDefs[name][defLoc].add(refLoc)

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
                pairs = rdOuts[fromBlock].intersection(lvOuts[fromBlock])

                for defLoc,refLoc in pairs:
                    if block.hasInside(defLoc.block):
                        name = self._getFullName(defLoc.astObject)
                        if not defdUses.has_key(name):
                            defdUses[name] = {}
                        if not defdUses[name].has_key(defLoc):
                            defdUses[name][defLoc] = set()
                        defdUses[name][defLoc].add(refLoc)

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
