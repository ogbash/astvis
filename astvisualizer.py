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
import pango
import gaphas
import gaphas.examples
import math
import pickle
from astvis import gaphasx, event, xmlmap, thread, core, widgets
from astvis.common import *
from astvis.project import Project, ProjectService
from astvis import widgets, diagram
from astvis.misc import console
from astvis.model import ast
from astvis.action import Action
from astvis import action
from astvis.misc.list import ObservableList
import astvis.widgets.task

class MainWindow(object):
    
    def __init__(self):
        self.projects = ObservableList()
        self.files = {} #: opened files (model.File -> gtk.TextView)
        self.views = {} #: opened views (models -> widgets)
        
        self.wTree = gtk.glade.XML("astvisualizer.glade", 'main_window')
        self.mainWindow = self.wTree.get_widget("main_window")
        self.mainWindow.connect("destroy",gtk.main_quit)
        
        action.manager.registerActionService(self)
        self.globalActionGroup = action.manager.createActionGroup('global', self)
        action.connectWidgetTree(self.globalActionGroup, self.wTree)
        
        self.notebook = self.wTree.get_widget('notebook')
        self.sidebarNotebook = self.wTree.get_widget('sidebar_notebook')
        self.taskProgressbars = self.wTree.get_widget('task_progressbars')
        gtklabel = self.taskProgressbars.get_parent().get_tab_label(self.taskProgressbars)
        self.taskHandler = astvis.widgets.task.TaskHandler(self.taskProgressbars, gtklabel)

        tool = gaphas.tool.ToolChain()
        tool.append(gaphas.tool.HoverTool())
        tool.append(gaphasx.ConnectingTool())
        tool.append(gaphas.tool.ItemTool())
        tool.append(gaphas.tool.RubberbandTool())
        #self.view.tool = tool

        # project tree
        self.projectTree = widgets.ProjectTree(self.projects, root=self)
        leftPanel = self.wTree.get_widget('left_panel_top')
        leftPanel.pack_start(self.projectTree.outerWidget)
        
        self.notebook = self.wTree.get_widget("notebook")

        self.wTree.signal_autoconnect(self)
        
        self.consoleWindow = gtk.Window()
        pyconsole = console.GTKInterpreterConsole()
        pyconsole.set_size_request(640,480)
        self.consoleWindow.add(pyconsole)
        #self.consoleWindow.show_all()
        
    def _data_recv(self, widget, context, x, y, data, info, timestamp, obj):
        LOG.debug("GTK DnD data_recv with info=%d"%info)
        if info==INFO_OBJECT_PATH.number:
            diagram = obj
            clazz, path = pickle.loads(data.data)
            if clazz==ast.ProgramUnit or clazz==ast.Subprogram:
                # get canvas coordinates
                m = cairo.Matrix(*widget.matrix)
                m.invert()
                cx, cy = m.transform_point(x,y)
                # add item
                obj = diagram.project.astModel.getObjectByPath(path)
                item = diagram.add(obj, cx,cy)
                context.drop_finish(True, timestamp)
            else:
                context.drop_finish(False, timestamp)                
        else:
            context.drop_finish(False, timestamp)
    
    @Action('project-new', label='New project', contextClass=widgets.ProjectTree, icon='gtk-new')
    def _newProject(self, target, context):
        self._addProject(Project())

    def _addProject(self, project):
        LOG.debug("Adding %s" % project)
        self.projects.append(project)
        #event.manager.notifyObservers(self.projects, event.PROPERTY_CHANGED, 
        #        (None, event.PC_ADDED, project, None), {'index':len(self.projects)-1})
            
    @Action('project-save', label='Save project', icon='gtk-save', targetClass=Project)
    def _saveProject(self, project, context):
        "Save project with all trees and diagrams to disk."

        wTree = gtk.glade.XML("astvisualizer.glade", 'saveproject_dialog')
        dialog = wTree.get_widget('saveproject_dialog')
        
        try:        
            result = dialog.run()
            if result > 0 and dialog.get_filename():
                filename = dialog.get_filename()
                import pickle
                file_ = open(filename, 'w')
                try:
                    LOG.debug("Pickling %s", project)
                    pickle.dump(project, file_)
                finally:
                    file_.close()
                project.filename = filename
        finally:
            dialog.destroy()

    @Action('project-open', label='Open project', contextClass=widgets.ProjectTree, )
    def _openProject(self, widget, context):
        wTree = gtk.glade.XML("astvisualizer.glade", 'openproject_dialog')
        dialog = wTree.get_widget('openproject_dialog')

        try:
            result = dialog.run()
            if result > 0 and dialog.get_filename():
                filename = dialog.get_filename()
                import pickle
                file_ = open(filename, 'r')
                project = pickle.load(file_)
                file_.close()
                project.filename = filename
                self._addProject(project)
        finally:
            dialog.destroy()

    def addView(self, obj, widget, labelText):
        self.views[obj] = widget
        self.sidebarNotebook.append_page(widget, gtk.Label(labelText))

    @Action('show-ast', 'Show AST tree', targetClass=ast.ASTModel)
    def openASTTree(self, astModel, context):
        "ast tree view"
        astTree = widgets.AstTree(self, astModel)        
        self.addView(astTree, astTree.outerWidget, 'ast')
    
    @Action('show-calls', 'Show calls', contextClass=widgets.AstTree)
    def openCallTree(self, target, context):
        "create call tree"
        callTree = widgets.CallTree(self, context)
        self.addView(callTree, callTree.outerWidget, 'call')

    @Action('show-references', 'Show references', contextClass=widgets.AstTree)
    def openBackCallTree(self, target, context):
        "create back call tree"
        backCallTree = widgets.BackCallTree(self, context)
        self.addView(backCallTree, backCallTree.outerWidget, 'back')

    @Action('show-diagram', 'Show diagram', targetClass=diagram.Diagram)
    def openDiagram(self, diagram, context):
        if self.views.has_key(diagram):
            return
        view = gaphas.view.GtkView()
        view.canvas = diagram.getCanvas()
        view.show()
        #outer.set_hadjustment(view.hadjustment)
        #outer.set_vadjustment(view.vadjustment)
        view.connect("key-press-event", self.keyPress, diagram)
        view.drag_dest_set(gtk.DEST_DEFAULT_MOTION|gtk.DEST_DEFAULT_DROP,
                [(INFO_OBJECT_PATH.name,0,INFO_OBJECT_PATH.number)],
                gtk.gdk.ACTION_COPY)
        view.connect("drag-data-received", self._data_recv, diagram)
        self.views[diagram] = view
        self.notebook.append_page(view, gtk.Label('diagram'))

        
    def openObjectList(self):
        lst = widgets.ObjectList()
        _model, iRow = self.astTree.view.get_selection().get_selected()
        astObj = _model[iRow][1]
        obj = astObj.model.basicModel.getObjectByASTObject(astObj)
        lst.showObject(obj)
        lst.show_all()
        self.sidebarNotebook.append_page(lst, gtk.Label('refs(%s)'%obj))        


    def keyPress(self, widget, event, diagram):
        if isinstance(widget, gaphas.view.GtkView):
            view = widget
            if event.keyval==ord("+"):
                view.zoom(1.2)
            elif event.keyval==ord("-"):
                view.zoom(1/1.2)
            elif event.keyval==ord("."):
                item = view.focused_item
                if item and item.object:
                    self.astTree.selectObject(item.object)
            elif event.keyval==ord("d"):
                item = view.focused_item
                if item and hasattr(item, "object"):
                    diagram.remove(item.object)
            elif event.keyval==ord("x"):
                item = view.focused_item
                if item and item.object:
                    item.object.setActive(not item.object.getActive())

    def showFile(self, project, fileName, location = None):
        if not self.files.has_key(fileName):
            import os.path
            fl = file(os.path.join(project.sourceDir or '', fileName.name))
            view = self._openFile(fl)
            self.files[fileName] = view
        else:
            view = self.files[fileName]
        
        # find view index in notebook and open it
        children = self.notebook.get_children()
        for i, child in enumerate(children):
            if child==view or \
                   isinstance(child,gtk.ScrolledWindow) and child.child==view:
                self.notebook.set_current_page(i)
                buf = view.get_buffer()

                iBegin=None
                iEnd=None
                if location is not None:
                    if location.begin.line>0:
                        iBegin = buf.get_iter_at_line_offset(location.begin.line-1, location.begin.column)
                        iEnd = buf.get_iter_at_line_offset(location.end.line-1, location.end.column)
                else:
                    iBegin = buf.get_iter_at_line(0)
                    iEnd = buf.get_iter_at_line(0)

                if iBegin is not None:
                    view.scroll_to_iter(iBegin, 0, True, 0., 0.)
                    if iEnd is not None:
                        buf.select_range(iBegin, iEnd)
                    
    def _openFile(self, fl):
        import os.path
        view = gtk.TextView()
        view.set_editable(False)
        font = pango.FontDescription("Courier 12")
        view.modify_font(font)
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

    @Action('show-object-browser', 'Browse objects')
    def openBrowser(self, target, context):
        from astvis.misc.browser import Browser
        if target==None:
            target=self.projects
        self._objectBrowser = Browser('browser', target)

if __name__ == "__main__":
    from astvis.services import references, tags
    core.registerService('ASTTreeWalker', references.ASTTreeWalker())
    core.registerService('ReferenceResolver', references.ReferenceResolver())
    tagService = tags.TagService()
    action.manager.registerActionService(tagService)
    core.registerService('TagService', tagService)
    action.manager.registerActionService(ProjectService())
    action.manager.registerActionService(widgets)
    window = MainWindow()
    gtk.main()

