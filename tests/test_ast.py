
from tests.ast import ASTTestCase

class LoadAST(ASTTestCase):

    def testLoad(self):
        self.assert_(self.astModel!=None)

