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
#INFO_OBJECT_NAME=DragInfo("python-object/class-and-name", 2)
INFO_OBJECT_PATH=DragInfo("python-object/class-and-path", 3)

OPTIONS = {
    "view MPI tags": False
}

