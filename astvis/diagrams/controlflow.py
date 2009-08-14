
"Control flow diagram."

import logging
LOG=logging.getLogger('diagrams.controlflow')
from astvis.common import FINE, FINER, FINEST

from astvis.common import *
from astvis import diagram, action, core
from astvis.model import ast, flow
from astvis.gaphasx import RectangleItem, DiamondItem, MorphBoundaryPort, EllipseItem
from astvis import event
from astvis.event import REMOVED_FROM_DIAGRAM
from astvis.taggraph import TagGraph
from astvis.hgraph import HierarchicalGraph

import gtk
import pickle
import cairo
import gaphas
import gaphas.tool
from gaphas.connector import PointPort, VariablePoint

class ItemFactory(diagram.ItemFactory):
    def __init__(self, diagram):
        self.diagram = diagram
    
    def getDiagramItem(self, obj):
        if isinstance(obj, flow.StartBlock):
            return EntryExitItem(obj, self.diagram, 'start') 
        if isinstance(obj, flow.EndBlock):
            return EntryExitItem(obj, self.diagram, 'end')
        elif isinstance(obj, flow.ConditionBlock):
            return ConditionBlockItem(obj, self.diagram, obj.astObjects and str(obj.astObjects[-1]) or '')
        elif isinstance(obj, flow.DoHeaderBlock):
            return DoItem(obj, self.diagram, obj.astObjects and str(obj.astObjects[-1]) or '')            
        elif isinstance(obj, flow.Block):
            return GeneralBlockItem(obj, self.diagram, obj.astObjects and str(obj.astObjects[-1]) or '')

class BlockItem(object):
    def __init__(self, block, diagram):
        self.block = block
        self.diagram = diagram
        children = []
        if block.subBlocks:
            children.append(OpenItem(self))
        if block.parentBlock!=None:
            children.append(CloseItem(self))
        self.children = children

    def _drawTags(self, context):
        # write tags
        w = max((self.w+self.PADX*2), self.MIN_WIDTH)
        h = max((self.h+self.PADY*2), self.MIN_HEIGHT)
        cr = context.cairo
        cr.save()
        y = -h/2+10
        graph = self.diagram._tagGraph
        if graph._tags.has_key(self.block):
            names = map(lambda x: (x[0].name, x[1]) , graph._tags[self.block].keys())
            for name, op in names:
                cr.move_to(w/2,y)
                if op=='write':
                    cr.set_source_rgb(0.5,.0,0.)
                elif op=='read':
                    cr.set_source_rgb(0.,.5,0.)
                else:
                    cr.set_source_rgb(0.,0.,0.)                    
                cr.show_text(u"t(%s)" % name)
                y+=10
        if graph._inducedTags.has_key(self.block):
            names = map(lambda x: (x[0].name, x[1]), graph._inducedTags[self.block].keys())
            for name, op in names:
                cr.move_to(w/2,y)
                if op=='write':
                    cr.set_source_rgb(0.5,.0,0.)
                elif op=='read':
                    cr.set_source_rgb(0.,.5,0.)
                else:
                    cr.set_source_rgb(0.,0.,0.)                    
                cr.show_text(u"i(%s)" % name)
                y+=10
        cr.restore()

class BlockTagGraph(TagGraph):
    """TagGraph with blocks as vertices, parent blocks point to children
    blocks. """

    def __init__(self):
        TagGraph.__init__(self, self.getTargetBlocks, self.getSourceBlocks)
    
    def getSourceBlocks(self, block):
        if block.parentBlock != None:
            return set([block.parentBlock])
        else:
            return set()
        
    def getTargetBlocks(self, block):
        if block.subBlocks != None:
            return set(block.subBlocks)
        else:
            return set()

class BlockGraph(HierarchicalGraph):
    
    def _getParent(self, block):
        return block.parentBlock

    def _getChildren(self, block):
        return block.subBlocks
    
