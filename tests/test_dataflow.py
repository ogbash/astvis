
import tests.ast
from astvis import core

class FibonacciTestCase(tests.ast.ASTTestCase):
    "Test case that tests dataflow on fibonacci algorithm."

    FILENAME="fortran/fib.f90.xml"

    def setUp(self):
        super(FibonacciTestCase, self).setUp()

        from astvis import services
        core.registerServices(services.dataflow)
        core.registerServices(services.controlflow)
        
        self.service = core.getService('DataflowService')

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

    def testFilesLoad(self):
        "Test that file is loaded into AST model."
        self.assertNotEqual(self.astModel, None)
        self.assertEqual(len(self.astModel.files), 1)

    def testReachingDefinitions(self):
        "Test reaching definition algorithm for fibonacci function"
        
        fibModule = self.astModel.files[0].units[0]
        fibonacciFunction = fibModule.subprograms[0]

        ins, outs = self.service.getReachingDefinitions(fibonacciFunction)
        
        # more tests for the result follow here
        print ins
        print outs

