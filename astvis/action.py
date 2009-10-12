#! /usr/bin/env python

"Classes and methods related to the UI actions."

import logging as _logging
from astvis.common import FINE, FINER, FINEST
LOG = _logging.getLogger('action')

import gtk
import types

class Action(object):
    "Logical action that is used as a template for the GTK actions."
    def __init__(self, name, label = None, tooltip = None, icon = None, accel=None,
                 targetClass=None, contextClass=None,
                 sensitivePredicate=None, getSubmenuItems=None):
        self.name = name
        self.label = label or name
        self.tooltip = tooltip
        self.icon = icon
        self.accel = accel

        self.targetClass = targetClass #: required target class
        self.contextClass = contextClass #: required context class
        self.sensitivePredicate = sensitivePredicate #: given target and context returns if action should be enabled
        self.getSubmenuItems = getSubmenuItems
    
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
    def __init__(self, manager, groupName, contextAdapter=None, contextClass=None,
                 targetClasses=[], categories=[],
                 actionFilter=None, radioPrefix=None):
        self.manager = manager #: host manager
        self.name = groupName #: group name
        self.contextAdapter = contextAdapter #: function to extract target from context
        self.contextClass = contextClass
        self.targetClasses = targetClasses
        if not categories:
            categories = [groupName]
        standardFilter = AndFilter(ContextFilter(),
                                   TargetFilter(),
                                   OneOfCategoriesFilter(categories),
                                   PredicateFilter())
        if actionFilter:
            self.filter = AndFilter(standardFilter, actionFilter)
        else:
            self.filter = standardFilter
        
        self.radioPrefix = radioPrefix #: action name prefix for the radio group
        
        self.radioGroup = None
        self.radioActions = []
        
        self.gtkgroups = set()
        self.actions = {}

        for action in self.manager._actions.values():
            if self.acceptsAction(action):
                self.actions[action.name] = action

    def acceptsAction(self, action):
        "Checks that at least one filter for the action holds."
        s = self.filter.satisfies(self, action)
        return s

    def addAction(self, action):
        self.actions[action.name] = action

    def updateAction(self, gtkaction, target, widget=None):
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "updateAction() for %s", gtkaction.get_name())
        
        actionName = gtkaction.get_name()
        action = self.actions[actionName]
        gtkgroup = gtkaction.props.action_group
        context = gtkgroup.get_data('context')

        # enable/disable action
        if self.filter.enabled(self, action, target, context):
            gtkaction.set_sensitive(True)
        else:
            gtkaction.set_sensitive(False)        

        # get submenu items
        if action.getSubmenuItems!=None:
            sub = gtk.Menu()
            if widget!=None:
                widget.set_submenu(sub)
            else:
                for proxy in gtkaction.get_proxies():
                    proxy.set_submenu(sub)
            
            items = action.getSubmenuItems(context)
            for name, sensitive in items:
                subItem = gtk.MenuItem(name)
                subItem.set_sensitive(sensitive)
                subItem.connect('activate', self._activateItem,
                                actionName, name, context)
                sub.append(subItem)

            sub.show_all()
        
    def updateActions(self, gtkgroup, target):
        """Show/hide actions based on the currently selected object.
        
        @param target: selected object"""
        LOG.log(FINE, 'updateActions(%s)', target)
        # for all group actions
        for gtkaction in gtkgroup.list_actions():
            self.updateAction(gtkaction, target)
        self.manager.ui.ensure_update()
    
    def _addGtkAction(self, gtkgroup, action):
        if self.radioPrefix==None:
            gtkaction = gtk.Action(action.name, action.label, action.tooltip, action.icon)
        else:
            gtkaction = gtk.RadioAction(action.name, action.label, action.tooltip, action.icon, len(self.radioActions))
            self.radioActions.append(action)
            if self.radioGroup==None:
                self.radioGroup=gtkaction
            else:
                gtkaction.set_group(self.radioGroup)
        context = gtkgroup.get_data('group')
            
        gtkaction.connect("activate", self._activate)
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "Adding gtk instance of %s with context %s" % (action, context))
        gtkgroup.add_action_with_accel(gtkaction, action.accel)


    def _activateItem(self, item, actionName, name, context):
        print context, name
        self.manager.activate(actionName, name, context)

    def _activate(self, gtkaction):
        # resolve target
        gtkgroup = gtkaction.props.action_group
        group = gtkgroup.get_data('group')
        context =  gtkgroup.get_data('context')
        action = group.actions[gtkaction.get_name()]

        if action.getSubmenuItems==None:
            target = None
            if self.contextAdapter!=None:
                target = self.contextAdapter(context)
            manager.activate(gtkaction.get_name(), target, context)
        else:
            pass # action with submenu
        
    def connectProxy(self, gtkgroup, actionName, widget):
        gtkaction = gtkgroup.get_action(actionName)
        if not gtkaction:
            LOG.warn("Action %s not found, cannot connect %s" % (actionName, widget))
            return False
        LOG.log(FINER, "Connecting proxy %s to %s" % (widget, gtkaction))
        gtkaction.connect_proxy(widget)
        return True

    def createGtkActionGroup(self, context):
        "Creates new gtk group and fills it with gtk actions"
        LOG.debug('Creating gtk action group "%s" with context %s', self.name, context)
                
        gtkgroup = gtk.ActionGroup(self.name) #: corresponding GTK group
        gtkgroup.set_data('group', self)
        gtkgroup.set_data('context', context)
        
        for action in self.actions.values():
            self._addGtkAction(gtkgroup, action)
        
        self.gtkgroups.add(gtkgroup)  
        return gtkgroup
        
    def __str__(self):
        return "ActionGroup{%s}" % self.name
        
