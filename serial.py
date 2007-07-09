#! /usr/bin/python
"""

$Id$

Printing of N3 and RDF formulae

2007-07-07 Rewrite fron scratch functionality
This is or was http://www.w3.org/2000/10/swap/serial.py

Historical note:  2007-07-07:  This was started as a replacement for pretty.py
which is slow, and has a weird and obsolescent RDFSink interface to the N3 and
RDF/XML output adapters.      The intention is that the same code will be able
to be converted to Jvascript to work in an AJAX environemnt in the AJAR library.
There, it will also serialize to a HTML DON user rendering of the data in a
particular document.
"""


import types
import string

import diag
from diag import progress, verbosity, tracking
from term import   Literal, XMLLiteral, Symbol, Fragment, AnonymousNode, \
    AnonymousVariable, FragmentNil, AnonymousUniversal, \
    Term, CompoundTerm, List, EmptyList, NonEmptyList, N3Set
from formula import Formula, StoredStatement
from notarion3 import stringToN3, backslashify, hexify, _notNameChars

from RDFSink import Logic_NS, RDFSink, forSomeSym, forAllSym
from RDFSink import CONTEXT, PRED, SUBJ, OBJ, PARTS, ALL4, \
	    ANONYMOUS, SYMBOL, LITERAL, LITERAL_DT, LITERAL_LANG, XMLLITERAL
from RDFSink import N3_nil, N3_first, N3_rest, OWL_NS, N3_Empty, N3_List, \
		    List_NS
from RDFSink import RDF_NS_URI
from RDFSink import RDF_type_URI

from xmlC14n import Canonicalize

cvsRevision = "$Revision$"

# Magic resources we know about

from RDFSink import RDF_type_URI, DAML_sameAs_URI

INTEGER_DATATYPE = "http://www.w3.org/2001/XMLSchema#integer"
FLOAT_DATATYPE = "http://www.w3.org/2001/XMLSchema#double"
DECIMAL_DATATYPE = "http://www.w3.org/2001/XMLSchema#decimal"
BOOLEAN_DATATYPE = "http://www.w3.org/2001/XMLSchema#boolean"

XML_LITERAL_DATATYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#XMLLiteral"

prefixchars = "abcdefghijklmnopqustuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


Class TreeNode:
    def __init__(self)
        pass

Class Leaf(TermNode):
    def __init__(self, sz, term)
        self._term = term
        self._sz = sz

Class Serializer:

    def __init__(self, f, write=None, base=None, flags=""):
        self.formula = f
        self.base = base
        self.write = write
        self.incoming = {}
        self.subjects = []
        self.nextNodeId = 1
        self.bnodeMap = {}
        self.indent = 0
        self.prefixes = {}  # reverse of:
        self.namespaces = {}
        self._flags = flags
        self.defaultNamespace = None

    
    def scan(self):
        for st in self.f.statements:
            x = st.object()
            self.incoming[x] = self.incoming.get(x, 0) + 1
            self.subjects[st.subject()] = 1