class ControlFlowDiagram (diagram.Diagram):
    UI_DESCRIPTION='''
    <popup name="controlflowdiagram-popup">
      <menuitem action="controlflowdiagram-open-ast"/>
      <menuitem action="controlflowdiagram-open-code"/>
      <menuitem action="controlflowdiagram-show-references"/>
      <menuitem action="controlflowdiagram-hide-references"/>
    </popup>
    '''

    @classmethod
    def getActionGroup(cls):
        if not hasattr(cls, 'ACTION_GROUP'):
            cls.ACTION_GROUP=action.ActionGroup(
                action.manager,
                'controlflowdiagram',
                contextClass=ControlFlowDiagram,
                contextAdapter=cls.getSelected,
                targetClasses = [BlockItem])
        return cls.ACTION_GROUP

    def __init__(self, name, project):
        diagram.Diagram.__init__(self, ItemFactory(self))
        self.project = project
        self.name = name
        self.flowModel = None
        self._connectTool = gaphas.tool.ConnectHandleTool()

        action.manager.registerActionService(self)        
        self.gtkActionGroup = self.getActionGroup().createGtkActionGroup(self)
        action.manager.addGtkGroup(self.gtkActionGroup)
        self.contextMenu = action.getMenu(self.gtkActionGroup, 'controlflowdiagram-popup')

        # tags
        self._referenceTags = set()
        self._tagGraph = BlockTagGraph()

        # register for events
        event.manager.subscribe(self._tagGraphChanged, self._tagGraph)

    def _tagGraphChanged(self, obj, ev, args, dargs):
        if ev==event.PROPERTY_CHANGED:
            name, evtype, newvalue, oldvalue = args
            if evtype==event.PC_ADDED and name in ('tags','inducedTags'):
                tag,block,target = newvalue
                blockItem = self.getItem(block)
                if blockItem:
                    self.view.canvas.request_update(blockItem)

            elif evtype==event.PC_REMOVED and name in ('tags','inducedTags'):
                tag,block,target = oldvalue
                blockItem = self.getItem(block)
                if blockItem:
                    self.view.canvas.request_update(blockItem)

    def setupView(self, view):
        super(ControlFlowDiagram, self).setupView(view)
        
        import weakref
        self.view = weakref.proxy(view)
        view.drag_dest_set(gtk.DEST_DEFAULT_MOTION|gtk.DEST_DEFAULT_DROP,
                [(INFO_OBJECT_PATH.name,0,INFO_OBJECT_PATH.number)],
                gtk.gdk.ACTION_COPY)
        view.connect("drag-data-received", self._dragDataRecv)

    def getSelected(self):
        if self.view==None:
            return
        item=self.view.hovered_item
        return item

    def _dragDataRecv(self, widget, context, x, y, data, info, timestamp):
        if self.flowModel != None:
            return
        
        LOG.debug("GTK DnD data_recv with info=%d"%info)
        if info==INFO_OBJECT_PATH.number:
            clazz, path = pickle.loads(data.data)
            if issubclass(clazz, ast.Code):
                # get canvas coordinates
                m = cairo.Matrix(*widget.matrix)
                m.invert()
                cx, cy = m.transform_point(x,y)
                # add item
                obj = self.project.astModel.getObjectByPath(path)
                cfservice = core.getService('ControlflowService')
                self.flowModel = cfservice.getModel(obj)
                self.astObjects = self.flowModel.collectASTObjects()
                LOG.debug("Number of AST objects in code is %d",
                          len(self.astObjects[self.flowModel.block]))
                
                connections = self.flowModel.getConnections()
                self._hgraph = BlockGraph(set([self.flowModel.block]), connections)
                self.processBlockGraphChanges((cx,cy))

                context.drop_finish(True, timestamp)
            else:
                context.drop_finish(False, timestamp)                
        else:
            context.drop_finish(False, timestamp)

    def getDefaultTool(self):
        tool = gaphas.tool.ToolChain()
        tool.append(gaphas.tool.HoverTool())
        tool.append(ContextMenuTool())
        tool.append(OpenCloseBlockTool())
        tool.append(gaphas.tool.PanTool())
        tool.append(gaphas.tool.ZoomTool())
        tool.append(gaphas.tool.ItemTool())
        tool.append(gaphas.tool.RubberbandTool())
        return tool

    def processBlockGraphChanges(self, point):
        x, y = point
        print '--'
        changes = self._hgraph.changes
        for action, obj in changes:
            print action, obj
            if isinstance(obj, flow.Block):
                if action=='ADDED':
                    self.add(obj, x, y)
                    y+=50
                elif action=='REMOVED':
                    self.remove(obj)

            elif isinstance(obj, tuple): # edge
                fromBlock, toBlock = obj
                if action=='ADDED':
                    self.addConnector((fromBlock, toBlock), ControlFlowConnector(fromBlock, toBlock, self))
                    y+=50
                elif action=='REMOVED':
                    self.removeConnector(obj)

        self._hgraph.changes = []

    def _connectItems(self, items, connectorItem):
        LOG.debug('connect %s', items)
        handles = connectorItem.handles()[-1], connectorItem.handles()[0] # tail --> head

        self._connectTool.connect_handle(connectorItem, handles[0], items[0], items[0].port)
        self._connectTool.connect_handle(connectorItem, handles[1], items[1], items[1].port)


    def selectBlocksByObject(self, astObj):
        selected = self.flowModel.findBlocksByObject(astObj, self._items.keys())
        self.view.unselect_all()
        
        for block in selected:
            self.view.select_item(self.getItem(block))

    @action.Action('controlflowdiagram-open-ast', label='Open AST', targetClass=BlockItem)
    def _openAST(self, target, context):
        # open item in AST tree
        ocItem = target
        if ocItem.block!=None:
            block=ocItem.block
            if block!=None and block.astObjects:
                astObj = block.astObjects[0]
                action.manager.activate('show-ast-object', astObj, None)

    @action.Action('controlflowdiagram-open-code', label='Open code', targetClass=BlockItem)
    def _openCode(self, target, context):
        # open item in AST tree
        ocItem = target
        if ocItem.block!=None:
            block=ocItem.block
            if block!=None and block.astObjects:
                astObj = block.astObjects[0]
                self.project.root.showFile(self.project, astObj.getFile(), astObj.location)


    def _getRefs(self):
        items = []
        if self.flowModel:
            astCode = self.flowModel.code
            basicModel = astCode.model.basicModel
            scope = basicModel.getObjectByASTObject(astCode)
            names = list(scope.variables.keys())
            names.sort()

            for name in names:
                sensitive = not name in self._referenceTags
                items.append((name, sensitive))
                
        return items

    @action.Action('controlflowdiagram-show-references', label='Show references',
                   getSubmenuItems=_getRefs)
    def showReferences(self, target, context):
        name = target
        service = core.getService('ReferenceResolver')
        astCode = self.flowModel.code
        basicModel = astCode.model.basicModel
        scope = basicModel.getObjectByASTObject(astCode)
        references = service.getReferringObjects(scope.variables[target])

        # for each reference
        for ref in references.get(astCode, []):
            # get the basic block that contain the reference statement
            blocks = self.flowModel.findBlocksByObject(ref)
            for block in blocks:
                isAssign = ref.isAssignment()
                op = isAssign is True and 'write' or isAssign is False and 'read' or 'unknown'
                self._tagGraph.addTag((scope.variables[name],op), block, ref)

        self._referenceTags.add(name)

    def _getShownRefs(self):
        items = []
        if self.flowModel:
            names = list(self._referenceTags)
            names.sort()

            for name in names:
                items.append((name, True))
                
        return items
    
    @action.Action('controlflowdiagram-hide-references', label='Hide references',
                   getSubmenuItems=_getShownRefs)
    def hideReferences(self, target, context):
        name = target
        service = core.getService('ReferenceResolver')
        astCode = self.flowModel.code
        basicModel = astCode.model.basicModel
        scope = basicModel.getObjectByASTObject(astCode)
        references = service.getReferringObjects(scope.variables[name])

        for ref in references.get(astCode, []):
            blocks = self.flowModel.findBlocksByObject(ref)
            for block in blocks:
                isAssign = ref.isAssignment()
                op = isAssign is True and 'write' or isAssign is False and 'read' or 'unknown'
                self._tagGraph.removeTag((scope.variables[name],op), block, ref)

        self._referenceTags.remove(name)

    @action.Action('controlflowdiagram-show-active', label='Show active', targetClass=BlockItem)
    def showActiveObjects(self, target, context):
        "Show active objects (used variables) in block."
        
        ocItem = target
        if ocItem.block!=None:
            block=ocItem.block
            service = core.getService('DataflowService')
            service.getActiveDefinitionsByBlock(block)

    @action.Action('controlflowdiagram-show-out', label='Show OUT', targetClass=BlockItem)
                   
    def showOutDefinitions(self, target, context):
        "Show definitions that reach the block output (in Reaching Definitions)."
        
        ocItem = target
        block = ocItem.block
        code = block.model.code
        diagram = context
        
        dfService = core.getService('DataflowService')
        ins, outs = dfService.getReachingDefinitions(code)

        blockGraph = diagram._hgraph
        outDefs = set()
        for edge in blockGraph.outEdges[block]:
            for fromBlock, toBlock in blockGraph.edges[edge]:
                outDefs.update(outs[fromBlock].keys())
        print outDefs


    @action.Action('controlflowdiagram-show-useddef', label='Used defs', targetClass=BlockItem,
                   sensitivePredicate=lambda t,c: isinstance(t.block, flow.BasicBlock))
    def showUsedDefinitions(self, target, context):
        "Show used (variable) definitions for the block (Use-Definition chain)."
        
        ocItem = target
        
        dfService = core.getService('DataflowService')
        usedDefs = dfService.getUsedDefinitions(ocItem.block)
        print usedDefs
        
