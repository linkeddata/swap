#! /usr/bin/python
"""

$Id$

Operating systems built-ins for cwm
http://www.w3.org/2000/10/swap/string.py

See cwm.py and the os module in python

"""

from thing import *
import thing

import os

OS_NS_URI = "http://www.w3.org/2000/10/swap/os#"



###############################################################################################
#
#                              O P E R A T I N G   S Y T E M   B U I L T - I N s
#
#
#   Light Built-in classes

# Read Operating sytem environment lookup - read-only
#
# Not fatal if not defined
class BI_environ(LightBuiltIn, Function):
    def evaluateObject(self, store, context, subj, subj_py):
        if thing.verbosity() > 80: progress("os:environ input:"+`subj_py`+ " has value "+os.environ[subj_py])
        if type(subj_py) == type(''):
            return store._fromPython(os.environ.get(subj_py, None))

#  Register the string built-ins with the store

def register(store):
    str = store.internURI(OS_NS_URI[:-1])
    str.internFrag("environ", BI_environ)

# ends

