#!/usr/local/bin/python
"""
$Id$


This module implements basic sources and sinks for RDF data.
It defines a stream interface for such data.
It has a command line interface, can work as a web query engine,
and has built in test(), all of which demosntrate how it is used.

To make a new RDF processor, subclass RDFSink.

See also:

Notation 3
http://www.w3.org/DesignIssues/Notation3

Closed World Machine - and RDF Processor
http;//www.w3.org/2000/10/swap/cwm

______________________________________________

Module originally by Dan Connolly, includeing notation3
parser and RDF generator. TimBL added RDF stream model
and N3 generation.

DWC:
oops... I'm not doing qname expansion as described
there (i.e. adding a # if it's not already there).

I allow unprefixed qnames, so not all barenames
are keywords.

---- hmmmm ... not expandable - a bit of a trap.

I haven't done quoting yet.

idea: migrate toward CSS notation?

idea: use notation3 for wiki record keeping.


"""



import string
import urlparse
import urllib
import re

# Magic resources we know about

RDF_type_URI = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
RDF_NS_URI = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
DAML_equivalentTo_URI = "http://www.daml.org/2000/10/daml-ont#equivalentTo"
DAML_NS = "http://www.daml.org/2000/10/daml-ont#"
Logic_NS = "http://www.w3.org/2000/10/swap/log.n3#"

RDF_spec = "http://www.w3.org/TR/REC-rdf-syntax/"

ADDED_HASH = "#"  # Stop where we use this in case we want to remove it!
# This is the hash on namespace URIs

# The statement is stored as a quad - affectionately known as a triple ;-)

CONTEXT = 0
PRED = 1  # offsets when a statement is stored as a Python tuple (p, s, o, c)
SUBJ = 2
OBJ = 3

PARTS =  PRED, SUBJ, OBJ
ALL4 = CONTEXT, PRED, SUBJ, OBJ

# The parser outputs quads where each item is a pair   type, value

RESOURCE = 0        # which or may not have a fragment
LITERAL = 2         # string etc - maps to data:
ANONYMOUS = 3       # existentially qualified unlabelled resource
VARIABLE = 4        # 

RDF_type = ( RESOURCE , RDF_type_URI )
DAML_equivalentTo = ( RESOURCE, DAML_equivalentTo_URI )

N3_forSome_URI = Logic_NS + "forSome"
#N3_subExpression_URI = Logic_NS + "subExpression"
N3_forAll_URI = Logic_NS + "forAll"

DPO_NS = "http://www.daml.org/2000/12/daml+oil#"  # DAML plus oil

List_NS = DPO_NS     # We have to pick just one all te time

# For lists:
N3_first = (RESOURCE, List_NS + "first")
N3_rest = (RESOURCE, List_NS + "rest")
N3_nil = (RESOURCE, List_NS + "nil")
N3_List = (RESOURCE, List_NS + "List")
N3_Empty = (RESOURCE, List_NS + "Empty")


chatty = 0   # verbosity flag

option_noregen = 0   # If set, do not regenerate genids on output

N3CommentCharacter = "#"     # For unix script #! compatabilty

################################################################### Sinks
#
# This is the interface which connects modules in RDF processing.
#


class RDFSink:

    """  Dummy RDF sink prints calls

    This is a superclass for other RDF processors which accept RDF events
    -- maybe later Swell events.  Adapted from printParser.
    An RDF stream is defined by startDoc, bind, makeStatement, endDoc methods.
    """
    
#  Keeps track of prefixes
# there are some things which are in the superclass for commonality 

    def __init__(self):
        self.prefixes = { }     # Convention only - human friendly to track these
        self.namespaces = {}    # reverse mapping of prefixes

    def bind(self, prefix, nsPair):
        if not self.prefixes.get(nsPair, None):  # If we don't have a prefix for this ns
            if not self.namespaces.get(prefix,None):   # For conventions
                self.prefixes[nsPair] = prefix
                self.namespaces[prefix] = nsPair
                if chatty: print "# RDFSink: Bound %s to %s" % (prefix, nsPair[1])
            else:
                self.bind(prefix+"g1", nsPair) # Recurive
        
    def makeStatement(self, tuple):  # Quad of (type, value) pairs
        pass

    def makeComment(self, str):
        print "sink: comment: ", str 

    def startDoc(self):
        print "\nsink: start."

    def endDoc(self):
        print "sink: end.\n"


########################################## Parse string to sink
#

class SinkParser:
    def __init__(self, sink, thisDoc, baseURI="", bindings = {},
                 genPrefix = "", varPrefix = ""):
	""" note: namespace names should *not* end in #;
	the # will get added during qname processing """
        self._sink = sink
    	self._bindings = bindings
	self._thisDoc = thisDoc
        self._baseURI = baseURI
	self._context = RESOURCE , self._thisDoc    # For storing with triples @@@@ use stack
        self._contextStack = []      # For nested conjunctions { ... }
        self._varPrefix = varPrefix
        self._nextId = 0
        self.lines = 0              # for error handling
        self._genPrefix = genPrefix

        if not self._baseURI: self._baseURI = self._thisDoc
        if not self._genPrefix: self._genPrefix = self._thisDoc + "#_g"
        if not self._varPrefix: self._varPrefix = self._thisDoc + "#_v"

    def load(self, uri, _baseURI=""):
        if uri:
            _inputURI = urlparse.urljoin(_baseURI, uri) # Make abs from relative
            self._sink.makeComment("Taking input from " + _inputURI)
            netStream = urllib.urlopen(_inputURI)
            self.startDoc()
            self.feed(netStream.read())     # @ May be big - buffered in memory!
            self.endDoc()
        else:
            self._sink.makeComment("Taking input from standard input")
            _inputURI = urlparse.urljoin(_baseURI, "STDIN") # Make abs from relative
            self.startDoc()
            self.feed(sys.stdin.read())     # May be big - buffered in memory!
            self.endDoc()


    def feed(self, str):
	"""if BadSyntax is raised, the string
	passed in the exception object is the
	remainder after any statements have been parsed.
	So if there is more data to feed to the
	parser, it should be straightforward to recover."""
        i = 0
	while i >= 0:
	    j = self.skipSpace(str, i)
	    if j<0: return

            i = self.directiveOrStatement(str,j)
            if i<0:
                print "# next char: ", `str[j]` 
                raise BadSyntax(self.lines, str, j, "expected directive or statement")

    def directiveOrStatement(self, str,h):
    
	    i = self.skipSpace(str, h)
	    if i<0: return i   # EOF

	    j = self.directive(str, i)
	    if j>=0: return  self.checkDot(str,j)
	    
            j = self.statement(str, i)
            if j>=0: return self.checkDot(str,j)
            
	    return j


    #@@I18N
    _namechars = string.lowercase + string.uppercase + string.digits + '_-'

    def tok(self, tok, str, i):
        """tokenizer strips whitespace and comment"""
        j = self.skipSpace(str,i)
        if j<0: return j
        i = j
        
