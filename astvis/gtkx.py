
import gtk
import types
import event

import logging as _logging
from astvis.common import FINE, FINER, FINEST
LOG = _logging.getLogger('gtkx')

class GtkModel(object):
    def __init__(self):
        self._attributes = {}
        self._children = []
         
    def appendAttribute(self, attrName, propertyName = None):
        self._attributes[attrName] = propertyName or attrName
    
    def appendChild(self, childName, propertyName = None):
        self._children.append((childName, propertyName or childName))

class GtkModelData(object):
    def __init__(self, parentData, index):
        #import weakref
        self.parentData = parentData #: GtkModelData of the parent
        self.index = index #: current index of the self.object in self.parentData.parent
        self.object = None #: object

    def __str__(self):
        return "GtkModelData{parentData=%s, index=%d, object=%s}" % (self.parentData,self.index,self.object)
        
class PythonTreeModel(gtk.GenericTreeModel):
    def __init__(self, root, columns = ['name']):
        gtk.GenericTreeModel.__init__(self)
        self._columns = columns
        self._root = root
        #self._data = {} #: object data cache: rowref -> GtkModelData
        event.manager.subscribeEvent(self._objectChanged, event.PROPERTY_CHANGED)
        
    def _objectChanged(self, obj, event_, args, dargs):
        if event_==event.PROPERTY_CHANGED:
            if LOG.isEnabledFor(FINEST):
                LOG.log(FINEST, "Property changed obj=%s, args=%s, dargs=%s", obj, args, dargs)
            propName, action, new, old = args
            if obj is self._root:
                # root list changed
                index = dargs['index']
                if action is event.PC_ADDED:
                    path = (index,)
                    iter_ = self.get_iter(path)
                    self.row_inserted(path, iter_)
            else:
                # other objects changed
                
                if action is event.PC_CHANGED:
                    if new is not None and old is None:
                        self.row_inserted()
                                                

    def _getAttribute(self, obj, attrName):
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "_getAttribute(attrName=%s)" % (attrName,))
        try:
            propName = obj.__gtkmodel__._attributes.get(attrName, None)
        except Exception, e:
            LOG.warn("Error",exc_info=e)
            raise e        
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "_getAttribute{propName=%s}" % (propName,))
        return getattr(obj, propName)

    def _getChildData(self, objData, index):
        """Return certain child of the object."""
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "_getChildData(objData=%s, index=%d)", objData, index)
        if objData is None:
            obj = self._root
        else:
            obj = objData.object

        if isinstance(obj, types.ListType):
            child = obj[index]
        else:
            childIndex, childSubindex = self._findChildIndices(obj, index)
            childName, propName = obj.__gtkmodel__._children[childIndex]
            child = getattr(obj, propName)
    
        data = GtkModelData(objData, index)
        data.object = child
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "_getChildData() returns: %s", data)
        return data

    def _findChildIndices(self, obj, index):
        indexSum = 0
        for childIndex,(childName, propName) in enumerate(obj.__gtkmodel__._children):
            child = getattr(obj, propName)
            if child is not None:
                size = 1
            # @todo: extend to included lists

            if index<indexSum+size:
                childSubindex = index-indexSum
                break
        else:
            raise IndexError()

        return childIndex, childSubindex

    def _calculateChildrenSize(self, obj):
        indexSum = 0
        for childIndex,(childName, propName) in enumerate(obj.__gtkmodel__._children):
            child = getattr(obj, propName)
            if child is not None:
                size = 1
            # @todo: extend to included lists
            indexSum = indexSum+size

        return indexSum

    def on_get_flags(self):
        return 0
        
    def on_get_n_columns(self):
        return len(self._columns)
        
    def on_get_column_type(self, index):
        return str
        
    def on_get_iter(self, path):
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "on_get_iter(path=%s)", path)
        objData = None
        for index in path:
            objData = self._getChildData(objData, index)
        return objData
        
    def on_get_path(self, rowref):
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "on_get_path(rowref=%s)", rowref)
        path = []
        data = rowref
        while data!=None:
            path.append(data.index)
            data = data.parentData
        path.reverse()
        return path
        
    def on_get_value(self, rowref, column):
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "on_get_value(rowref=%s)", rowref)
        return self._getAttribute(rowref.object, self._columns[column])
        
    def on_iter_next(self, rowref):
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "on_iter_next(rowref=%s)", rowref)
        parentData = rowref.parentData
        index = rowref.index
        try:
            return self._getChildData(parentData, index+1)
        except IndexError, e:
            return None
            
    def on_iter_children(self, rowref):
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "on_iter_children(rowref=%s)", rowref)
        if not self.on_iter_has_child(rowref):
            return None
        return self._getChildData(rowref, 0)
        
    def on_iter_has_child(self, rowref):
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "on_iter_has_child(rowref=%s)", rowref)
        return self.on_iter_n_children(rowref) > 0
        
    def on_iter_n_children(self, rowref):
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "on_iter_n_children(rowref=%s)", rowref)
        if rowref is None:
            obj = self.root
        else:
            obj = rowref.object
            
        if isinstance(rowref, types.ListType):
            return len(obj)
        else:
            return self._calculateChildrenSize(obj)
        
    def on_iter_nth_child(self, parent, n):
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "on_iter_nth_child(parent=%s,n=%d)", parent, n)
        try:
            return self._getChildData(parent, n)
        except IndexError, e:
            return None
            
    def on_iter_parent(self, rowref):
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "on_iter_parent(rowref=%s)", rowref)
        return rowref.parentData

    def getObject(self, iter_):
        data = self.get_user_data(iter_)
        return data.object
