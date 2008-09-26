#! /usr/bin/env python

# debug levels
FINE=5
FINER=3
FINEST=1

class DragInfo:
    def __init__(self, name, number):
        self.name = name
        self.number = number

INFO_TEXT=DragInfo("text/plain", 1)
 # starting with projects in root:
 #  data of type "list(int|string)" where int is used as index in list or tuples
 #   and string is used with getattr()
INFO_PROJECTS_ATTRPATH=DragInfo("python-object/projects-attrpath", 2)
INFO_OBJECT_PATH=DragInfo("python-object/class-and-path", 3)

OPTIONS = {
    "view MPI tags": False
}

