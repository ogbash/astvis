
import unittest

from astvis import action

action.manager = action.ActionManager()

class TestCase(unittest.TestCase):
    def browse(self, obj):
        import gtk
        from astvis.misc.browser import Browser
        objectBrowser = Browser('browser', obj)
        objectBrowser.window.connect('destroy', gtk.main_quit)
        gtk.main()
