"""Call doctest on all our modules, or something.

"""

__version__ = "$Revision$"
# $Id$

import doctest
import LX
import LX.engine

for x in [ "LX.expr", "LX.engine.otter" ]:
    print "Module", x
    __import__(x)
    print eval("doctest.testmod(%s)" % x)
    
# $Log$
# Revision 1.1  2003-01-08 17:48:27  sandro
# test harness for doctest across modules
#
