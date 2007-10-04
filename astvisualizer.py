#!/usr/bin/env python

import logging
if __name__=="__main__":
    logging.basicConfig(level=logging.DEBUG)

LOG = logging.getLogger("main")

try:
    import pygtk
    pygtk.require('2.10')
except:
    pass

import gtk  
import gtk.glade
import cairo
import gaphas
import gaphas.examples
import math
import pickle
from astvis import INFO_OBJECT_NAME, OPTIONS
from astvis import gaphasx
from astvis.project import Project
from astvis.calltree import CallTree
from astvis.asttree import AstTree
from astvis.model import ProgramUnit, Subprogram
from astvis.diagram import CallDiagram

class MainWindow:
    
    def __init__(self):
        self.project = None

        self.wTree = gtk.glade.XML("astvisualizer.glade", "main_window")
        self.mainWindow = self.wTree.get_widget("main_window")
        self.mainWindow.connect("destroy",gtk.main_quit)

        self.diagram = CallDiagram()
        self.view = gaphas.view.GtkView(self.diagram.getCanvas())
        outer = self.wTree.get_widget("canvas_view_outer")
        self.view.show()
        outer.add(self.view)
        outer.set_hadjustment(self.view.hadjustment)
        outer.set_vadjustment(self.view.vadjustment)        
        self.view.connect("key-press-event", self.keyPress, None)
        self.view.drag_dest_set(gtk.DEST_DEFAULT_MOTION|gtk.DEST_DEFAULT_DROP,
                [(INFO_OBJECT_NAME[0],0,INFO_OBJECT_NAME[1])],
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
        
        # create call tree
        callTreeView = self.wTree.get_widget("call_tree")
        self.callTree = CallTree(self, callTreeView)

        self.wTree.signal_autoconnect(self)
                
        #self._setProject(Project(astFileName="tree.xml"))
        self._setProject(Project())

    def _data_recv(self, widget, context, x, y, data, info, timestamp):
        if info==INFO_OBJECT_NAME[1]:
            clazz, name = pickle.loads(data.data)
            if clazz==ProgramUnit or clazz==Subprogram:
                # get canvas coordinates
                m = cairo.Matrix(*self.view.matrix)
                m.invert()
                cx, cy = m.transform_point(x,y)
                # add item
                obj = self.project.objects[name.lower()]
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
        LOG.debug("Loading %s" % obj.get_filename())
        try:
            self.project._loadAstFile(obj.get_filename())
        except(Exception), e:
            LOG.error("Error loading file, %s", e)
            obj.unselect_all()
        else:
            LOG.info("Loaded %s" % obj.get_filename())
        
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
                    iObject = self.project._findInTree(item.object)
                    if iObject:
                        path = self.project.astModel.get_path(iObject)
                        self.astTree.view.expand_to_path(path)
                        self.astTree.view.get_selection().select_path(path)
                        self.astTree.view.scroll_to_cell(path)
            elif event.keyval==ord("d"):
                item = self.view.focused_item
                if item and hasattr(item, "object"):
                    self.diagram.remove(item.object)
            elif event.keyval==ord("x"):
                item = self.view.focused_item
                if item and item.object:
                    item.object.setActive(not item.object.getActive())

            
    def generate_mpi_tags(self, widget):
        if not self.project:
            return   
        # clean tags and generate MPI caller tags
        for name, obj in self.project.objects.iteritems():
            obj.tags.clear()
            if not hasattr(obj, "callNames"):
                continue
            for callname in obj.callNames:
                if callname.lower().startswith("mpi_"):
                    obj.tags.add("MPI caller")
                    break
        # generate _indirect_ MPI caller tags
        reverseCalls = {}
        for obj in self.project.objects.itervalues():
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
            callee = self.project.objects.get(name, None)
            if callee and not callee.getActive(): # do not process inactive
                continue
            for callerName in reverseCalls.get(name, ()):
                self.project.objects[callerName].tags.add("indirect MPI caller")
                if not callerName in processed:
                    unprocessed.add(callerName)

        self.view.queue_draw_refresh()

    def view_mpi_tags(self, widget):
        OPTIONS["view MPI tags"] = not OPTIONS["view MPI tags"]
        self.view.queue_draw_refresh()

if __name__ == "__main__":
    window = MainWindow()
    gtk.main()

