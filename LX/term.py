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

class Variable(Term):
    def __init__(self, name=None, uriref=None):
        self.name = name
        self.value = uriref

class ExiVar(Variable):
    pass

class UniVar(Variable):
    pass
             
class Function(Term):
    pass

class Symbol(Term):      # or is this a zero-arity Function?  
    pass
    
class Constant(Symbol):     
    pass
    
class URIRef(Constant):

    def __init__(self, u):
        try:
            self.racine, self.fragment = split(u, "#")
            #print "initialized URIRef to %s, %s" % (self.racine, self.fragment)
        except ValueError:
            self.racine = u; self.fragment = None
        self.value = u

class String(Constant):

    def __init__(self, u):
        self._u = u

    def value(self):
        return self._u
    




# $Log$
# Revision 1.4  2002-08-29 21:56:54  sandro
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

 
