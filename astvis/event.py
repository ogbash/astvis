#! /usr/bin/env python

import logging
LOG = logging.getLogger("event")

# observer
ADDED_TO_DIAGRAM = "added to diagram" # object, diagram
REMOVED_FROM_DIAGRAM = "removed from diagram" # object, diagram

class Observer:
    "Interface for observers"
    def notify(self, obj, event, args):
        pass

# observer is either
#  1) Observer with observer.notify(obj, event, args=(arg,..))
#  2) observer(obj, event, args=(arg,..))

class EventManager:
    def __init__(self):
        self._subs = {} # obj -> set<observer>
        self._classSubs = {} # class -> set<observer>

    def subscribe(self, observer, obj):
        if not self._subs.has_key(obj):
            self._subs[obj] = set()
        return self._subs[obj].add(observer)
        
    def unsubscribe(self, observer, obj):
        if self._subs.has_key(obj):
            return self._subs.remove(observer)
        return False
        
    def subscribeClass(self, observer, clazz):
        if not self._classSubs.has_key(clazz):
            self._classSubs[clazz] = set()
        return self._classSubs[clazz].add(observer)        

    def unsubscribeClass(self, observer, clazz):
        if self._classSubs.has_key(clazz):
            return self._classSubs.remove(observer)
        return False

    def _getMatchingBaseClasses(self, clazz):
        return filter(lambda base: issubclass(clazz, base), self._classSubs.keys())

    def notifyObservers(self, obj, event, args):
        # first notify class observers
        bases = self._getMatchingBaseClasses(obj.__class__)
        for base in bases:
            observers = self._classSubs[base]
            for observer in observers:
                try:
                    if isinstance(observer,Observer):
                        observer.notify(obj, event, args)
                    else:
                        observer(obj, event,args)
                except(Exception), e:
                    LOG.warn("Exception during notify, %s", e, exc_info=True)            

        # notify object observers
        for observer in self._subs.get(obj, ()):
            try:
                if isinstance(observer,Observer):
                    observer.notify(obj, event, args)
                else:
                    observer(obj, event,args)
            except(Exception), e:
                LOG.warn("Exception during notify, %s", e, exc_info=True)

manager = EventManager()

