#! /usr/bin/env python

import logging
LOG = logging.getLogger("xmlmap")
from common import FINE, FINER, FINEST

import xml.sax
import operator
import event
import os.path

__all__ = ('XMLLoader','XMLTag')

def getAdapter(klass):
    if isinstance(klass, list):
        return ListAdapter
    return ObjectAdapter

class Adapter:
    @staticmethod
    def getClassForChild(parent, tagName, tagAttrs):
        "Identify class for the XML tag"
        pass

    @staticmethod
    def getObject(klass, tagName, attrs, model):
        "Get object from XML tag"
        pass

    @staticmethod
    def addChild(parent, child, pythonObject):
        "Add child object to parent object"
        pass

class XMLTag(object):
    "Helper class to define how xml tags are mapped to python objects."
    def __init__(self, name, attrs={}):
        self.name = name
        self.attrs = attrs

    def __lt__(self, tag):
        "Tag is more narrow (smaller) if it has the same name and attributes as another tag but can have more of its own attributes."
        if self.name!=tag.name:
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
        
class XMLAttribute(object):
    "Helper class to mapping of XML attributes to object properties"
    def __init__(self, name):
        self.name = name

class PythonObject(object):
    def __init__(self, klass=None, ref=None):
        self.klass = klass
        self.ref = ref

    def __str__(self):
        return "PythonObject{klass=%s,ref=%s}" % (self.klass, self.ref)

    def __repr__(self):
        return "PythonObject{klass=%s,ref=%s}" % (self.klass, self.ref)

#
class ObjectAdapter(Adapter):
    "Maps python objects into XML and back."

    klassAttributeMap = {} #: class -> (attrName -> attribute)

    @staticmethod
    def getObject(klass, tagName, attrs, model): # TODO: get rid of model
        obj = klass(model)
        
        # if not available, setup attribute map
        if not ObjectAdapter.klassAttributeMap.has_key(klass):
            klassAttributes = {} # attrName -> attribute
            for attr,prop in klass._xmlAttributes:
                klassAttributes[attr.name] = attr, prop
            ObjectAdapter.klassAttributeMap[klass] = klassAttributes

        # set properties from tag attributes
        klassAttributes = ObjectAdapter.klassAttributeMap[klass]
        for attrName, attrValue in attrs.items():
            if klassAttributes.has_key(attrName):
                attr, prop = klassAttributes[attrName]
                propertyName = prop.name
                if prop.klass!=None:
                    attrValue = prop.klass(attrValue)
                if LOG.isEnabledFor(FINER):
                    LOG.log(FINER, "Setting property '%s' to attr value %s" % (propertyName, attrValue))
                # set property
                setattr(obj, propertyName, attrValue)
                
        return obj

    @staticmethod
    def getClassForChild(parent, tagName, tagAttrs):
        childTag = XMLTag(tagName, tagAttrs)
        children = parent._xmlChildren
        for tag,prop in children:
            if childTag<tag: # satisfies name and all attr conditions
                return prop.klass

    @staticmethod
    def addChild(parent, child, pythonObject):
        childTag = XMLTag(tagName, tagAttrs)
        children = parent._xmlChildren
        for tag,prop in children:
            if childTag<tag: # satisfies name and all attr conditions
                setattr(parent, prop.name, child)
                break
        else:
            LOG.warn('No property found for the %s in %s', child, parent)
        

