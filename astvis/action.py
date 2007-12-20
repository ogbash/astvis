#! /usr/bin/env python

import logging as _logging
from astvis.common import FINE, FINER, FINEST
LOG = _logging.getLogger('action')

import gtk


class Action(object):
    def __init__(self, name, label = None, tooltip = None, icon = None,
            group = 'global', targetClass=None, contextClass=None):
        self.name = name
        self.label = label
        self.tooltip = tooltip
        self.icon = icon
        
        self.group = group
        self.targetClass = targetClass
        self.contextClass = contextClass
    
    def __call__(self, fun):
        fun.__action__ = self
        return fun
        
    def __str__(self):
        return "Action<%s>" % self.name
        
class ActionGroup(object):
    def __init__(self, manager, groupName, context, contextAdapter, actionFilter):
        self.manager = manager #: host manager
        self.name = groupName #: group name
        self.context = context #: widget or other action context
        self.contextAdapter = contextAdapter #: function to extract target from context
        self.actionFilter = actionFilter #: filter of action to include in this group
        self.gtkgroup = gtk.ActionGroup(groupName) #: corresponding GTK group
        self.gtkactions = {} #: action name -> GTK action
 
    def acceptsAction(self, action):       
        if self.actionFilter!=None and not self.actionFilter(action):
            if LOG.isEnabledFor(FINEST):
                LOG.log(FINEST, "Skip %s, filter returned False" % (action,))
            return False
        if action.contextClass!=None and not isinstance(self.context, action.contextClass):
            if LOG.isEnabledFor(FINEST):
                LOG.log(FINEST, "Skip %s, %s is not instance of %s" % (action, self.context, action.contextClass))
            return False

        return True
        
    def addAction(self, action):
        gtkaction = gtk.Action(action.name, action.label, action.tooltip, action.icon)
        gtkaction.connect("activate", self._activate)
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "Adding gtk instance of %s with context %s" % (action, self.context))
        self.gtkgroup.add_action(gtkaction)
        self.gtkactions[action.name] = gtkaction


    def _activate(self, gtkaction):
        # resolve target
        target = self.context
        if self.contextAdapter!=None:
            target = self.contextAdapter(context)
        manager.activate(gtkaction.get_name(), target, self.context)
        
    def connectProxy(self, actionName, widget):                
        if not self.gtkactions.has_key(actionName):
            LOG.warn("Action %s not found, cannot connect %s" % (actionName, widget))
            return False
        gtkaction = self.gtkactions[actionName]
        LOG.log(FINER, "Connecting proxy %s to %s" % (widget, gtkaction))
        gtkaction.connect_proxy(widget)
        return True
        
    def connectWidgetTree(self, wTree):
        "Scan widget tree and connect widgets to their actions"
        for prefix in ['menu-', 'button-']:
            widgets = wTree.get_widget_prefix(prefix)        
            for widget in widgets:
                name = gtk.glade.get_widget_name(widget)
                actionName = name[len(prefix):]
                self.connectProxy(actionName, widget)

        
class ActionManager(object):

    def __init__(self):
        self._actions = {} #: name -> gtk action
        self._groups = {} #: name -> list(gtk action group)
        self._services = [] #: list(dict(action -> service method))
        
    def getGroups(self, groupName):
        return self._groups[groupName]
        
    def getAction(self, name):
        return self._actions.get(name, None)
        
    def addAction(self, action):
        if not self._actions.has_key(action.name):
            LOG.log(FINE, 'Registering action %s', action.name)
            self._actions[action.name] = action
            return True
        return False
        
    def addGroup(self, groupName, group):
        if not self._groups.has_key(groupName):
            self._groups[groupName] = []
        LOG.debug('Adding action group %s', groupName)
        self._groups[groupName].append(group)    
        
    def registerActionService(self, service):
        "Collects actions of action service and "
        clazz = type(service)
        actions = {} #: action -> service method
        
        for attrname in dir(clazz):
            attr = getattr(clazz, attrname)
            if hasattr(attr, '__action__'):
                action = attr.__action__
                self.addAction(action)
                method = getattr(service, attrname)
                actions[action] = method
        
        LOG.debug("Registering service %s with %d actions" % (service, len(actions)))
        self._services.append(actions)
        return actions

    def createActionGroup(self, groupName, context, contextAdapter=None, actionFilter=None):
        "Creates new group and fills it with gtk actions"
        LOG.debug('Creating action group "%s" with context %s', groupName, context)
                
        group = ActionGroup(self, groupName, context, contextAdapter, actionFilter)
        for action in self._actions.itervalues():
            if group.acceptsAction(action):            
                group.addAction(action)
        
        self.addGroup(groupName, group)        
        return group
        
    def activate(self, actionName, target, context):
        LOG.log(FINE,"action %s activated with %s within %s" % (actionName, target, context))

        action = self._actions[actionName]
                    
        # look through all action services and call given action
        if LOG.isEnabledFor(FINER):
            LOG.log(FINER, "Looking for action in %d services" % len(self._services))
        for service in self._services:
            if service.has_key(action):
                method = service[action]
                try:
                    LOG.debug("Action activation calls %s" % method)
                    method(target, context=context)
                except Exception, e:
                    LOG.warn("Error during %s activation", action, exc_info=e)

manager = ActionManager()

