
import gtk.glade
from astvis import action
from astvis.model import ast

__all__=['TagTypeDialog','TagDialog']

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

class TaggedObjectsList:
    
    def __init__(self, tag, objs, root):
        self.tag = tag
        self.objs = objs
        self.root = root
    
        wTree = gtk.glade.XML("astvisualizer.glade", 'taggedobjects_dialog')
        wTree.signal_autoconnect(self)
        self.wTree = wTree
        self.widget = wTree.get_widget('taggedobjects_dialog')
        
        objsView = wTree.get_widget('tobjects_list')

        column = gtk.TreeViewColumn("Object")
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 1)
        objsView.append_column(column)

        column = gtk.TreeViewColumn("File")
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 2)
        objsView.append_column(column)
        
        column = gtk.TreeViewColumn("Row")
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 3)
        objsView.append_column(column)

        column = gtk.TreeViewColumn("Column")
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 4)
        objsView.append_column(column)

        objsModel = gtk.ListStore(object,str,str,str,str)
        objsView.set_model(objsModel)
        self.objsModel = objsModel
        self.objsView = objsView

        objsView.connect("button-press-event", self._buttonPress)

        for obj in self.objs:
            filename = obj.getFile().name
            line = ""
            column = ""
            if obj.location!=None:
                line=str(obj.location.begin.line)
                column=str(obj.location.begin.column)                    
                           
            objsModel.append((obj, str(obj), filename, line, column))

    def run(self):
        try:
            res = self.widget.run()
        finally:
            self.widget.destroy()
        
    def _buttonPress(self, widget, event):
        if event.type==gtk.gdk._2BUTTON_PRESS:
            _model, iRow = self.objsView.get_selection().get_selected()
            obj = _model[iRow][0]
            astViews = filter(lambda x: x.__class__.__name__=="AstTree", self.root.views.keys())
            if astViews:
                astViews[0].selectObject(obj)
                return True
        
        return False
