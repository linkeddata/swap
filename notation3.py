#! /usr/bin/env python
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

RDF_type_URI = "http://www.w3.org/1999/02/22-rdf-syntax-ns#Type"
DAML_equivalentTo_URI = "http://www.daml.org/2000/10/daml-ont#equivalentTo"
Logic_NS = "http://www.w3.org/2000/10/swap/log.n3#"
N3_forSome_URI = Logic_NS + "forSome"
N3_forAll_URI = Logic_NS + "forAll"

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
        self._genPrefix = genPrefix

        if not self._baseURI: self._baseURI = self._thisDoc
        if not self._genPrefix: self._genPrefix = self._thisDoc + "#_g"
        if not self._varPrefix: self._varPrefix = self._thisDoc + "#_v"

    def load(self, uri, _baseURI=""):
        if uri:
            _inputURI = urlparse.urljoin(_baseURI, uri) # Make abs from relative
            print "# Input from ", _inputURI
            netStream = urllib.urlopen(_inputURI)
            self.startDoc()
            self.feed(netStream.read())     # @ May be big - buffered in memory!
            self.endDoc()
        else:
            print "# Taking N3 input from standard input"
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
                raise BadSyntax(str, j, "expected directive or statement")

    def directiveOrStatement(self, str,h):
    
	    i = self.skipSpace(str, h)
	    if i<0: return i   # EOF

	    j = self.directive(str, i)
	    if j>=0: return  self.checkDot(str,j)
	    
            j = self.statement(str, i)
            if j>=0: return self.checkDot(str,j)
            
	    return j


    #@@I18N
    _namechars = string.lowercase + string.uppercase + string.digits + '_'

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
	if str[i:i+len(tok)] == tok:
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
	if i<0: raise BadSyntax(str, j, "expected qname after bind or prefix")
	j = self.uri_ref2(str, i, t)
	if j<0: raise BadSyntax(str, i, "expected uriref2 after bind _qname_")

        ns = t[1][1] + delim
        if string.find(ns,"##")>=0: raise BadSyntax(str, j-2, "trailing # illegal on bind: use @prefix")
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

	if j<0: raise BadSyntax(str, i, "expected propertylist")

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
	    if i < 0: raise BadSyntax(str, j, "expected prop")
	    res.append(('->', r[0]))
	    return i
	else:
	    j = self.tok('is', str, i)
	    if j>=0:
		i = self.prop(str, j, r)
		if i < 0: raise BadSyntax(str, j, "expected prop")
		j = self.tok('of', str, i)
		if j<0: raise BadSyntax(str, i, "expected 'of' after prop")
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
				if j<0: raise BadSyntax(str, i, "-> expected")
				res.append(('->', r[0]))
				return j
			    else:
				j = self.tok('<-', str, i)
				if j>=0:
				    i = self.prop(str, j, r)
				    if i<0: raise BadSyntax(str, j, "bad verb syntax")
				    j = self.tok('<-', str, i)
				    if j<0: raise BadSyntax(str, i, "<- expected")
				    res.append(('<-', r[0]))
				    return j
				else:
				    return self.operator(str, i, res)

    def prop(self, str, i, res):
	return self.node(str, i, res)

    def node(self, str, i, res):
	j = self.uri_ref2(str, i, res)
	if j >= 0:
	    return j
	else:
	    j = self.tok('[', str, i)
	    if j>=0:
                subj = RESOURCE , self._genPrefix + `self._nextId`  #
                self._nextId = self._nextId + 1
                self.makeStatement((self._context, # quantifiers - use inverse?
                                    (RESOURCE, N3_forSome_URI),
                                    self._context,
                                    subj)) # @@@ Note this is anonymous node
                i = self.property_list(str, j, subj)
                if i<0: raise BadSyntax(str, j, "property_list expected")
                j = self.tok(']', str, i)
                if j<0: raise BadSyntax(str, i, "']' expected")
                res.append(subj)
                return j

	    j = self.tok('{', str, i)
	    if j>=0:
                oldContext = self._context
                subj = RESOURCE , self._genPrefix + `self._nextId` # ANONYMOUS - Call out???
                self._nextId = self._nextId + 1  # intern
                self.makeStatement((oldContext, # quantifiers - use inverse?
                                    (RESOURCE, N3_forSome_URI), #pred
                                    oldContext,  #subj
                                    subj))                      # obj

                self._context = subj
                
                while 1:
                    i = self.skipSpace(str, j)
                    if i<0: raise BadSyntax(str, i, "needed '}', found end.")
                    
                    j = self.tok('}', str,i)
                    if j >=0: break
                    
                    j = self.directiveOrStatement(str,i)
                    if j<0: raise BadSyntax(str, i, "expected statement or '}'")

                self._context = oldContext # restore
                res.append(subj)
                return j

            return -1
        
    def property_list(self, str, i, subj):
	while 1:
	    v = []
	    j = self.verb(str, i, v)
	    if j<=0:
		return i # void
	    else:
		objs = []
		i = self.object_list(str, j, objs)
		if i<0: raise BadSyntax(str, j, "object_list expected")
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

            raise BadSyntax(str, j, "expected '.' or '}' or ']' at end of statement")
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
		    raise BadSyntax(str, i, "prefix not bound")
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
            raise BadSyntax(str, j, "unterminated URI reference")
        else:
            return -1

    def skipSpace(self, str, i):
	while 1:
            while i<len(str) and str[i] in string.whitespace:
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
                j = string.find(str, delim, i)
                if j<0: raise BadSyntax(str, i, "unterminated string literal")
                res.append((LITERAL, str[i:j])) # @@@@@ ^decoding escapes
		return j+len(delim)
	    else:
		return -1

    def operator(self, str, i, res):
	j = self.tok('+', str, i)
	if j >= 0:
	    res.append('+') #@@ convert to operator:plus and then to URI
	    return j

	j = self.tok('-', str, i)
	if j >= 0:
	    res.append('-') #@@
	    return j

	j = self.tok('*', str, i)
	if j >= 0:
	    res.append('*') #@@
	    return j

	j = self.tok('/', str, i)
	if j >= 0:
	    res.append('/') #@@
	    return j
	else:
	    return -1