#	while 1:
#            while i<len(str) and str[i] in string.whitespace:
#                i = i + 1
#            if i == len(str): return -1
#            if str[i] == N3CommentCharacter:     # "#"?
#                while i<len(str) and str[i] != "\n":
#                    i = i + 1
#            else: break
	if (str[i:i+len(tok)] == tok
            and (tok[0] not in self._namechars    # check keyword is not prefix
                or str[i+len(tok)] in string.whitespace )):
	    i = i + len(tok)
	    return i
	else:
	    return -1

    def directive(self, str, i):
        delim = "#"
	j = self.tok('bind', str, i)        # implied "#". Obsolete.
	if j<0:
            j=self.tok('@prefix', str, i)   # no implied "#"
            delim = ""
            if j<0: return -1
	
	t = []
	i = self.qname(str, j, t)
	if i<0: raise BadSyntax(self.lines, str, j, "expected qname after bind or prefix")
	j = self.uri_ref2(str, i, t)
	if j<0: raise BadSyntax(self.lines, str, i, "expected uriref2 after bind _qname_")

        ns = t[1][1] + delim
        if string.find(ns,"##")>=0: raise BadSyntax(self.lines, str, j-2, "trailing # illegal on bind: use @prefix")
	self._bindings[t[0][0]] = ns
	self.bind(t[0][0], (RESOURCE, ns))
	return j

    def bind(self, qn, nsPair):
        self._sink.bind(qn, nsPair)

    def startDoc(self):
        self._sink.startDoc()

    def endDoc(self):
        self._sink.endDoc()

    def makeStatement(self, triple):
#        print "# Parser output: ", `triple`
        self._sink.makeStatement(triple)



    def statement(self, str, i):
	r = []

	i = self.subject(str, i, r)
	if i<0:
	    return -1

	j = self.property_list(str, i, r[0])

	if j<0: raise BadSyntax(self.lines, str, i, "expected propertylist")

	return j

    def subject(self, str, i, res):
	return self.node(str, i, res)

    def verb(self, str, i, res):
	""" has _prop_
	is _prop_ of
	a
	=
	_prop_
	>- prop ->
	<- prop -<
	_operator_"""

	r = []
	j = self.tok('has', str, i)
	if j>=0:
	    i = self.prop(str, j, r)
	    if i < 0: raise BadSyntax(self.lines, str, j, "expected prop")
	    res.append(('->', r[0]))
	    return i
	else:
	    j = self.tok('is', str, i)
	    if j>=0:
		i = self.prop(str, j, r)
		if i < 0: raise BadSyntax(self.lines, str, j, "expected prop")
		j = self.tok('of', str, i)
		if j<0: raise BadSyntax(self.lines, str, i, "expected 'of' after prop")
		res.append(('<-', r[0]))
		return j
	    else:
		j = self.tok('a', str, i)
		if j>=0:
		    res.append(('->', RDF_type))
		    return j
		else:
		    j = self.tok('=', str, i)
		    if j>=0:
			res.append(('->', DAML_equivalentTo))
			return j
		    else:
			j = self.prop(str, i, r)
			if j >= 0:
			    res.append(('->', r[0]))
			    return j
			else:
	    
			    j = self.tok('>-', str, i)
			    if j>=0:
				i = self.prop(str, j, r)
				j = self.tok('->', str, i)
				if j<0: raise BadSyntax(self.lines, str, i, "-> expected")
				res.append(('->', r[0]))
				return j
			    else:
				j = self.tok('<-', str, i)
				if j>=0:
				    i = self.prop(str, j, r)
				    if i<0: raise BadSyntax(self.lines, str, j, "bad verb syntax")
				    j = self.tok('<-', str, i)
				    if j<0: raise BadSyntax(self.lines, str, i, "<- expected")
				    res.append(('<-', r[0]))
				    return j
				else:
				    return self.operator(str, i, res)

    def prop(self, str, i, res):
	return self.node(str, i, res)

    def node(self, str, i, res, subjectAlready=None):
        subj = subjectAlready

        j = self.tok('this', str, i)   # This context
        if j>=0:
            res.append(self._context)
            return j

	if subj is None:   # If this can be a named node, then check for a name.
            j = self.uri_ref2(str, i, res)
            if j >= 0:
                return j


        j = self.tok('[', str, i)
        if j>=0:
            if subj is None: subj=self.genid()
            i = self.property_list(str, j, subj)
            if i<0: raise BadSyntax(self.lines, str, j, "property_list expected")
            j = self.tok(']', str, i)
            if j<0: raise BadSyntax(self.lines, str, i, "']' expected")
            res.append(subj)
            return j

        j = self.tok('{', str, i)
        if j>=0:
            oldContext = self._context
            if subj is None: subj = self.genid()

            self._context = subj
            
            while 1:
                i = self.skipSpace(str, j)
                if i<0: raise BadSyntax(self.lines, str, i, "needed '}', found end.")
                
                j = self.tok('}', str,i)
                if j >=0: break
                
                j = self.directiveOrStatement(str,i)
                if j<0: raise BadSyntax(self.lines, str, i, "expected statement or '}'")

            self._context = oldContext # restore
            res.append(subj)
            return j

        j = self.tok('(', str, i)    # List abbreviated syntax?
        if j>=0:
            tail = None  # remember value to return
            while 1:
                i = self.skipSpace(str, j)
                if i<0: raise BadSyntax(self.lines, str, i, "needed ')', found end.")                    
                j = self.tok(')', str,i)
                if j >=0: break

                item = []
                j = self.object(str,i, item)
                if j<0: raise BadSyntax(self.lines, str, i, "expected item in list or ')'")
                this = self.genid()
                if tail:
                    self.makeStatement((self._context, N3_rest, tail, this ))
                else:
                    head = this
                tail = this
                self.makeStatement((self._context, N3_first, this, item[0] ))           # obj

            if not tail:
                res.append(N3_nil)
                return j
            self.makeStatement((self._context, N3_rest, tail, N3_nil ))           # obj
            res.append(head)
            return j

        return -1
        
    def property_list(self, str, i, subj):
	while 1:
            j = self.tok(":-", str,i)
            if j >=0:
                res = []
                i = self.node(str, j, res, subj)
                if i<0: raise BadSyntax(self.lines, str, j, "bad {} or () or [] node after :- ")
                continue
                
	    v = []
	    j = self.verb(str, i, v)
            if j<=0:
		return i # void
	    else:
		objs = []
		i = self.object_list(str, j, objs)
		if i<0: raise BadSyntax(self.lines, str, j, "object_list expected")
		for obj in objs:
		    dir, sym = v[0]
		    if dir == '->':
			self.makeStatement((self._context, sym, subj, obj))
		    else:
			self.makeStatement((self._context, sym, obj, subj))

		j = self.tok(';', str, i)
		if j<0:
		    return i
		i = j

    def object_list(self, str, i, res):
	i = self.object(str, i, res)
	if i<0: return -1
	while 1:
	    j = self.tok(',', str, i)
	    if j<0: return i    # Found something else!
            i = self.object(str, j, res)

    def checkDot(self, str, i):
            j = self.tok('.', str, i)
            if j >=0: return j
            
            j = self.tok('}', str, i)
            if j>=0: return i # Can omit . before these
            j = self.tok(']', str, i)
            if j>=0: return i # Can omit . before these

            raise BadSyntax(self.lines, str, i, "expected '.' or '}' or ']' at end of statement")
            return i


    def uri_ref2(self, str, i, res):
	"""Generate uri from n3 representation.

	Note that the RDF convention of directly concatenating
	NS and local name is now used though I prefer inserting a '#'
	to make the namesapces look more like what XML folks expect.
	"""
	qn = []
	j = self.qname(str, i, qn)
	if j>=0:
	    pfx, ln = qn[0]
	    if pfx is None:
		ns = self._thisDoc + ADDED_HASH   # @@@ "#" CONVENTION
	    else:
		try:
		    ns = self._bindings[pfx]
		except KeyError:
		    raise BadSyntax(self.lines, str, i, "prefix not bound")
            res.append(( RESOURCE, ns + ln)) # @@@ "#" CONVENTION
            if not string.find(ns, "#"):print"Warning: no # on NS %s,"%(ns,)
	    return j

        v = []
        j = self.variable(str,i,v)
        if j>0:                    #Forget varibles as a class, only in context.
