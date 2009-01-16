
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
            block = block.getEndBlock().getFirstBasicBlock()
            blocks.append(block)
                
        self.assertEquals(len(blocks), 4)

    def testNextBasicBlocks1(self):
        block = self.flowModel.startBlock
        blocks1 = []
        while block!=None:
            block = block.getEndBlock().getFirstBasicBlock()
            blocks1.append(block)

        block = self.flowModel.startBlock
        blocks2 = []
        while block!=None:
            block = block.getNextBasicBlocks()[-1]
            blocks2.append(block)

        self.assertEquals(blocks1,blocks2)

    def testNextBasicBlocks0(self):
        block = self.flowModel.startBlock
        blocks = []
        while block!=None:
            block = block.getNextBasicBlocks()[0]
            blocks.append(block)

        print map(str,blocks)
