
import tests.ast
from astvis import core
from astvis.model import flow

class FibonacciTestCase(tests.ast.ASTTestCase):
    "Test case that tests dataflow on fibonacci algorithm."

    FILENAME="fortran/fib.f90.xml"

    def setUp(self):
        super(FibonacciTestCase, self).setUp()

        from astvis import services
        core.registerServices(services.dataflow)
        core.registerServices(services.controlflow)
        
        self.service = core.getService('DataflowService')
        subprogram = self.astModel.files[0].units[0].subprograms[0]
        cfService = core.getService('ControlflowService')
        self.flowModel = cfService.getModel(subprogram)

    def testFilesLoad(self):
        "Test that file is loaded into AST model."
        self.assertNotEqual(self.astModel, None)
        self.assertEqual(len(self.astModel.files), 1)

    def testFibonacci(self):
        "Test that module has function named 'fibonacci'"
        
        fibModule = self.astModel.files[0].units[0]
        fibonacciFunction = fibModule.subprograms[0]

        self.assertEquals(fibonacciFunction.name.lower(), "fibonacci")

    def testReachingDefinitions(self):
        "Test reaching definition algorithm for fibonacci function"
        
        fibModule = self.astModel.files[0].units[0]
        fibonacciFunction = fibModule.subprograms[0]

        ins, outs = self.service.getReachingDefinitions(fibonacciFunction)
        
        # more tests for the result follow here
        print ins
        print outs


class SpMtxAggregate(tests.ast.ASTTestCase):
    "Test case that tests dataflow on SpMtx_aggregate algorithm."

    FILENAME="fortran/SpMtx_aggregation.F90.xml"

    def setUp(self):
        super(SpMtxAggregate, self).setUp()

        from astvis import services
        core.registerServices(services.dataflow)
        core.registerServices(services.controlflow)
        
        self.service = core.getService('DataflowService')
        subprogram = self.astModel.files[0].units[0].subprograms[0]
        cfService = core.getService('ControlflowService')
        self.flowModel = cfService.getModel(subprogram)

    def testFilesLoad(self):
        "Test that file is loaded into AST model."
        self.assertNotEqual(self.astModel, None)
        self.assertEqual(len(self.astModel.files), 1)

    def testReachingDefinitions(self):
        "Test reaching definition algorithm for the aggregate subprogram"
        
        module = self.astModel.files[0].units[0]
        function = module.subprograms[0]

        ins, outs = self.service.getReachingDefinitions(function)
        
        # more tests for the result follow here
        print ins
        print outs


    def testUsedDefinitions(self):
        "Test used definitions algorithm for the aggregate subprogram"
        
        module = self.astModel.files[0].units[0]
        function = module.subprograms[0]

        block = self.flowModel.block
        codeBlock = block.subBlocks[1]

        usedDefs = self.service.getUsedDefinitions(codeBlock.subBlocks[6])
        
        # more tests for the result follow here
        print usedDefs