#            res.append(internVariable(self._thisDoc,v[0]))
            res.append((VARIABLE, v[0]))
            return j
        
        j = self.skipSpace(str, i)
        if j<0: return -1
        else: i=j

        if str[i]=="<":
            i = i + 1
            st = i
            while i < len(str):
                if str[i] == ">":
                    uref = str[st:i] # the join should dealt with "":
                    uref = urlparse.urljoin(self._baseURI, str[st:i])
                    if str[i-1:i]=="#" and not uref[-1:]=="#":
                        uref = uref + "#"  # She meant it! Weirdness in urlparse?
                    res.append((RESOURCE , uref))
                    return i+1
                i = i + 1
            raise BadSyntax(self.lines, str, j, "unterminated URI reference")
        else:
            return -1

    def skipSpace(self, str, i):
	while 1:
            while i<len(str) and str[i] in string.whitespace:
                if str[i] == "\n": self.lines = self.lines + 1
                i = i + 1
            if i == len(str): return -1
            if str[i] == N3CommentCharacter:     # "#"?
                while i<len(str) and str[i] != "\n":
                    i = i + 1
            else: break
	return i

    def variable(self, str, i, res):
	"""	?abc -> 'abc'
  	"""

	j = self.skipSpace(str, i)
	if j<0: return -1

        if str[j:j+1] != "?": return -1
        j=j+1
        i = j
	while i <len(str) and str[i] in self._namechars:
            i = i+1
        res.append( self.varPrefix + str[j:i])
#        print "Variable found: <<%s>>" % str[j:i]
        return i

    def qname(self, str, i, res):
	"""
	xyz:def -> ('xyz', 'def')
	def -> ('', 'def')                   @@@@
	:def -> ('', 'def')    
	"""

	j = self.skipSpace(str, i)
	if j<0: return -1
	else: i=j

	c = str[i]
	if c in self._namechars:
	    ln = c
	    i = i + 1
	    while i < len(str):
		c = str[i]
		if c in self._namechars:
		    ln = ln + c
		    i = i + 1
		else: break
	else:
            ln = ''   # Was:  None - TBL (why? useful?)

	if i<len(str) and str[i] == ':':
	    pfx = ln
	    i = i + 1
	    ln = ''
	    while i < len(str):
		c = str[i]
		if c in self._namechars:
		    ln = ln + c
		    i = i + 1
		else: break

	    res.append((pfx, ln))
	    return i

	else:
	    if ln:
		res.append(('', ln))
		return i
	    else:
		return -1
	    
    def object(self, str, i, res):
	j = self.subject(str, i, res)
	if j>= 0:
	    return j
	else:
	    j = self.skipSpace(str, i)
	    if j<0: return -1
	    else: i=j

	    if str[i]=='"':
		if str[i:i+3] == '"""': delim = '"""'
		else: delim = '"'

                i = i + len(delim)
                # @@I18n  This is NOT internationalised. Should have unicode escaping too.
                j = i
                ustr = u""   # Empty unicode string
                startline = self.lines # Reember where for error messages
                while str[j:j+len(delim)] != delim:
                    ch = str[j:j+1]
                    j = j + 1
                    uch = u""
                    if ch == "":
                        raise BadSyntax(self.lines, str, i, "unterminated string literal")
                    if ch == "\r": continue   # Strip carriage returns
                    if ch == "\n":
                        if delim == '"': raise BadSyntax(startline, str, i, "newline found in string literal")
                        self.lines = self.lines + 1
                        
                    if ch == "\\":
                        j = j + 1
                        ch = str[j:j+1]  # Will be empty if string ends
                        if ch == "":
                            raise BadSyntax(startline, str, i, "unterminated string literal (2)")
                        k = string.find('abfrtvn\\"', ch)
                        if k >= 0:
                            uch = '\a\b\f\r\t\v\n\\"'[k]
                        else:
                            k = string.find("01234567", ch)
                            if k >=0:
                                count = 0
                                value = k
                                while count < 2:  # Get two more characters
                                    ch = str[j:j+1]
                                    j = j + 1
                                    if ch == "":
                                        raise BadSyntax(startline, str, i, "unterminated string literal")
                                    k = string.find("01234567", ch)
                                    if k <=0:
                                        raise BadSyntax(startline, str, i, "bad string literal octal escape")
                                    value = value * 8 + k
                                    count = count + 1
                                uch = struct.pack("B", value) # Unsigned binary byte @@I18n
                            else:
                                if ch == "u":
                                    count = 0
                                    value = 0
                                    while count < 4:  # Get two more characters
                                        ch = str[j:j+1]
                                        j = j + 1
                                        if ch == "":
                                            raise BadSyntax(startline, str, i, "unterminated string literal(3)")
                                        k = string.find("0123456789abcdef", ch)
                                        if k <=0:
                                            raise BadSyntax(startline, str, i, "bad string literal hex escape")
                                        value = value * 16 + k
                                        count = count + 1
                                    uch = unicode.ntou (value) # @@I18n Need n->unicode mapping @@@@
                                    
                    if uch == u"": uch = ch  # coerce
                    ustr = ustr + uch

                res.append((LITERAL, ustr))
		return j+len(delim)
	    else:
		return -1

    def genid(self):  # Generate existentially quantified variable id
        subj = RESOURCE , self._genPrefix + `self._nextId` # ANONYMOUS node
        self._nextId = self._nextId + 1
        self.makeStatement((self._context, # quantifiers - use inverse?
                            (RESOURCE, N3_forSome_URI), #pred
                            self._context,  #subj
                            subj))                      # obj
        return subj

    def operator(self, str, i, res):
	j = self.tok('+', str, i)
	if j >= 0:
	    res.append((RESOURCE, '+')) #@@ convert to operator:plus and then to URI
	    return j

	j = self.tok('-', str, i)
	if j >= 0:
	    res.append((RESOURCE,'-')) #@@
	    return j

	j = self.tok('*', str, i)
	if j >= 0:
	    res.append((RESOURCE,'*')) #@@
	    return j

	j = self.tok('/', str, i)
	if j >= 0:
	    res.append((RESOURCE,'/')) #@@
	    return j
	else:
	    return -1

