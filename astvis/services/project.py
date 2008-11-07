from astvis import widgets
from astvis.project import TagTypeList, DiagramList, TagType, Concepts
from astvis.calldiagram import CallDiagram
from astvis.generaldiagram import GeneralDiagram
from astvis import model
from astvis import action, core

class ProjectService(core.Service):

    conceptTypes = {'activity':model.concept.Activity,
                    'data':model.concept.Data}
    
    @action.Action('project-new-tag-type', 'New tag', targetClass=TagTypeList, contextClass=widgets.ProjectTree)
    def newTagType(self, tagList, context):
        tagList.append(TagType(tagList.project, '(unnamed)'))

    @action.Action('project-new-diagram', 'New diagram', targetClass=DiagramList, contextClass=widgets.ProjectTree)
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

    @action.Action('project-new-concept', 'New concept', contextClass=widgets.ConceptTree)
    def newConcept(self, obj, context):
        conceptList = context.concepts
        dialog = widgets.ConceptDialog(self.conceptTypes)
        if dialog.run()>0:
            if dialog.conceptType=='activity':
                concept = model.concept.Activity(conceptList.project)
            elif dialog.conceptType=='data':
                concept = model.concept.Data(conceptList.project)
            else:
                raise "Unknown concept type: %s" % dialog.concepType

            if dialog.conceptName:
                concept.name = dialog.conceptName
                
            conceptList.append(concept)

    @action.Action('concept-edit', 'Edit concept', targetClass=model.concept.Concept)
    def editConcept(self, obj, context):
        concept = obj
        dialog = widgets.ConceptDialog(self.conceptTypes, concept=concept)
        
        if dialog.run()>0:
            if dialog.conceptName:
                concept.name = dialog.conceptName
