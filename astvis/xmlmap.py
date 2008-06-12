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
        attrs = dict(tag.attrs)
        attrs.update(self.attrs)
        self.attrs = attrs

        return self
        
class XMLAttribute(object):
    "Helper class to mapping of XML attributes to object properties"
    def __init__(self, name, special=False):
        self.name = name
        self.special = special

class PythonObject(object):
    def __init__(self, klass=None, ref=None):
        self.klass = klass
        self.ref = ref

    def __iadd__(self, other):
        if other is None:
            return self
        if self.klass==None:
            self.klass = other.klass
        if not self.ref:
            self.ref = other.ref
        return self

    def __str__(self):
        return "PythonObject{klass=%s,ref=%s}" % (self.klass, self.ref)

    def __repr__(self):
        return "PythonObject{klass=%s,ref=%s}" % (self.klass, self.ref)

# Chain

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
            xmlO, pO = chain[len(chain)-i-1]
            iSelf = len(self)-i-1
            xmlOSelf, pOSelf = self[iSelf]
            
            if xmlOSelf is None: xmlOSelf = XMLTag()
            xmlOSelf += xmlO
                
            if pOSelf is None: pOSelf = PythonObject()
            pOSelf += pO
                
            self[iSelf] = (xmlOSelf, pOSelf)

        return self

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
            return str(value)
        return klass(value)

    def addChild(self, parent, child, pythonObject):
        "Add child object to parent object"
        pass
valueAdapter = ValueAdapter()

# getAdapter
def getAdapter(klass):
    if klass in (None, int, float):
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
            LOG.warn("No reference for %s to setattr to parent %s", child, parent)
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

