
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
        block = self.flowModel.block.getFirstBasicBlock()

        blocks = []
        while block!=None:
            blocks.append(block)
            block = block.getEndBlock()
                
        self.assertEquals(len(blocks), 3)

    def testNextBasicBlocks1(self):
        block = self.flowModel.block.getFirstBasicBlock()
        blocks1 = []
        while block!=None:
            blocks1.append(block)
            endBlock = block.getEndBlock()
            block = endBlock!=None and endBlock.getFirstBasicBlock() or None

        block = self.flowModel.block.getFirstBasicBlock()
        blocks2 = []
        while block!=None:
            blocks2.append(block)
            nextBlocks = block.getNextBasicBlocks()
            block = nextBlocks and nextBlocks[-1] or None

        self.assertEquals(blocks1,blocks2)

    def testNextBasicBlocks0(self):
        block = self.flowModel.block.getFirstBasicBlock()
        blocks = []
        while block!=None:
            blocks.append(block)
            nextBlocks = block.getNextBasicBlocks()
            block = nextBlocks and nextBlocks[0] or None

        self.assertEqual(len(blocks), 6)

    def testGetConnections(self):
        connections = self.flowModel.getConnections()
        self.assertEquals(len(connections), 8)

    def testClassifyConnectionsBy(self):
        connections = self.flowModel.getConnections()
        block = self.flowModel.block
        codeBlock = block.subBlocks[1]
        blocks = [block.subBlocks[0]] + [block.subBlocks[2]] + block.subBlocks[1].subBlocks
        clConnections = self.flowModel.classifyConnectionsBy(connections, blocks)

        #for key in clConnections.keys():
        #    print '--', key, ':', map(lambda x: (str(x[0]),str(x[1])), clConnections[key])

        self.assertEquals(len(clConnections), 5)
        
        startToIf1 = block.subBlocks[0], codeBlock.subBlocks[0]
        self.assertEquals(len(clConnections[startToIf1]), 1)
        
        if1ToIf2 = codeBlock.subBlocks[0], codeBlock.subBlocks[1]
        self.assertEquals(len(clConnections[if1ToIf2]), 2)
        
        if2ToEnd = codeBlock.subBlocks[1], block.subBlocks[2]
        self.assertEquals(len(clConnections[if2ToEnd]), 2)
        

    def testClassifyConnectionsBy2(self):
        "test with unfolded if1 block"
        connections = self.flowModel.getConnections()
        block = self.flowModel.block
        codeBlock = block.subBlocks[1]
        if1Block = codeBlock.subBlocks[0]
        if2Block = codeBlock.subBlocks[1]
        blocks = [block.subBlocks[0]] + [block.subBlocks[2]] + \
                 if1Block.subBlocks + [if2Block]
        clConnections = self.flowModel.classifyConnectionsBy(connections, blocks)

        #for key in clConnections.keys():
        #    print '--', key, ':', map(lambda x: (str(x[0]),str(x[1])), clConnections[key])

        self.assertEquals(len(clConnections), 6)
        
        startToIf1Cond = block.subBlocks[0], if1Block.subBlocks[0]
        self.assertEquals(len(clConnections[startToIf1Cond]), 1)
        
        if1CondToIf2 = if1Block.subBlocks[0], codeBlock.subBlocks[1]
        self.assertEquals(len(clConnections[if1CondToIf2]), 1)
        
        if2ToEnd = codeBlock.subBlocks[1], block.subBlocks[2]
        self.assertEquals(len(clConnections[if2ToEnd]), 2)


class Loop(FlowTest):

    FILENAME="fortran/loop.f90.xml"

    def setUp(self):
        super(Loop, self).setUp()
        sumSubprogram = self.astModel.files[0].units[0].subprograms[0]
        self.flowModel = flow.ControlFlowModel(sumSubprogram)        

    def testCreate(self):
        self.assertEqual(self.flowModel.code.name, "Sum")
        self.assertEqual(len(self.flowModel.code.statementBlock.statements), 4)

    def testGetConnections(self):
        connections = self.flowModel.getConnections()
        self.assertEquals(len(connections), 17)

    def testCollectASTObjects(self):
        astObjects = self.flowModel.collectASTObjects()

        #for block, objs in astObjects.items():
        #    print block, len(objs)

        # statements in total
        self.assertEquals(len(astObjects[self.flowModel.block]), 19)
