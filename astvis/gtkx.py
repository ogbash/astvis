
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
        self.childIndex = None #: index of the child in parent children list
        self.object = None #: object

    def __str__(self):
        return "GtkModelData{parentData=%s, index=%d, object=%s}" % (self.parentData,self.index,self.object)
        

class _Adapter:
    pass

def _getAdapter(obj):
    if isinstance(obj, types.ListType):
        return _ListAdapter
    return _ObjectAdapter

class _ListAdapter(_Adapter):
    "Adapter for the List."
    
    @staticmethod
    def size(obj):
        return len(obj)
        
    @staticmethod
    def getIndex(obj, childIndex=-1, childSubindex = None):
        if childIndex==-1:
            return len(obj)
        else:
            return childIndex
            
    @staticmethod
    def iterChildren(obj):
        for child, childIndex in enumerate(obj):
            yield child, childIndex

    @staticmethod
    def getChild(parent, index):
        return parent[index], index

    @classmethod
    def childChanged(clazz, obj, event_, args, dargs, model):
        index = dargs['index']
        propName, action, new, old = args
        return action, index

        
class _ObjectAdapter(_Adapter):
    "Adapter for the usual Object."
    
    @classmethod
    def size(clazz, obj):
        if not hasattr(obj, '__gtkmodel__'):
            return 0        
        return clazz.getIndex(obj)

    @classmethod
    def getIndex(clazz, obj, childIndex=-1, childSubindex = None):        
        index = 0
        if childIndex==-1:
            childIndex = len(obj.__gtkmodel__._children)
            
        for iChildIndex in xrange(childIndex):
            childName, propName = obj.__gtkmodel__._children[iChildIndex]
            size = clazz._getSize(obj, propName)
            index = index+size
            
        if childSubindex is not None:
            index = index+childSubindex
        return index

    @staticmethod
    def iterChildren(obj):
        for childIndex, (childName,propName) in enumerate(obj.__gtkmodel__._children):
            child = getattr(obj, propName)
            if child is not None:
                yield child, childIndex

    @classmethod
    def getChild(clazz, parent, index):
        i = 0
        for iChild, (child, childIndex) in enumerate(clazz.iterChildren(parent)):
            if index==iChild:
                return child, childIndex
        else:
            raise IndexError(index)

    @classmethod
    def childChanged(clazz, obj, event_, args, dargs, model):
        propName, action, new, old = args
        childIndex = clazz._getChildIndex(obj, childName=propName)
        index = clazz.getIndex(obj, childIndex)

        objData = model._getData(obj)
        clazz._fixChildrenIndices(objData, model)
        
        if action is event.PC_CHANGED:
            if old is None and new is not None:
                action = event.PC_ADDED
            elif old is not None and new is None:
                action = event.PC_REMOVED
        return action, index

    @staticmethod
    def _getChildIndex(obj, childName = None, propName = None):
        for childIndex,(childNameP, propNameP) in enumerate(obj.__gtkmodel__._children):
            if childName==childNameP or propName==propNameP:
                return childIndex
        raise KeyError("No childName=%s nor propName=%s found for the %s" % (childName, propName, obj))

    @staticmethod
    def _getSize(obj, propName):
        child = getattr(obj, propName)
        if child is not None:
            size = 1
        else:
            size = 0
        # @todo: extend to included lists
        return size

    @classmethod
    def _fixChildrenIndices(clazz, objData, model):
        for i, (child, childIndex) in enumerate(clazz.iterChildren(objData.object)):
            data = model._getData(child)
            if data is None:
                data = GtkModelData(objData, i)
                data.object = child
                data.childIndex = childIndex
                model._setData(child, data)
            elif data.index!=i:
                if LOG.isEnabledFor(FINEST):
                    LOG.log(FINEST, "Fixing index %d -> %d", data.index, i)
                    data.index = i