class GeneralBlockItem(RectangleItem, BlockItem):

    MIN_WIDTH=30
    MIN_HEIGHT=30

    def __init__(self, block, diagram, text):
        RectangleItem.__init__(self, text)
        BlockItem.__init__(self, block, diagram)

        self.port = MorphBoundaryPort(VariablePoint((0.,0.)), self)
        self.port.connectable = False

    def draw(self, context):
        super(GeneralBlockItem, self).draw(context)
        cr = context.cairo
        w = max((self.w+self.PADX*2), self.MIN_WIDTH)
        h = max((self.h+self.PADY*2), self.MIN_HEIGHT)
        # write number of substatements
        cr.move_to(-w/2,-h/2+10)
        cr.show_text(u"%d" % (len(self.canvas.diagram.astObjects[self.block]), ))

        self._drawTags(context)

class ConditionBlockItem(DiamondItem, BlockItem):

    def __init__(self, block, diagram, text):
        DiamondItem.__init__(self, text)
        BlockItem.__init__(self, block, diagram)

        self.port = MorphBoundaryPort(VariablePoint((0.,0.)), self)
        self.port.connectable = False

    def draw(self, context):
        super(ConditionBlockItem, self).draw(context)
        
        self._drawTags(context)

class DoItem(EllipseItem, BlockItem):

    def __init__(self, block, diagram, text):
        EllipseItem.__init__(self, text)
        BlockItem.__init__(self, block, diagram)

        self.port = MorphBoundaryPort(VariablePoint((0.,0.)), self)
        self.port.connectable = False

