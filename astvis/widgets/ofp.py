
import gtk
import os.path

class NewASTXMLDialog:
    def __init__(self):
        wTree = gtk.glade.XML("astvisualizer.glade", 'newastxml_dialog')
        wTree.signal_autoconnect(self)
        self.wTree = wTree
        self.widget = wTree.get_widget('newastxml_dialog')
        self.filesButton = wTree.get_widget('newastxml_file')
        self.includedirsButton = wTree.get_widget('newastxml_includedirs')
        self.okButton = wTree.get_widget('newastxml_ok')
        self.okButton.set_sensitive(False)

    def run(self):
        res = self.widget.run()
        if res > 0:
            self.filename=self._extractFilename()
            
        self.widget.destroy()     
        return res

    def _extractFilename(self):
        return self.filesButton.get_filename()

    def _file_set(self, w):
        name=self._extractFilename()
        if name and os.path.isfile(name):
            self.okButton.set_sensitive(True)

