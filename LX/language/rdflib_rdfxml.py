
import rdflib.URIRef 
import rdflib.BNode 
import rdflib.Literal
import rdflib.syntax.parser

import LX.fol
import LX.expr
import LX.kb
import LX.rdf


#  t[0] = apply(LX.fol.RDF, (args[1], args[0], args[2]))

class Parser(rdflib.syntax.parser.Parser):

    def __init__(self, sink=None, flags=""):
        self.kb = sink
        self.bnodes = { }

    def load(self, inputURI):
        self.parse(inputURI)

    def termFor(self, s):
        if isinstance(s, rdflib.URIRef.URIRef):
            return LX.logic.ConstantForURI(s)
        if isinstance(s, rdflib.Literal.Literal):
            return LX.logic.ConstantForDatatypeValue(s)
        if isinstance(s, rdflib.BNode.BNode):
            try:
                return self.bnodes[s]
            except KeyError:
                tt = kb.newExistential(s)
                self.bnodes[s] = tt
                return tt
        raise RuntimeError, "conversion from rdflib of: "+s.n3()
        
    def add(self, t):
        #print t[0].n3(), t[1].n3(), t[2].n3()
        #    convert each to Term
        self.kb.add(apply(LX.fol.RDF, (self.termFor(t[0]),
                                  self.termFor(t[1]),
                                  self.termFor(t[2]))))

class Serializer:

    def __init__(self, stream, flags=""):
        self.stream = stream

    def makeComment(self, comment):
        self.stream.write("% "+comment+"\n")

    def serializeKB(self, kb):
        pass

# $Log$
# Revision 1.1  2003-07-19 12:00:46  sandro
# wrapper for rdflib's RDF/XML parser
#
