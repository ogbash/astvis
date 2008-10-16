
from astvis import action, event
from astvis.model import concept
from wrapbox import Wrapbox

import gtk
import gaphas

gladeFile='astvisualizer.glade'

class NewDiagramDialog:
    def __init__(self, diagramTypes):
        wTree = gtk.glade.XML("astvisualizer.glade", 'newdiagram_dialog')
        wTree.signal_autoconnect(self)
        self.wTree = wTree
        self.widget = wTree.get_widget('newdiagram_dialog')

        self.diagramTypeModel = gtk.ListStore(str)
        for t in diagramTypes:
            self.diagramTypeModel.append((t,))
            
        self.diagramTypeBox = wTree.get_widget('diagram_type')
        cell = gtk.CellRendererText()
        self.diagramTypeBox.pack_start(cell, True)
        self.diagramTypeBox.add_attribute(cell, 'text', 0)  
        self.diagramTypeBox.set_model(self.diagramTypeModel)
        self.diagramTypeBox.set_active(0)
        
        self.diagramNameEntry = wTree.get_widget('diagram_name')


    def run(self):
        res = self.widget.run()
        if res > 0:
            type_ = self.diagramTypeBox.get_active_text()
            name = self.diagramNameEntry.get_text()
            self.diagramType = type_
            self.diagramName = name
            
        self.widget.destroy()            
        return res
        

class DiagramItemToolbox(object):

    def __init__(self, wTree, root):
        self.wTree = wTree
        self.root = root
        self.widget = Wrapbox()
        self.wTree.signal_autoconnect(self)

        action.manager.registerActionService(self)        
        self.actionGroup = action.manager.createActionGroup('toolbox', context=self, radioPrefix='toolbox-item')
        for action_ in self.actionGroup.radioActions:
            if not action_.name.startswith('toolbox-item'):
                continue
            button = gtk.ToggleToolButton()
            gtkaction = self.actionGroup.gtkactions[action_.name]
            gtkaction.connect_proxy(button)
            self.widget.add(button)
            
        #action.connectWidgetTree(self.actionGroup, self.wTree)

    @action.Action('toolbox-item-pointer', 'pointer', icon='pointer')
    def item_pointer(self, target, context):
        diagram = self.root.getDiagram()
        view = self.root.views[diagram]
            
        view.tool = gaphas.tool.DefaultTool()


    @action.Action('toolbox-item-flow', 'flow', icon='flow')
    def item_flow(self, target, context):
        diagram = self.root.getDiagram()
        view = self.root.views[diagram]
        def add():
            obj=concept.Flow()
            diagram.add(obj)
            return diagram.getItem(obj)
            
        view.tool = gaphas.tool.PlacementTool(add, gaphas.tool.HandleTool(), 0)

    @action.Action('toolbox-item-use', 'use', icon='use')
    def item_use(self, target, context):
        diagram = self.root.getDiagram()
        view = self.root.views[diagram]
        def add():
            obj=concept.Use()
            diagram.add(obj)
            return diagram.getItem(obj)
            
        view.tool = gaphas.tool.PlacementTool(add, gaphas.tool.HandleTool(), 0)
