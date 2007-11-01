#! /usr/bin/env python

import logging
LOG = logging.getLogger("xmlmap")
from common import FINE, FINER, FINEST

import xml.sax
import operator

class XMLLoader(xml.sax.handler.ContentHandler):
    def __init__(self, project, classes, path="/"):
        self.project = project
        self.classes = classes
        self.elements = [] # (tagname, attrs, obj)
        self.objects = []
        self.callback = None
        self.pathList = self._parsePath(path)
        LOG.debug("pathList = %s" % self.pathList)
        
    def startElement(self, name, attrs):
        for clazz in self.classes:
            if name in clazz._xmlTags:
                obj = clazz(self.project)
                for propName in clazz._xmlAttributes.iterkeys():
                    attrName = clazz._xmlAttributes[propName]
                    if LOG.isEnabledFor(FINER):
                        LOG.log(FINER, "Setting property %s to attr value %s" % (propName, attrs[attrName]))
                    setattr(obj, propName, attrs[attrName])
                break
        else:
            obj = None
            
        if obj and self.callback:
            self.callback(obj)
        
        self.elements.append((name, attrs, obj))

    def endElement(self, name):
        name, attrs, obj = self.elements[-1]
        del self.elements[-1]
        if obj and self._match(self.pathList):
            if LOG.isEnabledFor(FINE):
                LOG.log(FINE, 'Added top level %s' % obj)
            self.objects.append(obj)
        elif obj:
            parentName, parentAttrs, parentObj = self.elements[-1]
            if parentObj:
                for propName, childNames in parentObj.__class__._xmlChildren.iteritems():
                    if LOG.isEnabledFor(FINEST):
                        LOG.log(FINEST, "Testing tagName '%s' in required childNames %s" %(name, childNames))
                    if name in childNames:
                        prop = getattr(parentObj, propName)
                        if isinstance(prop, list):
                            prop.append(obj)
                            if LOG.isEnabledFor(FINE):
                                LOG.log(FINE, "Added child %s to %s" %(obj, parentObj))
                        else:
                            setattr(parentObj, propName, obj)
                            if LOG.isEnabledFor(FINE):
                                LOG.log(FINE, "Set child %s to %s" %(obj, parentObj))
                            
                        obj.parent = parentObj

                        break
                else:
                    if LOG.isEnabledFor(FINE):
                        LOG.log(FINE, "Ignore %s, because parent %s does no require it" %(obj, parentObj))
            else:
                if LOG.isEnabledFor(FINE):
                    LOG.log(FINE, "Ignore %s, because no parent %s" % (obj, parentName))
        
    def loadFile(self, filename):
        f = open(filename, "r")
        try:
            xmlTree = xml.sax.parse(f, self)
        finally:
            f.close()
        return self.objects
        
    def _parsePath(self, path):
        pathList = path.split("/")
        if len(pathList)>1 and not pathList[-1]:
            del pathList[-1] # remove empty element in case there was trailing /
        return pathList
        
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

