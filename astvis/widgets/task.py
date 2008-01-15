#!/usr/bin/env python

import gtk
from astvis import event, xmlmap

__all__ = ['TaskHandler']

class TaskHandler:

    def __init__(self, gtktable, gtklabel):
        self.gtktable = gtktable
        self.gtklabel = gtklabel
        self.tasks = {}
        event.manager.subscribeEvent(self._notify, 'task')
        
    def _notify(self, obj, event_, args, dargs):
        if event_ is event.TASK_STARTED:
            text, = args
            bar = gtk.ProgressBar()
            bar.set_text(text)
            bar.show()
            nrows = len(self.tasks)
            self.tasks[obj] = bar
            self.gtktable.attach(bar,0,1,nrows,nrows+1,yoptions=0)
            self.gtklabel.set_text('tasks(%d)' % len(self.tasks))
        elif event_ is event.TASK_ENDED or event_ is event.TASK_CANCELLED:
            self.gtktable.remove(self.tasks[obj])
            del self.tasks[obj]
            self.gtklabel.set_text('tasks(%d)' % len(self.tasks))
        elif event_ is event.TASK_PROGRESSED:
            ratio, = args
            self.tasks[obj].set_fraction(ratio)
            #print event_, ratio