class BadSyntax:
    def __init__(self, lines, str, i, why):
	self._str = str
	self._i = i
	self._why = why
	self.lines = lines

    def __str__(self):
	str = self._str
	i = self._i

	if i>30: pre="..."
	else: pre=""
	if len(str)-i > 30: post="..."
	else: post=""

	return 'Line %i: Bad syntax (%s) at ^ in: "%s%s^%s%s"' \
	       % (self.lines +1, self._why, pre, str[i-30:i], str[i:i+30], post)


def stripCR(str):
    res = ""
    for ch in str:
        if ch != "\r":
            res = res + ch
    return res


########################## RDF 1.0 Syntax generator
	    
class ToRDF(RDFSink):
    """keeps track of most recent subject, reuses it"""

    _valChars = string.lowercase + string.uppercase + string.digits + "_ !#$%&().,+*/"
    #@ Not actually complete, and can encode anyway
    def __init__(self, outFp, thisURI):
        RDFSink.__init__(self)
	self._wr = XMLWriter(outFp)
	self._subj = None
	self._thisDoc = thisURI
	self._docOpen = 0  # Delay doc open <rdf:RDF .. till after binds

    #@@I18N
    _namechars = string.lowercase + string.uppercase + string.digits + '_'
    _rdfns = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
    _myns = 'http://www.w3.org/2000/10/n3/notation3.py#'

    def startDoc(self):
        pass

    def endDoc(self):
        self.flushStart()  # Note: can't just leave empty doc if not started: bad XML
	if self._subj:
	    self._wr.endElement()
	self._subj = None
	self._wr.endElement()  # </rdf:RDF>
	self._wr.endDocument()

    def makeComment(self, str):
        self._wr.makeComment(str)

    def flushStart(self):
        if not self._docOpen:
            if self.prefixes.get((RESOURCE, RDF_NS_URI), ":::") == ":::":
                if self.namespaces.get("rdf", ":::") ==":::":
                    self.bind("rdf", (RESOURCE, RDF_NS_URI))
            ats = []
            for pfx in self.prefixes.values():
                if pfx:
                    ats.append(('xmlns:'+pfx, self.namespaces[pfx][1]))
                else:
                    ats.append(('xmlns', self.namespaces[pfx][1]))
            self._wr.startElement(RDF_NS_URI+'RDF', ats, self.prefixes)
            self._subj = None
            self._nextId = 0
            self._docOpen = 1

    def makeStatement(self,  tuple):
        self.flushStart()
        context, pred, subj, obj = tuple # Context is ignored
	predn = relativeURI(self._thisDoc, pred[1])
	subjn = relativeURI(self._thisDoc, subj[1])

	if self._subj != subj:
	    if self._subj:
		self._wr.endElement()
	    self._subj = subj
	    if pred == (RESOURCE, RDF_type_URI) and obj[0] != LITERAL: # Special case starting with this
                self._wr.startElement(obj[1], [("about", subjn),], self.prefixes)
                return
	    self._wr.startElement(RDF_NS_URI+'Description',
				 [("about", subjn),], self.prefixes)

	if obj[0] != LITERAL: 
	    objn = relativeURI(self._thisDoc, obj[1])
	    self._wr.emptyElement(pred[1], [('resource', objn)], self.prefixes)
	    return
# Actually this shorthand notatoin is not RDF, it was my misunderstanding! rats...
#	for ch in obj[1]:  # Is literal representable as an attribute value?
#            if ch in self._valChars: continue
#            else: break # No match
#        else:
#            if len(obj[1]) < 40:    # , say
#                self._wr.emptyElement(pred[1], [('value', obj[1])], self.prefixes)
#                return
        self._wr.startElement(pred[1], [], self.prefixes)
        self._wr.data(obj[1])
        self._wr.endElement()

# Below is for writing an anonymous node which is the object of only one arc
# This is the arc leading to it.

    def startAnonymous(self,  tuple, isList =0):
        self.flushStart()
        context, pred, subj, obj = tuple 
	if self._subj != subj:
	    if self._subj:
		self._wr.endElement()
	    subjn = relativeURI(self._thisDoc, subj[1])
	    self._wr.startElement(RDF_NS_URI + 'Description',
				 (('about', subjn),), self.prefixes)
	    self._subj = subj

        self._wr.startElement(pred[1], [('parseType','Resource')], self.prefixes)  # @@? Parsetype RDF

        self._subj = obj    # The object is now the current subject


    def endAnonymous(self, subject, verb):    # Remind me where we are

        self._wr.endElement()
#        self._subj = subject
        self._subj = subject       # @@@ This all needs to be thought about!


# Below we do anonymous top level node - arrows only leave this circle

    def startAnonymousNode(self, subj):
        self.flushStart()
        if self._subj:
            self._wr.endElement()
            self._subj = None
        self._wr.startElement(RDF_NS_URI+'Description', [], self.prefixes)
        self._subj = subj    # The object is not the subject context
        self._pred = None

    def endAnonymousNode(self):    # Remove context
    	self._wr.endElement()
	self._subj = None
        self._pred = None

