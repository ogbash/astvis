
import gtk
import types
import event

class GtkModel(object):
    def __init__(self):
        self._attributes = set()
        self._children = []
        
    def appendAttribute(self, attrName, propertyName = None):
        self._attributes.add((attrName, propertyName or attrName))
    
    def appendChild(self, childName, propertyName = None):
        self._children.append((childName, propertyName or childName))

class GtkModelData(object):
    def __init__(self, parentData, index):
        #import weakref
        self.parentData = parentData #: GtkModelData of the parent
        self.index = index #: current index of the self.object in self.parentData.parent
        self.object = None #: object
        
class PythonTreeModel(gtk.GenericTreeModel):
    def __init__(self, root, columns = ['name']):
        self._columns = columns
        self._root = root
        #self._data = {} #: object data cache: rowref -> GtkModelData
        event.manager.subscribeEvent(self._objectChanged, event.PROPERTY_CHANGED)
        
    def _objectChanged(self, obj, event_, args):
        if event_==event.PROPERTY_CHANGED:
            print "Changed obj=%s, args=%s" % (obj, args)

    def _getAttribute(self, obj, attrName):
        propName = obj.__gtkmodel__.attributes[attrName]
        return getattr(obj, propName)

    def _getChildData(self, objData, index):
        """Return certain child of the object."""
        if objData is None:
            obj = self.root
        else:
            obj = objData.object

        if isinstance(obj, types.ListType):
            child = obj[index]
        else:
            childName, propName = obj.__gtkmodel__.children[index]
            child = getattr(obj, propName)
    
        data = GtkModelData(objData, index)
        data.object = child
        return data

    def _hashable(self, obj):
        try:
            hash(obj)
            return True
        except TypeError, e:
            return False

    def on_get_flags(self):
        return 0
        
    def on_get_n_columns(self):
        return len(self._columns)
        
    def on_get_column_type(self, index):
        return str
        
    def on_get_iter(self, path):
        objData = None
        for index in path:
            objData = self._getChildData(objData, index)
        return objData.object
        
    def on_get_path(self, rowref):
        path = []
        data = rowref
        while data!=None:
            path.append(data.index)
            data = data.parentData
        path.reverse()
        return path
        
    def on_get_value(self, rowref, column):
        return self._getAttribute(rowref.object, self._columns[column])
        
    def on_iter_next(self, rowref):
        parentData = rowref.parentData
        index = rowref.index
        try:
            return self._getChildData(parentData, index+1)
        except IndexError, e:
            return None
            
    def on_iter_children(self, rowref):
        if not self.on_iter_has_child(rowref):
            return None
        return self._getChildData(rowref, 0)
        
    def on_iter_has_child(self, rowref):
        return self.on_iter_n_children > 0
        
    def on_iter_n_children(self, rowref):
        if rowref is None:
            obj = self.root
        else:
            obj = rowref.object
            
        if isinstance(rowref, types.ListType):
            return len(obj)
        else:
            return len(obj.__gtkmodel__.children)
        
    def on_iter_nth_child(self, parent, n):
        try:
            return self._getChildData(parent, n)
        except IndexError, e:
            return None
            
    def on_iter_parent(self, rowref):
        return rowref.parentData

