"""


"""
__version__ = "$Revision$"
# $Id$

class KB(list):
    """A Knowledge Base, a list of implicitely conjoined sentences.

    This is comparable to an RDF "Graph" if the Sentences are all
    triples.

    ISSUE: should we have top-level lists of UniVars and ExiVars,
    so the sentences can be much simpler?  This would be nice for RDF
    Graphs.   If so, should we move quantification to the top scope
    implicitely or explicitely?    Explicitely.

    Note that ExiVars are OUTSIDE of UniVars, so they are much
    simpler, more like constants.
    """

    def __init__(self):
        self.exivars = []
        self.univars = []
        self.exIndex = 0
        
    def prep(kb):
        """return a KB if possible, perhaps just the argument; throw
        an error we can't make a KB out of this thing"""
        if isinstance(kb, KB): return kb
        if isinstance(kb, list): return KB(kb)
        # nothing else for now
        raise RuntimeError, "Not convertable to a KB"
    prep = staticmethod(prep)

    def add(self, formula):
        self.append(formula)

    def newExistential(self, name=None):
        if name is None:
            name = "g" + str(self.exIndex)
            self.exIndex = self.exIndex + 1
        # @@@ check to make sure name not used!
        v = LX.ExiVar(name)
        self.exivars.append(v)
        return v

    
  
# $Log$
# Revision 1.1  2002-08-29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

  
