
import gtk.glade

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