# Below we notate a nested bag of statements - a context

    def startBagSubject(self, context):  # Doesn't work with RDF sorry ILLEGAL
        self.flushStart()
        self._wr.startElement(RDF_NS_URI+'Description', 
			      [],
#			      [('about', relativeURI(self._thisDoc,context[1]))],
                              self.prefixes)
        self._wr.startElement(RDF_NS_URI+"is", [('parseType', 'Quote')], self.prefixes)
        self._subj = None
        self._pred = None


    def endBagSubject(self, subj):    # Remove context
        self._wr.endElement()
        self._wr.endElement()
        self._subj = subj
        self._pred = None

    def startBagObject(self, tuple):
        self.flushStart()
        context, pred, subj, obj = tuple 
	if self._subj != subj:
	    if self._subj:
		self._wr.endElement()
	    subjn = relativeURI(self._thisDoc, subj[1])
	    self._wr.startElement(RDF_NS_URI + 'Description',
				 (('about', subjn),), self.prefixes)
	    self._subj = subj

        self._wr.startElement(pred[1], [('parseType','Quote')], self.prefixes)  # @@? Parsetype RDF
        self._subj = None
        self._pred = None


    def endBagObject(self, pred, subj):    # Remove context
        self._wr.endElement()
        self._wr.endElement()
        self._subj = pred
        self._pred = subj     

def relativeTo(here, there):
    print "### Relative to ", here[1], there[1]
    return relativeURI(here[1], there[1])
    

# Not perfect - should use root-relative in correct case but never mind.
def relativeURI(base, uri):
    if base == uri: return ""
    i=0
    while i<len(uri) and i<len(base):
        if uri[i] == base[i]:
            i = i + 1
        else:
            break
#    print "# relative", base, uri, "   same up to ", i
    # i point to end of shortest one or first difference
    if uri[i] =="#": return uri[i:]  # fragment of base
    while i>0 and uri[i-1] != '/' : i=i-1  # scan for slash
    if i < 3: return uri  # No way.
    if string.find(base, "//", i-2)>0: return uri # An unshared "//"
    n = string.count(base, "/", i)
    return ("../" * n) + uri[i:]
            
    
########################################### XML Writer

class XMLWriter:
    """ taken from
    Id: tsv2xml.py,v 1.1 2000/10/02 19:41:02 connolly Exp connolly
    """

    def __init__(self, outFp, squeaky=0):
	self._outFp = outFp
	self._wr = outFp.write
	self._elts = []
	self.squeaky = squeaky  # No, not squeaky clean output
	self.tab = 4        # Number of spaces to indent per level
        self.needClose = 0  # 1 Means we need a ">" but save till later
        self.noWS = 0       # 1 Means we cant use white space for prettiness
        self.currentNS = None # @@@ Hack
        
    #@@ on __del__, close all open elements?

    _namechars = string.lowercase + string.uppercase + string.digits + '_'


    def newline(self, howmany=1):
        if self.noWS:
            self.noWS = 0
            self.flushClose()
            return
        i = howmany
        if i<1: i=1
        self._wr("\n\n\n\n"[:i])
        self.indent()

    def indent(self, extra=0):
        self._wr(' ' * ((len(self._elts)+extra) * self.tab))
        self.flushClose()
        
    def closeTag(self):
        if self.squeaky:
            self.needClose =1
        else:
            self._wr(">")
            
    def flushClose(self):
        if self.needClose:
            self._wr(">")
            self.needClose = 0

    def figurePrefix(self, uriref, rawAttrs, prefixes):
	i = len(uriref)
	while i>0:
	    if uriref[i-1] in self._namechars:
		i = i - 1
	    else:
		break
	ln = uriref[i:]
	ns = uriref[:i]
#        print "@@@ ns=",ns, "@@@ prefixes =", prefixes
        prefix = prefixes.get((RESOURCE, ns), ":::")
        attrs = []
        for a, v in rawAttrs:   # Caller can set default namespace
            if a == "xmlns": self.currentNS = v
        if ns != self.currentNS:
            if prefix == ":::" or not prefix:  # Can't trust stored null prefix
                attrs = [('xmlns', ns)]
                self.currentNS = ns
            else:
                if prefix: ln = prefix + ":" + ln
        for at, val in rawAttrs:
            i = string.find(at," ")  #  USe space as delim like parser
            if i<=0:            # No namespace - that is fine for rdf syntax
#                print  ("# Warning: %s has no namespace on attr %s" %
#                        (ln, at)) 
                attrs.append((at, val))
                continue
            ans = at[:i]
            lan = at[i+1:]
            if ans == ns:    #  self.currentNS ?!! Default is same as
                attrs.append((lan, val))
                continue
            prefix = prefixes.get((RESOURCE, ans),":::")
            if prefix == ":::":
                print ("#@@@@@ tag %s: atr %s has no prefiex :-(" %
                       (uriref, at, `prefixes`))
                raise NoPrefixForAttributeError
            attrs.append(( prefix+":"+lan, val))    

	self.newline(3-len(self._elts))    # Newlines separate higher levels
	self._wr("<%s" % (ln,))

        needNL = 0
	for n, v in attrs:
	    #@@BUG: need to escape markup chars in v
            if needNL:
                self.newline()
                self._wr("   ")
	    self._wr(" %s=\"%s\"" % (n, v))
	    needNL = 1

            
        return (ln, attrs)

    def makeComment(self, str):
        self.newline()
        self._wr("<!-- " + str + "-->") # @@
        
    def startElement(self, n, attrs = [], prefixes={}):
        oldNS = self.currentNS
        ln, at2 = self.figurePrefix(n, attrs, prefixes)
	
	self._elts.append((ln, oldNS))
	self.closeTag()

    def emptyElement(self, n, attrs=[], prefixes={}):
        oldNS = self.currentNS
        ln, at2 = self.figurePrefix(n, attrs, prefixes)

	self.currentNS = oldNS  # Forget change - no nesting
	self._wr("/")
        self.closeTag()

    def endElement(self):

	n, self.currentNS = self._elts.pop()
        self.newline()
	self._outFp.write("</%s" % n)
	self.closeTag()


    markupChar = re.compile(r"[\r<>&]")  # timbl removed \n as can be in data

    def data(self, str):
	#@@ throw an exception if the element stack is empty
	o = self._outFp
        self.flushClose()
	i = 0
	while i < len(str):
	    m = self.markupChar.search(str, i)
	    if not m:
		o.write(str[i:])
		break
	    j = m.start()
	    o.write(str[i:j])
	    o.write("&#%d;" % (ord(str[j]),))
	    i = j + 1
	self.noWS = 1  # Suppress whitespace - we are in data

    def endDocument(self):
        while len(self._elts) > 0:
            self.endElement()
        self.flushClose()
        self._wr("\n")

class ToN3(RDFSink):
    """keeps track of most recent subject and predicate reuses them

      Adapted from Dan's ToRDFParser(Parser);
    """
