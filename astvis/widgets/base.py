#! /usr/bin/env python

import gtk.glade
from astvis import action, gtkx

class BaseWidget(object):
    "Base widget for the tree widgets."

    def __init__(self, widgetName, outerWidgetName=None, gladeFile='astvisualizer.glade', widgetsWindow='widgets_window',
            actionGroupName=None, menuName=None, **kvargs):
            #contextAdapter=None, actionFilters=[{}], menuName=None):
        self.wTree = gtk.glade.XML(gladeFile, widgetsWindow) #: widget tree
        self.widget = self.wTree.get_widget(widgetName) #: widget that holds basic logic
        self.outerWidget = self.wTree.get_widget(outerWidgetName or widgetName) #: widget that encloses all others (usually scrollbar window or so)
        self.wTree.signal_autoconnect(self)
        "action group"
        self.actionGroup = action.manager.createActionGroup(actionGroupName or widgetName, context=self, contextAdapter=self.getSelected,
                **kvargs)

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
        self.widget.get_selection().connect("changed", self.__selectionChanged)

    def getSelected(self, context):
        model, iRow = self.widget.get_selection().get_selected()
        if iRow==None:
            return None
        return model[iRow][1] # actual object is by convention stored at index 1

    def _popupMenu(self, widget, time=0):
        _model, iRow = self.widget.get_selection().get_selected()
        if iRow is not None:
            if isinstance(_model, gtkx.PythonTreeModel):
                obj = _model.getObject(iRow)
                self.contextMenu.popup(None, None, None, 3, time)
            else:
                obj = _model[iRow][1]
                self.contextMenu.popup(None, None, None, 3, time)

    def __buttonPress(self, widget, event):
        if event.type==gtk.gdk.BUTTON_PRESS and event.button==3:
            self._popupMenu(widget, event.get_time())
            return True
            
    def __selectionChanged(self, selection):
        model, iRow = selection.get_selected()
        if iRow!=None:
            if isinstance(model, gtkx.PythonTreeModel):
                obj = model.getObject(iRow)
            else:
                obj = model[iRow][1]
        else:
            obj = None
        self.actionGroup.updateActions(obj)

