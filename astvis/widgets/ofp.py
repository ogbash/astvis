
import gtk
import os.path

class NewASTXMLDialog:
    def __init__(self):
        wTree = gtk.glade.XML("astvisualizer.glade", 'newastxml_dialog')
        wTree.signal_autoconnect(self)
        self.wTree = wTree
        self.widget = wTree.get_widget('newastxml_dialog')
        self.directoryButton = wTree.get_widget('newastxml_directory')
        self.includedirsButton = wTree.get_widget('newastxml_includedirs')
        self.xmlFileEntry = wTree.get_widget('newastxml_xmlname')
        self.okButton = wTree.get_widget('newastxml_ok')
        self.okButton.set_sensitive(False)

        # fortran files
        self.addFilesButton = wTree.get_widget('newastxml_addfiles')
        self.fileListModel = gtk.ListStore(str)
        
        treeView = wTree.get_widget('newastxml_files')
        treeView.set_model(self.fileListModel)

        column = gtk.TreeViewColumn("File name")
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 0)
        treeView.append_column(column)

        # include directories
        self.addDirectoriesButton = wTree.get_widget('newastxml_adddirs')
        self.directoryListModel = gtk.ListStore(str)
        
        treeView = wTree.get_widget('newastxml_dirs')
        treeView.set_model(self.directoryListModel)

        column = gtk.TreeViewColumn("Directory name")
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 0)
        treeView.append_column(column)
        
    def run(self):
        res = self.widget.run()
        if res > 0:
            self.directoryName=self.directoryButton.get_filename()
            self.xmlFilename = self.xmlFileEntry.get_text()
            self.filenames = set()
            for (filename,) in self.fileListModel:
                self.filenames.add(filename)
            self.dirnames = set()
            for (dirname,) in self.directoryListModel:
                self.dirnames.add(dirname)
            
        self.widget.destroy()
        return res

    def _addFiles(self, widget):
        filesDialog = gtk.FileChooserDialog(title="Choose Fortran files to add",
                                            parent=self.widget,
                                            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                                     gtk.STOCK_OK, gtk.RESPONSE_OK))
        directory = self.directoryButton.get_filename()
        filesDialog.set_current_folder(directory)
        
        fileFilter = gtk.FileFilter()
        fileFilter.set_name("All files")
        fileFilter.add_pattern("*")
        filesDialog.add_filter(fileFilter)
        
        fileFilter = gtk.FileFilter()
        fileFilter.set_name("Fortran files")
        acceptedExts = ("f", "F", "f90", "F90", "f95", "F95")
        def filterFortranFiles(filterInfo):
            
            name = filterInfo[0]
            parts = name.rsplit('.')
            if parts[-1] in acceptedExts:
                if len(parts)>2 and parts[-2] in acceptedExts:
                    return False # ignore *.f90.F90, etc
                return True
            return False
        
        fileFilter.add_custom(gtk.FILE_FILTER_FILENAME, filterFortranFiles)
        filesDialog.add_filter(fileFilter)
        filesDialog.set_filter(fileFilter)
        
        filesDialog.props.select_multiple = True
        result = filesDialog.run()
        if result==gtk.RESPONSE_OK:
            existing = set()
            for (filename,) in self.fileListModel:
                existing.add(filename)
            
            for filename in filesDialog.get_filenames():
                if not filename in existing:
                    self.fileListModel.append((filename,))
            
        filesDialog.destroy()

        self.okButton.set_sensitive(len(self.fileListModel))


    def _addDirectories(self, widget):
        dirsDialog = gtk.FileChooserDialog(title="Choose include directories for CPP",
                                           parent=self.widget,
                                           action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                           buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                                    gtk.STOCK_OK, gtk.RESPONSE_OK))
                
        directory = self.directoryButton.get_filename()
        dirsDialog.set_current_folder(directory)

        dirsDialog.props.select_multiple = True
        result = dirsDialog.run()
        if result==gtk.RESPONSE_OK:
            existing = set()
            for (dirname,) in self.directoryListModel:
                existing.add(dirname)
            
            for dirname in dirsDialog.get_filenames():
                if not dirname in existing:
                    self.directoryListModel.append((dirname,))
            
        dirsDialog.destroy()
