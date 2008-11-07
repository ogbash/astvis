#! /usr/bin/env python

from astvis import action, core

__all__=['DataflowService']

class DataflowService(core.Service):
    UI_DESCRIPTION='''
    <menubar name="Menubar">
      <menu action="analysis" name="Analysis">
        <menuitem action="ast-reaching-definitions"
      </menu>
    </menubar>
    '''

    @action.Action('ast-reaching-definitions')
    def getReachingDefinitions(astNode, context=None):
        print "reaching definitions"
