# import packages from modules directory
import sys, os
pathname = os.path.dirname(sys.argv[0])
sys.path.append(os.path.join(os.path.abspath(pathname), '..'))

from astvis.xmlmap import XMLWriter

from astvis.model import ast

f1 = ast.File(None)
f1.name = 'myfile.f90'
f2 = ast.File(None)
f2.name = 'myfile2.f90'
w = XMLWriter([ast.File, ast.ProgramUnit, ast.Subprogram], [f1, f2])
w.saveFile('my.xml')
