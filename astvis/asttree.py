#!/usr/bin/env python

"""Abstract syntax tree module."""

import logging
LOG = logging.getLogger("asttree")
from common import FINE, FINER, FINEST

from common import *
import gtk
import pickle
from model import ast
import event
import project

class RowFactory:
    thumbnailFilenames = {ast.File: "data/thumbnails/file.png",
            ast.ProgramUnit: lambda obj: obj.type=='module' and "data/thumbnails/module.png"
                    or "data/thumbnails/program.png",
            ast.Subprogram: "data/thumbnails/subroutine.png",
            ast.Statement: lambda obj: obj.type=='call' and 'data/thumbnails/call.png' or None,
            ast.Call: "data/thumbnails/call.png",
            ast.Use: "data/thumbnails/use.png"}
            
    def __init__(self):
        self.thumbnails = {}    

    def getRow(self, obj):
        name = hasattr(obj,"name") and obj.name or str(obj)
        
        return [name, obj, self._getThumbnail(obj), gtk.gdk.color_parse("black")]

    def _getThumbnail(self, obj):
        "Thumbnail to be shown in GtkTreeView for the C{obj} element"
        filename = RowFactory.thumbnailFilenames.get(obj.__class__, None)
        if callable(filename):
            filename = filename(obj)

        if not filename:
            return None
        if not self.thumbnails.has_key(filename):
            import gtk.gdk
            thumbnail = gtk.gdk.pixbuf_new_from_file_at_size(filename, 16, 16)
            self.thumbnails[filename] = thumbnail
        return self.thumbnails.get(filename, None)

factory = RowFactory()

class Filter:
    ALLOW = 'allow'
    DENY = 'deny'

    TYPES_FILTER = {'file': lambda obj: isinstance(obj, ast.File),
        'module':  lambda obj: isinstance(obj, ast.ProgramUnit),
        'subprogram':  lambda obj: isinstance(obj, ast.Subprogram)
        }
    FILTERS = {'type':TYPES_FILTER}
    
    def __init__(self):
        self.filters = [(Filter.FILTERS['type']['file'], Filter.DENY)] #
        
    def apply(self, obj):
        for filt, action in self.filters:
            res = filt(obj)
            if res:
                return action
        return None

class AstTree:
    
    def __init__(self, root, view):
        self.root = root
        self.project = None
        self.model = None    
        self.view = view
        self.filter = Filter()
        
        column = gtk.TreeViewColumn("Name")
        cell = gtk.CellRendererPixbuf()
        column.pack_start(cell, False)
        column.add_attribute(cell, "pixbuf", 2)
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 0)
        column.add_attribute(cell, "foreground-gdk", 3)
        self.view.append_column(column)

        self.view.connect("key-press-event", self._keyPress, None)
        self.view.connect("button-press-event", self._buttonPress)
        self.view.connect_after("popup-menu", self._popupMenu)
        self.view.get_selection().connect("changed", self._selectionChanged, None)        
        self.view.connect("drag-data-get", self._dragDataGet)
        self.view.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, 
                [(INFO_TEXT.name, 0, INFO_TEXT.number),
                 (INFO_OBJECT_PATH.name, 0, INFO_OBJECT_PATH.number)],
                gtk.gdk.ACTION_COPY)
        self.model = gtk.TreeStore(str, object, gtk.gdk.Pixbuf, gtk.gdk.Color)
                
        event.manager.subscribeClass(self._objectChanged, ast.ASTObject)                
        event.manager.subscribeClass(self._objectChanged, project.Project)
        
    def _selectionChanged(self, selection, param):
        model, iRow = selection.get_selected()
        if not model or not iRow:
            return

        obj = model[iRow][1]
        self.root.callTree.showObject(obj)
        basicObj = obj.model.basicModel.getObjectByASTObject(obj)
        self.root.backCallTree.showObject(basicObj)

    def setProject(self, project):
        self.project = project
        self.view.set_model(self.model)
        
        # generate sidebar tree
        astModel = self.project.astModel
        self._generateSidebarTree(None, astModel and astModel.files or ())
        
    def _generateSidebarTree(self, iParent, astObjects):            
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "Generating for %s %d children" % \
                    (iParent and self.model[iParent][1] or '', len(astObjects)))
        for obj in astObjects:
            action = self.filter.apply(obj)
            if LOG.isEnabledFor(FINER):
                LOG.log(FINER, "Filter result for %s is %s" % (obj, action))
            if action is Filter.ALLOW or action is None:
                #data=[obj.getName(), obj, obj.getThumbnail(), gtk.gdk.color_parse("black")]
                data = factory.getRow(obj)
                iRow = self.model.append(iParent,data)
                self._generateSidebarTree(iRow, obj.getChildren())
            else:
                self._generateSidebarTree(iParent, obj.getChildren())
        
    def _findInTree(self, obj):
        if hasattr(obj, "parent"):
            iParent = self._findInTree(obj.parent)
        else:
            iParent = None        
        iChild = self.model.iter_children(iParent)
        while iChild:
            childObj, = self.model.get(iChild, 1)
            if obj is childObj:
                return iChild
            iChild = self.model.iter_next(iChild)
        return iParent
        
    def _objectChanged(self, obj, _event, args):
        if _event==event.ADDED_TO_DIAGRAM:
            diagram, = args
            iObject = self._findInTree(obj)
            self.model[iObject][3] = gtk.gdk.color_parse("darkgreen")
        elif _event==event.REMOVED_FROM_DIAGRAM:
            diagram, = args
            iObject = self._findInTree(obj)
            self.model[iObject][3] = gtk.gdk.color_parse("black")
        elif _event==event.ASTMODEL_CHANGED and obj==self.project:
            # generate sidebar tree
            self.model.clear()
            astModel = self.project.astModel
            self._generateSidebarTree(None, astModel and astModel.files or ())
        

    def selectObject(self, obj):
        iObject = self._findInTree(obj)
        if iObject:
            path = self.model.get_path(iObject)
            self.view.expand_to_path(path)
            self.view.get_selection().select_path(path)
            self.view.scroll_to_cell(path)    

    def _keyPress(self, widget, event, data):
        pass

    def _buttonPress(self, widget, event):
        if event.type==gtk.gdk._2BUTTON_PRESS:
            _model, iRow = self.view.get_selection().get_selected()
            obj = _model[iRow][1]
            if isinstance(obj, ast.File):
                self.root.showFile(obj)
                return True
            if hasattr(obj, 'location'):
                self.root.showFile(obj.getFile(), obj.location)
                return True

        if event.type==gtk.gdk.BUTTON_PRESS and event.button==3:
            self._popupMenu(widget, event.get_time())
            return True
        
        return False

    def _popupMenu(self, widget, time=0):
        _model, iRow = self.view.get_selection().get_selected()
        obj = _model[iRow][1]
        if obj is not None:
            self.menu.popup(None, None, None, 3, time)
     
    def _dragDataGet(self, widget, context, data, info, timestamp):
        "Returns data for the GTK DnD protocol."
        model, iRow = self.view.get_selection().get_selected()
        obj = model[iRow][1]
        path = obj.model.getPath(obj)
        data.set(INFO_OBJECT_PATH.name, 0, pickle.dumps((obj.__class__,path)) )
        LOG.debug("GTK DnD dragDataGet with info=%d, path=%s"%(info, path))