class BadSyntax:
    def __init__(self, str, i, why):
	self._str = str
	self._i = i
	self._why = why

    def __str__(self):
	str = self._str
	i = self._i

	if i>30: pre="..."
	else: pre=""
	if len(str)-i > 30: post="..."
	else: post=""

	return 'bad syntax (%s) at: "%s%s^%s%s"' \
	       % (self._why, pre, str[i-30:i], str[i:i+30], post)





########################## RDF 1.0 Syntax generator
	    
class ToRDF(RDFSink):
    """keeps track of most recent subject, reuses it"""

    def __init__(self, outFp, thisURI):
        RDFSink.__init__(self)
	self._wr = XMLWriter(outFp)
	self._subj = None
	self._thisDoc = thisURI

    #@@I18N
    _namechars = string.lowercase + string.uppercase + string.digits + '_'
    _rdfns = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
    _myns = 'http://www.w3.org/2000/10/n3/notation3.py#'

    def startDoc(self):
	self._wr.startElement('web:RDF',
			      (('xmlns:web', self._rdfns),
			       ('xmlns:g', self._myns)))
	self._subj = None
	self._nextId = 0

    def endDoc(self):
	if self._subj:
	    self._wr.endElement()
	self._subj = None
	self._wr.endElement()

    def makeStatement(self,  tuple):
        context, pred, subj, obj = tuple # Context is ignored
	predn = relativeTo(self._thisDoc, pred)
	subjn = relativeTo(self._thisDoc, subj)

	if self._subj is not subj:
	    if self._subj:
		self._wr.endElement()
	    self._wr.startElement('web:Description',
				 (('about', subjn),))
	    self._subj = subj


	i = len(predn)
	while i>0:
	    if predn[i-1] in self._namechars:
		i = i - 1
	    else:
		break
	ln = predn[i:]
	ns = predn[:i]

	if obj[0] != LITERAL: 
	    objn = relativeTo(self._thisDoc, obj)
	    self._wr.emptyElement(ln,
				 (('xmlns', ns),
				  ('resource', objn)))
	else:
	    self._wr.startElement(ln,
				 (('xmlns', ns),))
	    self._wr.data(obj[1])
	    self._wr.endElement()

# Below is for writing an anonymous node which is the object of only one arc
# This is the arc leading to it.

    def startAnonymous(self,  tuple):
        context, pred, subj, obj = tuple 
	if self._subj is not subj:
	    if self._subj:
		self._wr.endElement()
	    subjn = relativeTo(self._thisDoc, subj)
	    self._wr.startElement('web:Description',
				 (('about', subjn),))
	    self._subj = subj

        predn = pred[1]
	i = len(predn)
	while i>0:
	    if predn[i-1] in self._namechars:
		i = i - 1
	    else:
		break
	ln = predn[i:]
	ns = predn[:i]

        self._wr.startElement(ln, (('xmlns', ns),))  # Parsetype RDF
	    
        self._subj = obj    # The object is now the current subject


    def endAnonymous(self, subject, verb):    # Remind me where we are

        self._wr.endElement()
#        self._subj = subject
        self._subj = None       # @@@ This all needs to be thought about!


