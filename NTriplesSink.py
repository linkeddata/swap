#!/usr/bin/env python
"""

"""
__version__ = "$Revision$"
# $Id$

import re

class Error(RuntimeError):
   pass

################################################################

class FormulaSink:

    def __init__(self):
        self.nodeIDCounter = 0

    def termFor(self, value=None, uri=None):
        """This implementation pushed the interface contract a bit
        by returning plain strings, NOT Terms.  Not so good, really."""
        if uri is None:
            if value is None:
                result = "_:g"+str(self.nodeIDCounter)
                self.nodeIDCounter += 1
            else:
                # @@@ datatype support goes here!
                value = re.sub(r'\n', r'\\n', str(value))
                result = '"'+str(value)+'"'
        else:
            if value is None:
                # do URI-escaping to 7-bit ascii?  what's the spec say?
                result = "<"+uri+">"
            else:
                raise Error, "You can't give both a value and a uri"
        return result

    def insert(self, arg):
        for a in arg:
            print a,
        print "."

if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])

# $Log$
# Revision 1.2  2003-04-04 12:52:10  sandro
# added quoting of newlines
# made characters be RDF literals, grouped together
#
# Revision 1.1  2003/04/03 21:55:06  sandro
# First cut prototype of a parser which reads plain XML as if it were RDF.
#
