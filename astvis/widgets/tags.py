
import gtk.glade
from astvis import action
from astvis.model import ast

__all__=['TagTypeDialog','TagDialog','handleTagDialog']

class TagTypeDialog:
    def __init__(self, tagType):
        self.tagType = tagType
    
        wTree = gtk.glade.XML("astvisualizer.glade", 'tagtype_dialog')
        wTree.signal_autoconnect(self)
        self.wTree = wTree
        self.widget = wTree.get_widget('tagtype_dialog')
        self.nameEntry = wTree.get_widget('tag_name')
        self.nameEntry.set_text(tagType.name)
        self.colorButton = wTree.get_widget('tagcolor_button')
        self.colorButton.set_color(tagType.color)

    def run(self):
        res = self.widget.run()
        if res > 0:
            name = self.nameEntry.get_text()
            color = self.colorButton.get_color()
            self.tagType.name = name
            self.tagType.color = color
            
        self.widget.destroy()            
        return res

@action.Action('edit-tags', 'Edit tags', targetClass=ast.ASTObject)
def handleTagDialog(obj, context):
    dialog = TagDialog(obj)
    res = dialog.run()
    if res>0:
        pass

class TagDialog:
    def __init__(self, obj):
        self.obj = obj
    
        wTree = gtk.glade.XML("astvisualizer.glade", 'tag_dialog')
        wTree.signal_autoconnect(self)
        self.wTree = wTree
        self.widget = wTree.get_widget('tag_dialog')
        
        tagView = wTree.get_widget('tag_list')

        column = gtk.TreeViewColumn()
        cell = gtk.CellRendererToggle()
        column.pack_start(cell, False)
        cell.connect('toggled', self.__toggled)        
        column.add_attribute(cell, "active", 1)
        tagView.append_column(column)

        column = gtk.TreeViewColumn("Tag")
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 2)
        tagView.append_column(column)
        
        tagModel = gtk.ListStore(object,bool,str)
        tagView.set_model(tagModel)
        self.tagModel = tagModel

        self.project = obj.model.project
        for tagType in self.project.tagTypes:
            if self.project.tags.has_key(obj) and tagType in self.project.tags[obj]:
                active = True
            else:
                active = False
            tagModel.append((tagType,active,tagType.name))

    def __toggled(self, toggle, path):
        active = toggle.get_active()
        self.tagModel[path][1] = not active

    def run(self):
        res = self.widget.run()
        if res > 0:
            tags = set()
            for tagType,active,name in self.tagModel:
                if active:
                    tags.add(tagType)
            
            self.project.tags[self.obj] = tags
            
        self.widget.destroy()
        return res