# Below we do anonymous top level node - arrows only leave this circle

    def startAnonymousNode(self, subj):
        self._wr.endElement()
        self._wr.startElement('web:Description', ())
        self._subj = subj    # The object is not the subject context
        self._pred = None

    def endAnonymousNode(self):    # Remove context
    	self._wr.endElement()
	self._subj = None
        self._pred = None

# Below we notate a nested bag of statements

    def startBag(self, context):  # Doesn't work with RDF sorry ILLEGAL
        self.indent = self.indent + 1
        self._wr.startElement('web:RDF', # Like description but no subject?
				 (('bagid', context[1])))


    def endBag(self, subj):    # Remove context
        self._write(" }\n")
        self._subj = subj
        self._pred = None
        self.indent = self.indent - 1
     

def relativeTo(here, there):    # algorithm!? @@@@
    nh = here[1]
    l = len(nh)
    nt = there[1]
    if nt[:l] == nh:
	return nt[l:]
    else:
	return nt

########################################### XML Writer

class XMLWriter:
    """ taken from
    Id: tsv2xml.py,v 1.1 2000/10/02 19:41:02 connolly Exp connolly
    """

    def __init__(self, outFp):
	self._outFp = outFp
	self._elts = []

    #@@ on __del__, close all open elements?

    def startElement(self, n, attrs = ()):
	o = self._outFp

	o.write("<%s" % (n,))

	self._attrs(attrs)

	self._elts.append(n)

	o.write("\n%s>" % (' ' * (len(self._elts) * 2) ))

    def _attrs(self, attrs):
	o = self._outFp
	for n, v in attrs:
	    #@@BUG: need to escape markup chars in v
	    o.write("\n%s%s=\"%s\"" \
		    % ((' ' * (len(self._elts) * 2 + 3) ),
		       n, v))

    def emptyElement(self, n, attrs):
	self._outFp.write("<%s" % (n,))
	self._attrs(attrs)
	self._outFp.write("\n%s/>" % (' ' * (len(self._elts) * 2) ))

    def endElement(self):
	n = self._elts[-1]
	del self._elts[-1]
#	self._outFp.write("</%s\n%s>" % (n, (' ' * (len(self._elts) * 2) )))
	self._outFp.write("</%s>\n%s" % (n, (' ' * (len(self._elts) * 2) )))
# Why was the newline before the > initially, danc? 

    markupChar = re.compile(r"[\n\r<>&]")

    def data(self, str):
	#@@ throw an exception if the element stack is empty
	o = self._outFp

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

    def __init__(self, write, base=None, genPrefix = "#_" ):
	self._write = write
	self._subj = None
	self.prefixes = {}      # Look up prefix conventions
	self.indent = 1         # Level of nesting of output
	self.base = base
	self.nextId = 0         # Regenerate Ids on output
	self.regen = {}         # Mapping of regenerated Ids
	self.genPrefix = genPrefix  # Prefix for generated URIs on output

	
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
        self._write(" @prefix %s: <%s> .\n" % (prefixString, nsPair[1]) )
        self._write("    " * self.indent)


    def startDoc(self):
 
        self._write("\n#  Notation3 generation by\n")
        self._write("#  $Id$\n\n")
        self._write("    " * self.indent)
        self._subj = None
        self._nextId = 0

    def endDoc(self):
	self._endStatement()
	self._write("\n")

    def makeComment(self, str):
        for line in string.split(str, "\n"):
            self._write("#" + line + "\n")  # Newline order??@@

    def makeStatement(self, triple):
        self._makeSubjPred(triple[CONTEXT], triple[SUBJ], triple[PRED])        
        self._write(self.representationOf(triple[OBJ]))
#        self._write(" (in %s) " % `context`)    #@@@@
        
# Below is for writing an anonymous node which is the object of only one arc        
    def startAnonymous(self,  triple):
        self._makeSubjPred(triple[CONTEXT], triple[SUBJ], triple[PRED])
        self.indent = self.indent + 1
        self._write(" [ \n"+ "    " * self.indent + "    ")
        self._subj = triple[OBJ]    # The object is now the current subject
        self._pred = None

    def endAnonymous(self, subject, verb):    # Remind me where we are
        self.indent = self.indent - 1
        self._write(" ]")
        self._subj = subject
        self._pred = verb

# Below we do anonymous top level node - arrows only leave this circle

    def startAnonymousNode(self, subj):
	if self._subj:
	    self._write(" .\n")
        self._write("\n  [ "+ "    " * self.indent)
        self._subj = subj    # The object is not the subject context
        self._pred = None

    def endAnonymousNode(self):    # Remove context
        self._write(" ].\n")
        self._subj = None
        self._pred = None

