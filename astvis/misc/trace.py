
import logging
LOG = logging.getLogger(__name__)

import sys
import inspect
import os.path

def dispatch(frame, event, arg):
    code = frame.f_code
    locals = frame.f_locals

    # file patterns
    patterns = ['astvis%s' % os.path.sep, 'astvisualizer.py']
    #patterns = ['gaphas%s'%os.path.sep]
    for pattern in patterns:
        index = code.co_filename.find(pattern)
        if index!=-1: break
    else:
        return
    filename = code.co_filename[index:]

    # ignore file patterns
    ignore_patterns = ['gtkx.py']
    for pattern in ignore_patterns:
        if filename.find(pattern)!=-1:
            return

    # ignore names
    ignore_names = set(['__str__','__hash__'])
    if code.co_name in ignore_names:
        return

    if locals.has_key('self'):
        # try to guess class.method name
        name = "%s.%s" % (locals['self'].__class__.__name__, code.co_name)
    else:
        name = code.co_name

    # calculate stack frame depth
    depth=0
    f = frame
    while f.f_back!=None:
        f=f.f_back
        depth+=1
    
    print '%s---' % ('  '*depth), name, 'at', "%s:%d" %(filename,frame.f_lineno)

_enabled = False

def toggle():
    global _enabled
    if _enabled:
        sys.settrace(None)
        _enabled = False
        LOG.info("Tracing disabled")
    else:
        sys.settrace(dispatch)
        _enabled = True
        LOG.info("Tracing enabled")