#  Structure is rendered into nested sequences

    def serialize(self):
        self.scan()
        self.subjects.sort()
        lastSubject = None
        for x in self.subjects:
            if x is lastSubject: continue
            lastSubject = x
            if s.termType == 'bnode' and self.incoming[x] == 1: continue 
            retun [ self.node(x), self.plist(x)]

    def plist(self, x):
        "Property List -- this version good when store has subject index"
        pl = self.f.statementsMatching(subj=x);
        pl.sort(StoredStatement.comparePredObj);
        res = []
        while i < len(pl)
            st = pl[i];
            p = st.predicate()
            res.append(self.representation(p))
            objs = [self.represenation(st.objct())]
            while i+1 < len(pl) and pl[i+1].predicate().sameTermAs(p)
                i++
                objs[-1] += ','
                objs.append(self.represenation(pl[i].predicate())
            i++
            if i < len(pl): objs[-1] += ';'
            res.append(objs)
        return res
    
    def renderTree(self, write, tree, level=0):
        "Could have many variations on this theme"
        for branch in tree:
            if (type(branch) is type([])):
                self.renderTree(write, branch, level+1)
            else:
            write(" "*self.indent*level) + branch
            
                
################################################## Individual Terms
            
    def representation(self, term)
        if term.termType == 'symbol':
            return self.repSybol(term.uri);

        if term.termType == 'bnode':
            return '_:b' + sz.bnodeId(term)
            
        if term.termType == 'literal':
            return self.repLiteral(term);
            
        raise InternalError(
            "should not be called for this type: "+term.termType)


    def repLiteral(self, term):
        if term.lang:
            return stringToN3(term.value, 'n' in self._flags,
                                    flags=self._flags)+ "@" + lang
            return stringToN3(term.value, 'n' in self.flags, self.flags)
        if not term.dt:
            return stringToN3(term.value, 'n' in self.flags, self.flags)
        
        dt = term.dt.uriref()
        
        if dt == XML_LITERAL_DATATYPE:
            return (stringToN3(
                        Canonicalize(value, None, unsuppressedPrefixes=['foo']),
                        singleLine=singleLine,
                        flags=self._flags)
                    + "^^"
                    + self.repSymbol(dt))

        if "b" not in self._flags:
            if dt == BOOLEAN_DATATYPE:
                return toBool(s) and "true" or "false"
        if "n" not in self._flags:
            if dt == INTEGER_DATATYPE:
                return str(long(s))
            if dt == FLOAT_DATATYPE:
                retVal =  str(float(s))    # numeric value python-normalized
                if 'e' not in retVal:
                    retVal += 'e+00'
                return retVal
            if dt == DECIMAL_DATATYPE:
                retVal = str(Decimal(s))
                if '.' not in retVal:
                    retVal += '.0'
                return retVal
            return stringToN3(term.value, 'n' in self._flags,
                                flags=self._flags)+ "^^" +
                                self.representation(term.dt)
            

    def repSymbol(uri):
        "The represenattion of a symbol with a given URI"
        j = string.rfind(uri, "#")
	if j<0 and "/" in self._flags:
	    j=string.rfind(uri, "/")   # Allow "/" namespaces as a second best
	
        if (j>=0
            and "p" not in self._flags):   # Suppress use of prefixes?
	    for ch in uri[j+1:]:  #  Examples: "." ";"  we can't have in qname
		if ch in _notNameChars:
		    if verbosity() > 20:
			progress("Cannot have character %i in local name for %s"
				    % (ord(ch), `uri`))
		    break
	    else:
		namesp = uri[:j+1]
		if (self.defaultNamespace
		    and self.defaultNamespace == namesp
		    and "d" not in self._flags):
		    return ":"+uri[j+1:]
		self.countNamespace(namesp)
		prefix = self.prefixes.get(namesp, None) # @@ #CONVENTION
		if prefix != None : return prefix + ":" + uri[j+1:]
	    
		if uri[:j] == self.base:   # If local to output stream,
		    return "<#" + uri[j+1:] + ">" # use local frag id
        
	if "r" not in self._flags and self.base != None:
	    uri = hexify(refTo(self.base, uri))
	elif "u" in self._flags: uri = backslashUify(uri)
	else: uri = hexify(uri)

        return "<" + uri + ">" 

    
    def countNamespace(self, namesp):
	"""On output, count how many times each namespace is used.
        
        This is used so that after a dummy run, the best dfault namespace
        can be figured out from the most common."""
        
	try:
	    self._counts[namesp] += 1
	except KeyError:
	    self._counts[namesp] = 1

    def bnodeId(self, term):
        if self.incoming.get(term, 0) == 1:
            return None # None required
        res = self.bnodeMap.get(term, None)
        if res is None:
            self.nextNodeId += 1 # never zero so aloways 
            res = self.nextNodeId
            self.bnodeMap[term] = res
        return res


############ Namespace counting

Class NamespaceCounter(Serializer):

    def __init__(self, f, base=None, flags=""):
        Serializer.init(self, f, base, flags)

    def repLiteral(sellf, term):
        pass  # for speed

#################################### Testing

def _test:
    from mySyore import theStore
    kb = theStore.load()
    sz = Serializer(kb)
    sz.serialize(kb, stdout.write)
    
if __name__ == '__main__':
    _test()



#ends

