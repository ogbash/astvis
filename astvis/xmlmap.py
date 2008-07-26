#! /usr/bin/env python

import logging
LOG = logging.getLogger("xmlmap")
from common import FINE, FINER, FINEST

import xml.sax
import operator
import event
import os.path
from copy import deepcopy, copy

__all__ = ('XMLLoader','XMLTag')

class XMLTag(object):
    "Helper class to define how xml tags are mapped to python objects."
    def __init__(self, name=None, attrs={}, priority=1):
        self.name = name
        self.attrs = dict(attrs)
        self.priority = priority

    def __lt__(self, tag):
        "Tag is more narrow (smaller) if it has the same name and attributes as another tag but can have more of its own attributes."
        if tag.name!=None and self.name!=tag.name:
            return False
        for attrName, attrValue in tag.attrs.items():
            if not self.attrs.has_key(attrName) or self.attrs[attrName]!=attrValue:
                return False
        return True

    def __eq__(self, tag):
        return self.name==tag.name and self.attrs==tag.attrs
        
    def __str__(self):
        return "XMLTag{name=%s,attrs=%s}" % (self.name, self.attrs)

    def __repr__(self):
        return "XMLTag{name=%s,attrs=%s}" % (self.name, self.attrs)

    def __iadd__(self, tag):
        if tag is None:
            return self
        if self.name==None:
            self.name = tag.name
        if self.priority>=tag.priority:
            attrs = dict(tag.attrs)
            attrs.update(self.attrs)
        else:
            attrs = dict(self.attrs)
            attrs.update(tag.attrs)
            
        self.attrs = attrs

        return self
        
class XMLAttribute(object):
    "Helper class to mapping of XML attributes to object properties"
    def __init__(self, name, special=False):
        self.name = name
        self.special = special

class PythonObject(object):
    def __init__(self, klass=None, ref=None, priority=1):
        self.klass = klass
        self.ref = ref
        self.priority = priority

    def __iadd__(self, other):
        if other is None:
            return self
        
        if self.klass==None or \
               other.klass!=None and self.priority<other.priority:
            self.klass = other.klass
        
        if not self.ref or \
               other.ref and self.priority<other.priority:
            self.ref = other.ref
            
        return self

    def __str__(self):
        return "PythonObject{klass=%s,ref=%s}" % (self.klass, self.ref)

    def __repr__(self):
        return "PythonObject{klass=%s,ref=%s}" % (self.klass, self.ref)

# Chain

class Link:
    def __init__(self, xml=None, obj=None):
        self.xml = xml
        self.obj = obj

    def __iadd__(self, link):            
        if self.xml is None:
            self.xml = link.xml
        else:
            self.xml += link.xml
                
        if self.obj is None:
            self.obj = link.obj
        else:
            self.obj += link.obj
        return self
        
    def __str__(self):
        return "Link(%s,%s)" % (self.xml, self.obj)

    def __repr__(self):
        return "Link(%s,%s)" % (self.xml, self.obj)

class Chain(list):
    def __init__(self, *args, **kvargs):
        if kvargs.has_key('priority'):
            self.priority = kvargs['priority']
            del kvargs['priority']
        else:
            self.priority = 1
        list.__init__(self,*args,**kvargs)

    def __iadd__(self, chain):
        
        for i in xrange(len(chain)):    
            if i>=len(self):
                # just add the rest
                rest = chain[:len(chain)-i]
                self[0:0] = deepcopy(rest)
                break
            
            # add objects
            iSelf = len(self)-i-1
            link = Link()
            if self.priority >= chain.priority:
                link += self[iSelf]
                link += chain[len(chain)-i-1]
            else:
                link += chain[len(chain)-i-1]
                link += self[iSelf]
                
            self[iSelf] = link                

        return self

    def __getslice__(self, i, j):
        item = list.__getslice__(self, i, j)
        return Chain(item, priority=self.priority)

    def __str__(self):
        return "Chain%s"%list.__str__(self)

# Adapters

classAdapters = {} #: class -> adapter

class Adapter:
    def createObject(self, klass, tag, model):
        "Get object from XML tag"
        return klass()

    def addChild(self, parent, child, pythonObject):
        "Add child object to parent object"
        pass


