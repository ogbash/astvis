
from astvis.model import ast
from astvis import xmltool
from tests import general

class ASTTestCase(general.TestCase):
    "Base class for tests require AST."

    FILENAME="fortran/SpMtx_aggregation.F90.xml"

    def setUp(self):
        super(ASTTestCase, self).setUp()
        
        filename = self.FILENAME
        astModel = ast.ASTModel()
        astModel.filename = filename
        loader = xmltool.XMLLoader(astModel)
        astModel.files = loader.loadFile(filename)
        self.astModel = astModel
