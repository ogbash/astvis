from astvis import widgets
from astvis.project import TagTypeList, DiagramList, TagType, ConceptList
from astvis.calldiagram import CallDiagram
from astvis.generaldiagram import GeneralDiagram
from astvis import model
from astvis import action

class ProjectService(object):
    @action.Action('new-tag-type', 'New tag', targetClass=TagTypeList, contextClass=widgets.ProjectTree)
    def newTagType(self, tagList, context):
        tagList.append(TagType(tagList.project, '(unnamed)'))

    @action.Action('new-diagram', 'New diagram', targetClass=DiagramList, contextClass=widgets.ProjectTree)
    def newDiagram(self, diagrams, context):
        dialog = widgets.NewDiagramDialog(['general','call'])
        if dialog.run()>0:
            diagramName = dialog.diagramName or "(unnamed)"
            if dialog.diagramType=="general":
                diagram = GeneralDiagram(diagramName, diagrams.project)
            elif dialog.diagramType=="call":
                diagram = CallDiagram(diagramName, diagrams.project)
            else:
                raise "Unknown diagram type: %s" % dialog.diagramType
                
            diagrams.append(diagram)

    @action.Action('show-tagged-objects', 'Show objects', targetClass=TagType, contextClass=widgets.ProjectTree)
    def showTaggedObjects(self, tag, context):
        objs = []
        for obj,tags in tag.project.tags.items():
            if tag in tags:
                objs.append(obj)
        
        dialog = TaggedObjectsList(tag, objs, root=context.root)
        dialog.run()

    @action.Action('new-concept', 'New concept', targetClass=ConceptList, contextClass=widgets.ProjectTree)
    def newConcept(self, conceptList, context):
        dialog = widgets.NewConceptDialog(['activity','data'])
        if dialog.run()>0:
            if dialog.conceptType=='activity':
                concept = model.concept.Activity()
            elif dialog.conceptType=='data':
                concept = model.concept.Data()
            else:
                raise "Unknown concept type: %s" % dialog.concepType

            if dialog.conceptName:
                concept.name = dialog.conceptName
                
            conceptList.append(concept)