class ValueAdapter(Adapter):
    def createObject(self, klass, tag, value):
        "Get object from XML tag"
        if klass is None:
            klass = str
        if value is not None:
            return klass(value)
        else:
            return klass()

    def addChild(self, parent, child, pythonObject):
        "Add child object to parent object"
        pass
valueAdapter = ValueAdapter()

# getAdapter
def getAdapter(klass):
    if klass in (None, int, float, str):
        return valueAdapter
    return classAdapters.get(klass)

class ObjectAdapter(Adapter):
    "Maps python objects into XML and back."
    
    def __init__(self, klass):
        self.klass = klass
        self._attributes = []
        
        for xmlObject, pythonObject in klass._xmlAttributes:
            self._attributes.append((xmlObject, pythonObject))
            
    def createObject(self, klass, tag, model):
        obj = klass(model)
        
        for xmlAttribute, pythonObject in self._attributes:
            adapter = getAdapter(pythonObject.klass)
            
            if not xmlAttribute.special:
                if tag.attrs.has_key(xmlAttribute.name):
                    value = adapter.createObject(pythonObject.klass, xmlAttribute, tag.attrs[xmlAttribute.name])
                    setattr(obj, pythonObject.ref, value)
            else:
                if xmlAttribute.name=='tag':                    
                    setattr(obj, pythonObject.ref, tag.name)
                else:
                    LOG.waring("Unknown special attribute %s", xmlAttribute.name)
        return obj

    def addChild(self, parent, child, pythonObject):
        "Add child to parent, where pythonObject is child descr."
        if not pythonObject.ref:
            if LOG.isEnabledFor(FINER):
                LOG.log(FINER, "No reference for %s in %s: pythonObject=%s", child, parent, pythonObject)
            return
        setattr(parent, pythonObject.ref, child)

class ListAdapter(Adapter):
    def __init__(self):
        self.klass = list
    
    def addChild(self, parent, child, ref):
        parent.append(child)        
classAdapters[list] = ListAdapter()


def _tagMatches(xmlObject, tag):
    "If tag (from file) matches xmlObject (from a chain)"
    return isinstance(xmlObject, XMLTag) and \
           tag<xmlObject

class _XMLBasic:

    def __init__(self, classes):
        self.classes = classes
        self._chains = []
        for klass in classes:
            if not classAdapters.has_key(klass):
                self._scanClass(klass)
                classAdapters[klass] = ObjectAdapter(klass)

        LOG.debug("Number of chains: %d", len(self._chains))

    def _scanClass(self, klass):
        for tag in klass._xmlTags:
            chain = Chain([Link(tag, PythonObject(klass))], priority=tag.priority)
            self._chains.append(chain)
        
        for chain in klass._xmlChildren:
            for tag in klass._xmlTags:
                chainWithParent = Chain([Link(tag, PythonObject(klass))])
                chainWithParent.extend(map(lambda e: Link(*e), chain))
                self._chains.append(chainWithParent)

