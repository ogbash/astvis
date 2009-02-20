
class TagGraph:

    def __init__(self, getTargetVertices, getSourceVertices):
        self._getTargetVertices = getTargetVertices
        self._getSourceVertices = getSourceVertices

        self._tags = {} # vertex -> dict(tag -> set(target))
        self._inducedTags = {} # vertex -> dict(tag -> set(targetVertex))

    def addTag(self, tag, vertex, target):
        """Attach tag to the vertex, considering target as the reason.
        @type tag: any hashable object
        @type vertex: any hashable object
        @type target: any hashable object
        """
        if not self._tags.has_key(vertex):
            self._tags[vertex] = {}
        if not self._tags[vertex].has_key(tag):
            self._tags[vertex][tag] = set()

        if target in self._tags[vertex][tag]:
            return False

        self._tags[vertex][tag].add(target)

        for sourceVertex in self._getSourceVertices(vertex):
            self._addInducedTag(tag, sourceVertex, vertex)
            
        return True

    def removeTag(self, tag, vertex):
        pass

    def _addInducedTag(self, tag, vertex, targetVertex):
        if not self._inducedTags.has_key(vertex):
            self._inducedTags[vertex] = {}    
        inducedTags = self._inducedTags.get(vertex)
        
        if inducedTags.has_key(tag):
            inducedTags[tag].add(targetVertex)
        else:
            inducedTags[tag] = set([targetVertex])
            # proceed recursively
            for sourceVertex in self._getSourceVertices(vertex):
                self._addInducedTag(tag, sourceVertex, vertex)
