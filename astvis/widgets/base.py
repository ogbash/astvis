#! /usr/bin/env python

import gtk.glade
from astvis import action

class BaseWidget(object):
    "Base widget for the views/trees/widgets"

    def __init__(self, widgetName, outerWidgetName=None, gladeFile='astvisualizer.glade', widgetsWindow='widgets_window',
            actionGroupName=None, menuName=None):
        self.wTree = gtk.glade.XML(gladeFile, widgetsWindow) #: widget tree
        self.widget = self.wTree.get_widget(widgetName) #: widget that holds basic logic
        self.outerWidget = self.wTree.get_widget(outerWidgetName or widgetName) #: widget that encloses all others (usually scrollbar window or so)
        self.wTree.signal_autoconnect(self)
        self.actionGroup = action.manager.createActionGroup(actionGroupName or widgetName, context=self) #: action group

        # context menu
        self.outerWidget.get_parent().remove(self.outerWidget)
        if menuName:
            menuwTree = gtk.glade.XML(gladeFile, menuName)
            self.contextMenu = menuwTree.get_widget(menuName)
            action.connectWidgetTree(self.actionGroup, menuwTree)
        else:
            self.contextMenu = action.generateMenu(self.actionGroup)
        self.widget.connect("button-press-event", self.__buttonPress)
        self.widget.connect_after("popup-menu", self._popupMenu)

    def _popupMenu(self, widget, time=0):
        _model, iRow = self.widget.get_selection().get_selected()
        obj = _model[iRow][1]
        if obj is not None:
            self.contextMenu.popup(None, None, None, 3, time)

    def __buttonPress(self, widget, event):
        if event.type==gtk.gdk.BUTTON_PRESS and event.button==3:
            self._popupMenu(widget, event.get_time())
            return True
