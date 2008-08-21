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

from astvis.xmlmap import XMLWriter

from astvis.model import ast

f1 = ast.File(None)
f1.name = 'myfile.f90'
f2 = ast.File(None)
f2.name = 'myfile2.f90'
p1 = ast.ProgramUnit(None, parent=f1)
p1.name = 'module1'
f1.units.append(p1)
p2 = ast.ProgramUnit(None, parent=f1)
p2.name = 'module2'
f1.units.append(p2)
s1 = ast.Subprogram(None, parent=p1)
s1.name = 'Sub1'
p1.subprograms.append(s1)
s2 = ast.Subprogram(None, parent=p1)
s2.name = 'Sub2'
p1.subprograms.append(s2)

w = XMLWriter([ast.File, ast.ProgramUnit, ast.Subprogram], [f1, f2])
for c in w._chains:
    print '---\n',c
w.saveFile('my.xml')
