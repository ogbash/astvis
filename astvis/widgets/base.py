#! /usr/bin/env python

import logging
from astvis.common import FINE, FINER, FINEST
LOG = logging.getLogger('basetree')

import gtk.glade
from astvis import action, gtkx

class BaseWidget(object):
    "Base widget for the tree widgets."

    @classmethod
    def getActionGroup(cls):
        "Implement in subclasses."
        raise NotImplementedError

    def __init__(self, widgetName, outerWidgetName=None, wTree=None, gladeFile='astvisualizer.glade', widgetsWindow='widgets_window',
            actionGroupName=None, menuName=None, **kvargs):

        if wTree==None:
            self.wTree = gtk.glade.XML(gladeFile, widgetsWindow) #: widget tree
            self.outerWidget = self.wTree.get_widget(outerWidgetName or widgetName) #: widget that encloses all others (usually scrollbar window or so)
            self.outerWidget.get_parent().remove(self.outerWidget)
            self.wTree.signal_autoconnect(self)
        else:
            self.wTree = wTree
    
        self.widget = self.wTree.get_widget(widgetName) #: widget that holds basic logic

        # actions
        action.manager.registerActionService(self)
        
        self.gtkActionGroup = self.getActionGroup().createGtkActionGroup(self)
        action.manager.addGtkGroup(self.gtkActionGroup)

        # context menu
        if menuName:
            self.contextMenu = action.getMenu(self.gtkActionGroup, menuName)
        else:
            self.contextMenu = None
            
        self.widget.connect("button-press-event", self.__buttonPress)
        self.widget.connect("focus-in-event", self._focusIn)
        self.widget.connect_after("popup-menu", self._popupMenu)
        self.widget.get_selection().connect("changed", self.__selectionChanged)

        # browse history
        self._history = []
        self._historyPosition = -1
        self._historyForwardButton = self.wTree.get_widget("%s_history_forward" % widgetName)
        self._historyBackwardButton = self.wTree.get_widget("%s_history_backward" % widgetName)
        self._updateHistoryButtons()

    def getSelected(self):
        model, iRow = self.widget.get_selection().get_selected()
        if iRow==None:
            return None
        if isinstance(model, gtkx.PythonTreeModel):
            obj = model.getObject(iRow)
        else:
            obj = model[iRow][1] # actual object is by convention stored at index 1
        return obj

    def _popupMenu(self, widget, time=0):
        if self.contextMenu!=None:
            _model, iRow = self.widget.get_selection().get_selected()
            self.contextMenu.popup(None, None, None, 3, time)

    def __buttonPress(self, widget, event):
        if event.type==gtk.gdk.BUTTON_PRESS and event.button==3:
            self._popupMenu(widget, event.get_time())
            return True
            
    def __selectionChanged(self, selection):
        model, iRow = selection.get_selected()
        parent, childName, obj = _extractObjectInfo(model, iRow)
        self.getActionGroup().updateActions(self.gtkActionGroup, obj)

    def _focusIn(self, widget, ev):
        if self.gtkActionGroup!=None:
            action.manager.bringToFront(self.gtkActionGroup)

    def history_backward(self, widget):
        if self._historyPosition>0:
            self._historyPosition = self._historyPosition-1
            state = self._history[self._historyPosition]
            self.setState(state)

            self._updateHistoryButtons()

    def history_forward(self, widget):
        if self._historyPosition<len(self._history)-1:
            self._historyPosition = self._historyPosition+1
            state = self._history[self._historyPosition]
            self.setState(state)

            self._updateHistoryButtons()

    def updateHistory(self):
        "Take current state and insert it at the current history position."
        state = self.getState()
        if state!=None:
            LOG.debug("Update history state=%s", state)
            del self._history[self._historyPosition+1:]
            self._history.append(state)
            self._historyPosition = self._historyPosition+1
            self._updateHistoryButtons()

    def _updateHistoryButtons(self):
        if self._historyForwardButton!=None:
            self._historyForwardButton.set_sensitive(self._historyPosition<len(self._history)-1)
        if self._historyBackwardButton!=None:
            self._historyBackwardButton.set_sensitive(self._historyPosition>0)

    def getState(self):
        raise NotImplementedError()

    def setState(self, state):
        raise NotImplementedError()

def _extractObjectInfo(model, iRow):
    childName = None
    obj = None
    parent = None
    if iRow!=None:
        if isinstance(model, gtkx.PythonTreeModel):
            obj = model.getObject(iRow)
            childName = model.getChildName(iRow)
            parent = model.getParent(iRow)
        else:
            obj = model[iRow][1]
    return parent, childName, obj
