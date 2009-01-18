
from tests.ast import ASTTestCase

from astvis.model import flow, ast


class FlowTest(ASTTestCase):
    def browse(self):
        import gtk
        from astvis.misc.browser import Browser
        objectBrowser = Browser('browser', self.flowModel)
        objectBrowser.window.connect('destroy', gtk.main_quit)
        gtk.main()

class SpMtxAggregate(FlowTest):

    FILENAME="fortran/SpMtx_aggregation.F90.f90.xml"

    def setUp(self):
        super(SpMtxAggregate, self).setUp()
        aggregateSubprogram = self.astModel.files[0].units[0].subprograms[0]
        self.flowModel = flow.ControlFlowModel(aggregateSubprogram)        

    def testCreate(self):
        self.assertEqual(self.flowModel.code.name, "SpMtx_aggregate")

class Fib(FlowTest):

    FILENAME="fortran/fib.f90.xml"

    def setUp(self):
        super(Fib, self).setUp()
        fibSubprogram = self.astModel.files[0].units[0].subprograms[0]
        self.flowModel = flow.ControlFlowModel(fibSubprogram)        

    def testCreate(self):
        self.assertEqual(self.flowModel.code.name, "Fibonacci")


    def testEndBlock(self):
        block = self.flowModel.startBlock

        blocks = []
        while block!=None:
            blocks.append(block)
            block = block.getEndBlock()
                
        self.assertEquals(len(blocks), 3)

    def testNextBasicBlocks1(self):
        block = self.flowModel.startBlock
        blocks1 = []
        while block!=None:
            blocks1.append(block)
            endBlock = block.getEndBlock()
            block = endBlock!=None and endBlock.getFirstBasicBlock() or None

        block = self.flowModel.startBlock
        blocks2 = []
        while block!=None:
            blocks2.append(block)
            nextBlocks = block.getNextBasicBlocks()
            block = nextBlocks and nextBlocks[-1] or None

        self.assertEquals(blocks1,blocks2)

    def testNextBasicBlocks0(self):
        block = self.flowModel.startBlock
        blocks = []
        while block!=None:
            blocks.append(block)
            nextBlocks = block.getNextBasicBlocks()
            block = nextBlocks and nextBlocks[0] or None

        self.assertEqual(len(blocks), 6)

    def testGetConnections(self):
        connections = self.flowModel.getConnections()
        #for f,t in connections:
        #    print f, "--->", t
        self.assertEquals(len(connections), 8)
