#!/usr/bin/env python

import gtk
from astvis import event, xmlmap

class TaskHandler:

    def __init__(self, gtktable, gtklabel):
        self.gtktable = gtktable
        self.gtklabel = gtklabel
        self.tasks = {}
        event.manager.subscribeClass(self._notify, xmlmap.XMLLoader)
        
    def _notify(self, obj, event_, args):
        if event_ is event.XMLMAP_STARTED:
            bar = gtk.ProgressBar()
            bar.set_text('Loading AST file')
            bar.show()
            nrows = len(self.tasks)
            self.tasks[obj] = bar
            self.gtktable.attach(bar,0,1,nrows,nrows+1,yoptions=0)
            self.gtklabel.set_text('tasks(%d)' % len(self.tasks))
        elif event_ is event.XMLMAP_ENDED:
            self.gtktable.remove(self.tasks[obj])
            del self.tasks[obj]
            self.gtklabel.set_text('tasks(%d)' % len(self.tasks))
        elif event_ is event.XMLMAP_PROGRESSED:
            ratio, = args
            self.tasks[obj].set_fraction(ratio)
            #print event_, ratio

