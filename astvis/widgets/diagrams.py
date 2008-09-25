
import gtk

class NewDiagramDialog:
    def __init__(self, diagramTypes):
        wTree = gtk.glade.XML("astvisualizer.glade", 'newdiagram_dialog')
        wTree.signal_autoconnect(self)
        self.wTree = wTree
        self.widget = wTree.get_widget('newdiagram_dialog')

        self.diagramTypeModel = gtk.ListStore(str)
        for t in diagramTypes:
            self.diagramTypeModel.append((t,))
            
        self.diagramTypeBox = wTree.get_widget('diagram_type')
        cell = gtk.CellRendererText()
        self.diagramTypeBox.pack_start(cell, True)
        self.diagramTypeBox.add_attribute(cell, 'text', 0)  
        self.diagramTypeBox.set_model(self.diagramTypeModel)
        self.diagramTypeBox.set_active(0)
        
        self.diagramNameEntry = wTree.get_widget('diagram_name')


    def run(self):
        res = self.widget.run()
        if res > 0:
            type_ = self.diagramTypeBox.get_active_text()
            name = self.diagramNameEntry.get_text()
            self.diagramType = type_
            self.diagramName = name
            
        self.widget.destroy()            
        return res
        