class ActionManager(object):

    def __init__(self, ui=None):
        self._actions = {} #: name -> gtk action
        self._groups = {} #: name -> list(gtk action group)
        self._services = [] #: list(dict(action -> service method))
        self.ui = ui
        if ui is not None:
            self.ui.connect('connect-proxy', self._proxyConnected)

    def _proxyConnected(self, ui, gtkaction, widget):
        gtkgroup = gtkaction.props.action_group
        name = gtkaction.get_name()
        group = gtkgroup.get_data('group')
        group.updateAction(gtkaction, None, widget)
        
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
        
    def addGtkGroup(self, gtkActionGroup):
        
        LOG.debug('Adding action group %s', gtkActionGroup.get_name())
        self.ui.insert_action_group(gtkActionGroup, -1)
        context = gtkActionGroup.get_data('context')
        if hasattr(context, 'UI_DESCRIPTION'):
            self.ui.add_ui_from_string(context.UI_DESCRIPTION)

    def bringToFront(self, gtkgroup):
        self.ui.remove_action_group(gtkgroup)
        self.ui.insert_action_group(gtkgroup, 0)
        
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
        
    def activate(self, actionName, target, context):
        LOG.log(FINE,"action %s activated with %s within %s" % (actionName, target, context))

        if not self._actions.has_key(actionName):
            LOG.log(FINE,"action %s not found" % (actionName))
            return
        
        action = self._actions[actionName]
                    
        # look through all action services and call given action
        if LOG.isEnabledFor(FINER):
            LOG.log(FINER, "Looking for action in %d services" % len(self._services))
        # find services that provide given action
        methods = []
        for service in self._services:
            if service.has_key(action):
                method = service[action]
                if isinstance(method, types.MethodType) and \
                   method.im_self is context:
                    # context is the same as service, use it
                    methods = [method]
                    break
                # otherwise collect all services
                methods.append(method)

        for method in methods:
            try:
                LOG.debug("Action activation calls %s" % method)
                method(target, context=context)
            except Exception, e:
                LOG.warn("Error during %s activation", action, exc_info=e)

manager = None

def generateMenu(gtkActionGroup, menu=None, connectedActions = []):
    if menu==None:
        menu = gtk.Menu()

    actionGroup = gtkActionGroup.get_data('group')

    # add menu items for the actions missing from the menu
    LOG.log(FINER, "%s (actionGroup=%s)", menu, actionGroup)
    absentNames = set(actionGroup.actions.keys()) - set(connectedActions)

    if absentNames:
        menu.append(gtk.SeparatorMenuItem())
        extraMenu = gtk.Menu()
        extraMenuItem = gtk.MenuItem("extra")
        extraMenuItem.show_all()
        extraMenuItem.set_submenu(extraMenu)
        menu.append(extraMenuItem)
        for name in absentNames:
            gtkaction = gtkActionGroup.get_action(name)
            menuItem = gtkaction.create_menu_item()
            extraMenu.append(menuItem)
    return menu


def getMenu(gtkActionGroup, menuName):
    actionGroup = gtkActionGroup.get_data('group')
    menu=actionGroup.manager.ui.get_widget("/%s"%menuName)

    # add actions that are not in UI description
    def collectNames(menu):
        names = set()
        for child in menu.get_children():
            action = child.get_action()
            if action is not None:
                names.add(action.get_name())
            
            # recursively
            if isinstance(child, gtk.MenuItem) and child.get_submenu()!=None:
                names.update(collectNames(child.get_submenu()))
        return names    
    actionNames = collectNames(menu)
        
    #actionNames = map(lambda x: x.get_name(), menuActions)
    menu = generateMenu(gtkActionGroup, menu, actionNames)
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
            if actionGroup.contextClass!=None and \
                   issubclass(actionGroup.contextClass, action.contextClass):
                return True
            else:
                return False
        return True

    def enabled(self, actionGroup, action, target, context):
        if action.contextClass!=None:
            result = isinstance(context, action.contextClass)
            if LOG.isEnabledFor(FINEST):
                LOG.log(FINEST, "context filter enabled(): isinstance(%s,%s) -> %s",
                        context, action.contextClass, result)
            return result
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
            result = isinstance(target, action.targetClass)
            if LOG.isEnabledFor(FINEST):
                LOG.log(FINEST, "target filter enabled(): isinstance(%s,%s) -> %s",
                        target, action.targetClass, result)
            return result
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

class PredicateFilter(ActionFilter):

    def satisfies(self, actionGroup, action):
        return True

    def enabled(self, actionGroup, action, target, context):
        if action.sensitivePredicate!=None:
            result = action.sensitivePredicate(target, context)
            if LOG.isEnabledFor(FINEST):
                LOG.log(FINEST, "predicate filter enabled(): %s", result)
            return result
        return True
