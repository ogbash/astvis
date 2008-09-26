
from astvis.transfer import externalize, internalize

class Concept:
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

    def __init__(self, project):
        Concept.__init__(self, project)
        self.name = "(noname)"

class Data(Concept):

    def __init__(self, project):
        Concept.__init__(self, project)
        self.name = "(noname)"
