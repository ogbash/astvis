from astvis import widgets
from astvis.project import *

class ProjectService(object):
    @action.Action('new-tag-type', 'New tag', targetClass=TagTypeList, contextClass=widgets.ProjectTree)
    def newTagType(self, tagList, context):
        tagList.append(TagType(tagList.project, '(unnamed)'))

    @action.Action('new-diagram', 'New diagram', targetClass=DiagramList, contextClass=widgets.ProjectTree)
    def newDiagram(self, diagrams, context):
        diagram = CallDiagram('(call diagram)', diagrams.project)
        diagrams.append(diagram)

    @action.Action('show-tagged-objects', 'Show objects', targetClass=TagType, contextClass=widgets.ProjectTree)
    def showTaggedObjects(self, tag, context):
        objs = []
        for obj,tags in tag.project.tags.items():
            if tag in tags:
                objs.append(obj)
        
        dialog = TaggedObjectsList(tag, objs, root=context.root)
        dialog.run()
