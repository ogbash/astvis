#! /usr/bin/env python

import logging
LOG = logging.getLogger("backtree")
from astvis.common import FINE, FINER, FINEST

from astvis.model import basic
from astvis import core
from astvis.widgets.base import BaseWidget

import gtk

class RowFactory:
    thumbnailFilenames = {basic.ProgramUnit: lambda obj: obj.type=='module' and "data/thumbnails/module.png"
                    or "data/thumbnails/program.png",
            basic.Subprogram: "data/thumbnails/subroutine.png",
            basic.Variable: "data/thumbnails/variable.png"}
            
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

class BackCallTree(BaseWidget):

    def __init__(self, root, astTree=None):
        BaseWidget.__init__(self, 'back_call_tree', actionFilters=[{'category':'show-'}])
        self.root = root
        self.view = self.widget

        column = gtk.TreeViewColumn("Name")
        cell = gtk.CellRendererPixbuf()
        column.pack_start(cell, False)
        column.add_attribute(cell, "pixbuf", 2)
        cell = gtk.CellRendererText()
        column.pack_start(cell, True)
        column.add_attribute(cell, "text", 0)
        column.add_attribute(cell, "foreground-gdk", 3)
        
        self.view.append_column(column)

        self.model = gtk.TreeStore(str, object, gtk.gdk.Pixbuf, gtk.gdk.Color)
        self.view.set_model(self.model)
        
        if astTree!=None:
            astTree.view.get_selection().connect('changed', self._astTreeChanged)
            self._astTreeChanged(astTree.view.get_selection())
        
    def _astTreeChanged(self, selection):
        _model, iRow = selection.get_selected()
        if iRow!=None:
            astObj = _model[iRow][1]
            obj = astObj.model.basicModel.getObjectByASTObject(astObj)
            if not obj is None:
                self.showObject(obj)
            else:
                LOG.debug("No object found for AST object %s", astObj)

    def _clearModel(self):
        def free(model, path, iRow):
            obj = model[iRow][1]
    
        self.model.foreach(free)
        self.model.clear()

    def showObject(self, obj):
        "@type: BasicObject"
        self._clearModel()
        self._addObject(obj, None)

    def _addObject(self, obj, iParent):
        data = factory.getRow(obj)
        iObj = self.model.append(iParent, data)
        
        resolver = core.getService('ReferenceResolver')
        references = resolver.getReferringObjects(obj).keys()

        LOG.log(FINER, "Number of referring objects for %s: %d", obj, len(references))
        for ref in references:
            basicObj = ref.model.basicModel.getObjectByASTObject(ref)
            self._addObject(basicObj, iObj)

        self.view.expand_row(self.model.get_path(iObj), False)        

