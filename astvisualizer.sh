#! /usr/bin/env sh

GAPHAS=libs/gaphas
PYNALYZE=libs/pynalyze

env PYTHONPATH="$GAPHAS:$PYNALYZE:$PYTHONPATH" python2.6 astvisualizer.py

