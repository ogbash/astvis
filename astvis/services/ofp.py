
import os

from astvis import action, core
from astvis.widgets.ofp import NewASTXMLDialog

class OFPService(core.Service):
    "Actions for Open Fortran Parser, eg generate XML from fortran files."

    @action.Action('main-generate-ofp-astxml', 'Generate AST XML')
    def generateASTXML(self, target, context):
        dialog=NewASTXMLDialog()
        if dialog.run()>0:
            filepath = dialog.filename
            filename = os.path.basename(filepath)
            xmlname = "%s.xml" % filename
            dirpath = os.path.dirname(filepath)
            os.spawnlp(os.P_WAIT, 'java', 'java', '-jar', 'parser/ofp/FortranCPR.jar',
                       filename,
                       '-X', os.path.join(dirpath,xmlname),
                       '-I', dirpath,
                       '-O', dirpath)

