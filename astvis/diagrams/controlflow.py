
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
        self.connections = set()

    def _drawTags(self, context):
        # write tags
        w = max((self.w+self.PADX*2), self.MIN_WIDTH)
        h = max((self.h+self.PADY*2), self.MIN_HEIGHT)
        cr = context.cairo
        cr.save()
        y = -h/2+10
        graph = self.diagram._tagGraph
        if graph._tags.has_key(self.block):
            names = map(lambda x: x.name, graph._tags[self.block].keys())
            for name in names:
                cr.move_to(w/2,y)
                cr.set_source_rgb(0.,.5,0.0)
                cr.show_text(u"t(%s)" % name)
                y+=10
        if graph._inducedTags.has_key(self.block):
            names = map(lambda x: x.name, graph._inducedTags[self.block].keys())
            for name in names:
                cr.move_to(w/2,y)
                cr.set_source_rgb(0.,.5,0.0)
                cr.show_text(u"i(%s)" % name)
                y+=10
        cr.restore()

class BlockTagGraph(TagGraph):

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
    
class ControlFlowDiagram (diagram.Diagram):
    UI_DESCRIPTION='''
    <popup name="controlflowdiagram-popup">
      <menuitem action="controlflowdiagram-open-ast"/>
      <menuitem action="controlflowdiagram-open-code"/>
      <menuitem action="controlflowdiagram-show-references"/>
      <menuitem action="controlflowdiagram-hide-references"/>
    </popup>
    '''

    def __init__(self, name, project):
        diagram.Diagram.__init__(self, ItemFactory(self))
        self.project = project
        self.name = name
        self.flowModel = None
        self._unboundConnections = set()
        self._connectTool = gaphas.tool.ConnectHandleTool()

        action.manager.registerActionService(self)        
        self.actionGroup = action.manager.createActionGroup('controlflowdiagram',
                context=self, contextAdapter=self.getSelected,
                targetClasses = [BlockItem])
        self.contextMenu = action.getMenu(self.actionGroup, 'controlflowdiagram-popup')

        # tags
        self._referenceTags = set()
        self._tagGraph = BlockTagGraph()

        # register for events
        event.manager.subscribe(self._tagGraphChanged, self._tagGraph)
        
        # TODO refactor into action
        def fillRefs(item):
            sub = item.get_submenu()
            sub.foreach(lambda c: sub.remove(c))
            if self.flowModel:
                astCode = self.flowModel.code
                basicModel = astCode.model.basicModel
                scope = basicModel.getObjectByASTObject(astCode)
                names = list(scope.variables.keys())
                names.sort()
                def showRef(menu, name):
                    service = core.getService('ReferenceResolver')
                    references = service.getReferringObjects(scope.variables[name])

                    for ref in references.get(astCode, []):
                        blocks = self.flowModel.findBlocksByObject(ref)
                        for block in blocks:
                            self._tagGraph.addTag(scope.variables[name], block, ref)
                            
                    self._referenceTags.add(name)
                    
                for name in names:
                    menu = gtk.MenuItem(name)
                    if name in self._referenceTags:
                        menu.set_sensitive(False)
                    else:
                        menu.connect('activate', showRef, name)
                    sub.append(menu)
                
            sub.show_all()
            
        menuAction = self.actionGroup.gtkactions['controlflowdiagram-show-references']
        menuItem = menuAction.get_proxies()[0]
        sm = gtk.Menu()
        menuItem.set_submenu(sm)
        menuItem.connect('activate', fillRefs)

        def fillHideRefs(item):
            sub = item.get_submenu()
            sub.foreach(lambda c: sub.remove(c))
            if self.flowModel:
                astCode = self.flowModel.code
                basicModel = astCode.model.basicModel
                scope = basicModel.getObjectByASTObject(astCode)
                names = list(self._referenceTags)
                names.sort()
                def hideRef(menu, name):
                    service = core.getService('ReferenceResolver')
                    references = service.getReferringObjects(scope.variables[name])

                    for ref in references.get(astCode, []):
                        blocks = self.flowModel.findBlocksByObject(ref)
                        for block in blocks:
                            self._tagGraph.removeTag(scope.variables[name], block, ref)
                            
                    self._referenceTags.remove(name)
                    
                for name in names:
                    menu = gtk.MenuItem(name)
                    menu.connect('activate', hideRef, name)
                    sub.append(menu)
                
            sub.show_all()
            
        menuAction = self.actionGroup.gtkactions['controlflowdiagram-hide-references']
        menuItem = menuAction.get_proxies()[0]
        sm = gtk.Menu()
        menuItem.set_submenu(sm)
        menuItem.connect('activate', fillHideRefs)

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
        import weakref
        self.view = weakref.proxy(view)
        view.drag_dest_set(gtk.DEST_DEFAULT_MOTION|gtk.DEST_DEFAULT_DROP,
                [(INFO_OBJECT_PATH.name,0,INFO_OBJECT_PATH.number)],
                gtk.gdk.ACTION_COPY)
        view.connect("drag-data-received", self._dragDataRecv)

    def getSelected(self, context):
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
                self.flowModel = flow.ControlFlowModel(obj)
                self.astObjects = self.flowModel.collectASTObjects()
                LOG.debug("Number of AST objects in code is %d",
                          len(self.astObjects[self.flowModel.block]))
                
                self.add(self.flowModel.block, cx,cy)
                self._unboundConnections = self.flowModel.getConnections()
                self.bindConnections()

                context.drop_finish(True, timestamp)
            else:
                context.drop_finish(False, timestamp)                
        else:
            context.drop_finish(False, timestamp)

    def bindConnections(self):
        clConnections = self.flowModel.classifyConnectionsBy(self._unboundConnections, self._items.keys())
        if LOG.isEnabledFor(FINER):
            LOG.log(FINER, "%d unbound connections, %d classified connections",
                    len(self._unboundConnections), len(clConnections))

        newUnboundConnections = set()
        for key in clConnections.keys():
            fromBlock, toBlock = key
            if fromBlock is toBlock:
                self._items[fromBlock].connections.update(clConnections[key])
                if LOG.isEnabledFor(FINEST):
                    LOG.log(FINEST, "Internal block connection: %s", fromBlock)
            elif fromBlock!=None and toBlock!=None:
                self.addConnector(ControlFlowConnector(fromBlock, toBlock, self, clConnections[key]))
            else:
                if LOG.isEnabledFor(FINEST):
                    LOG.log(FINEST, "Missing block(s) for the connection: %s, %s; basic connections: %s",
                            fromBlock,
                            toBlock,
                            map(lambda cs: (str(cs[0]), str(cs[1])), clConnections[key]))
                newUnboundConnections.update(clConnections[key])
                
        self._unboundConnections = newUnboundConnections

    def removeConnector(self, connector):
        res = super(ControlFlowDiagram, self).removeConnector(connector)
        if res:
            if LOG.isEnabledFor(FINEST):
                LOG.log(FINEST, "Updating unbound connections with %s", connector.connections)
            self._unboundConnections.update(connector.connections)

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

    def remove(self, obj):
        item = self.getItem(obj)
        res = super(ControlFlowDiagram, self).remove(obj)
        if res:
            self._unboundConnections.update(item.connections)
        return res


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

    @action.Action('controlflowdiagram-show-references', label='Show references')
    def showReferences(self, target, context):
        print '-- showReferences', target

    @action.Action('controlflowdiagram-hide-references', label='Hide references')
    def hideReferences(self, target, context):
        print '-- unshowReferences', target

        
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
            subBlocks = ocItem.item.block.subBlocks
            diagram.remove(ocItem.item.block)
            for subBlock in subBlocks:
                diagram.add(subBlock, x, y)
                y += 50
            diagram.bindConnections()
            return True

        elif isinstance(ocItem, CloseItem):
            diagram = ocItem.canvas.diagram
            matrix = ocItem.item.matrix
            x,y = matrix[4], matrix[5]
            parentBlock = ocItem.item.block.parentBlock
            self.closeBlock(parentBlock, diagram)

            diagram.add(parentBlock, x, y)
            diagram.bindConnections()
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
            diagram.actionGroup.updateActions(context.view.hovered_item)
            diagram.contextMenu.popup(None, None, None, event.button, event.time)
            return True