#   A word about regenerated Ids.
#
# Within the program, the URI of a resource is kept the same, and in fact
# tampering with it would leave risk of all kinds of inconsistencies.
# Hwoever, on output, where there are URIs whose values are irrelevant,
# such as variables and generated IDs from anonymous ndoes, it makes the
# document very much more readable to regenerate the IDs.
#  We use here a convention that underscores at the start of fragment IDs
# are reserved for generated Ids. The caller can change that.

    def __init__(self, write, base=None, genPrefix = "#_", noLists=0 ):
	self._write = write
	self._subj = None
	self.prefixes = {}      # Look up prefix conventions
	self.indent = 1         # Level of nesting of output
	self.base = base
	self.nextId = 0         # Regenerate Ids on output
	self.regen = {}         # Mapping of regenerated Ids
	self.genPrefix = genPrefix  # Prefix for generated URIs on output
	self.stack = [ 0 ]      # List mode?
	self.noLists = noLists  # Suppress generation of lists?

	
	#@@I18N
    _namechars = string.lowercase + string.uppercase + string.digits + '_'
    _rdfns = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
    _myns = 'http://www.w3.org/2000/10/n3/notation3.py#'

    def newId(self):
        nextId = nextId + 1
        return nextId - 1
    
    def bind(self, prefixString, nsPair):
        """ Just accepting a convention here """
        self._endStatement()
        self.prefixes[nsPair] = prefixString
        self._write(" @prefix %s: <%s> ." % (prefixString, relativeURI(self.base, nsPair[1])) )
        self._newline()


    def startDoc(self):
 
        self._write("\n#  Notation3 generation by\n")
        idstring = "$Id$" # CVS CHANGES THIS
        self._write("#       " + idstring[5:-2] + "\n\n") # Strip $s in case result is checked in
        if self.base: self._write("#   Base was: " + self.base + "\n")
        self._write("    " * self.indent)
        self._subj = None
        self._nextId = 0

    def endDoc(self):
	self._endStatement()
	self._write("\n #ENDS\n")

    def makeComment(self, str):
        for line in string.split(str, "\n"):
            self._write("#" + line + "\n")  # Newline order??@@
        self._write("    " * self.indent + "    ")


    def _newline(self, extra=0):
        self._write("\n"+ "    " * (self.indent+extra))

    def makeStatement(self, triple):
        if self.stack[-1]:
            if triple[PRED] == N3_first:
                self._write(self.representationOf(triple[CONTEXT], triple[OBJ])+" ")
            elif triple[PRED] == RDF_type and triple[OBJ] == N3_List:
                pass  # We knew
            elif triple[PRED] == RDF_type and triple[OBJ] == N3_Empty:
                pass  # not how we would have put it but never mind
#                self._write("# Empty set terminated\n")
            elif triple[PRED] != N3_rest:
                print "####@@@@@@ ooops:", triple
                raise intenalError # Should only see first and rest in list mode
            return
        self._makeSubjPred(triple[CONTEXT], triple[SUBJ], triple[PRED])        
        self._write(self.representationOf(triple[CONTEXT], triple[OBJ]))
#        self._write(" (in %s) " % `context`)    #@@@@
        
# Below is for writing an anonymous node which is the object of only one arc        
    def startAnonymous(self,  triple, isList=0):
        if isList and not self.noLists:
            wasList = self.stack[-1]
            if wasList and triple[PRED]==N3_rest:   # rest p of existing list
                self.stack.append(2)    # just a rest - no parens
                self._subj = triple[OBJ]
            else:
                self._makeSubjPred(triple[CONTEXT], triple[SUBJ], triple[PRED])
                self.stack.append(1)    # New list
                self._write(" (")
                self.indent = self.indent + 1
            self._pred = N3_first
        else:
            self._makeSubjPred(triple[CONTEXT], triple[SUBJ], triple[PRED])
            self.stack.append(0)
            self._write(" [")
            self.indent = self.indent + 1
            self._pred = None
        self._newline()
        self._subj = triple[OBJ]    # The object is now the current subject

    def endAnonymous(self, subject, verb):    # Remind me where we are
        wasList = self.stack.pop()
        isList = self.stack[-1]
        if wasList:
            if not isList or wasList == 1:
                self._write(" )")
                self.indent = self.indent - 1
        else:
            self._write(" ]")
            self.indent = self.indent - 1
        self._subj = subject
        self._pred = verb

# Below we do anonymous top level node - arrows only leave this circle

    def startAnonymousNode(self, subj):
        self.stack.append(0)
	if self._subj:
	    self._write(" .")
	self._newline()
        self.indent = self.indent + 1
        self._write("  [ ")
        self._subj = subj    # The object is not the subject context
        self._pred = None


    def endAnonymousNode(self):    # Remove default subject
        self.stack.pop()
        self._write(" ].")
        self.indent = self.indent - 1
        self._newline()
        self._subj = None
        self._pred = None

# Below we notate a nested bag of statements

    def startBagSubject(self, context):
        self.stack.append(0)
	if self._subj != context:
	    self._endStatement()
        self.indent = self.indent + 1
        self._write("{")
        self._newline()
	self._subj = None
        self._pred = None

    def endBagSubject(self, subj):    # Remove context
        self.stack.append(0)
        self.stack.pop()
        self._endStatement()     # @@@@@@@@ remove in syntax change to implicit
        self._newline()
        self._write("}")
        self._subj = subj
        self._pred = None
        self.indent = self.indent - 1
     
    def startBagNamed(self, context, subj):
        if self._subj != subj:
            self._endStatement()
            if self.indent == 1:  # Top level only - extra newline
                self._newline()
            self._write(self.representationOf(context, subj))
            self._subj = subj
            self._pred = None

        if self._pred is not None:
            self._write(";")
 #       self._makeSubjPred(somecontext, subj, ( RESOURCE,  DAML_equivalentTo_URI ))
        self.stack.append(0)
        self.indent = self.indent + 1
        self._write(" :- {")
        self._newline()
        self._subj = None
        self._pred = None

    def endBagNamed(self, subj):    # Remove context
        self.stack.pop()
        self._endStatement()     # @@@@@@@@ remove in syntax change to implicit
        self._newline()
        self._write("}")
        self._subj = subj
        self._pred = None
        self.indent = self.indent - 1
     
    def startBagObject(self, triple):
        self._makeSubjPred(triple[CONTEXT], triple[SUBJ], triple[PRED])
        self.stack.append(0)
        self.indent = self.indent + 1
        self._write("{")
        self._subj = None
        self._pred = None

    def endBagObject(self, pred, subj):    # Remove context
        self.stack.pop()
        self._endStatement() # @@@@@@@@ remove in syntax change to implicit
        self.indent = self.indent - 1
        self._write("}")
