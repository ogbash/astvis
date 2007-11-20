#!/usr/bin/env python

import logging
from astvis.common import FINE, FINER, FINEST
if __name__=="__main__":
    logging.addLevelName(FINE, "FINE")
    logging.addLevelName(FINER, "FINER")
    logging.addLevelName(FINEST, "FINEST")    
    #logging.basicConfig(level=FINEST)
    import logging.config
    logging.config.fileConfig("logging.conf")

LOG = logging.getLogger("main")

try:
    import pygtk
    pygtk.require('2.10')
except:
    pass

import gtk, gobject
gtk.gdk.threads_init()
import gtk.glade
import cairo
import gaphas
import gaphas.examples
import math
import pickle
from astvis import gaphasx, event, xmlmap, thread, core, widgets
from astvis.common import *
from astvis.project import Project
from astvis.calltree import CallTree
from astvis.asttree import AstTree
from astvis import widgets
from astvis.model import ast
from astvis.calldiagram import CallDiagram

class MainWindow:
    
    def __init__(self):
        self.project = None
        self.files = {} # model.File -> gtk.TextView

        self.wTree = gtk.glade.XML("astvisualizer.glade")
        self.mainWindow = self.wTree.get_widget("main_window")
        self.mainWindow.connect("destroy",gtk.main_quit)
        
        self.sidebarNotebook = self.wTree.get_widget('sidebar_notebook')
        self.taskProgressbars = self.wTree.get_widget('task_progressbars')
        gtklabel = self.taskProgressbars.get_parent().get_tab_label(self.taskProgressbars)
        import astvis.widgets.task
        self.taskHandler = astvis.widgets.task.TaskHandler(self.taskProgressbars, gtklabel)

        self.view = gaphas.view.GtkView()
        outer = self.wTree.get_widget("canvas_view_outer")
        self.view.show()
        outer.add(self.view)
        outer.set_hadjustment(self.view.hadjustment)
        outer.set_vadjustment(self.view.vadjustment)        
        self.view.connect("key-press-event", self.keyPress, None)
        self.view.drag_dest_set(gtk.DEST_DEFAULT_MOTION|gtk.DEST_DEFAULT_DROP,
                [(INFO_OBJECT_PATH.name,0,INFO_OBJECT_PATH.number)],
                gtk.gdk.ACTION_COPY)
        self.view.connect("drag-data-received", self._data_recv)

        tool = gaphas.tool.ToolChain()
        tool.append(gaphas.tool.HoverTool())
        tool.append(gaphasx.ConnectingTool())
        tool.append(gaphas.tool.ItemTool())
        tool.append(gaphas.tool.RubberbandTool())
        self.view.tool = tool

        self._initProjectTreeView()
        
        # ast tree view
        astTreeView = self.wTree.get_widget("ast_tree")
        self.astTree = AstTree(self, astTreeView)
        self.astTree.menu = self.wTree.get_widget('object_menu')
        
        # create call tree
        callTreeView = self.wTree.get_widget("call_tree")
        self.callTree = CallTree(self, callTreeView)

        # create back call tree
        backCallTreeView = self.wTree.get_widget("back_call_tree")
        self.backCallTree = widgets.BackCallTree(self, backCallTreeView)

        self.notebook = self.wTree.get_widget("notebook")

        self.wTree.signal_autoconnect(self)

        #self._setProject(Project(astFileName="tree.xml"))
        self._setProject(Project())
        self.diagram = CallDiagram(self.project)
        self.view.canvas = self.diagram.getCanvas()

    def _data_recv(self, widget, context, x, y, data, info, timestamp):
        LOG.debug("GTK DnD data_recv with info=%d"%info)
        if info==INFO_OBJECT_PATH.number:
            clazz, path = pickle.loads(data.data)
            if clazz==ast.ProgramUnit or clazz==ast.Subprogram:
                # get canvas coordinates
                m = cairo.Matrix(*self.view.matrix)
                m.invert()
                cx, cy = m.transform_point(x,y)
                # add item
                obj = self.project.astModel.getObjectByPath(path)
                item = self.diagram.add(obj, cx,cy)
                context.drop_finish(True, timestamp)
            else:
                context.drop_finish(False, timestamp)                
        else:
            context.drop_finish(False, timestamp)
         
    def newProject(self, obj):
        # self._setProject(Project())
        pass

    def _setProject(self, project):
        if self.project:
            LOG.info("%s is being replaced" % self.project)
        self.project = project
        if project:
            self.wTree.get_widget("astfile_chooserbutton").show()
            self.astTree.setProject(project)
        else:
            self.wTree.get_widget("astfile_chooserbutton").hide()

    def astFileChanged(self, obj):
        self.sidebarNotebook.set_current_page(self.sidebarNotebook.page_num(self.taskProgressbars))
        self._astFileChanged(obj.get_filename())

    @thread.threaded                
    def _astFileChanged(self, filename):
        LOG.debug("Loading %s" % filename)
        try:
            self.project._loadAstFile(filename)
        except(Exception), e:
            LOG.error("Error loading file, %s", e, exc_info=e)
        else:
            LOG.info("Loaded %s" % filename)
    
    
    def _initProjectTreeView(self):
        self.projectTreeView = self.wTree.get_widget("project_tree")
        column = gtk.TreeViewColumn("Name")
        #cell = gtk.CellRendererPixbuf()
        #column.pack_start(cell, False)
        #column.add_attribute(cell, "pixbuf", 2)
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 0)
        #column.add_attribute(cell, "foreground-gdk", 3)
        self.projectTreeView.append_column(column)
        
    
    def keyPress(self, widget, event, data):
        if widget is self.view:
            if event.keyval==ord("+"):
                self.view.zoom(1.2)
            elif event.keyval==ord("-"):
                self.view.zoom(1/1.2)
            elif event.keyval==ord("."):
                item = self.view.focused_item
                if item and item.object:
                    self.astTree.selectObject(item.object)
            elif event.keyval==ord("d"):
                item = self.view.focused_item
                if item and hasattr(item, "object"):
                    self.diagram.remove(item.object)
            elif event.keyval==ord("x"):
                item = self.view.focused_item
                if item and item.object:
                    item.object.setActive(not item.object.getActive())

    def showFile(self, _file, location = None):
        if not self.files.has_key(_file):
            import os.path
            fl = file(os.path.join(self.project.sourceDir or '', _file.name))
            view = self._openFile(fl)
            self.files[_file] = view
        else:
            view = self.files[_file]
        
        # find view index in notebook and open it
        children = self.notebook.get_children()
        for i, child in enumerate(children):
            if child==view or child.child==view:
                self.notebook.set_current_page(i)
                buf = view.get_buffer()
                if location is not None:
                    iBegin = buf.get_iter_at_line_offset(location.begin.line-1, location.begin.column)
                    iEnd = buf.get_iter_at_line_offset(location.end.line-1, location.end.column)
                else:
                    iBegin = buf.get_iter_at_line(0)
                    iEnd = buf.get_iter_at_line(0)
                view.scroll_to_iter(iBegin, 0, True, 0., 0.)
                buf.select_range(iBegin, iEnd)
                    
    def _openFile(self, fl):
        import os.path
        view = gtk.TextView()
        view.set_editable(False)
        view.get_buffer().set_text(unicode(fl.read(), 'iso8859-15'))
        window = gtk.ScrolledWindow()
        window.add(view)
        window.show_all()
        self.notebook.append_page(window, gtk.Label(os.path.basename(fl.name)))
        return view
        
    def _sourceDirChanged(self, button):
        self.project.sourceDir = button.get_filename()
        LOG.debug("Source directory set to %s" % self.project.sourceDir)
            
    def generate_mpi_tags(self, widget):
        if not self.project:
            return   
        # clean tags and generate MPI caller tags
        for name, obj in self.project.astObjects.iteritems():
            obj.tags.clear()
            if not hasattr(obj, "callNames"):
                continue
            for callname in obj.callNames:
                if callname.lower().startswith("mpi_"):
                    obj.tags.add("MPI caller")
                    break
        # generate _indirect_ MPI caller tags
        reverseCalls = {}
        for obj in self.project.astObjects.itervalues():
            if not hasattr(obj, "callNames"):
                continue
            for name in obj.callNames:
                if not reverseCalls.has_key(name.lower()):
                    reverseCalls[name.lower()] = set()
                reverseCalls[name.lower()].add(obj.name.lower())
        unprocessed = set()
        processed = set()
        for name in reverseCalls.iterkeys():
            if name.lower().startswith("mpi_"):
                unprocessed.add(name.lower())
        while len(unprocessed)>0:
            name = unprocessed.pop()
            processed.add(name)
            callee = self.project.astObjects.get(name, None)
            if callee and not callee.getActive(): # do not process inactive
                continue
            for callerName in reverseCalls.get(name, ()):
                self.project.astObjects[callerName].tags.add("indirect MPI caller")
                if not callerName in processed:
                    unprocessed.add(callerName)

        self.view.queue_draw_refresh()

    def view_mpi_tags(self, widget):
        OPTIONS["view MPI tags"] = not OPTIONS["view MPI tags"]
        self.view.queue_draw_refresh()
        
        
    def _on_show_references_activate(self, widget):
        lst = widgets.ObjectList()
        _model, iRow = self.astTree.view.get_selection().get_selected()
        astObj = _model[iRow][1]
        obj = astObj.model.basicModel.getObjectByASTObject(astObj)
        lst.showObject(obj)
        lst.show_all()
        self.sidebarNotebook.append_page(lst, gtk.Label('refs(%s)'%obj))

if __name__ == "__main__":
    from astvis.services import references
    core.registerService('ASTTreeWalker', references.ASTTreeWalker())
    core.registerService('ReferenceResolver', references.ReferenceResolver())
    window = MainWindow()
    gtk.main()

