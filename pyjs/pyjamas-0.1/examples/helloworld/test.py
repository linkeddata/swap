#!/usr/bin/env python

import sys
sys.path.append("../../library")

from Hello import Hello

Hello().onModuleLoad()

print "Simple python test of onModuleLoad succeeded."
