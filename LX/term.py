"""


"""
__version__ = "$Revision$"
# $Id$

import LX
from LX.language.otter import serialize
from string import split

class Term:

    def __str__(self):
        return serialize(self)

    def getVars(self):
        """not called OpenVars to give us more type checking"""
        raise RuntimeError, "please override"
    
class Variable(Term):
    def __init__(self, name=None, uriref=None):
        self.name = name
        self.value = uriref
    def openVars(self):
        return [self]
    def getName(self):
        return self.name     # @@@@ no guarantees about it!
                            # see "expr" for better version
      
class ExiVar(Variable):
    pass

class UniVar(Variable):
    pass
             
class Function(Term):
    """TODO: implement; should reroute to Constant if zero-arity"""
    pass

class Constant(Function):     
    """A Function Term with no arguments (zero-arity)."""
    def getVars(self):
        return []
    
class URIRef(Constant):

    def __init__(self, u):
        try:
            self.racine, self.fragment = split(u, "#")
            #print "initialized URIRef to %s, %s" % (self.racine, self.fragment)
        except ValueError:
            self.racine = u; self.fragment = None
        self.value = u
    def openVars(self):
        return []

class String(Constant):

    def __init__(self, u):
        self._u = u

    def value(self):
        return self._u
    def openVars(self):
        return []

    
class RDFLiteral(Constant):

    def __init__(self, text, lang=None, isXML=0):
        pass
    def openVars(self):
        return []




# $Log$
# Revision 1.6  2002-10-03 16:13:02  sandro
# some minor changes to LX-formula stuff, but it's still broken in ways
# that don't show up on the regression test.
#
# mostly: moved llyn-LX conversion stuff out of llyn.py, into
# LX.engine.llynInterface.py
#
# Revision 1.5  2002/10/02 22:56:35  sandro
# Switched cwm main-loop to keeping state in llyn AND/OR an LX.formula,
# as needed by each command-line option.  Also factored out common
# language code in main loop, so cwm can handle more than just "rdf" and
# "n3".  New functionality is not thoroughly tested, but old functionality
# is and should be fine.  Also did a few changes to LX variable
# handling.
#
# Revision 1.4  2002/08/29 21:56:54  sandro
# remove debugging print left in accidentally
#
# Revision 1.3  2002/08/29 21:02:13  sandro
# passes many more tests, esp handling of variables
#
# Revision 1.2  2002/08/29 16:39:55  sandro
# fixed various early typos and ommissions; working on logic bug which is manifesting in description loops
#
# Revision 1.1  2002/08/29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

 
