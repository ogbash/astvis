
from astvis import event

class TagGraph:
    """This class allows to add tags to the vertices of a directed graph
    and track any induced tags, produced by this. Induced tags are created
    recursively for all vertices that precede (in the sense of directed graph)
    the vertex with a tag.

    Hierarchical structure can be represented as directed graph, where
    parent leads to children. In this case if a tag is added to a child,
    then corresponding induced tag is added to its parents. This is used in
    many places where we want to know if a node contains children with specific
    property.
    """

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
        event.manager.notifyObservers(self, event.PROPERTY_CHANGED,
                                      ('tags',event.PC_ADDED,(tag,vertex,target),None))

        for sourceVertex in self._getSourceVertices(vertex):
            self._addInducedTag(tag, sourceVertex, vertex)
            
        return True

    def removeTag(self, tag, vertex, target):
        if not self._tags[vertex] or \
               not self._tags[vertex][tag] or \
               not target in self._tags[vertex][tag]:
            return False

        self._tags[vertex][tag].remove(target)
        event.manager.notifyObservers(self, event.PROPERTY_CHANGED,
                                      ('tags',event.PC_REMOVED,None,(tag,vertex,target)))
        
        if not self._tags[vertex][tag]:
            # no, the tag for the vertex anymore
            del self._tags[vertex][tag]

            if not self._tags[vertex]:
                # no tags for the vertex anymore                
                del self._tags[vertex]

            # recursively
            if not self._inducedTags.has_key(vertex) or \
                   not self._inducedTags[vertex].has_key(tag):
                # no, the induced tag for sources
                for sourceVertex in self._getSourceVertices(vertex):
                    self._removeInducedTag(tag, sourceVertex, vertex)            

    def _addInducedTag(self, tag, vertex, targetVertex):
        if not self._inducedTags.has_key(vertex):
            self._inducedTags[vertex] = {}    
        inducedTags = self._inducedTags.get(vertex)
        
        if inducedTags.has_key(tag):
            inducedTags[tag].add(targetVertex)
            event.manager.notifyObservers(self, event.PROPERTY_CHANGED,
                                          ('inducedTags',event.PC_ADDED,(tag,vertex,targetVertex),None))
        else:
            inducedTags[tag] = set([targetVertex])
            event.manager.notifyObservers(self, event.PROPERTY_CHANGED,
                                          ('inducedTags',event.PC_ADDED,(tag,vertex,targetVertex),None))
            # proceed recursively
            for sourceVertex in self._getSourceVertices(vertex):
                self._addInducedTag(tag, sourceVertex, vertex)

    def _removeInducedTag(self, tag, vertex, targetVertex):
        self._inducedTags[vertex][tag].remove(targetVertex)
        event.manager.notifyObservers(self, event.PROPERTY_CHANGED,
                                      ('inducedTags',event.PC_REMOVED,None,(tag,vertex,targetVertex)))

        if not self._inducedTags[vertex][tag]:
            # no, the induced tag for the vertex anymore
            del self._inducedTags[vertex][tag]

            if not self._inducedTags[vertex]:
                # no induced tags for the vertex anymore                
                del self._inducedTags[vertex]
        
            # recursively
            if not self._tags.has_key(vertex) or \
                   not self._tags[vertex].has_key(tag):
                # no, the tag for sources
                for sourceVertex in self._getSourceVertices(vertex):
                    self._removeInducedTag(tag, sourceVertex, vertex)