class ListAdapter(Adapter):
    @staticmethod
    def addChild(parent, child, ref):
        parent.append(child)

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
            self._scanClass(klass)
            
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
            chain = [(tag, PythonObject(klass))]
            self._chains.append(chain)

        for xmlObject, pythonObject in klass._xmlAttributes:
            if not self._attributes.has_key(klass):
                self._attributes[klass] = []
            self._attributes[klass].append((xmlObject, pythonObject))
        
        for chain in klass._xmlChildren:
            chainWithParent = [(tag, None)]
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
        newMatchedChains = []
        tag = XMLTag(name, attrs)
        # find matched chains from the root
        chains = self._rootTags.get(name, [])
        for chain in chains:
            xmlObject, pythonObject = chain[0]
            if isinstance(xmlObject, XMLTag) and tag<xmlObject:
                newMatchedChains.append((chain, 1))
            
        # find chains that still match
        if len(self._matchedChains)>0:
            for ichain in self._matchedChains[-1]:
                chain, index = ichain
                while index<len(chain):
                    xmlObject, pythonObject = chain[index]
                    if xmlObject!=None and xmlObject.name==name:
                        newMatchedChains.append((chain, index+1))
                        break
                    index=index+1
                
        # create new python object
        obj, newMatchedChains = self._extractObject(newMatchedChains, name, attrs)
        if obj!=None and self._isAtRoot():
            LOG.log(FINER, "Root object found: %s", obj)
            self.objects.append(obj)

        # new values
        self._matchedChains.append(newMatchedChains)
        self._elements.append((name,attrs,obj))


    def _extractObject(self, ichains, name, attrs):
        newiChains = []
        matchedChains = []
        
        for ichain in ichains:
            chain, index = ichain
            if len(chain)==index: # tag match
                matchedChains.append(chain)
            else:
                newiChains.append(ichain)

        # create object
        klass = None
        tag = None

        for chain in matchedChains:
            xmlObject, pythonObject = chain[-1]
            if pythonObject:
                if tag is None:
                    tag = xmlObject
                    klass = pythonObject.klass
                    matchedChain = chain
                else:
                    # pick more specific tag (with more attributes defined)
                    if xmlObject<tag:
                        tag = xmlObject
                        klass = pythonObject.klass
                        matchedChain = chain            

        if klass:
            obj = klass(self.model)
            self._extractAttributes(obj, attrs)
            # add to parent
            for chain in matchedChains:
                if len(chain)>1: # simplified parent search for now, generally should combine the chains
                    self._addToParent(obj, chain)
                    break 
        else:
            obj = None
        return obj, newiChains

    def _addToParent(self, child, chain):
        # find the most recent object
        index=len(chain)-2
        eindex=len(self._elements)-2
        while(index>=0):
            tag = chain[index][0]
            if tag is not None:
                break
            index = index-1
            eindex = eindex-1

        parent = self._elements[eindex][2]
        
        # move forward and ask for subobjects (to find parent)
        for i in xrange(index, len(chain)-2):
            tag, obj = chain[i+1]
            parent = getattr(parent, obj.ref)

        # add child to parent
        adapter = getAdapter(parent)
        childTag, childObject = chain[-1]
        adapter.addChild(parent, child, childObject)

    def _extractAttributes(self, obj, attrs):
        attrMap = self._attributes.get(obj.__class__, [])
        for xmlAttribute, pythonObject in attrMap:
            if attrs.has_key(xmlAttribute.name):
                setattr(obj, pythonObject.ref, attrs[xmlAttribute.name])
        
    def __startElement(self, name, attrs):
        # get class from parent
        parent = None
        parentAdapter = None
        if self.elements:
            parent = self.elements[-1][2]
            parentAdapter = self.elements[-1][3]

        if parentAdapter!=None:
            klass1 = parentAdapter.getClassForChild(parent, name, attrs)
        else:
            klass1 = None

        # get class by tag
        klass2 = self.getClassForTag(name, attrs)

        # classes conflict?
        if klass1 and klass2 and klass1 is not klass2:
            raise Exception("Parent and tag name define different classes: %s and %s" % (klass1, klass2))
        klass = klass1 or klass2

        # create object
        if klass is not None:
            # get adapter by class and object from adapter
            if LOG.isEnabledFor(FINEST):
                LOG.log(FINEST, 'Found class %s for tag %s', klass, name)
            adapter = getAdapter(klass)
            obj = adapter.getObject(klass, name, attrs, self.model)
        else:
            adapter = None
            obj = None
        
        # add object to parent
        if parentAdapter!=None:
            parentAdapter.addChild(parent, name, attrs, obj)
        elif self.elements:
            LOG.warn('No adapter for parent %s', parent)

        # add to root objects if path is as required for the root
            
        pass # isAtRoot
        
        if LOG.isEnabledFor(FINEST):
            LOG.log(FINEST, 'Adding to elements: %s', (name, attrs, obj, adapter))
        self.elements.append((name, attrs, obj, adapter))

        # notify about progress
        newProgress = float(self._file.tell())
        if newProgress - self._fileProgress > 0.05:
            event.manager.notifyObservers(self, event.TASK_PROGRESSED, (newProgress/self._fileSize,))
            self._fileProgress = newProgress

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

