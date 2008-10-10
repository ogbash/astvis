# import packages from modules directory
import sys, os
pathname = os.path.dirname(sys.argv[0])
sys.path.append(os.path.join(os.path.abspath(pathname), '..'))

# logging
import logging
from astvis.common import FINE, FINER, FINEST
if __name__=="__main__":
    logging.addLevelName(FINE, "FINE")
    logging.addLevelName(FINER, "FINER")
    logging.addLevelName(FINEST, "FINEST")    
    #logging.basicConfig(level=FINEST)
    import logging.config
    logging.config.fileConfig("../logging.conf")
    logging.getLogger('xmlmap').setLevel(FINEST)

from astvis.model import concept
from astvis.generaldiagram import GeneralDiagram

diagram = GeneralDiagram('test diagram', None)
obj=concept.Data('data')
diagram.add(obj)