# Below we notate a nested bag of statements

    def startBagSubject(self, context):
	if self._subj != context:
	    self._endStatement()
	else:
	    self._write(" = ")   # hack - for things with contentand properties!
        self.indent = self.indent + 1
        self._write(" { \n"+ "    " * self.indent + "    ")
	self._subj = None
        self._pred = None

    def endBagSubject(self, subj):    # Remove context
        self._write("    " * self.indent + " }\n")
        self._subj = subj
        self._pred = None
        self.indent = self.indent - 1
     
    def startBagObject(self, triple):
        self._makeSubjPred(triple[CONTEXT], triple[SUBJ], triple[PRED])
        self.indent = self.indent + 1
        self._write(" { \n"+ "    " * self.indent + "    ")
	self._subj = None
        self._pred = None

    def endBagObject(self, pred, subj):    # Remove context
        self._write(" }\n")
        self._subj = subj
        self._pred = pred
        self.indent = self.indent - 1
     
    def _makeSubjPred(self, context, subj, pred):
        
	if self._subj != subj:
	    self._endStatement()
	    if self.indent == 1:  # Top level only
                self._write("\n")
                self._write("    " * self.indent)
	    self._write(self.representationOf(subj))
	    self._subj = subj
	    self._pred = None

	if self._pred != pred:
	    if self._pred:
		  self._write(";\n" + "    " * self.indent+ "    ")

            if pred == ( RESOURCE,  DAML_equivalentTo_URI ) :
                self._write(" = ")
            elif pred == ( RESOURCE, RDF_type_URI ) :
                self._write(" a ")
            else :
#	        self._write( " >- %s -> " % self.representationOf(pred))
                self._write( " %s " % self.representationOf(pred))
                
	    self._pred = pred
	else:
	    self._write(",\n" + "    " * (self.indent+3))    # Same subject and pred => object list

    def _endStatement(self):
        if self._subj:
            self._write(" .\n")
            self._write("    " * self.indent)
            self._subj = None

    def representationOf(self, pair):
        """  Representation of a thing in the output stream

        Regenerates genids and variable names if required.
        Uses prefix dictionary to use qname syntax if possible.
        """

#        print "# Representation of ", `pair`
        type, value = pair
        if ((type == VARIABLE or type == ANONYMOUS)
            and not option_noregen ):
                i = self.regen.get(value,self.nextId)
                if i == self.nextId:
                    self.regen[value] = i
                    self.nextId = self.nextId + 1
                if type == ANONYMOUS: return "<"+self.genPrefix + "g" + `i`+">"
                else: return "<" + self.genPrefix + "v" + `i` + ">"   # variable

        if type == LITERAL:
            if string.find(value, "\n") >=0 or string.find(value, '"') >=0:
                return '"""' + value + '"""'
            return '"' + value + '"'   # @@@@ escaping, encoding !!!!!!

        j = string.rfind(value, "#")
        if j>=0:
            prefix = self.prefixes.get((RESOURCE, value[:j+1]), None) # @@ #CONVENTION
            if prefix != None : return prefix + ":" + value[j+1:]
        
            if value[:j] == self.base:   # If local to output stream,
                return "<#" + value[j+1:] + ">" #   use local frag id (@@ lone word?)

        return "<" + value + ">"    # Everything else



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
    thisMessage = 'mid:t%s-r%f@%s' % (time.time(), random.random(), serviceDomain)

    data = form['data'].value

    if form.has_key('genspace'):
	genspace = form['genspace'].value
    else: genspace = thisMessage + '#_'

    if form.has_key('baseURI'):	baseURI = form['baseURI'].value
    elif env.has_key('HTTP_REFERER'): baseURI = env['HTTP_REFERER']
    else: baseURI = None

    # output is buffered so that we only send
    # 200 OK if all went well
    buf = StringIO.StringIO()

    xlate = ToRDFParser(buf, baseURI, thisMessage, genspace)
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
	print "# Base URI of process is" , _baseURI
	
        _outURI = urlparse.urljoin(_baseURI, "STDOUT")
	if option_rdf1out:
            _sink = ToRDF(sys.stdout, _outURI)
        else:
            _sink = ToN3(sys.stdout.write, _outURI)

        
#  Parse and regenerate RDF in whatever notation:

        inputContexts = []
        for i in option_inputs:
            _inputURI = urlparse.urljoin(_baseURI, i) # Make abs from relative
            p = SinkParser(_sink,  _inputURI)
            p.load(_inputURI)
            del(p)

        if option_inputs == []:
            _inputURI = urlparse.urljoin( _baseURI, "STDIN") # Make abs from relative
            print "# Taking input from standard input"
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

