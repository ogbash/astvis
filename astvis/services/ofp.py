import logging
LOG = logging.getLogger("services.ofp")
from astvis.common import FINE, FINER, FINEST

import os

from astvis import action, core
from astvis.widgets.ofp import NewASTXMLDialog

class OFPService(core.Service):
    "Actions for Open Fortran Parser, eg generate XML from fortran files."

    @action.Action('main-generate-ofp-astxml', 'Generate AST XML')
    def generateASTXML(self, target, context):
        dialog=NewASTXMLDialog()
        if dialog.run()>0:
            dirpath = dialog.directoryName
            xmlFilename = dialog.xmlFilename
            fortranFiles = list(dialog.filenames)
            if not xmlFilename:
                xmlFilename="%s.xml" % fortranFiles[0]
            relFortranFiles = []
            for name in fortranFiles:
                if name.startswith(dirpath):
                    name = name[len(dirpath):]
                    if name[0]==os.path.sep:
                        name = name[1:]
                    relFortranFiles.append(name)
            dirnames = list(dialog.dirnames)

            commandLine = ['java', '-Xmx512M', '-jar', 'parser/ofp/FortranCPR.jar',
                       '-X', os.path.join(dirpath,xmlFilename),
                       '-O', dirpath,
                       '-I', dirpath]
            if dirnames:
                commandLine.append("-P")
                commandLine.append(",".join(dirnames))
            commandLine.extend(relFortranFiles)

            LOG.info("Running %s", " ".join(commandLine))
            os.spawnvp(os.P_WAIT, 'java', commandLine)

