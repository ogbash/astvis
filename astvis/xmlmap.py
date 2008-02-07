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
        pass

    @staticmethod
    def getObject(tagName, attrs):
        pass

class XMLTag(object):
    "This is helper class to define how xml tags are mapped to python objects."
    def __init__(self, name, attrs={}):
        self.name = name
        self.attrs = attrs

    def __lt__(self, tag):
        "Tag is more narrow if it has the same name and attributes as another tag but can add more of its own attributes."
        if self.name!=tag.name:
            return False
        for attrName, attrValue in tag.attrs.iteritems():
            if not self.attrs.has_key(attrName) or self.attrs[attrName]!=attrValue:
                return False
        return True

    def __eq__(self, tag):
        return self.name==tag.name and self.attrs==tag.attrs

class XMLLoader(xml.sax.handler.ContentHandler):
    def __init__(self, model, classes, path="/"):
        self.model = model
        self.classes = classes
        self.elements = [] #: [(tagname, attrs, obj, adapter)]
        self.objects = [] #: top level objects to return
        self.callback = None
        self.pathList = self._parsePath(path) #: holds XML path of the root element
        LOG.debug("pathList = %s" % self.pathList)
        
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
        return pathList
        
    def startElement(self, name, attrs):
        # get class from parent
        parent, parentAdapter = self.elements and self.elements[-1][2,3] or None,None
        if parentAdapter!=None:
            klass1 = parentAdapter.getClassForChild(parent, name, attrs)
        else:
            klass1 = None

        # get class by tag
        klass2 = self.getClassForTag(name, attrs)

        # classes conflict?
        if klass1 and klass2 and klass1 is not klass2:
            raise Exception("Parent and tag name define different classes: %s and %s", klass1, klass2)
        if not klass1 and not klass2:
            raise Exception("No class defined for tag name '%s'", name)
        klass = klass1 or klass2

        # get adapter by class and object from adapter
        adapter = getAdapter(klass)
        obj = adapter.getObject(name, attrs)

        for clazz in self.classes:
            if self._tagMatches(name, attrs, clazz._xmlTags):
                LOG.log(FINER, "Found tag '%s'" % name)
                obj = clazz(self.model)
                for propEval, attrName in clazz._xmlAttributes.iteritems():
                    if attrs.has_key(attrName):
                        if LOG.isEnabledFor(FINER):
                            LOG.log(FINER, "Setting property '%s' to attr value '%s'" % (propEval, attrs[attrName]))
                        self._setProperty(obj, propEval, attrs[attrName])                            
                    else:
                        if LOG.isEnabledFor(FINEST):
                            LOG.log(FINEST, "No tag attribute '%s' set" % attrName)
                            
                self._findAndSetParent(name, obj)
                if hasattr(obj, '_xmlPreProcess'):
                    obj._xmlPreProcess(name, attrs)
                break
        else:
            obj = None
        
        self.elements.append((name, attrs, obj))

        # notify about progress
        newProgress = float(self._file.tell())
        if newProgress - self._fileProgress > 0.05:
            event.manager.notifyObservers(self, event.TASK_PROGRESSED, (newProgress/self._fileSize,))
            self._fileProgress = newProgress

    def getClassForTag(tagName, attrs):
        pass

    def _tagMatches(self, name, attrs, _xmlTags):
        for tagName, attrPredicate in _xmlTags:
            if name==tagName:
                if not attrPredicate or attrPredicate(attrs):
                    return True
        else:
            return False

    def endElement(self, name):
        del self.elements[-1]

    def characters(self, content):
        if not content.strip():
            return
        
        (parentName, parentAttrs, parentObj), childName = self._findParent('__content__(%d chars)' % len(content))
        if parentObj!=None:
            if parentObj!=None and hasattr(parentObj.__class__, '_xmlContent'):
                parentObj.__class__._xmlContent(parentObj, childName, content)
                if LOG.isEnabledFor(FINE):
                    LOG.log(FINE, "Set content of %s" % parentObj)
    
    def _findAndSetParent(self, name, obj):
        # find where to add element
        if obj!=None and self._match(self.pathList):
            # top level
            if LOG.isEnabledFor(FINE):
                LOG.log(FINE, 'Added top level %s' % obj)
            self.objects.append(obj)
        elif obj!=None:
            # find "any" parent element that requires this element
            
            # first, find any non empty parent, set childName
            (parentName, parentAttrs, parentObj), childName = self._findParent(name)
                    
            if parentObj!=None:
                # iterate all "desired" properties of the parent, TODO can be made more effective
                for propEval, childNames in parentObj.__class__._xmlChildren.iteritems():
                    if LOG.isEnabledFor(FINEST):
                        LOG.log(FINEST, "Testing tagName '%s' in required childNames %s" %(childName, repr(childNames)))
                    # is it (child) tag name that parentObj requires?
                    if childName in childNames:
                        self._setProperty(parentObj, propEval, obj)
                        obj.parent = parentObj
                        break # parent found
                else:
                    if LOG.isEnabledFor(FINE):
                        LOG.log(FINE, "Ignore %s, because parent %s does no require it" %(obj, parentObj))
            else:
                if LOG.isEnabledFor(FINE):
                    LOG.log(FINE, "Ignore %s, because no parent %s" % (obj, parentName))

        if obj!=None and self.callback:
            self.callback(obj)
    

    def _findParent(self, childName):
        origChildName = childName
        
        parentIndex = len(self.elements)-1
        while parentIndex >= 0:
            parentName, parentAttrs, parentObj = self.elements[parentIndex]
            if parentObj!=None:
                if LOG.isEnabledFor(FINER):
                    LOG.log(FINER, "Found parent %s for '%s'" % (parentObj, origChildName))
                break
            childName = parentName
            parentIndex = parentIndex-1
        else:
            if LOG.isEnabledFor(FINER):
                LOG.log(FINER, "Not found parent for '%s'" % (origChildName))
        return (parentName, parentAttrs, parentObj), childName    

    def _setProperty(self, parentObj, propEval, obj):
        if isinstance(propEval, str):
            prop = getattr(parentObj, propEval)
            if isinstance(prop, list):
                # property is list, append to the end
                prop.append(obj)
                if LOG.isEnabledFor(FINE):
                    LOG.log(FINE, "Added child %s to %s" %(obj, parentObj))
            else:
                # set property
                setattr(parentObj, propEval, obj)
                if LOG.isEnabledFor(FINE):
                    LOG.log(FINE, "Set child %s to %s" %(obj, parentObj))
        else:
            # set property with parent specified function
            propEval(parentObj, obj)
            if LOG.isEnabledFor(FINE):
                LOG.log(FINE, "Set (with eval) child %s to %s" %(obj, parentObj))    

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

