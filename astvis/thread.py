#! /usr/bin/env python
import logging
LOG = logging.getLogger('thread')

import threading

_threads = set()

def threaded(func):
    "Decorator to run function in separate thread"
    def decor(*args, **kwargs):
        thread = Thread(func, args, kwargs)
        _threads.add(thread)
        thread.start()
    return decor

class Thread(threading.Thread):

    def __init__(self, func, args, kwargs):
        threading.Thread.__init__(self)
        self.func = func
        self.args = args
        self.kwargs = kwargs
        
    def run(self):
        try:
            LOG.info("Start running %s in thread" % self.func)
            self.func(*self.args, **self.kwargs)
        except(), e:
            LOG.error("Error running %s in thread: %s" % (self.func, e))
            _threads.remove(self)
        else:
            LOG.info("End running %s in thread" % self.func)
            _threads.remove(self)


class Actor(object):

    def __init__(self, obj):
        self._obj = obj
        self._condition = threading.Condition()
        self._messages = []
        self._thread = threading.Thread(self.__run)
        

    def __run(self):
        while True:
            self._condition.acquire()
            while len(self._messages)==0:
                self._condition.wait()
            message = self._messages[0]
            del self._messages[0]
            self._condition.release()

            try:
                self.__call(message)
            except Exception, e:
                LOG.error(e, exc_info)

            
