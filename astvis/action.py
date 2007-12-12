#! /usr/bin/env python

import logging as _logging
LOG = _logging.getLogger('action')

import gtk


class action(object):
    def __init__(self, name, label, tooltip = None, icon=None):
        action = manager.getAction(name)
        action.set_property('label', label)
        if tooltip!=None:
            action.set_property('tooltip', tooltip)
        if icon!=None:
            action.set_property('stock-id', icon)
        self.gtkaction = action
    
    def __call__(self, fun):
        fun.__action__ = self.gtkaction
        return fun
        
class ActionManager(object):

    def __init__(self):
        self._actions = {} #: name -> gtk action
        
    def getAction(self, name):
        if not self._actions.has_key(name):
            action = gtk.Action(name, name, None, None)
            self.register(name, action)
        return self._actions.get(name, None)
        
    def register(self, name, action):
        LOG.debug('Registering action %s', name)
        self._actions[name] = action
        
    def registerGroup(self, groupName, obj):
        LOG.debug('Register action group %s with object %s', groupName, obj)
        group = gtk.ActionGroup(groupName)
        clazz = type(obj)
        
        for attrname in dir(clazz):
            attr = getattr(clazz, attrname)
            if hasattr(attr, '__action__'):
                action_ = attr.__action__
                method = getattr(obj, attrname)
                LOG.debug('Connecting %s to the action %s', method, action_.get_name())
                action_.connect('activate', method)
                
        return group

manager = ActionManager()

