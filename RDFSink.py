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
# However, the recopmmended way is for the source to call the factory methods new* rather
# than just make up pairs.

SYMBOL = 0          # URI which or may not have a fragment.
                    # (formerly: RESOURCE)
FORMULA = 1         # A { } set of statements. (identifier is arbitrary)
LITERAL = 2         # string etc - maps to data: @@??
ANONYMOUS = 3       # As SYMBOL except actual symbol is arbitrary, can be regenerated


# quanitifiers... @@it's misleading to treat these as predicates...
Logic_NS = "http://www.w3.org/2000/10/swap/log#"
# For some graphs you can express with NTriples, there is no RDF syntax. The 
# following allows an anonymous node to be merged with another node.
# It really is the same node, at the ntriples level, do not confuse with daml:equivalentTO
NODE_MERGE_URI = Logic_NS + "is"  # Pseudo-property indicating node merging
forSomeSym = Logic_NS + "forSome"
forAllSym = Logic_NS + "forAll"

RDF_type_URI = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
RDF_NS_URI = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
DAML_NS=DPO_NS = "http://www.daml.org/2001/03/daml+oil#"  # DAML plus oil
DAML_equivalentTo_URI = DPO_NS+"equivalentTo"
parsesTo_URI = Logic_NS + "parsesTo"
RDF_spec = "http://www.w3.org/TR/REC-rdf-syntax/"
List_NS = DPO_NS     # We have to pick just one all the time


_Old_Logic_NS = "http://www.w3.org/2000/10/swap/log.n3#"


# For lists:
N3_first = (SYMBOL, List_NS + "first")
N3_rest = (SYMBOL, List_NS + "rest")
N3_nil = (SYMBOL, List_NS + "nil")
N3_List = (SYMBOL, List_NS + "List")
N3_Empty = (SYMBOL, List_NS + "Empty")




class URISyntaxError(ValueError):
    """A parameter is passed to a routine that requires a URI reference"""
    pass


class RDFSink:

    """interface to connect modules in RDF processing.

    This is a superclass for other RDF processors which accept RDF events
    -- maybe later Swell events.  Adapted from printParser.
    An RDF stream is defined by startDoc, bind, makeStatement, endDoc methods.
    
    Keeps track of prefixes. There are some things which are in the
    superclass for commonality (i.e. implementation inheritance)
    
    This interface has the advantage that it does n ot have any dependencies
    on object types, it is really one-way (easily serialized as no return values).
    It has the disadvantages that
	- It uses the pseudoproperties log:forSome and log:forAll to
	  make variables, which is a bit of a kludge.
	- It may involve on the receiver side the same thing being interned
	  many times, which wastes time searching hash tables.
    
    """

    def __init__(self, genPrefix=None):
        self.prefixes = { }     # Convention only - human friendly to
                                # track these.
        self.namespaces = {}    # reverse mapping of prefixes
        self.defaultNamespace = None

	self._genPrefix = genPrefix
#	if not self._genPrefix: self._genPrefix = "uuid:@@@@whatever@@@@1234_"
	self._nextId = 0

    def startDoc(self):
        pass

    def endDoc(self, rootFormulaPair):
	"""End a document
	
	Call this once only at the end of parsing so that the receiver can wrap
	things up, oprimize, intern, index and so on.  The pair given is the (type, value)
	identifier of the root formula of the thing parsed."""
        pass

    def reopen(self):
	"""Un-End a document
	
	If you have added stuff to a document, thought you were done, and
	then want to add more, call this to get back into the sate that makeSatement
	is again acceptable. Remember to end the document again when done."""
        pass

    def makeStatement(self, tuple):
        """add a statement to a stream/store.

        raises URISyntaxError on bad URIs
        tuple is a quad (context, predicate, subject, object) of (type, value) pairs
        """
        
        pass

    def bind(self, prefix, nsPair):
	"""Pass on a binding hint for later use in output

	This really is just a hint. The parser calls bind to pass on the prefix which
	it came across, as this is a useful hint for a human readable prefix for output
	of the same namespace. Otherwise, output processors will have to invent
	or avoid useing namespaces, which will look ugly
	"""

        # If we don't have a prefix for this ns...
        if not self.prefixes.get(nsPair, None):
            if not self.namespaces.get(prefix,None):   # For conventions
                self.prefixes[nsPair] = prefix
                self.namespaces[prefix] = nsPair
                #@@progress?
                #if chatty: print "# RDFSink: Bound %s to %s" % (prefix, nsPair[1])
            else:
                self.bind(prefix+"g1", nsPair) # Recurive

    def setDefaultNamespace(self, nsPair):
	"""Pass on a binding hint for later use in output

	This really is just a hint. The parser calls this to pass on the default namespace which
	it came across, as this is a useful hint for a human readable prefix for output
	of the same namespace. Otherwise, output processors will have to invent
	or avoid useing namespaces, which will look ugly.
	"""
        self.defaultNamespace = nsPair
  
    def makeComment(self, str):
	"""This passes on a comment line which of course has no semantics.
	
	This is only useful in direct piping of parsers to output, to preserve
	comments in the original file.
	"""
	pass

#Class RDFPlusSink(RDFSink):
#    """This class has explicit extensions to make it cleaner to
#    make N3 extensions on top of plain RDF:
#    """

#   def __init__(self, genPrefix=None):
#	RDFSink.__init__(self)
#	self._genPrefix = genPrefix
#	if not self._genPrefix: self._genPrefix = "uuid:@@@@whatever@@@@1234_"
#	self._nextId = 0
	
    def genId(self):
	subj = self._genPrefix
	if subj == None: subj = "#_h"
        subj = subj + `self._nextId`
        self._nextId = self._nextId + 1
#	print "@@@@@@@ generating ", subj
        return subj

    def setGenPrefix(self, genPrefix):
	if not self._genPrefix:
	    self._genPrefix = genPrefix

    def newLiteral(self, str):
	return (LITERAL, str)

    def newSymbol(self, uri):
	return (SYMBOL, uri)

    def newFormula(self, uri=None):
	if uri==None: return FORMULA, self.genId()
	else: return (FORMULA, uri)

    def newBlankNode(self, context):
	return self.newExistential(context)
	
    def newUniversal(self, context, uri=None):
	if uri==None: subj = ANONYMOUS, self.genId()  # ANONYMOUS means "arbitrary symbol"
	else: subj=(SYMBOL, uri)
        self.makeStatement((context,
                            (SYMBOL, forAllSym), #pred
                            context,  #subj
                            subj))                      # obj	
	return subj
	
    def newExistential(self, context, uri=None):
	if uri==None: subj = ANONYMOUS, self.genId()
	else: subj=(SYMBOL, uri)
        self.makeStatement((context,
                            (SYMBOL, forSomeSym), #pred
                            context,  #subj
                            subj))                      # obj	
	return subj
	

class RDFStructuredOutput(RDFSink):

    # The foillowing are only used for structured "pretty" outyput of structrued N3.
    # They roughly correspond to certain syntax forms in N3, but the whole area
    # is just a kludge for pretty output and not worth going into unless you need to.
    
    # These simple versions may be inherited, by the reifier for example

    def startAnonymous(self,  triple, isList=0):
        return self.makeStatement(triple)
    
    def endAnonymous(self, subject, verb):    # Remind me where we are
        pass
    
    def startAnonymousNode(self, subj):
        pass
    
    def endAnonymousNode(self, endAnonymousNode):    # Remove default subject, restore to subj
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
    
  
# ends