#        self._newline()
        self._subj = subj
        self._pred = pred
     
    def _makeSubjPred(self, context, subj, pred):

        if self.stack[-1]: return  # If we are in list mode, don't need to.
        
        if self._subj != subj:
            self._endStatement()
            if self.indent == 1:  # Top level only - extra newline
                self._newline()
            self._write(self.representationOf(context, subj))
            self._subj = subj
            self._pred = None

        if self._pred != pred:
            if self._pred:
                  self._write(";")
                  self._newline(1)   # Indent predicate from subject
            else: self._write("    ")

            if pred == ( RESOURCE,  DAML_equivalentTo_URI ) :
                self._write(" = ")
            elif pred == ( RESOURCE, RDF_type_URI ) :
                self._write(" a ")
            else :
#               self._write( " >- %s -> " % self.representationOf(context, pred))
                self._write( " %s " % self.representationOf(context, pred))
                
            self._pred = pred
        else:
            self._write(",")
            self._newline(3)    # Same subject and pred => object list

    def _endStatement(self):
        if self._subj:
            self._write(" .")
            self._newline()
            self._subj = None

    def representationOf(self, context, pair):
        """  Representation of a thing in the output stream

        Regenerates genids and variable names if required.
        Uses prefix dictionary to use qname syntax if possible.
        """

#        print "# Representation of ", `pair`
        if pair == context:
            return "this"
        if pair == N3_nil and not self.noLists:
            return"()"
        type, value = pair
        if ((type == VARIABLE or type == ANONYMOUS)
            and not option_noregen ):
                i = self.regen.get(value,self.nextId)
                if i == self.nextId:
                    self.regen[value] = i
                    self.nextId = self.nextId + 1
                if type == ANONYMOUS: return "<"+self.genPrefix + "g" + `i`+">"
                else: return "<" + self.genPrefix + "v" + `i` + ">"   # variable

        if type == LITERAL: return stringToN3(value)

        j = string.rfind(value, "#")
        if j>=0:
            prefix = self.prefixes.get((RESOURCE, value[:j+1]), None) # @@ #CONVENTION
            if prefix != None : return prefix + ":" + value[j+1:]
        
            if value[:j] == self.base:   # If local to output stream,
                return "<#" + relativeURI(self.base, value[j+1:]) + ">" #   use local frag id (@@ lone word?)

        return "<" + relativeURI(self.base, value) + ">"    # Everything else

###################################################
#
#   Utilities
#

def stringToN3(str):
        res = ""
        if len(str) > 20 and string.find(str, "\n") >=0:
                delim= '"""'
                forbidden = "\\\"\a\b\f\r\t\v"
        else:
                delim = '"'
                forbidden = "\\\"\a\b\f\r\t\v\n"
        for i in range(len(str)):
                ch = str[i]
                j = string.find(forbidden, ch)
                if j>=0: ch = "\\" + '\"abfrtvn'[j]
                elif ch < " " or ch > "}" : ch= 'x'+`ch`[1:-1] # Use python
                res = res + ch
        return delim + res + delim


#########################################################
#
#    Reifier
#
# Use:
#   sink = notation3.Reifier(sink, outputURI)


class Reifier(RDFSink):

    def __init__(self, sink, context, genPrefix=None):
        RDFSink.__init__(self)
        self.sink = sink
        self._ns = "http://www.w3.org/2000/10/swap/model.n3#"
        self.sink.bind("n3", (RESOURCE, self._ns))
        self._nextId = 1
        self._context = context
        self._genPrefix = genPrefix
        if self._genPrefix == None:
            self._genPrefix = self._context + "#_s"
        
    def bind(self, prefix, nsPair):
        self.sink.bind(prefix, nsPair)
               
    def makeStatement(self, tuple):  # Quad of (type, value) pairs
        _statementURI = self._genPrefix + `self._nextId`
        self._nextId = self._nextId + 1
        N3_NS = "http://www.w3.org/2000/10/swap/model.n3#"
        name = "context", "predicate", "subject", "object"

        self.sink.makeStatement(( (RESOURCE, self._context), # quantifiers - use inverse?
                                  (RESOURCE, N3_forSome_URI),
                                  (RESOURCE, self._context),
                                  (RESOURCE, _statementURI) )) #  Note this is anonymous
        
        self.sink.makeStatement(( (RESOURCE, self._context), # Context
                              (RESOURCE, self._ns+"statement"), #Predicate
                              tuple[CONTEXT], # Subject
                              (RESOURCE, _statementURI) ))  # Object

        for i in PARTS:
            self.sink.makeStatement((
                (RESOURCE, self._context), # Context
                (RESOURCE, self._ns+name[i]), #Predicate
                (RESOURCE, _statementURI), # Subject
                tuple[i] ))  # Object


    def makeComment(self, str):
        return self.sink.makeComment(str) 

    def startDoc(self):
        return self.sink.startDoc()

    def endDoc(self):
        return self.sink.endDoc()

######################################################### Tests
  
def test():
    import sys
    testString = []
    
    t0 = """bind x: <http://example.org/x-ns/> .
	    bind dc: <http://purl.org/dc/elements/1.1/> ."""

    t1="""[ >- x:firstname -> "Ora" ] >- dc:wrote ->
    [ >- dc:title -> "Moby Dick" ] .
     bind default <http://example.org/default>.
     <uriPath> :localProp defaultedName .
     
"""
    t2="""
[ >- x:type -> x:Receipt;
  >- x:number -> "5382183";
  >- x:for -> [ >- x:USD -> "2690" ];
  >- x:instrument -> [ >- x:type -> x:visa ] ]

>- x:inReplyTo ->

[ >- x:type -> x:jobOrder;
  >- x:number -> "025709";
 >- x:from ->
 [
  >- x:homePage -> <http://www.topnotchheatingandair.com/>;
  >- x:est -> "1974";
  >- x:address -> [ >- x:street -> "23754 W. 82nd Terr.";
      >- x:city -> "Lenexa";
      >- x:state -> "KS";
      >- x:zip -> "66227"];
  >- x:phoneMain -> <tel:+1-913-441-8900>;
  >- x:fax -> <tel:+1-913-441-8118>;
  >- x:mailbox -> <mailto:info@topnotchheatingandair.com> ]
].    

<http://www.davelennox.com/residential/furnaces/re_furnaces_content_body_elite90gas.asp>
 >- x:describes -> [ >- x:type -> x:furnace;
 >- x:brand -> "Lennox";
 >- x:model -> "G26Q3-75"
 ].
"""
    t3="""
@prefix pp: <http://example.org/payPalStuff?>.
@prefix default <http://example.org/payPalStuff?>.

<> a pp:Check; pp:payee :tim; pp:amount "$10.00";
  dc:author :dan; dc:date "2000/10/7" ;
  is pp:part of [ a pp:Transaction; = :t1 ] .
"""

