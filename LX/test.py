#! /usr/bin/env python
"""Call doctest on all our modules, or something.

"""

__version__ = "$Revision$"
# $Id$

import doctest
import LX

for x in LX.__all__:
    print "Module", "%-25s" %x,
    lx = __import__("LX."+x)
    m = getattr(lx, x)
    print "failed %3d of %3d doctest lines." % doctest.testmod(m)

    for (name, value) in m.__dict__.iteritems():
        if name.startswith("__test") and callable(value):
            print "...running",x+"."+name+"()"
            apply(value, [])
    
# $Log$
# Revision 1.7  2003-09-17 16:09:58  sandro
# also run any functions starting with __test...
#
# Revision 1.6  2003/02/13 19:25:04  sandro
# Use LX.__all__ to get the module names automagically
#
# Revision 1.5  2003/02/03 17:20:40  sandro
# factored logic.py out of fol.py
#
# Revision 1.4  2003/01/29 18:54:02  sandro
# added testing ../html module
#
# Revision 1.3  2003/01/10 21:33:36  sandro
# added sniff.py
#
# Revision 1.2  2003/01/08 17:51:22  sandro
# improved output format
#
# Revision 1.1  2003/01/08 17:48:27  sandro
# test harness for doctest across modules
#
