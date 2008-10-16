
import gtk


class ConceptDialog:
    def __init__(self, conceptTypes, concept=None):
        wTree = gtk.glade.XML("astvisualizer.glade", 'concept_dialog')
        wTree.signal_autoconnect(self)
        self.wTree = wTree
        self.widget = wTree.get_widget('concept_dialog')

        # concept types
        self.conceptTypeModel = gtk.ListStore(str)
        conceptTypeList = conceptTypes.items()
        for i, (tname, t) in enumerate(conceptTypeList):
            self.conceptTypeModel.append((tname,))
            if isinstance(concept, t):
                conceptTypeIndex = i
            
        self.conceptTypeBox = wTree.get_widget('concept_type')
        cell = gtk.CellRendererText()
        self.conceptTypeBox.pack_start(cell, True)
        self.conceptTypeBox.add_attribute(cell, 'text', 0)  
        self.conceptTypeBox.set_model(self.conceptTypeModel)
        if concept==None:
            self.conceptTypeBox.set_active(0)
        else:
            self.conceptTypeBox.set_active(conceptTypeIndex)
            self.conceptTypeBox.set_sensitive(False)

        # concept name
        self.conceptNameEntry = wTree.get_widget('concept_name')
        if concept!=None:
            self.conceptNameEntry.set_text(concept.name)

    def run(self):
        res = self.widget.run()
        if res > 0:
            type_ = self.conceptTypeBox.get_active_text()
            name = self.conceptNameEntry.get_text()
            self.conceptType = type_
            self.conceptName = name
            
        self.widget.destroy()            
        return res
        
