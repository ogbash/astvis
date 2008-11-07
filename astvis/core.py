#! /usr/bin/env python

import logging as _logging
LOG = _logging.getLogger('core')

import action

#ASTReferenceResolverService = 'ASTReferenceResolverService'

__all__ = ['getService', 'registerService', 'registerServices']

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

    action.manager.registerActionService(component)


def registerServices(obj):
    "Collect services from the module obj and register them."
    import types

    # register all module classes which are services
    assert isinstance(obj, types.ModuleType)
    
    # services
    services = filter(lambda s: isinstance(getattr(obj,s), types.TypeType) and \
                      issubclass(getattr(obj,s), Service), dir(obj))
    for name in services:
        class_ = getattr(obj, name)
        registerService(name, class_())

    # recurse into submodules
    submodules = filter(lambda s: isinstance(getattr(obj,s), types.ModuleType) and \
                        getattr(obj,s).__name__.startswith(obj.__name__), dir(obj))
    for name in submodules:
        registerServices(getattr(obj,name))


class Service(object):
    pass
