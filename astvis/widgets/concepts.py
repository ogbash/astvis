
import gtk


class NewConceptDialog:
    def __init__(self, conceptTypes):
        wTree = gtk.glade.XML("astvisualizer.glade", 'newconcept_dialog')
        wTree.signal_autoconnect(self)
        self.wTree = wTree
        self.widget = wTree.get_widget('newconcept_dialog')

        self.conceptTypeModel = gtk.ListStore(str)
        for t in conceptTypes:
            self.conceptTypeModel.append((t,))
            
        self.conceptTypeBox = wTree.get_widget('concept_type')
        cell = gtk.CellRendererText()
        self.conceptTypeBox.pack_start(cell, True)
        self.conceptTypeBox.add_attribute(cell, 'text', 0)  
        self.conceptTypeBox.set_model(self.conceptTypeModel)
        self.conceptTypeBox.set_active(0)
        
        self.conceptNameEntry = wTree.get_widget('concept_name')


    def run(self):
        res = self.widget.run()
        if res > 0:
            type_ = self.conceptTypeBox.get_active_text()
            name = self.conceptNameEntry.get_text()
            self.conceptType = type_
            self.conceptName = name
            
        self.widget.destroy()            
        return res
        