class XMLLoader(_XMLBasic, xml.sax.handler.ContentHandler):
    def __init__(self, model, classes, path="/"):
        _XMLBasic.__init__(self, classes)
        
        self.model = model
        self._elements = [] #: [(tagname, attrs, obj, adapter)]
        self.objects = [] #: top level objects to return
        self.callback = None
        self.rootPathList = self._parsePath(path) #: holds XML path of the root element
        LOG.debug("rootPathList = %s" % self.rootPathList)
            
        # add tag chain map (for faster access)
        self._rootTags = {}
        for chain in self._chains:
            xmlObject, pythonObject = chain[0].xml, chain[0].obj
            if not isinstance(xmlObject, XMLTag):
                continue
            if not self._rootTags.has_key(xmlObject.name):
                self._rootTags[xmlObject.name]=[]
            self._rootTags[xmlObject.name].append(chain)

        LOG.log(FINE, "Lengths of chains: %s",
                map(lambda e: (e[0],len(e[1])), self._rootTags.items()))

        self._matchedChains = []
        self._matchedChain = []
        self._matchedChainIndices = [0]

    def loadFile(self, filename):
        LOG.debug("loadFile started")
        self._file = open(filename, "r")
        import os
        stat = os.fstat(self._file.fileno())
        self._fileSize = stat.st_size
        self._fileProgress = 0.
        try:
            LOG.debug("File %s opened" % self._file)
            event.manager.notifyObservers(self, event.TASK_STARTED, \
                    ('Loading AST %s' % os.path.basename(filename),))
            #import cProfile
            #xmlTree =cProfile.run(xml.sax.parse(self._file, self))
            xmlTree = xml.sax.parse(self._file, self)
        finally:
            self._file.close()
            LOG.debug("File %s closed" % self._file)
            event.manager.notifyObservers(self, event.TASK_ENDED, None)
        return self.objects
        
    def _parsePath(self, path):
        pathList = path.split("/")
        if len(pathList)>1 and not pathList[-1]:
            del pathList[-1] # remove empty element in case there was trailing /
        if len(pathList)>1 and not pathList[0]:
            del pathList[0] # remove empty element in case there was root /
        return pathList


    def startElement(self, name, attrs):
        if LOG.isEnabledFor(FINER):
            LOG.log(FINER, "Processing tag '%s'", name)
        newMatchedChains = []
        tag = XMLTag(name, attrs)
        # find matched chains from the root
        chains = self._rootTags.get(name, [])
        for chain in chains:
            newMatchedChains.append((chain, 0))

        if len(self._matchedChains) > 0:
            newMatchedChains.extend(self._matchedChains[-1])
      
        # create new python object
        stillMatchedChains, newExtChain = self._extractCompletedChains(newMatchedChains, tag)

        self._matchedChain.extend(newExtChain)
        self._matchedChainIndices.append(len(self._matchedChain))

        obj = self._extractObject(tag, self.model)
        if obj!=None and self._isAtRoot():
            LOG.log(FINER, "Root object found: %s", obj)
            self.objects.append(obj)

        # new values
        self._elements.append((tag,obj))
        self._matchedChains.append(stillMatchedChains)

        # notify about progress
        newProgress = float(self._file.tell())
        if newProgress - self._fileProgress > 0.05:
            event.manager.notifyObservers(self, event.TASK_PROGRESSED, (newProgress/self._fileSize,))
            self._fileProgress = newProgress


    def _matchTagInChain(self, chain, index, tag):
        """Returns the index of the next matching tag in the chain
        starting from the given index"""
        # find next tag to match
        while index<len(chain) and chain[index].xml is None:
            index = index+1

        # if the tag matches
        if index<len(chain):
            xmlObject, pythonObject = chain[index].xml, chain[index].obj
            if _tagMatches(xmlObject, tag):
                return index

        return None


    def _extractCompletedChains(self, ichains, tag):
        """Finds new link(s) that match the given tag
        from the chain continuations."""
        newiChains = []
        matchedChains = []

        # find chains that match
        newChain = Chain()
        for ichain in ichains:
            chain, index = ichain
            mIndex = self._matchTagInChain(chain, index, tag)
            if mIndex is not None:
                newChain += chain[index:mIndex+1]

                # sort chains
                if len(chain)==mIndex: # end of chain
                    matchedChains.append(chain)
                else:
                    newiChains.append((chain,mIndex+1))

        return newiChains, newChain

    def _extractObject(self, tag, content):
        """Extract object from the last matching link group."""
        
        matchedChain = self._matchedChain
        startIndex, endIndex = self._matchedChainIndices[-2:]
        if endIndex-startIndex==0:
            if LOG.isEnabledFor(FINER):
                LOG.log(FINER, "Can't extract object, last matching tag group is empty")
            return None

        matchedTag = matchedChain[-1].xml
        if not tag<matchedTag:
            if LOG.isEnabledFor(FINER):
                LOG.log(FINER, "Can't extract object, given %s does not correspond to the matched %s", tag, matchedTag)
            return None

        if LOG.isEnabledFor(FINER):
            LOG.log(FINER, "Extracting object for %s, indices %d, %d", tag, startIndex, endIndex)
        
        if matchedChain[-1].obj is None:
            LOG.log(FINER, "No python object defined for class %s in chain %s", tag.name, matchedChain)
            return None
        
        klass = matchedChain[-1].obj.klass
        if klass:
            adapter = getAdapter(klass)
            obj = adapter.createObject(klass, tag, content)
            # add to parent
            self._addToParent(obj, matchedChain)
        else:
            if LOG.isEnabledFor(FINER):
                LOG.log(FINER, "No class defined for %s", matchedChain[-1])
            obj = None
        return obj

    def _addToParent(self, child, chain):
        # find the most recent object with tag

        index=len(self._elements)-1
        while(index>0):
            start, end = self._matchedChainIndices[index:index+2]
            if end-start>0:
                tag = chain[end-1].xml
                if tag is not None:
                    if self._elements[index][1]!=None:
                        break
            index = index-1
        else:
            if LOG.isEnabledFor(FINEST):
                LOG.log(FINEST, "Most recent parent not found")
            return

        parent = self._elements[index][1]
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "Most recent parent is %s", parent)
        
        # move forward and ask for subobjects (to find direct parent)
        directParent = parent
        for i in xrange(end-1, len(chain)-2):
            tag, obj = chain[i+1].xml, chain[i+1].obj
            if obj is None:
                continue
            directParent = getattr(directParent, obj.ref)

        # add child to parent
        if directParent is None:
            if LOG.isEnabledFor(FINER):
                LOG.log(FINER, "No parent found for %s", child)
            return
        
        adapter = getAdapter(directParent.__class__)
        childTag, childObject = chain[-1].xml, chain[-1].obj

        if LOG.isEnabledFor(FINER):
            LOG.log(FINER, "Subobject for %s found: %s applied with %s", directParent, child, childObject)
        adapter.addChild(directParent, child, childObject)

        # quick hack for parent
        if hasattr(child, 'parent'):
            child.parent = parent
        

    def _isAtRoot(self):
        pathList = [e[0].name for e in self._elements]
        if len(pathList)==len(self.rootPathList) and \
               pathList==self.rootPathList:
            return True
        return False

    def endElement(self, name):
        del self._matchedChains[-1]
        del self._elements[-1]
        startIndex, endIndex = self._matchedChainIndices[-2:]
        del self._matchedChain[startIndex:]
        del self._matchedChainIndices[-1]

    def characters(self, content):
        content=content.strip()
        if not content:
            return

        tag = XMLTag('__content__')

        if len(self._matchedChains) == 0:
            return
        
        stillMatchedChains, newExtChain = self._extractCompletedChains(self._matchedChains[-1], tag)
                    
        # create new python object
        self._matchedChain.extend(newExtChain)
        self._matchedChainIndices.append(len(self._matchedChain))

        obj = self._extractObject(tag, content)
        if obj!=None and LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "Found tag content '%s'", content[:40])

        startIndex, endIndex = self._matchedChainIndices[-2:]
        del self._matchedChain[startIndex:]
        del self._matchedChainIndices[-1]
        

