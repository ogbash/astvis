#!/usr/bin/env python

import astvis.misc.trace

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
import cPickle as pickle
import astvis.stock
from astvis import gaphasx, event, xmlmap, thread, core, widgets
from astvis.common import *
from astvis.project import Project
from astvis import widgets, diagram
from astvis.misc import console
from astvis.model import ast, basic
from astvis.action import Action
from astvis import action
from astvis.misc.list import ObservableList
import astvis.widgets.task
from astvis.widgets.frames import FrameBox

class MainWindow(object):
    
    UI_DESCRIPTION = '''
    <menubar name="MenuBar">
      <menu action="file">
        <placeholder name="project">
          <menuitem action="project-new"/>
          <menuitem action="project-open"/>
        </placeholder>
        <separator/>
        <menuitem action="main-quit"/>
      </menu>

      <menu action="frames">
        <menuitem action="frame-horizontal"/>
        <menuitem action="frame-vertical"/>
        <menuitem action="frame-unsplit"/>
      </menu>

      <menu action="tools">
        <menuitem action="main-generate-ofp-astxml"/>
        <separator/>
        <menuitem action="main-toggle-tracing"/>
        <menuitem action="main-show-console"/>
      </menu>
    </menubar>
    <toolbar name="Toolbar">
      <placeholder name="project">
        <toolitem action="project-new"/>
        <toolitem action="project-open"/>
      </placeholder>
      <separator/>      
      <placeholder name="frames">
        <toolitem action="frame-horizontal"/>
        <toolitem action="frame-vertical"/>
        <toolitem action="frame-unsplit"/>
      </placeholder>
    </toolbar>
    '''

    windows = {}

    def _setFocusedFrame(self, frame):
        self._focusedFrame = frame
        group = self.globalGtkActionGroup.get_data('group')
        group.updateActions(self.globalGtkActionGroup, None)
    focusedFrame = property(lambda self: self._focusedFrame, _setFocusedFrame)
    
    def __init__(self, ui):
        MainWindow.windows[id(self)] = self
        self.projects = ObservableList()
        self.files = {} #: opened files (model.File -> gtk.TextView)
        self.views = {} #: opened views (models -> widgets)
        
        self.wTree = gtk.glade.XML("astvisualizer.glade", 'main_window')
        self.mainWindow = self.wTree.get_widget("main_window")
        self.mainWindow.connect("destroy",self._quit)
        self._focusedFrame = None

        ## UI Manager
        self.ui = ui

        # main action group
        action.manager.registerActionService(self)
        
        globalActionGroup = action.ActionGroup(action.manager,
                                               'global',
                                               categories = ['main','file','project', 'frame'])

        for aname, atitle in [('file', "File"),
                              ('frames',"Frame"),
                              ('tools',"Tools")]:
            globalActionGroup.addAction(action.Action(aname, atitle))
            
        self.globalGtkActionGroup = globalActionGroup.createGtkActionGroup(self)
        action.manager.addGtkGroup(self.globalGtkActionGroup)
        
        self.ui.add_ui_from_string(self.UI_DESCRIPTION)
        self.menubar = self.ui.get_widget('/MenuBar')
        self.toolbar = self.ui.get_widget('/Toolbar')

        vbox = self.wTree.get_widget('main_window_header')
        vbox.pack_start(self.menubar)
        vbox.pack_start(self.toolbar)

        ## widgets
        self._astTree = None
        self._callTree = None
        self._referenceTree = None # call back tree
        self._conceptTree = None
        self._udList = None # used definitions list
        
        #self.code_notebook = self.wTree.get_widget('code_notebook')
        self.sidebarNotebook = self.wTree.get_widget('sidebar_notebook')
        self.taskProgressbars = self.wTree.get_widget('task_progressbars')
        gtklabel = self.taskProgressbars.get_parent().get_tab_label(self.taskProgressbars)
        self.taskHandler = astvis.widgets.task.TaskHandler(self.taskProgressbars, gtklabel)

        # project tree
        self.projectTree = widgets.ProjectTree(self.projects, root=self)
        leftPanel = self.wTree.get_widget('left_panel_top')
        leftPanel.pack_start(self.projectTree.outerWidget)
        
        self.mainbox = self.wTree.get_widget("mainbox")
        frame = FrameBox(self, 3)
        self.mainbox.add(frame.eventBox)
        
        self.wTree.signal_autoconnect(self)
        
        self._consoleWindow = gtk.Window()
        def _hide(w,o): w.hide(); return True
        self._consoleWindow.connect('delete-event', _hide)
        def _reloadService(name):
            import sys
            s=core.getService(name)
            reload(sys.modules[s.__module__])
            clazz=getattr(sys.modules[s.__module__], s.__class__.__name__)
            core.registerService(name, clazz())
        pyconsole = console.GTKInterpreterConsole({'window':self, 'reloadService':_reloadService})
        pyconsole.set_size_request(640,480)
        self._consoleWindow.add(pyconsole)

        self.toolbox = widgets.DiagramItemToolbox(self.wTree, self)
        vbox = gtk.VBox()
        vbox.pack_start(self.toolbox.widget, expand=False)
        vbox.show_all()
        self.sidebarNotebook.append_page(vbox, gtk.Label('Items'))

        globalActionGroup.updateActions(self.globalGtkActionGroup, None)

    @Action('main-quit', label='Quit')
    def _quit(self, obj, context=None):
        gtk.main_quit()

    def externalize(self):
        return id(self)

    @staticmethod
    def internalize(data):
        return MainWindow.windows[data]

    def getFrame(self):
        "Get a frame where new things to be added."
        child = self.mainbox.get_child2()
        if isinstance(child, gtk.Paned):
            paned = child
            while isinstance(paned.get_child1(), gtk.Paned):
                paned = paned.get_child1()
            child = paned.get_child1() 
        else:
            pass            
            
        return child.get_data('framebox')
        
    
    @Action('project-new', label='New project', icon='gtk-new') #contextClass=widgets.ProjectTree
    def _newProject(self, target, context):
        self._addProject(Project(self))

    def _addProject(self, project):
        LOG.debug("Adding %s" % project)
        self.projects.append(project)
        #event.manager.notifyObservers(self.projects, event.PROPERTY_CHANGED, 
        #        (None, event.PC_ADDED, project, None), {'index':len(self.projects)-1})
            
    @Action('project-save', label='Save project', icon='gtk-save', targetClass=Project,\
            sensitivePredicate=lambda x,c: isinstance(x,Project))
    def _saveProject(self, project, context):
        "Save project with all trees and diagrams to disk."
        import gaphas.picklers

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

    @Action('project-open', label='Open project', icon='gtk-open')
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
                project.root = self
                self._addProject(project)
        finally:
            dialog.destroy()

    def addSidebarView(self, obj, widget, labelText):
        self.views[obj] = widget
        self.sidebarNotebook.append_page(widget, gtk.Label(labelText))
        self.sidebarNotebook.set_tab_detachable(widget, True)

    def addView(self, obj, view, label, window=None, notebook=None):
        if window==None:
            window = view
        if notebook==None:
            notebook = self.getFrame().notebook

        self.views[obj] = view
        notebook.append_page(window, label)
        notebook.set_tab_detachable(window, True)        

    @Action('show-ast', 'Show AST tree', targetClass=ast.ASTModel)
    def openASTTree(self, astModel, context):
        "ast tree view"
        if self._astTree==None:
            self._astTree = widgets.AstTree(self, astModel)        
            self.addSidebarView(self._astTree, self._astTree.outerWidget, 'ast')

    @Action('show-ast-object', 'Show in AST', targetClass=ast.ASTObject)
    def openASTObject(self, astObj, context):
        if self._astTree!=None:
            self._astTree.selectObject(astObj)
            self._astTree.updateHistory()

    @Action('show-ast-object-by-basic', 'Show in AST', targetClass=basic.BasicObject)
    def openASTObjectByBasic(self, basicObj, context):
        astObj = basicObj.astObject
        if self._astTree!=None:
            self._astTree.selectObject(astObj)
            self._astTree.updateHistory()

    @Action('show-calls', 'Show calls', contextClass=widgets.AstTree)
    def openCallTree(self, target, context):
        "create call tree"
        if self._callTree==None:
            self._callTree = widgets.CallTree(self, context)
            self.addSidebarView(self._callTree, self._callTree.outerWidget, 'call')

    @Action('show-references', 'Show references', contextClass=widgets.AstTree)
    def openBackCallTree(self, target, context):
        "create back call tree"
        if self._referenceTree==None:
            self._referenceTree = widgets.BackCallTree(self)
            self.addSidebarView(self._referenceTree, self._referenceTree.outerWidget, 'back')

        basicModel = target.model.basicModel
        obj = basicModel.getObjectByASTObject(target)
        if obj!=None:
            self._referenceTree.showObject(obj)
            self._referenceTree.updateHistory()

    @Action('show-diagram', 'Show diagram', targetClass=diagram.Diagram)
    def openDiagram(self, diagram, context):
        if self.views.has_key(diagram):
            return
        view = gaphas.view.GtkView()
        view.tool = diagram.getDefaultTool()
        view.canvas = diagram.getCanvas()

        #t = gtk.Table(2,2)
        #hs = gtk.HScrollbar(view.hadjustment)
        #vs = gtk.VScrollbar(view.vadjustment)
        #t.attach(view, 0, 1, 0, 1)
        #t.attach(hs, 0, 1, 1, 2, xoptions=gtk.FILL, yoptions=gtk.FILL)
        #t.attach(vs, 1, 2, 0, 1, xoptions=gtk.FILL, yoptions=gtk.FILL)
        #window = t
        window = gtk.ScrolledWindow(view.hadjustment, view.vadjustment)
        #window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        window.add_with_viewport(view)
        window.show_all()
        
        view.connect("key-press-event", self.keyPress, diagram)
        diagram.setupView(view)
        self.addView(diagram, view, gtk.Label(diagram.name), window=window)

    @Action('frame-horizontal',"Split V",
            sensitivePredicate=lambda t,o: o.focusedFrame!=None,
            icon='split-vertical')
    def _frameHorizontal(self, target, context):
        if self.focusedFrame:
            self.focusedFrame.split(gtk.HPaned())

    @Action('frame-vertical',"Split H",
            sensitivePredicate=lambda t,o: o.focusedFrame!=None,
            icon='split-horizontal')
    def _frameVertical(self, target, context):
        if self.focusedFrame:
            self.focusedFrame.split(gtk.VPaned())

    def _isNotTopBox(target, self):
        if self.focusedFrame==None:
            return False
        return self.focusedFrame.eventBox.get_parent()!=self.mainbox
    
    @Action('frame-unsplit',"Unsplit",
            sensitivePredicate=_isNotTopBox)
    def _frameUnsplit(self, target, context):
        self.focusedFrame.unsplit()

    def getDiagram(self):
        "Return current shown diagram."
        page = self.getCurrentPage()
        if isinstance(page, gtk.ScrolledWindow):
            page = page.get_children()[0].get_children()[0]
        if isinstance(page, gaphas.view.GtkView):
            diagrams = filter(lambda x: x[1]==page, self.views.items())
            return diagrams and diagrams[0][0] or None
        return None

    def getCurrentPage(self):
        i = self.focusedFrame.notebook.get_current_page()
        if i<0:
            return None
        page = self.focusedFrame.notebook.get_nth_page(i)
        return page
        
    def openObjectList(self):
        lst = widgets.ObjectList()
        _model, iRow = self.astTree.view.get_selection().get_selected()
        astObj = _model[iRow][1]
        obj = astObj.model.basicModel.getObjectByASTObject(astObj)
        lst.showObject(obj)
        lst.show_all()
        self.sidebarNotebook.append_page(lst, gtk.Label('refs(%s)'%obj))        

    def openUsedDefinitionsList(self, diagram, block, usedDefs):
        if self._udList==None:
            self._udList = widgets.UsedDefinitionsList(self)
            self.addSidebarView(self._udList, self._udList.outerWidget, 'usedef')
        self._udList.showData(diagram, block, usedDefs)

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
            view = self._openFile(fl, fileName)
            self.files[fileName] = view
        else:
            view = self.files[fileName]
        
        # find view index in notebook and open it
        notebook = view.get_parent()
        while not isinstance(notebook, gtk.Notebook):
            notebook = notebook.get_parent()
            
        children = notebook.get_children()
        for i, child in enumerate(children):
            if child==view or \
                   isinstance(child,gtk.ScrolledWindow) and child.child==view:
                self.getFrame().notebook.set_current_page(i)
                buf = view.get_buffer()

                iBegin=None
                iEnd=None
                if location is not None:
                    if location.begin.line>0 and location.begin.column>=0 and \
                           location.end.line>0 and location.end.column>=0:
                        iBegin = buf.get_iter_at_line_offset(location.begin.line-1, location.begin.column)
                        iEnd = buf.get_iter_at_line_offset(location.end.line-1, location.end.column)
                else:
                    iBegin = buf.get_iter_at_line(0)
                    iEnd = buf.get_iter_at_line(0)

                if iBegin is not None:
                    view.scroll_to_iter(iBegin, 0, True, 0., 0.)
                    if iEnd is not None:
                        buf.select_range(iBegin, iEnd)
                    
    def _openFile(self, fl, file_):
        import os.path
        view = widgets.CodeView(self, file_)
        view.get_buffer().set_text(unicode(fl.read(), 'iso8859-15'))
        window = gtk.ScrolledWindow()
        window.add(view)
        window.show_all()
        self.addView(file_, view, gtk.Label(os.path.basename(fl.name)), window=window )
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

    @Action('main-toggle-tracing', 'Toggle tracing', accel="<Control>t")
    def toggleTracing(self, target, context):
        from astvis.misc import trace
        trace.toggle()

    @Action('main-show-console', 'Show console')
    def _showConsole(self, target, context):
        self._consoleWindow.show_all()

if __name__ == "__main__":
    ui = gtk.UIManager()
    action.manager = action.ActionManager(ui)

    import astvis.services
    core.registerServices(astvis.services)
    
    window = MainWindow(ui)
    accelgroup = ui.get_accel_group()
    window.mainWindow.add_accel_group(accelgroup)

    gtk.main()

