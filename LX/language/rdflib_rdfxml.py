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

import pluggable
from sys import stderr

class Parser(pluggable.Parser):

    name = "rdflib_rdfxml"
    #language = "application/rdf"
    language = "http://www.w3.org/1999/02/22-rdf-syntax-ns#RDF"
    sinkStyle = LX.kb.KB

    def parse(self, stream, sink):
        p = ParserX(sink=sink)
        p.parse(stream)

    
class ParserX(rdflib.syntax.parser.Parser):

    def __init__(self, sink=None, flags=""):
        self.kb = sink
        self.bnodes = { }

    def load(self, inputURI):
        self.parse(urllib.urlopen(inputURI))

    def termFor(self, s):
        if isinstance(s, rdflib.URIRef.URIRef):
            return LX.logic.ConstantForURI(unicode(s).encode('UTF-8'))
        if isinstance(s, rdflib.Literal.Literal):
            # print "LIT: ", str(s), s.datatype
            if s.datatype:
                return LX.logic.ConstantForDatatypeValue(s, LX.logic.ConstantForURI(str(s.datatype)))
            else:
                return LX.logic.ConstantForDatatypeValue(s)
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
# Revision 1.8  2003-11-07 06:53:05  sandro
# support for running RDF Core tests
#
# Revision 1.7  2003/09/10 20:13:56  sandro
# removed obsolete comment
#
# Revision 1.6  2003/09/05 04:39:07  sandro
# changed handling of i18n chars
#
# Revision 1.5  2003/09/04 07:14:15  sandro
# fixed plain literal handling
#
# Revision 1.4  2003/08/22 20:49:41  sandro
# midway on getting load() and parser abstraction to work better
#
# Revision 1.3  2003/08/01 15:27:22  sandro
# kind of vaguely working datatype support (for xsd unsigned ints)
#
# Revision 1.2  2003/07/31 18:26:02  sandro
# unknown older stuff
#
# Revision 1.1  2003/07/19 12:00:46  sandro
# wrapper for rdflib's RDF/XML parser
#
