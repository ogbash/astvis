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
    
    @param actionFilter: action filter
    """
    def __init__(self, manager, groupName, context, contextAdapter, targetClasses=[], categories=[],
                 actionFilter=None, radioPrefix=None):
        self.manager = manager #: host manager
        self.name = groupName #: group name
        self.context = context #: widget or other action context
        self.contextAdapter = contextAdapter #: function to extract target from context
        self.targetClasses = targetClasses
        if not categories:
            categories = [groupName]
        standardFilter = AndFilter(ContextFilter(), TargetFilter(), OneOfCategoriesFilter(categories))
        if actionFilter:
            self.filter = AndFilter(standardFilter, actionFilter)
        else:
            self.filter = standardFilter
        
        self.radioPrefix = radioPrefix #: action name prefix for the radio group

        self.gtkgroup = gtk.ActionGroup(groupName) #: corresponding GTK group
        self.gtkactions = {} #: action name -> GTK action
        self.radioGroup = None
        self.radioActions = []

    def acceptsAction(self, action):
        "Checks that at least one filter for the action holds."
        s = self.filter.satisfies(self, action)
        return s
        
    def updateActions(self, target):
        """Show/hide actions based on the currently selected object.
        
        @param target: selected object"""
        LOG.log(FINE, 'updateActions(%s)', target)
        
        # for all group actions
        for name, gtkaction in self.gtkactions.iteritems():
            action = manager.getAction(name)
            # enable/disable action
            if self.filter.enabled(self, action, target, self.context):
                gtkaction.set_sensitive(True)
            else:
                gtkaction.set_sensitive(False)
        self.manager.ui.ensure_update()
        
    def addAction(self, action):
        if self.radioPrefix==None:
            gtkaction = gtk.Action(action.name, action.label, action.tooltip, action.icon)
        else:
            gtkaction = gtk.RadioAction(action.name, action.label, action.tooltip, action.icon, len(self.radioActions))
            self.radioActions.append(action)
            if self.radioGroup==None:
                self.radioGroup=gtkaction
            else:
                gtkaction.set_group(self.radioGroup)
        
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

    def __init__(self, ui=None):
        self._actions = {} #: name -> gtk action
        self._groups = {} #: name -> list(gtk action group)
        self._services = [] #: list(dict(action -> service method))
        self.ui = ui
        
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

        LOG.debug('Adding action group %s with actions %s', groupName, group.gtkactions.keys())
        if hasattr(group.context, 'UI_DESCRIPTION'):
            self.ui.add_ui_from_string(group.context.UI_DESCRIPTION)
        self.ui.insert_action_group(group.gtkgroup, -1)

        self._groups[groupName].append(group)

    def bringToFront(self, group):
        self.ui.remove_action_group(group.gtkgroup)
        self.ui.insert_action_group(group.gtkgroup, 0)
        
    def registerActionService(self, service):
        "Collects actions of action service."
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

    def createActionGroup(self, groupName, context, contextAdapter=None, **kvargs):
        "Creates new group and fills it with gtk actions"
        LOG.debug('Creating action group "%s" with context %s', groupName, context)
                
        group = ActionGroup(self, groupName, context, contextAdapter, **kvargs)
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

manager = None

def generateMenu(actionGroup, menu=None, connectedActions = []):
    if menu==None:
        menu = gtk.Menu()

    # add menu items for the actions missing from the menu
    LOG.log(FINER, "%s (actionGroup=%s): selecting and adding %s", menu, actionGroup, actionGroup.gtkactions)
    absentNames = set(actionGroup.gtkactions.keys()) - set(connectedActions)

    if absentNames:
        menu.append(gtk.SeparatorMenuItem())
        extraMenu = gtk.Menu()
        extraMenuItem = gtk.MenuItem("extra")
        extraMenuItem.show_all()
        extraMenuItem.set_submenu(extraMenu)
        menu.append(extraMenuItem)
        for name in absentNames:
            gtkaction = actionGroup.gtkactions[name]
            menuItem = gtkaction.create_menu_item()
            extraMenu.append(menuItem)
    return menu


def getMenu(actionGroup, menuName):
    menu=actionGroup.manager.ui.get_widget("/%s"%menuName)

    # add actions that are not in UI description
    menuActions = filter(lambda x: x!=None,
                         map(lambda x: x.get_action(),
                             menu.get_children()))
    actionNames = map(lambda x: x.get_name(), menuActions)
    menu = generateMenu(actionGroup, menu, actionNames)
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



class ActionFilter:

    def satisfies(self, actionGroup, action):
        raise NotImplementedError('Implement in subclass')

    def enabled(self, actionGroup, action, target, context):
        raise NotImplementedError('Implement in subclass')

class AndFilter(ActionFilter):

    def __init__(self, *filters):
        self.filters = filters

    def satisfies(self, actionGroup, action):
        for actionFilter in self.filters:
            if not actionFilter.satisfies(actionGroup, action):
                return False
        return True

    def enabled(self, actionGroup, action, target, context):
        for actionFilter in self.filters:
            if not actionFilter.enabled(actionGroup, action, target, context):
                return False
        return True

class OrFilter(ActionFilter):

    def __init__(self, *filters):
        self.filters = filters

    def satisfies(self, actionGroup, action):
        for actionFilter in self.filters:
            if actionFilter.satisfies(actionGroup, action):
                return True
        return False

    def enabled(self, actionGroup, action, target, context):
        for actionFilter in self.filters:
            if actionFilter.enabled(actionGroup, action, target, context):
                return True
        return False

class ContextFilter(ActionFilter):

    def satisfies(self, actionGroup, action):
        # check that action required context is satisfied
        if action.contextClass!=None:
            if not isinstance(actionGroup.context, action.contextClass):
                return False
        return True

    def enabled(self, actionGroup, action, target, context):
        if action.contextClass!=None:
            return isinstance(context, action.contextClass)
        return True

class TargetFilter(ActionFilter):

    def satisfies(self, actionGroup, action):
        # check target class is satisfied
        if action.targetClass!=None:
            for targetClass in actionGroup.targetClasses:
                if issubclass(action.targetClass, targetClass):
                    break
            else:
                return False
        return True

    def enabled(self, actionGroup, action, target, context):
        if action.targetClass!=None:
            return isinstance(target, action.targetClass)
        return True

class CategoryFilter(ActionFilter):

    def __init__(self, categoryName):
        self.categoryName = categoryName

    def satisfies(self, actionGroup, action):
        return action.name.startswith(self.categoryName)

    def enabled(self, actionGroup, action, target, context):
        return True

class OneOfCategoriesFilter(ActionFilter):

    def __init__(self, categoryNames):
        filters = [CategoryFilter(name) for name in categoryNames]
        self.filter = OrFilter(*filters)

    def satisfies(self, actionGroup, action):
        return self.filter.satisfies(actionGroup, action)

    def enabled(self, actionGroup, action, target, context):
        return self.filter.enabled(actionGroup, action, target, context)
