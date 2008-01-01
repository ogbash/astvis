
import gtk

class PythonTreeModel(gtk.GenericTreeModel):
    def on_get_flags(self):
        return 0
    def on_get_n_columns(self):
        return 1
    def on_get_column_type(self, index):
        return str
    def on_get_iter(self, path):
        return 'ref'
    def on_get_path(self, rowref):
        return 0
    def on_get_value(self, rowref, column):
        return 'bb'
    def on_iter_next(self, rowref):
        return None
    def on_iter_children(self, parent):
        if parent==None:
            return 'ref'
        return None
    def on_iter_has_child(self, rowref):
        return False
    def on_iter_n_children(self, rowref):
        if rowref==None:
            return 1
        return 0
    def on_iter_nth_child(self, parent, n):
        return 'bb'
    def on_iter_parent(self, child):
        return None