class XMLLoader(xml.sax.handler.ContentHandler):
    def __init__(self, model, classes, path="/"):
        self.model = model
        self.classes = classes
        self._elements = [] #: [(tagname, attrs, obj, adapter)]
        self.objects = [] #: top level objects to return
        self.callback = None
        self.rootPathList = self._parsePath(path) #: holds XML path of the root element
        LOG.debug("rootPathList = %s" % self.rootPathList)

        self._chains = []
        self._attributes = {} #: klass -> [(xmlO, pO)]
        for klass in classes:
            if not classAdapters.has_key(klass):
                self._scanClass(klass)
                classAdapters[klass] = ObjectAdapter(klass)
            
        # add tag chain map (for faster access)
        self._rootTags = {}
        for chain in self._chains:
            xmlObject, pythonObject = chain[0]
            if not isinstance(xmlObject, XMLTag):
                continue
            if not self._rootTags.has_key(xmlObject.name):
                self._rootTags[xmlObject.name]=[]
            self._rootTags[xmlObject.name].append(chain)

        self._matchedChains = []

    def _scanClass(self, klass):
        for tag in klass._xmlTags:
            chain = Chain([(tag, PythonObject(klass))], priority=tag.priority)
            self._chains.append(chain)
        
        for chain in klass._xmlChildren:
            for tag in klass._xmlTags:
                chainWithParent = Chain([(tag, None)])
                chainWithParent.extend(chain)
                self._chains.append(chainWithParent)

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
            xmlObject, pythonObject = chain[0]
            if _tagMatches(xmlObject, tag):
                newMatchedChains.append((chain, 1))
            
        # find chains that still match
        if len(self._matchedChains)>0:
            for ichain in self._matchedChains[-1]:
                chain, index = ichain
                while index<len(chain):
                    xmlObject, pythonObject = chain[index]
                    if _tagMatches(xmlObject, tag):
                        newMatchedChains.append((chain, index+1))
                        break
                    index=index+1
                
        # create new python object
        obj, newMatchedChains = self._extractObject(newMatchedChains, tag)
        if obj!=None and self._isAtRoot():
            LOG.log(FINER, "Root object found: %s", obj)
            self.objects.append(obj)

        # new values
        self._matchedChains.append(newMatchedChains)
        self._elements.append((name,attrs,obj))

        # notify about progress
        newProgress = float(self._file.tell())
        if newProgress - self._fileProgress > 0.05:
            event.manager.notifyObservers(self, event.TASK_PROGRESSED, (newProgress/self._fileSize,))
            self._fileProgress = newProgress


    def _extractObject(self, ichains, tag):
        newiChains = []
        matchedChains = []

        for ichain in ichains:
            chain, index = ichain
            if len(chain)==index:
                matchedChains.append(chain)
            else:
                newiChains.append(ichain)

        if len(matchedChains)==0:
            return None, newiChains

        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "Matched chains: %s", matchedChains)

        # create object
        matchedChain = Chain(priority=0)

        for chain in matchedChains:
            matchedChain += chain

        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "Matched chain: %s", matchedChain)
        
        if matchedChain[-1][1] is None:
            LOG.debug("No class defined for class %s in chain %s", tag.name, matchedChain)
            return None, newiChains
        
        klass = matchedChain[-1][1].klass
        if klass:
            adapter = getAdapter(klass)
            obj = adapter.createObject(klass, tag, self.model)
            # add to parent
            self._addToParent(obj, matchedChain)
        else:
            obj = None
        return obj, newiChains

    def _addToParent(self, child, chain):
        # find the most recent object
        index=len(chain)-2
        eindex=len(self._elements)-1
        while(index>=0):
            tag = chain[index][0]
            if tag is not None:
                if self._elements[eindex][2]!=None:
                    break
                eindex = eindex-1 
            index = index-1

        parent = self._elements[eindex][2]
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "Most recent parent is %s", parent)
        
        # move forward and ask for subobjects (to find parent)
        for i in xrange(index, len(chain)-2):
            tag, obj = chain[i+1]
            if obj is None:
                continue
            parent = getattr(parent, obj.ref)

        # add child to parent
        if parent is None:
            if LOG.isEnabledFor(FINER):
                LOG.log(FINER, "No parent found for %s", child)
            return
        
        adapter = getAdapter(parent.__class__)
        childTag, childObject = chain[-1]

        if LOG.isEnabledFor(FINER):
            LOG.log(FINER, "Subobject for %s found: %s", parent, child)
        adapter.addChild(parent, child, childObject)
        

    def _isAtRoot(self):
        pathList = [e[0] for e in self._elements]
        if len(pathList)==len(self.rootPathList) and \
               pathList==self.rootPathList:
            return True
        return False


    def getClassForTag(self, tagName, attrs):
        tag = XMLTag(tagName, attrs)
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "Finding class for %s", tag)
        for clazz in self.classes:
            for templateTag in clazz._xmlTags:
                if LOG.isEnabledFor(FINEST):
                    LOG.log(FINEST, "Trying template tag %s>tag: %s", templateTag, templateTag>tag)
                if templateTag>tag: # if tag has all attributes required by template tag
                    LOG.log(FINER, "Found tag '%s'", templateTag)
                    return clazz
        else:
            return None

    def endElement(self, name):
        del self._matchedChains[-1]
        del self._elements[-1]

    def __endElement(self, name):
        del self.elements[-1]

    def characters(self, content):
        if not content.strip():
            return
    
    def _match(self, pathList):
        pathIndex = len(pathList)-1
        index = len(self.elements)-1
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, "_match: Testing, pathList=%s, self.elements=%s" % (pathList, self.elements))
        while index>=0 and pathIndex>=0:
            if pathList[pathIndex] != self.elements[index][0]: # i.e. element name
                if LOG.isEnabledFor(FINEST):
                    LOG.log(FINEST, "_match: False, %s != %s" % (pathList[pathIndex], self.elements[index][0]))
                break
            index = index-1
            pathIndex = pathIndex-1
        else:
            if pathIndex<0 or \
                    pathIndex==0 and not pathList[pathIndex] and index<0: # match up to the root
                return True
            else:
                if LOG.isEnabledFor(FINEST):
                    LOG.log(FINEST, "_match: False, pathIndex=%d, index=%d" % (pathIndex, index))
        return False

