"""
wrapper for rdflib's RDF/XML parser
"""
__version__ = "$Revision$"
# $Id$

import urllib

import rdflib.URIRef 
import rdflib.BNode 
import rdflib.Literal
import rdflib.syntax.parser

import LX.fol
import LX.expr
import LX.kb
import LX.rdf

class Parser(rdflib.syntax.parser.Parser):

    def __init__(self, sink=None, flags=""):
        self.kb = sink
        self.bnodes = { }

    def load(self, inputURI):
        self.parse(urllib.urlopen(inputURI))

    def termFor(self, s):
        if isinstance(s, rdflib.URIRef.URIRef):
            return LX.logic.ConstantForURI(s)
        if isinstance(s, rdflib.Literal.Literal):
            return LX.logic.ConstantForDatatypeValue(str(s), s.datatype)
        if isinstance(s, rdflib.BNode.BNode):
            try:
                tt = self.bnodes[s]
                #print "Reusing existential:", tt
            except KeyError:
                tt = self.kb.newExistential("q")
                #print "New existential:", tt
                self.bnodes[s] = tt
            return tt
        # that should be about it, right?
        raise RuntimeError, "conversion from rdflib of: "+s.n3()
        
    def add(self, t):
        # Store in RAISED (FOL, FlatBread) form for now....
        self.kb.add(self.termFor(t[0]),
                    self.termFor(t[1]),
                    self.termFor(t[2]))

class Serializer:

    def __init__(self, stream, flags=""):
        self.stream = stream

    def makeComment(self, comment):
        self.stream.write("% "+comment+"\n")

    def serializeKB(self, kb):
        pass

# $Log$
# Revision 1.2  2003-07-31 18:26:02  sandro
# unknown older stuff
#
# Revision 1.1  2003/07/19 12:00:46  sandro
# wrapper for rdflib's RDF/XML parser
#
