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
            self.actionGroup.connectWidgetTree(menuwTree)
        else:
            self.contextMenu = None

