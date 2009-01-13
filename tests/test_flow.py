
from tests.ast import ASTTestCase

from astvis.model import flow, ast

class ControlFlow(ASTTestCase):

    def setUp(self):
        super(ControlFlow, self).setUp()
        aggregateSubprogram = self.astModel.files[0].units[0].subprograms[0]
        self.flowModel = flow.ControlFlowModel(aggregateSubprogram)        

    def testCreate(self):
        self.assertEqual(self.flowModel.code.name, "SpMtx_aggregate")

#    def
