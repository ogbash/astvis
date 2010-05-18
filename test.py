#! /usr/bin/env python

import sys

def setLogging():
    "Set logging like from conf file like in application."
    import logging,utils.log
    from astvis.common import FINE, FINER, FINEST
    logging.addLevelName(FINE, "FINE")
    logging.addLevelName(FINER, "FINER")
    logging.addLevelName(FINEST, "FINEST")    
    #logging.basicConfig(level=FINEST)
    import logging.config
    logging.config.fileConfig("logging.conf")


if len(sys.argv)>=2 and '-h' in sys.argv[1:]:
    sys.stderr.write("Usage: %s <test name>, where the name is module, class or method path.\n" % sys.argv[0])
    sys.exit(1)    

import unittest
loader = unittest.defaultTestLoader

if len(sys.argv)<2:
    # switch off logging
    import logging
    logging.basicConfig(level=logging.ERROR)

    # find all tests in 'tests' package
    suite = unittest.TestSuite()
    import tests
    modulesNames = tests.testModuleNames
    for mName in modulesNames:
        m = getattr(tests, mName)
        suite.addTests(loader.loadTestsFromModule(m))
else:
    # normal logging
    setLogging()
    
    # get test(s) specified by user
    testname = sys.argv[1]
    suite = loader.loadTestsFromName(testname)


runner = unittest.TextTestRunner()
runner.run(suite)
