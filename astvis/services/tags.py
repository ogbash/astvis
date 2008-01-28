
from astvis import action
from astvis.project import TagTypeList, TagType

class TagService(object):
    @action.Action('new-tag', 'New tag', targetClass=TagTypeList)
    def newTag(self, target, context):
        target.append(TagType('(unnamed)'))