class ControlFlowConnector(diagram.Connector, event.Observer):

    def __init__(self, fromBlock, toBlock, diagram, connections):
        self._fromBlock = fromBlock
        self._toBlock = toBlock
        self._diagram = diagram
        self._line = ControlFlowLine()
        self._line.handles()[0].connectable=False
        self._line.handles()[-1].connectable=False
        self.connections = set(connections)
        event.manager.subscribe(self, self._toBlock)
        event.manager.subscribe(self, self._fromBlock)
        
    def setup_diagram(self):
        self._diagram._canvas.add(self._line)
        self._diagram._connectItems((self._diagram._items[self._fromBlock],
                                     self._diagram._items[self._toBlock]),
                                    self._line)
        
    def teardown_diagram(self):
        self._diagram._canvas.remove(self._line)        

    def notify(self, obj, event, args, dargs):
        if event==REMOVED_FROM_DIAGRAM:
            diagram, = args
            if not diagram==self._diagram or not obj in (self._toBlock, self._fromBlock):
                return
            self._diagram.removeConnector(self)

    def __setstate__(self, state):
        self.__dict__.update(state)
        event.manager.subscribe(self, self._toBlock)
        event.manager.subscribe(self, self._fromBlock)        

class ControlFlowLine(gaphas.item.Line):
    def draw_head(self, context):
        super(ControlFlowLine, self).draw_head(context)
        cr = context.cairo
        cr.line_to(6,3)
        cr.move_to(6,-3)
        cr.line_to(0,0)

