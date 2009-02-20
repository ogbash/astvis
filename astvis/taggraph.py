
class TagGraph:

    def __init__(self, getTargetVertices, getSourceVertices):
        self._getTargetVertices = getTargetVertices
        self._getSourceVertices = getSourceVertices

        self._tags = {} # vertex -> set(tag)
        self._inducedTags = {} # vertex -> dict(tag -> set(targetVertex))

    def addTag(self, tag, vertex):
        if not self._tags.has_key(vertex):
            self._tags[vertex] = set()
        if tag in self._tags[vertex]:
            return False

        self._tags[vertex].add(tag)

        for sourceVertex in self._getSourceVertices(vertex):
            self._addInducedTag(tag, sourceVertex, vertex)

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
