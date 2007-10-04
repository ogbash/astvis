#! /usr/bin/env python

import xml.dom
from model import File, ProgramUnit, Subprogram

def loadFile(filename):
    import xml.dom.minidom
    f = open(filename, "r")
    try:
        xmlTree = xml.dom.minidom.parse(f)
    finally:
        f.close()
    return filesFromXML(xmlTree.documentElement)

def filesFromXML(rootNode):
    files = []
    for node in rootNode.childNodes:
        if node.nodeType==xml.dom.Node.ELEMENT_NODE:
            if node.nodeName=="file":
                obj=fileFromXML(node)
                files.append(obj)
    return files
    
def fileFromXML(thisNode):
    fl = File()
    fl.name = thisNode.getAttribute("name")
    for node in thisNode.childNodes:
        if node.nodeType==xml.dom.Node.ELEMENT_NODE:
            if node.nodeName in ("program","module"):
                obj = programUnitFromXML(node, fl)
                fl.units.append(obj)
    return fl

def programUnitFromXML(thisNode, parent = None):
    pr = ProgramUnit(parent)
    pr.name = thisNode.getAttribute("id")
    # generate children
    for node in thisNode.childNodes:
        if node.nodeType==xml.dom.Node.ELEMENT_NODE:
            if node.nodeName in ("subroutine","function"):
                obj = subprogramFromXML(node, pr)
                pr.subprograms.append(obj)
    # generate calls
    nodes = thisNode.getElementsByTagName("calls")
    if nodes and len(nodes)>0:
        callsNode = nodes[0]
        for node in callsNode.childNodes:
            if node.nodeType==xml.dom.Node.ELEMENT_NODE:
                pr.callNames.append(node.getAttribute("name"))
    return pr

def subprogramFromXML(thisNode, parent = None):
    sub = Subprogram(parent)
    sub.name = thisNode.getAttribute("id")
    # generate children
    for node in thisNode.childNodes:
        if node.nodeType==xml.dom.Node.ELEMENT_NODE:
            if node.nodeName in ("subroutine","function"):
                obj = subprogramFromXML(node, sub)
                sub.subprograms.append(obj)
    # generate calls
    nodes = thisNode.getElementsByTagName("calls")
    if nodes and len(nodes)>0:
        callsNode = nodes[0]
        for node in callsNode.childNodes:
            if node.nodeType==xml.dom.Node.ELEMENT_NODE:
                sub.callNames.append(node.getAttribute("name"))
    return sub

