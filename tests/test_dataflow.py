
import tests.ast
from astvis import core

class DataflowTestCase(tests.ast.ASTTestCase):

    def setUp(self):
        super(DataflowTestCase, self).setUp()

        from astvis import services
        core.registerServices(services.dataflow)
        
        self.service = core.getService('DataflowService')

    def testMe(self):
        print self.service

