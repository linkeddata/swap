"""
Main LX package import point.

We import most modules here, so users can just use LX.Foo instead of
LX.foo.Foo.  That means we have to be more careful about naming
conflicts, but it also gives us more freedom to move code between
files without affecting the API.

"""
__version__ = "$Revision$"
# $Id$

# To allow "from LX import *", though I'm not sure when one would
# want that.
__all__ = [
    "language",
    "engine",
    "kb",
    "expr",
    "logic",
    "fol",
    "rdf",
    "namespace",
    "uri",
    "defaultns",
    ] 

# Let people use LX.Expr instead of LX.expr.Expr, etc, while
# having these parts in separate files
#
# This has the side-effect of meaning if you import any one module
# from LX, you are importing them all, since python runs all the
# __init__.py code first.  oops.   What to do?
#from LX.uri import *
#from LX.kb import *
#from LX.expr import *
#from LX.logic import *
#from LX.describer import *
#from LX.namespace import *
#from LX.rdf import *
#from LX.defaultns import *

# $Log$
# Revision 1.7  2003-02-13 19:47:48  sandro
# reformate a little
#
# Revision 1.6  2003/02/13 19:24:21  sandro
# Stopped importing everything, since doing so meant that any use of
# anything in LX/* meant important everything.  We'll need to use LX.all
# or some such if we want them all into one namespace.
#
# Revision 1.5  2003/02/13 17:20:19  sandro
# moved URI-related stuff over to uri.py
#
# Revision 1.4  2003/01/29 06:09:18  sandro
# Major shift in style of LX towards using expr.py.  Added some access
# to otter, via --check.  Works as described in
# http://lists.w3.org/Archives/Public/www-archive/2003Jan/0024
# I don't like this UI; I imagine something more like --engine=otter
# --think, and --language=otter (instead of --otterDump).
# No tests for any of this.
#
# Revision 1.3  2002/08/29 21:02:13  sandro
# passes many more tests, esp handling of variables
#
# Revision 1.2  2002/08/29 16:39:55  sandro
# fixed various early typos and ommissions; working on logic bug which
# is manifesting in description loops  
#
# Revision 1.1  2002/08/29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

  
