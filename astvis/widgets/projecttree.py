#! /usr/bin/env python

import logging
LOG = logging.getLogger("projecttree")
from astvis.common import FINE, FINER, FINEST

from astvis.project import Project, readASTModel, TagTypeList, TagType, Concepts
from astvis import event, thread, xmlmap, action, project
from astvis.model import ast, basic
from astvis.widgets.base import BaseWidget
from astvis.widgets.tags import TagTypeDialog
from astvis.widgets.concepttree import ConceptTree
from astvis import gtkx, diagram

import gtk

class ProjectTree(BaseWidget):
    
    UI_DESCRIPTION = '''
    <menubar name="MenuBar">
      <menu action="file">
        <placeholder name="project">
          <menuitem action="project-save"/>
        </placeholder>
      </menu>

      <menu action="tools">
        <placeholder name="other">
          <menuitem action="show-object-browser"/>
        </placeholder>
      </menu>
    </menubar>
    <toolbar name="Toolbar">
      <placeholder name="project">
        <toolitem action="project-save"/>
      </placeholder>
      <separator/>
    </toolbar>

    <popup name="projecttree-popup">
      <placeholder name="project">
        <menuitem action="project-save"/>
      </placeholder>
      <separator/>
      <menuitem action="project-new-tag-type"/>
      <menuitem action="project-new-diagram"/>
      <separator/>
      <placeholder name="other">
        <menuitem action="show-object-browser"/>
      </placeholder>
    </popup>    
'''

    @classmethod
    def getActionGroup(cls):
        if not hasattr(cls, 'ACTION_GROUP'):
            cls.ACTION_GROUP = action.ActionGroup(action.manager,
                               'project-tree',
                               contextAdapter=cls.getSelected,
                               categories=['project', 'diagram', 'concept', 'tag', 'show'],
                               contextClass=ProjectTree,
                               targetClasses=[Project, TagTypeList, TagType, Concepts,
                                              project.DiagramList, diagram.Diagram])
        return cls.ACTION_GROUP


    def __init__(self, projects, root):
        BaseWidget.__init__(self, 'project_tree', 'project_tree_outer',
                            
                            menuName='projecttree-popup')
        self.view = self.widget
        self.projects = projects
        self.root = root

        self.model = gtkx.PythonTreeModel(projects)
        
        gtkx.connectTreeView(self.view, self.model)

    def addProject(self, project):
        iProject = self.model.append(None, (project.name, project, None))
        if project.astModel!=None:
            self.model.append(iProject, ('AST model', project.astModel, None))
        if project.model!=None:
            self.model.append(iProject, ('Basic model', project.model, None))
            
        event.manager.subscribe(self._projectChanged, project)

    def __selectionChanged(self, selection):
        model, iRow = selection.get_selected()
        parent, childName, obj = _extractObjectInfo(model, iRow)
        self.getActionGroup().updateActions(self.gtkActionGroup, obj)

    def _projectChanged(self, project, event_, args, dargs):
        if event_ == event.PROPERTY_CHANGED:
            propertyName, newValue, oldValue = args
            iProject = self.findRow(lambda iRow: self.model[iRow][1] == project)
            if propertyName == 'name':
                self.model[iProject][0] = project.name
            elif propertyName == 'astModel':
                iASTModel = self.findRow(lambda iRow: isinstance(self.model[iRow][1], ast.ASTModel), iProject)
                if iASTModel==None and project.astModel!=None:
                    self.model.append(iProject, ('AST model', project.astModel, None))
                elif iASTModel is not None and project.astModel is None:
                    self.model.remove(iASTModel)
                elif iASTModel is not None:
                    self.model[iASTModel][1] = project.astModel

    def findRow(self, fun, parent = None):
        iRow = self.model.iter_children(parent)
        while iRow is not None:
            if fun(iRow):
                return iRow
            iResult = self.findRow(fun, iRow)
            if iResult is not None:
                return iResult
            iRow = self.model.iter_next(iRow)
        return None

    def _on_project_tree_row_activated(self, view, path, column):
        LOG.log(FINE, "Row activated: path=%s, column=%s", path, column)
        model = view.get_model()
        obj = model.getObject(model.get_iter(path))
        
        if isinstance(obj, Project):
            self._handleProjectDialog(obj)
        elif isinstance(obj, ast.ASTModel):
            action.manager.activate('show-ast', obj, self)
        elif isinstance(obj, diagram.Diagram):
            action.manager.activate('show-diagram', obj, self)
        elif isinstance(obj, TagType):
            self._handleTagTypeDialog(obj)
        elif isinstance(obj, Concepts):
            self._openConceptTree(obj)

    def _openConceptTree(self, concepts):
        if self.root._conceptTree==None:
            self.root._conceptTree = ConceptTree(self.root, concepts)
            self.root.addView(concepts, self.root._conceptTree.outerWidget, gtk.Label("Concepts"))

    def _handleTagTypeDialog(self, tagType):
        dialog = TagTypeDialog(tagType)
        res = dialog.run()
        if res > 0:
            pass

    def _handleProjectDialog(self, project):
        dialog = ProjectDialog(project)
        res = dialog.run()
        if res > 0:
            project.name = dialog.projectName
            if hasattr(dialog, 'astModel'):
                project.astModel = dialog.astModel
                project.model = basic.BasicModel(project.astModel)
            project.sourceDir = dialog.sourceDir


#    @thread.threaded                
#    def _astFileChanged(self, filename):
#        LOG.debug("Loading %s" % filename)
#        try:
#            astModel = readASTModel(filename)
#        except(Exception), e:
#            LOG.error("Error loading file, %s", e, exc_info=e)
#        else:
#            LOG.info("Loaded %s" % filename)        


class ProjectDialog:
    def __init__(self, project):
        self.project = project
        wTree = gtk.glade.XML("astvisualizer.glade", 'project_dialog')
        wTree.signal_autoconnect(self)
        self.wTree = wTree
        self.widget = wTree.get_widget('project_dialog')
        
        self.projectNameEntry = wTree.get_widget('projectname_entry')
        self.projectNameEntry.set_text(project.name)

        self.astfileChooserbutton = wTree.get_widget('astfile_chooserbutton')
        if project.astModel is not None:
            self.astfileChooserbutton.set_filename(project.astModel.filename)

        self.sourcedirChooserbutton = wTree.get_widget('sourcedir_chooserbutton')
        if project.sourceDir is not None:
            self.sourcedirChooserbutton.set_filename(project.sourceDir)

    def run(self):
        res = self.widget.run()

        if res > 0:
            # get project name
            self.projectName = self.projectNameEntry.get_text()
            # load ast file
            astFilename = self.astfileChooserbutton.get_filename()
            if astFilename:
                if self.project.astModel is None \
                        or astFilename != self.project.astModel.filename:
                    self.astModel = readASTModel(astFilename)
                    self.astModel.project = self.project
            # get source dir name
            self.sourceDir = self.sourcedirChooserbutton.get_filename()
        
        self.widget.destroy()
        return res
        
    def destroy(self):
        return self.widget.destroy()