class EntryExitItem(RectangleItem, BlockItem):

    def __init__(self, block, diagram, text):
        RectangleItem.__init__(self, text)
        BlockItem.__init__(self, block, diagram)

        self.port = MorphBoundaryPort(VariablePoint((0.,0.)), self)
        self.port.connectable = False

    def draw(self, context):
        super(EntryExitItem, self).draw(context)
        cr = context.cairo
        w = max((self.w+self.PADX*2), self.MIN_WIDTH)
        h = max((self.h+self.PADY*2), self.MIN_HEIGHT)
        cr.move_to(-w/2, h/4)
        cr.line_to(-w/4, h/2)
        cr.move_to(w/4, h/2)
        cr.line_to(w/2, h/4)
        cr.move_to(w/2, -h/4)
        cr.line_to(w/4, -h/2)
        cr.move_to(-w/4, -h/2)
        cr.line_to(-w/2, -h/4)
        cr.stroke()

class OpenItem(gaphas.item.Item):

    def __init__(self, openItem):
        gaphas.item.Item.__init__(self)
        self.item = openItem
    
    def draw(self, context):
        item = self.item
        cr = context.cairo
        w,h = max((item.w+item.PADX*2),item.MIN_WIDTH), \
              max((item.h+item.PADY*2),item.MIN_HEIGHT)
        x,y = -w/2, -h/2-10
        cr.move_to(x+5, y+1)
        cr.line_to(x+5, y+9)
        cr.stroke()
        cr.move_to(x+1, y+5)
        cr.line_to(x+9, y+5)
        cr.stroke()