# Janet's chart:
    t4="""
bind q: <http://example.org/>.
bind m: <>.
bind n: <http://example.org/base/>.
bind : <http://void-prefix.example.org/>.
bind w3c: <http://www.w3.org/2000/10/org>.

<#QA> :includes 
 [  = w3c:internal ; :includes <#TAB> , <#interoperability> ,
     <#validation> , w3c:wai , <#i18n> , <#translation> ,
     <#readability_elegance>, w3c:feedback_accountability ],
 [ = <#conformance>;
     :includes <#products>, <#content>, <#services> ],
 [ = <#support>; :includes
     <#tools>, <#tutorials>, <#workshops>, <#books_materails>,
     <#certification> ] .

<#internal> q:supports <#conformance> .  
<#support> q:supports <#conformance> .

"""

    t5 = """

bind u: <http://www.example.org/utilities>
bind default <#>

:assumption = { :fred u:knows :john .
                :john u:knows :mary .} .

:conclusion = { :fred u:knows :mary . } .

"""
    thisURI = "file:notation3.py"

    testString.append(  t0 + t1 + t2 + t3 + t4 )
#    testString.append(  t5 )

#    p=SinkParser(RDFSink(),'http://example.org/base/', 'file:notation3.py',
#		     'data:#')

    r=SinkParser(ToN3(sys.stdout.write, thisURI),
                  thisURI,'http://example.org/base/',)
    r.startDoc()
    
    print "=== test stringing: ===== STARTS\n ", t0, "\n========= ENDS\n"
    r.feed(t0)

    print "=== test stringing: ===== STARTS\n ", t1, "\n========= ENDS\n"
    r.feed(t1)

    print "=== test stringing: ===== STARTS\n ", t2, "\n========= ENDS\n"
    r.feed(t2)

    print "=== test stringing: ===== STARTS\n ", t3, "\n========= ENDS\n"
    r.feed(t3)

    r.endDoc()
                   
            
        
############################################################## Web service

import random
import time
import cgi
import sys
import StringIO

def serveRequest(env):
    import random #for message identifiers. Hmm... should seed from request

    #sys.stderr = open("/tmp/connolly-notation3-log", "w")

    form = cgi.FieldStorage()

    if form.has_key('data'):
	try:
	    convert(form, env)
	except BadSyntax, e:
	    print "Status: 500 syntax error in input data"
	    print "Content-type: text/plain"
	    print
	    print e
	    

	except:
	    import traceback

	    print "Status: 500 error in python script. traceback follows"
	    print "Content-type: text/plain"
	    print
	    traceback.print_exc(sys.stdout)
	    
    else:
	showForm()

def convert(form, env):
    """ raises KeyError if the form data is missing required fields."""

    serviceDomain = 'w3.org' #@@ should compute this from env['SCRIPT_NAME']
         # or whatever; cf. CGI spec

    data = form['data'].value

    if form.has_key('baseURI'):	baseURI = form['baseURI'].value
    elif env.has_key('HTTP_REFERER'): baseURI = env['HTTP_REFERER']
    else: baseURI = 'mid:' #@@

    # output is buffered so that we only send
    # 200 OK if all went well
    buf = StringIO.StringIO()

    gen = ToRDF(buf, baseURI)
    xlate = SinkParser(gen, baseURI, baseURI)
    xlate.startDoc()
    xlate.feed(data)
    xlate.endDoc()

    print "Content-Type: text/xml"
    #hmm... other headers? last-modified?
    # handle if-modified-since? i.e. handle input by reference?
    print # end of HTTP response headers
    print buf.getvalue()

def showForm():
    print """Content-Type: text/html

<html>
<title>A Wiki RDF Service</title>
<body>

<form method="GET">
<textarea name="data" rows="4" cols="40">
bind dc: &lt;http://purl.org/dc/elements/1.1/&gt;
</textarea>
<input type="submit"/>
</form>

<div>
<h2>References</h2>
<ul>
<li><a href="http://www.w3.org/DesignIssues/Notation3">Notation 3</a></li>
<li><a href="http://www.python.org/doc/">python documentation</a></li>
<li><a href="http://www.w3.org/2000/01/sw/">Semantic Web Development</a></li>
</ul>
</div>

<address>
<a href="http://www.w3.org/People/Connolly/">Dan Connolly</a>
</address>

</body>
</html>
"""
#################################################  Command line
    
def doCommand():
        """Command line RDF/N3 tool
        
 <command> <options> <inputURIs>
 
 -rdf1out   Output in RDF M&S 1.0 insead of n3 (only works with -pipe at the moment)
 -help      print this message
 -chatty    Verbose output of questionable use

See also: cwm 
"""
        
        import urllib
        option_ugly = 0     # Store and regurgitate with genids *
        option_pipe = 1     # Don't store, just pipe though
        option_rdf1out = 0  # Output in RDF M&S 1.0 instead of N3
        option_bySubject= 0 # Store and regurgitate in subject order *
        option_inputs = []
        option_filters = []
        option_test = 0
        chatty = 0          # not too verbose please
        hostname = "localhost" # @@@@@@@@@@@ Get real one
        
        for arg in sys.argv[1:]:  # Command line options after script name
            if arg == "-test": option_test = 1
            elif arg == "-rdf1out": option_rdf1out = 1
            elif arg == "-chatty": chatty = 1
            elif arg == "-help":
                print doCommand.__doc__
                return
            elif arg[0] == "-": print "Unknown option", arg
            else : option_inputs.append(arg)
            
        if option_test: return test()

        # The base URI for this process - the Web equiv of cwd
#	_baseURI = "file://" + hostname + os.getcwd() + "/"
	_baseURI = "file://" + os.getcwd() + "/"
	
        _outURI = urlparse.urljoin(_baseURI, "STDOUT")
	if option_rdf1out:
            _sink = ToRDF(sys.stdout, _outURI)
        else:
            _sink = ToN3(sys.stdout.write, _outURI)
        _sink.makeComment("# Base URI of process is " + _baseURI)
        
#  Parse and regenerate RDF in whatever notation:

        inputContexts = []
        for i in option_inputs:
            _inputURI = urlparse.urljoin(_baseURI, i) # Make abs from relative
            p = SinkParser(_sink,  _inputURI)
            p.load(_inputURI)
            del(p)

        if option_inputs == []:
            _inputURI = urlparse.urljoin( _baseURI, "STDIN") # Make abs from relative
            p = SinkParser(_sink,  _inputURI)
            p.load("")
            del(p)

        return




############################################################ Main program
    
if __name__ == '__main__':
    import os
    import urlparse
    if os.environ.has_key('SCRIPT_NAME'):
        serveRequest(os.environ)
    else:
        doCommand()

