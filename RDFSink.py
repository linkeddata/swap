#!/usr/bin/python
"""RDFSink -- RDF parser/serializer/store interface

HISTORY

This module is being factored out of notation3.py

REFERENCES
  Python Style Guide
  Author: Guido van Rossum
  http://www.python.org/doc/essays/styleguide.html

"""

__version__ = "$Id$"



# The statement is stored as a quad - affectionately known as a triple ;-)
# offsets when a statement is stored as a Python tuple (c, p, s, o)
CONTEXT = 0
PRED = 1  
SUBJ = 2
OBJ = 3

PARTS =  PRED, SUBJ, OBJ
ALL4 = CONTEXT, PRED, SUBJ, OBJ

# A sink takes quads where each item is a pair   type, value

SYMBOL = 0          # URI which or may not have a fragment.
                    # (formerly: RESOURCE)
FORMULA = 1         # A { } set of statements
LITERAL = 2         # string etc - maps to data: @@??
ANONYMOUS = 3       # existentially qualified unlabelled resource
VARIABLE = 4        # 

# quanitifiers... @@it's misleading to treat these as predicates...
Logic_NS = "http://www.w3.org/2000/10/swap/log#"
forSomeSym = Logic_NS + "forSome"
forAllSym = Logic_NS + "forAll"


_Old_Logic_NS = "http://www.w3.org/2000/10/swap/log.n3#"

class RDFSink:

    """interface to connect modules in RDF processing.

    This is a superclass for other RDF processors which accept RDF events
    -- maybe later Swell events.  Adapted from printParser.
    An RDF stream is defined by startDoc, bind, makeStatement, endDoc methods.
    [@@DWC: then what are all these other methods?]
    
    Keeps track of prefixes. There are some things which are in the
    superclass for commonality (i.e. implementation inheritance)
    
    """

    def __init__(self):
        self.prefixes = { }     # Convention only - human friendly to
                                # track these.
        self.namespaces = {}    # reverse mapping of prefixes

    def startDoc(self):
        print "\nsink: start."

    def endDoc(self):
        print "sink: end.\n"

    def makeStatement(self, tuple):
        """add a statement to a stream/store.

        tuple is a quad of (type, value) pairs
        """
        
        pass

    def bind(self, prefix, nsPair):
        if nsPair[1] == _Old_Logic_NS:
            warn("The N3 logic namespace has changed. Take the '.n3' out!")
            nsPair = SYMBOL, Logic_NS    # Temporary hack

        # If we don't have a prefix for this ns...
        if not self.prefixes.get(nsPair, None):
            if not self.namespaces.get(prefix,None):   # For conventions
                self.prefixes[nsPair] = prefix
                self.namespaces[prefix] = nsPair
                #@@progress?
                #if chatty: print "# RDFSink: Bound %s to %s" % (prefix, nsPair[1])
            else:
                self.bind(prefix+"g1", nsPair) # Recurive
        

    #@@DWC: not sure what these are for.
    # These simple versions may be inherited by the reifier for example

    def startAnonymous(self,  triple, isList=0):
        return self.makeStatement(triple)
    
    def endAnonymous(self, subject, verb):    # Remind me where we are
        pass
    
    def startAnonymousNode(self, subj):
        pass
    
    def endAnonymousNode(self):    # Remove default subject
        pass

    def startBagSubject(self, context):
        pass

    def endBagSubject(self, subj):    # Remove context
        pass
     
    def startBagNamed(self, context, subj):
        pass

    def endBagNamed(self, subj):    # Remove context
        pass
     
    def startBagObject(self, triple):
        return self.makeStatement(triple)

    def endBagObject(self, pred, subj):    # Remove context
        pass
    
    def makeComment(self, str):
        print "sink: comment: ", str 


def warn(text):
    import sys
    
    sys.stderr.write("# **** Warning: %s\n" % (text,))