class PythonTreeModel(gtk.GenericTreeModel):
    def __init__(self, root, columns = ['name', '__thumbnail__'], columnTypes = {'__thumbnail__': gtk.gdk.Pixbuf}):
        gtk.GenericTreeModel.__init__(self)
        self._columns = columns
        self._columnTypes = columnTypes
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
            adapter = _getAdapter(obj)
            resultingAction, index = adapter.childChanged(obj, event_, args, dargs, self)
            if obj is self._root:
                path = (index,)
            else:
                objData = self._getData(obj)
                if objData is None:
                    return
                objIter = self.create_tree_iter(objData)
                objPath = self.get_path(objIter)
                path = objPath + (index,)
            
            if resultingAction is event.PC_ADDED:
                iter_ = self.get_iter(path)
                self.row_inserted(path, iter_)
                if LOG.isEnabledFor(FINE):
                    LOG.log(FINE, "Row inserted: path=%s, iter=%s", path, iter_)
            elif resultingAction is event.PC_REMOVED:
                self.row_deleted(path)
                if LOG.isEnabledFor(FINE):
                    LOG.log(FINE, "Row deleted: path=%s", path)
            elif resultingAction is event.PC_CHANGED:
                iter_ = self.get_iter(path)
                self.row_changed(path, iter_)
                if LOG.isEnabledFor(FINE):
                    LOG.log(FINE, "Row changed: path=%s, iter=%s", path, iter_)
            else:
                raise Exception('childChanged() returned incorrect action %s' % resultingAction)

    def _getAttribute(self, objData, attrName):
        obj = objData.object
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "_getAttribute(attrName=%s)" % (attrName,))

        propName = None
        if hasattr(obj, '__gtkmodel__'):
            propName = obj.__gtkmodel__._attributes.get(attrName, None)        
            if LOG.isEnabledFor(FINEST):
                LOG.log(FINEST, "_getAttribute{propName=%s}" % (propName,))
        if propName is None:
            propName = attrName
            
        # @todo: get some attributes from parent (e.g. name for list)
        if hasattr(obj, propName):
            return getattr(obj, propName)
        elif attrName=='name' and objData.parentData!=None:
            parent = objData.parentData.object
            if hasattr(parent, '__gtkmodel__'):
                childName, propName = parent.__gtkmodel__._children[objData.childIndex]
                return childName
            
        return "%s.%s" % (obj, propName)
        
    def _getData(self, obj):
        hObj = makeHashable(obj)
        data = self._data.get(hObj, None)
        return data

    def _setData(self, obj, objData):
        hObj = makeHashable(obj)
        self._data[hObj] = objData

    def _getChildData(self, parentData, index):
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "_getChildData(%s, %s)", parentData, index)

        if parentData is None:
            parent = self._root
        else:
            parent = parentData.object

        adapter = _getAdapter(parent)
        child, childIndex = adapter.getChild(parent, index)

        childData = self._getData(child)
        if childData is None:
            childData = GtkModelData(parentData, index)
            childData.object = child
            childData.childIndex = childIndex
            self._setData(child, childData)
        
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "_getChildData() returns: %s", childData)
        return childData
        
    def on_get_flags(self):
        return 0
        
    def on_get_n_columns(self):
        return len(self._columns)
        
    def on_get_column_type(self, index):
        return self._columnTypes.get(self._columns[index], str)
        
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
        path = tuple(path)
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "on_get_path returns: %s", path)
        return path
        
    def on_get_value(self, rowref, column):
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "on_get_value(rowref=%s, column=%d)", rowref, column)
        childName = self._columns[column]
        return self._getAttribute(rowref, childName)
        
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
        if rowref is None: obj = self.root
        else: obj = rowref.object        
        adapter = _getAdapter(obj)

        size = adapter.size(obj)
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "on_iter_n_children() returns %d", size)
        return size
        
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

def connectTreeView(treeView, pythonTreeModel):
    columns = pythonTreeModel._columns
    
    column = gtk.TreeViewColumn("Name")
    if '__thumbnail__' in columns:
        cell = gtk.CellRendererPixbuf()
        column.pack_start(cell, False)
        column.add_attribute(cell, "pixbuf", columns.index('__thumbnail__'))
    cell = gtk.CellRendererText()
    column.pack_start(cell, True)
    column.add_attribute(cell, "text", columns.index('name'))
    #column.add_attribute(cell, "foreground-gdk", 3)
    treeView.append_column(column)

    treeView.set_model(pythonTreeModel)
        
if __name__=='__main__':
    l = [1,2,5]
    la = _getAdapter(l)
    print la.size(l)

    l1 = []
    l2 = []
    h1 = makeHashable(l1)
    h2 = makeHashable(l2)
    print l1==l2, h1==h2
    
