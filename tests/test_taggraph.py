
import unittest
from astvis import taggraph

class TagGraphTest(unittest.TestCase):

    def testInit(self):
        def gtv(vertex):
            pass
        def gsv(vertex):
            pass
        
        tg=taggraph.TagGraph(gtv, gsv)
        self.assertNotEquals(tg, None)

    def testAdd(self):
        class Vertex:
            def __init__(self, number, targets, sources):
                self.number = number
                self.targets = targets
                self.sources = sources
            def __str__(self):
                return "Vertex(%d)" % self.number
            __repr__=__str__
        
        graph = \
              {1: Vertex(1, set([2,3]), set()), # number, target, source
               2: Vertex(2, set(), set([1])),
               3: Vertex(3, set([4]), set([1])),
               4: Vertex(4, set(), set([3]))}
        
        def gtv(vertex):
            return map(lambda x: graph[x], vertex.targets)
            
        def gsv(vertex):
            return map(lambda x: graph[x], vertex.sources)
        
        tg=taggraph.TagGraph(gtv, gsv)
        tg.addTag('cool', graph[3], 'cool')

        self.assertEquals(len(tg._tags), 1)
        self.assertEquals(tg._tags.keys(), [graph[3]])
        self.assertEquals(tg._tags[graph[3]]['cool'], set(['cool']))

        tg=taggraph.TagGraph(gtv, gsv)
        tg.addTag('cool', graph[4], 'cool')

        self.assertEquals(len(tg._tags), 1)
        self.assertEquals(set(tg._inducedTags.keys()), set([graph[1],graph[3]]))
        self.assertEquals(tg._inducedTags[graph[1]].keys(), ['cool'])
        self.assertEquals(tg._inducedTags[graph[3]].keys(), ['cool'])
