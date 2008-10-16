
from astvis import event
from astvis.transfer import externalize, internalize

class Concept(object):
    "Concept on the concept diagram."
    def __init__(self, project):
        self.project = project

    def externalize(self):
        return self.project.concepts.index(self), externalize(self.project)

    @staticmethod
    def internalize(data):
        index, project = data[0], internalize(data[1])
        return project.concepts[index]

class Activity(Concept):

    def _setName(self, name): self._name = name
    name = property(lambda self: self._name, _setName)
    name = event.Property(name,'name')

    def __init__(self, project):
        Concept.__init__(self, project)
        self._name = "(noname)"

class Data(Concept):

    def _setName(self, name): self._name = name
    name = property(lambda self: self._name, _setName)
    name = event.Property(name,'name')

    def __init__(self, project):
        Concept.__init__(self, project)
        self._name = "(noname)"

class Flow:
    pass

class Use:
    pass
