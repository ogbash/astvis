#! /usr/bin/env python

import logging as _logging
LOG = _logging.getLogger('core')

ASTReferenceResolverService = 'ASTReferenceResolverService'

__all__ = ['getService', 'registerService']

"""Provides starting points for component architecture."""

_services = {} # name -> component instance providing this service

def getService(name):
    return _services.get(name, None)

def registerService(name, component):
    if name in _services.keys():
        LOG.info("Replacing service '%s': %s with %s" % (name, _services[name], component))
    else:
        LOG.info("Adding service '%s': %s" % (name, component))
    _services[name] = component

