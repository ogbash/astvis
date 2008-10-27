#! /usr/bin/env python

# logging
import logging
from astvis.common import FINE, FINER, FINEST
if __name__=="__main__":
    logging.addLevelName(FINE, "FINE")
    logging.addLevelName(FINER, "FINER")
    logging.addLevelName(FINEST, "FINEST")    
    #logging.basicConfig(level=FINEST)
    import logging.config
    logging.config.fileConfig("logging.conf")

import sys

if len(sys.argv)<2:
    sys.stderr.write("Usage: %s <test name>, where the name is module, class or method path.\n" % sys.argv[0])
    sys.exit(1)
testname = sys.argv[1]

import unittest
loader = unittest.defaultTestLoader
suite = loader.loadTestsFromName(testname)

runner = unittest.TextTestRunner()
runner.run(suite)