class CloseItem(gaphas.item.Item):

    def __init__(self, closeItem):
        gaphas.item.Item.__init__(self)
        self.item = closeItem
    
    def draw(self, context):
        item = self.item
        cr = context.cairo
        w,h = max((item.w+item.PADX*2),item.MIN_WIDTH), \
              max((item.h+item.PADY*2),item.MIN_HEIGHT)
        x,y = -w/2+10, -h/2-10
        cr.move_to(x+1, y+5)
        cr.line_to(x+9, y+5)
        cr.stroke()

class OpenCloseBlockTool(gaphas.tool.Tool):

    def on_button_press(self, context, event):
        ocItem = context.view.hovered_item
        if isinstance(ocItem, OpenItem):
            diagram = ocItem.canvas.diagram
            matrix = ocItem.item.matrix
            x,y = matrix[4], matrix[5]
            diagram._hgraph.unfold(ocItem.item.block)
            diagram.processBlockGraphChanges((x,y))
            return True

        elif isinstance(ocItem, CloseItem):
            diagram = ocItem.canvas.diagram
            matrix = ocItem.item.matrix
            x,y = matrix[4], matrix[5]
            parentBlock = ocItem.item.block.parentBlock
            diagram._hgraph.fold(ocItem.item.block)
            diagram.processBlockGraphChanges((x,y))            
            return True

    def closeBlock(self, block, diagram):
        blockItem = diagram.getItem(block)
        if blockItem==None:
            # item is opened, close subBlocks
            for subBlock in block.subBlocks:
                self.closeBlock(subBlock, diagram)
                
        else:
            # item is not open, remove it
            diagram.remove(block)

class ContextMenuTool(gaphas.tool.Tool):
    def on_button_press(self, context, event):

        diagram = context.view.canvas.diagram

        if event.button==3:
            diagram.getActionGroup().updateActions(diagram.gtkActionGroup,
                                                   context.view.hovered_item)
            diagram.contextMenu.popup(None, None, None, event.button, event.time)
            return True


class ControlFlowConnector(diagram.Connector, event.Observer):

    def __init__(self, fromBlock, toBlock, diagram):
        self._fromBlock = fromBlock
        self._toBlock = toBlock
        self._diagram = diagram
        self._line = ControlFlowLine()
        self._line.handles()[0].connectable=False
        self._line.handles()[-1].connectable=False
        
    def setup_diagram(self):
        self._diagram._canvas.add(self._line)
        self._diagram._connectItems((self._diagram._items[self._fromBlock],
                                     self._diagram._items[self._toBlock]),
                                    self._line)
        
    def teardown_diagram(self):
        self._diagram._canvas.remove(self._line)        

class ControlFlowLine(gaphas.item.Line):
    def draw_head(self, context):
        super(ControlFlowLine, self).draw_head(context)
        cr = context.cairo
        cr.line_to(6,3)
        cr.move_to(6,-3)
        cr.line_to(0,0)

