#! /usr/bin/env python

"Classes and methods related to the UI actions."

import logging as _logging
from astvis.common import FINE, FINER, FINEST
LOG = _logging.getLogger('action')

import gtk
import types

class Action(object):
    "Logical action that is used as a template for the GTK actions."
    def __init__(self, name, label = None, tooltip = None, icon = None,
            targetClass=None, contextClass=None, sensitivePredicate=None):
        self.name = name
        self.label = label or name
        self.tooltip = tooltip
        self.icon = icon
        
        self.targetClass = targetClass #: required target class
        self.contextClass = contextClass #: required context class
        self.sensitivePredicate = sensitivePredicate #: given target and context returns if action should be enabled
    
    def __call__(self, fun):
        fun.__action__ = self
        return fun
        
    def __str__(self):
        return "Action<%s>" % self.name
        
class ActionGroup(object):
    """Set of action instances (GTK actions) related to some widget.
    
    Action filter is a dictionary with the following possible key-value pairs:
      - C{'category':categoryName} filters actions with the given prefix in their names
    
    @param actionFilters: list of action filters
    """
    def __init__(self, manager, groupName, context, contextAdapter, actionFilters=[{}]):
        self.manager = manager #: host manager
        self.name = groupName #: group name
        self.context = context #: widget or other action context
        self.contextAdapter = contextAdapter #: function to extract target from context
        self.actionFilters = actionFilters #: filters for actions to include in this group
        self.gtkgroup = gtk.ActionGroup(groupName) #: corresponding GTK group
        self.gtkactions = {} #: action name -> GTK action

    def _filterAcceptsAction(self, action, actionFilter):
        "Check that if all conditions in the filter hold"
        # check that action is in a given category
        if actionFilter.has_key('category') and not action.name.startswith(actionFilter['category']):
            if LOG.isEnabledFor(FINEST):
                LOG.log(FINEST, "%s is not in the category '%s'" % (action, actionFilter['category']))
            return False        

        # check target classes
        if actionFilter.has_key('targetClasses') and action.targetClass!=None:
            for targetClass in actionFilter['targetClasses']:
                if issubclass(action.targetClass, targetClass):
                    return True
            else:
                return False

        return True
            
    def acceptsAction(self, action):
        "Checks that at least one filter for the action holds."

        # check that action required context is satisfied
        if action.contextClass!=None:
            if isinstance(self.context, action.contextClass):
                if LOG.isEnabledFor(FINEST):
                    LOG.log(FINEST, "Context %s for action %s is not satisfied (given %s)" 
                            % (action.contextClass, action, self.context.__class__))
                return True
            return False

        # user defined filters
        for actionFilter in self.actionFilters:
            if self._filterAcceptsAction(action, actionFilter):
                return True
        return False
        
    def updateActions(self, target):
        """Show/hide actions based on the currently selected object.
        
        @param target: selected object"""
        LOG.log(FINE, 'updateActions(%s)', target)
        
        # for all group actions
        for name, gtkaction in self.gtkactions.iteritems():
            action = manager.getAction(name)
            # show/hide action
            if action.targetClass!=None and not isinstance(target, action.targetClass):
                gtkaction.props.visible = False
            else:
                gtkaction.props.visible = True
            # enable/disable action
            if action.sensitivePredicate!=None and not action.sensitivePredicate(target, self.context):
                gtkaction.props.sensitive = False
            else:
                gtkaction.props.sensitive = True         
        
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
            target = self.contextAdapter(self.context)
        manager.activate(gtkaction.get_name(), target, self.context)
        
    def connectProxy(self, actionName, widget):                
        if not self.gtkactions.has_key(actionName):
            LOG.warn("Action %s not found, cannot connect %s" % (actionName, widget))
            return False
        gtkaction = self.gtkactions[actionName]
        LOG.log(FINER, "Connecting proxy %s to %s" % (widget, gtkaction))
        gtkaction.connect_proxy(widget)
        return True
        
    def __str__(self):
        return "ActionGroup{%s}" % self.name
        
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
        if type(service) not in [types.ModuleType]:
            clazz = type(service)
        else:
            clazz = service
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

    def createActionGroup(self, groupName, context, contextAdapter=None, actionFilters=[{}]):
        "Creates new group and fills it with gtk actions"
        LOG.debug('Creating action group "%s" with context %s', groupName, context)
                
        group = ActionGroup(self, groupName, context, contextAdapter, actionFilters=actionFilters)
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

def generateMenu(actionGroup, menu=None, connectedActions = set()):
    if menu==None:
        menu = gtk.Menu()

    # add menu items for the actions missing from the menu
    LOG.log(FINER, "%s (actionGroup=%s): selecting and adding %s", menu, actionGroup, actionGroup.gtkactions)
    for name, gtkaction in actionGroup.gtkactions.iteritems():
        if name in connectedActions:
            continue
        menuItem = gtkaction.create_menu_item()
        menu.append(menuItem)
    return menu
    

def generateMenuFromGlade(actionGroup, wTree=None, templateMenuName=None):
    menu = None
    if templateMenuName:
        menu = wTree.get_widget(templateMenuName)

    connectedActions = set()
    if wTree:
        connectedActions = connectWidgetTree(actionGroup, wTree)

    return generateMenu(actionGroup, menu, connectedActions)
    
def connectWidgetTree(actionGroup, wTree):
    "Scan widget tree and connect widgets to their actions"
    connectedActions = set()
    for prefix in ['menu-', 'button-']:
        widgets = wTree.get_widget_prefix(prefix)        
        for widget in widgets:
            name = gtk.glade.get_widget_name(widget)
            actionName = name[len(prefix):]
            actionGroup.connectProxy(actionName, widget)
            connectedActions.add(actionName)
    return connectedActions

