
import gtk
import types
import event

import logging as _logging
from astvis.common import FINE, FINER, FINEST
LOG = _logging.getLogger('gtkx')

from astvis.misc.tools import makeHashable

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
        self._data = {} #: object data cache: obj -> GtkModelData
        event.manager.subscribeEvent(self._objectChanged, event.PROPERTY_CHANGED)
    
    def _objectChanged(self, obj, event_, args, dargs):
        try:
            self.__objectChanged(obj, event_, args, dargs)
        except Exception, e:
            LOG.debug(e, exc_info=e)
            raise e
    
    def __objectChanged(self, obj, event_, args, dargs):
        if event_==event.PROPERTY_CHANGED:
            if LOG.isEnabledFor(FINEST):
                LOG.log(FINEST, "Property changed obj=%s, args=%s, dargs=%s", obj, args, dargs)
            propName, action, new, old = args

            # update attribute
            if hasattr(obj, '__gtkmodel__') and obj.__gtkmodel__._attributes.has_key(propName):
                objData = self._getData(obj)
                if objData is None:
                    return
                iter_ = self.create_tree_iter(objData)
                path = self.get_path(iter_)
                self.row_changed(path, iter_)
                if LOG.isEnabledFor(FINE):
                    LOG.log(FINE, "Attribute changed: path=%s, iter=%s", path, iter_)
                return

            # update child
            if propName is None:
                childIndex = dargs['index']
                index = childIndex
            else:
                childIndex = self._getChildIndex(obj, childName=propName)

            # get parent path
            objData = self._getData(obj)
            objIter = self.create_tree_iter(objData)
            objPath = self.get_path(objIter)
            
            if action is event.PC_ADDED:
                path = objPath + (index,)
                iter_ = self.get_iter(path)
                self.row_inserted(path, iter_)
            if action is event.PC_CHANGED:
                if new is not None and old is None:
                    #: @todo: must be childName instead of propName
                    if objData is None:
                        return

                    childIndex = self._getChildIndex(obj, childName=propName)
                    index = self._findIndex(obj, childIndex)
                    path = objPath + (index,)
                    iter_ = self.get_iter(path)
                    self._fixIndices(obj, index)
                    self.row_inserted(path, iter_)
                    if LOG.isEnabledFor(FINE):
                        LOG.log(FINE, "Row inserted: path=%s, iter=%s", path, iter_)

    def _fixIndices(self, obj, index):
        childIndex, childSubindex = self._findChildIndices(obj, index)
        for i in xrange(childIndex, len(obj.__gtkmodel__.children)):
            child = 
            data = self._getData(child)
            
            print "fixing %s" % data

    def _getAttribute(self, obj, attrName):
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "_getAttribute(attrName=%s)" % (attrName,))
        
        if hasattr(obj, '__gtkmodel__'):
            propName = obj.__gtkmodel__._attributes.get(attrName, None)        
            if LOG.isEnabledFor(FINEST):
                LOG.log(FINEST, "_getAttribute{propName=%s}" % (propName,))
        else:
            propName = attrName
            
        # @todo: get some attributes from parent (e.g. name for list)
        return getattr(obj, propName, "%s.%s" % (obj, propName))
        
    def _getData(self, obj):
        hObj = makeHashable(obj)
        data = self._data.get(hObj, None)
        return data

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
            
        hObject = makeHashable(obj)
        if self._data.has_key(hObject):
            return self._data[hObject]            
    
        data = GtkModelData(objData, index)
        data.object = child
        self._data[hObject] = data
        
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "_getChildData() returns: %s", data)
        return data

    def _getChildIndex(self, obj, childName = None, propName = None):
        for childIndex,(childNameP, propNameP) in enumerate(obj.__gtkmodel__._children):
            if childName==childNameP or propName==propNameP:
                return childIndex
        raise KeyError("No childName=%s nor propName=%s found for the %s" % (childName, propName, obj))

    def _getSize(self, obj, propName):
        child = getattr(obj, propName)
        if child is not None:
            size = 1
        else:
            size = 0
        # @todo: extend to included lists
        return size


    def _findChildIndices(self, obj, index=None):
        indexSum = 0
        for childIndex,(childName, propName) in enumerate(obj.__gtkmodel__._children):
            size = self._getSize(obj, propName)
            
            if index is not None and index<indexSum+size:
                childSubindex = index-indexSum
                break
            indexSum = indexSum+size
        else:
            if index is not None:
                raise IndexError("Index %d in %s", index, obj)
            else:
                childIndex = indexSum
                childSubindex = None

        return childIndex, childSubindex
        
    def _findIndex(self, obj, childIndex=-1, childSubindex = None):
        if isinstance(obj, types.ListType):
            if childIndex==-1:
                return len(obj)
            else:
                return childIndex
    
        index = 0
        if childIndex==-1:
            childIndex = len(obj.__gtkmodel__._children)
        for iChildIndex in xrange(childIndex):
            childName, propName = obj.__gtkmodel__._children[iChildIndex]
            size = self._getSize(obj, propName)
            index = index+1
            
        if childSubindex is not None:
            index = index+childSubindex
        return index
        
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
            if data.parentData!=None:
                path.append(data.index)
            data = data.parentData
        path.reverse()
        path = tuple(path)
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "on_get_path returns: %s", path)
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
            return self._findIndex(obj)
        
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

