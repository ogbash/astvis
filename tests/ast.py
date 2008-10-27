
import unittest
from astvis.model import ast
from astvis import xmltool

class ASTTestCase(unittest.TestCase):
    "Base class for tests require AST."

    FILENAME="tests/pcg_ast.xml.gz"

    def setUp(self):
        filename = self.FILENAME
        astModel = ast.ASTModel()
        astModel.filename = filename
        loader = xmltool.XMLLoader(astModel)
        astModel.files = loader.loadFile(filename)
        self.astModel = astModel
