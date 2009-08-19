
class HierarchicalGraph(object):

    def __init__(self, initialNodes, basicEdges):
        self.changes = []
        self.nodes = set()
        self.edges = {} # edge -> set(basicEdges)
        self.outEdges = {} # node -> edge
        self.inEdges = {} # node -> edge
        self.loopEdges = {} # node -> basicEdge
        self._unclassifiedEdges = set(basicEdges)

        for node in initialNodes:
            self._add(node)
        self._classifyEdges()

    def _classifyEdges(self):
        "Add unclassified edges into"
        edges = self._unclassifiedEdges
        newUnclassifiedEdges = set()
        for edge in edges:
            nodeFrom, nodeTo = edge
            clNodeFrom = self._findParent(nodeFrom)
            clNodeTo = self._findParent(nodeTo)

            if clNodeTo is None or clNodeFrom is None:
                newUnclassifiedEdges.add(edge)
                continue

            if clNodeFrom==clNodeTo: # loop
                if not self.loopEdges.has_key(clNodeFrom):
                    self.loopEdges[clNodeFrom] = set()
                self.loopEdges[clNodeFrom].add(edge)
                
            else: # not loop
                clEdge = clNodeFrom, clNodeTo

                # edge
                if not self.edges.has_key(clEdge):
                    self.edges[clEdge] = set()
                    self.changes.append(('ADDED', clEdge))
                self.edges[clEdge].add(edge)
                # out edge
                if not self.outEdges.has_key(clNodeFrom):
                    self.outEdges[clNodeFrom] = set()
                self.outEdges[clNodeFrom].add(clEdge)
                # in edge
                if not self.inEdges.has_key(clNodeTo):
                    self.inEdges[clNodeTo] = set()
                self.inEdges[clNodeTo].add(clEdge)

        self._unclassifiedEdges = newUnclassifiedEdges

    def _findParent(self, node):
        while not (node in self.nodes) and node is not None:
            node = self._getParent(node)
        return node

    def _getParent(self, node):
        raise NotImplementedError

    def _getChildren(self, node):
        raise NotImplementedError

    def _remove(self, node):
        if node in self.nodes:
            # loop edges
            for edge in self.loopEdges.get(node, []):
                self._unclassifiedEdges.add(edge)
            self.loopEdges.pop(node, None)
            
            # out edges
            for edge in self.outEdges.get(node, []):
                for basicEdge in self.edges.get(edge, []):
                    self._unclassifiedEdges.add(basicEdge)
                if self.edges.pop(edge, None)!=None:
                    self.changes.append(('REMOVED', edge))
            self.outEdges.pop(node, None)

            # in edges
            for edge in self.inEdges.get(node, []):
                for basicEdge in self.edges.get(edge, []):
                    self._unclassifiedEdges.add(basicEdge)
                if self.edges.pop(edge, None)!=None:
                    self.changes.append(('REMOVED', edge))
            self.inEdges.pop(node, None)

            self.nodes.remove(node)
            self.changes.append(('REMOVED', node))
            return True
        
        return False

    def _add(self, node):
        if node in self.nodes:
            return False
        
        self.nodes.add(node)
        self.changes.append(('ADDED', node))
        return True

    def unfold(self, node):
        
        if not node in self.nodes:
            parent = self._getParent(node)
            if parent is not None:
                self.unfold(parent)
            
        if not node in self.nodes:
            raise KeyError(node)

        self._remove(node)
        for child in self._getChildren(node):
            self._add(child)

        self._classifyEdges()

    def fold(self, node):
        parent = self._getParent(node)
        if not node in self.nodes or parent is None:
            raise KeyError(node)

        self._closeNode(parent)
        
        self._add(parent)
        self._classifyEdges()

    def _closeNode(self, node):
        if not node in self.nodes:
            # node is opened, close subNodes
            for subNode in self._getChildren(node):
                self._closeNode(subNode)
                
        else:
            # node is not open, remove it
            self._remove(node)