from xml.sax.xmlreader import AttributesImpl as Attrs
class XMLWriter(_XMLBasic):
    def __init__(self, classes, objects):
        _XMLBasic.__init__(self, classes)
        
        self.objects = objects
        self._rootClasses = {}

        for chain in self._chains:
            if chain[0].obj==None:
                LOG.warn("No python object defined for chain: %s", chain)
                continue
            obj = chain[0].obj
            if obj.klass==None:
                LOG.warn("No objec class defined for chain: %s", chain)
                continue
            if not obj.klass in self._rootClasses:
                self._rootClasses[obj.klass] = []
            self._rootClasses[obj.klass].append(chain)

    def saveFile(self, filename):
        self._file = open(filename, 'w')
        try:
            import xml.sax.saxutils
            self._gen=xml.sax.saxutils.XMLGenerator(self._file, 'utf-8')
            self._gen.startDocument()
            self._gen.startElement('ASTCollection', Attrs({}))
            
            for obj in self.objects:
                self.processObject(obj)
                
            self._gen.endElement('ASTCollection')
            self._gen.endDocument()
        finally:
            self._file.close()

    def processObject(self, obj, ref=None):
        
        
        name = 'class'
        content = str(obj.__class__)
        self._gen.startElement(name, Attrs({}))
        self._gen.characters(content)
        self._gen.endElement(name)

        

