
from astvis import action, core
from astvis.project import TagTypeList, TagType
from astvis.widgets import TagDialog
from astvis.model import ast

class TagService(core.Service):

    @action.Action('ast-edit-tags', 'Edit tags', targetClass=ast.ASTObject)
    def handleTagDialog(self, obj, context):
        dialog = TagDialog(obj)
        res = dialog.run()
        if res>0:
            pass # changes done in run()
