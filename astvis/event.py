#! /usr/bin/env python

import logging
LOG = logging.getLogger("event")

from astvis.misc.tools import hashable

# observer
ADDED_TO_DIAGRAM = "added to diagram" #: object, diagram
REMOVED_FROM_DIAGRAM = "removed from diagram" #: object, diagram

TASK_STARTED = 'task started'
TASK_PROGRESSED = 'task progressed'
TASK_ENDED = 'task ended'
TASK_CANCELLED = 'task cancelled'

PROPERTY_CHANGED = 'property changed' #: args = (name, action,newvalue, oldvalue)
PC_CHANGED = 1
PC_ADDED = 2
PC_REMOVED = 3

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
        self._eventSubs = {} # class -> set<observer>

    def subscribe(self, observer, obj):
        if not self._subs.has_key(obj):
            self._subs[obj] = set()
        return self._subs[obj].add(observer)
        
    def unsubscribe(self, observer, obj):
        if self._subs.has_key(obj):
            return self._subs[obj].remove(observer)
        return False
        
    def subscribeClass(self, observer, clazz):
        if not self._classSubs.has_key(clazz):
            self._classSubs[clazz] = set()
        return self._classSubs[clazz].add(observer)        

    def unsubscribeClass(self, observer, clazz):
        if self._classSubs.has_key(clazz):
            return self._classSubs[clazz].remove(observer)
        return False

    def subscribeEvent(self, observer, event_):
        if not self._eventSubs.has_key(event_):
            self._eventSubs[event_] = set()
        return self._eventSubs[event_].add(observer)        

    def unsubscribeEvent(self, observer, event_):
        if self._eventSubs.has_key(event_):
            return self._eventSubs[event_].remove(observer)
        return False

    def _getMatchingBaseClasses(self, clazz):
        return filter(lambda base: issubclass(clazz, base), self._classSubs.keys())

    def notifyObservers(self, obj, event, args, dargs=None):
        # notify for event observers
        for obsEvent in self._eventSubs.iterkeys():
            if event.startswith(obsEvent):
                observers = self._eventSubs[obsEvent]
                for observer in observers:
                    try:
                        if isinstance(observer,Observer):
                            observer.notify(obj, event, args, dargs)
                        else:
                            observer(obj, event,args, dargs)
                    except(Exception), e:
                        LOG.warn("Exception during event notify<observer=%s>(obj=%s,event=%s): %s", 
                                observer, obj, event, e, exc_info=True)
    
        # first notify class observers
        bases = self._getMatchingBaseClasses(obj.__class__)
        for base in bases:
            observers = self._classSubs[base]
            for observer in observers:
                try:
                    if isinstance(observer,Observer):
                        observer.notify(obj, event, args, dargs)
                    else:
                        observer(obj, event, args, dargs)
                except(Exception), e:
                    LOG.warn("Exception during class notify<observer=%s>(obj=%s,event=%s): %s", 
                            observer, obj, event, e, exc_info=True)

        # notify object observers
        if hashable(obj):
            for observer in self._subs.get(obj, ()):
                try:
                    if isinstance(observer,Observer):
                        observer.notify(obj, event, args, dargs)
                    else:
                        observer(obj, event,args, dargs)
                except(Exception), e:
                    LOG.warn("Exception during object notify<observer=%s>(obj=%s,event=%s): %s", 
                            observer, obj, event, e, exc_info=True)

manager = EventManager()

class Property(object):
    "Property wrapper that notifies event manager when setter is called."
    def __init__(self, prop, propertyName):
        self.property = prop
        self.propertyName = propertyName

    def __get__(self, obj, type=None):
        return self.property.__get__(obj, type)
        
    def __set__(self, obj, value):
        oldValue = self.property.__get__(obj)
        self.property.__set__(obj, value)
        manager.notifyObservers(obj, PROPERTY_CHANGED, (self.propertyName,PC_CHANGED,value,oldValue))

