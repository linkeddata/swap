#! /usr/bin/env python
"""
$Id$

cf

http://www.w3.org/DesignIssues/Notation3
Date: 2000/07/17 21:46:13  

DWC:
oops... I'm not doing qname expansion as described
there (i.e. adding a # if it's not already there).

I allow unprefixed qnames, so not all barenames
are keywords.

---- hmmmm ... not expandable - a bit of a trap.

I haven't done quoting yet.

idea: migrate toward CSS notation?

idea: use notation3 for wiki record keeping.

TBL: more cool things:
 - sucking in the schema (http library?) - to know about r see r
 - metaindexes - "to know more about x please see r" - described by
 - equivalence handling inc. equivalence of equivalence
 - @@ regeneration of genids on output.
- regression test - done once
 Shakedown:
 - Find all synonyms of synonym
 - Find closure for all synonyms
 - Find superclass closure?
 - Use unambiguous property to infer synomnyms

 - Separate the store hash table from the parser. (Intern twice?!)
 
 Manipulation:
  { } as notation for bag of statements
  - filter 
  - graph match
  - recursive dump of nested bags
Validation:  validate domain and range constraints against closuer of classes and
   mutually disjoint classes.

Translation;  Try to represent the space (or a context) using a subset of namespaces

"""

import string
import urlparse
import re

# Magic resources we know about

RDF_type_URI = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
DAML_equivalentTo_URI = "http://www.daml.org/2000/10/daml-ont#equivalentTo"

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
    -- maybe later Swell events.  Adapted from printParser
    """
#  Keeps track of prefixes
	    

    def __init__(self):
        self.prefixes = { }     # Convention only - human friendly
        self.namespaces = {}    # Both ways

    def bind(self, prefix, nsPair):
        if not self.prefixes.get(nsPair, None):  # If we don't have a prefix for this ns
            if not self.namespaces.get(prefix,None):   # For conventions
                self.prefixes[nsPair] = prefix
                self.namespaces[prefix] = nsPair
                if chatty: print "# RDFSink: Bound %s to %s" % (prefix, ns[1])
            else:
                self.bind(prefix+"g1", nsPair) # Recurive
        
    def makeStatement(self, tuple):  # Quad of (type, value) pairs
        pass

    def startDoc(self):
        print "sink: start.\n"

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
	self._context = RESOURCE , self._thisDoc    # For storing with triples
        self._contextStack = []      # For nested conjunctions { ... }
        self._varPrefix = varPrefix
        self._nextId = 0
        self._genPrefix = genPrefix

        if not self._baseURI: self._baseURI = self._thisDoc
        if not self._genPrefix: self._genPrefix = self._thisDoc + "#_g"
        if not self._varPrefix: self._varPrefix = self._thisDoc + "#_v"

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
	j = self.tok('bind', str, i)
	if j<0: return -1
	t = []
	i = self.qname(str, j, t)
	if i<0: raise BadSyntax(str, j, "expected qname after bind")
	j = self.uri_ref2(str, i, t)
	if j<0: raise BadSyntax(str, i, "expected uriref2 after bind _qname_")

	self._bindings[t[0][0]] = t[1][1]
	self.bind(t[0][0], t[1])
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
                subj = ANONYMOUS , self._genPrefix + `self._nextId`
                self._nextId = self._nextId + 1  # intern
                i = self.property_list(str, j, subj)
                if i<0: raise BadSyntax(str, j, "property_list expected")
                j = self.tok(']', str, i)
                if j<0: raise BadSyntax(str, i, "']' expected")
                res.append(subj)
                return j

	    j = self.tok('{', str, i)
	    if j>=0:
                oldContext = self.context
                subj = ANONYMOUS , self._genPrefix + `self._nextId`
                self._nextId = self._nextId + 1  # intern
                self.context = subj
                
                while 1:
                    i = self.skipSpace(str, j)
                    if i<0: raise BadSyntax(str, i, "needed '}', found end.")
                    
                    j = self.tok('}', str,i)
                    if j >=0: break
                    
                    j = self.directiveOrStatement(str,i)
                    if j<0: raise BadSyntax(str, i, "expected statement or '}'")

                self.context = oldContext # restore
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

            print "# N3: expected '.' in %s^%s" %(str[i-30:i], str[i:i+30])
            return i


    def uri_ref2(self, str, i, res):
	#hmm... intern the resulting symbol?
	qn = []
	j = self.qname(str, i, qn)
	if j>=0:
	    pfx, ln = qn[0]
	    if pfx is None:
		ns = self._thisDoc
	    else:
		try:
		    ns = self._bindings[pfx]
		except KeyError:
		    raise BadSyntax(str, i, "prefix not bound")
#	    res.append(internFrag(ns, ln))
            res.append( RESOURCE, ns+ "#" + ln)
	    return j

        v = []
        j = self.variable(str,i,v)
        if j>0:
#            res.append(internVariable(self._thisDoc,v[0]))
            res.append(VARIABLE, v[0])
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
                    res.append(RESOURCE , uref)
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
		i = i + 1
		st = i
		while i < len(str):
		    if str[i] == '"':
			res.append(LITERAL, str[st:i])
			return i+1
		    i = i + 1
		raise BadSyntax(str, i, "unterminated string literal")
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
bind pp: <http://example.org/payPalStuff?>.
bind default <http://example.org/payPalStuff?>.

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
bind default <>

:assumption = { :fred u:knows :john .
                :john u:knows :mary .} .

:conclusion = { :fred u:knows :mary . } .

"""
    thisURI = "file:notation3.py"
    thisDoc = thisURI
    testString.append(  t0 + t1 + t2 + t3 + t4 )
#    testString.append(  t5 )

#    p=SinkParser(RDFSink(),'http://example.org/base/', 'file:notation3.py',
#		     'data:#')

    r=SinkParser(SinkToN3(sys.stdout.write, 'file:output'),
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

    print "----------------------- Test store:"

    testEngine = Engine()
    store = RDFStore(testEngine)
    # (sink,  thisDoc,  baseURI, bindings)
    p = SinkParser(store,  thisURI, 'http://example.org/base/')
    p.startDoc()
    p.feed(testString[0])
    p.endDoc()

    print "\n\n------------------ dumping chronologically:"

    store.dumpChronological(thisDoc, SinkToN3(sys.stdout.write, thisURI))

    print "\n\n---------------- dumping in subject order:"

    store.dumpBySubject(thisDoc, SinkToN3(sys.stdout.write, thisURI))

    print "\n\n---------------- dumping nested:"

    store.dumpNested(thisDoc, SinkToN3(sys.stdout.write, thisURI))

    print "Regression test **********************************************"

    
    testString.append(reformat(testString[-1], thisDoc))

    if testString[-1] == testString[-2]:
        print "\nRegression Test succeeded FIRST TIME- WEIRD!!!!??!!!!!\n"
        return
    
    testString.append(reformat(testString[-1], thisDoc))

    if testString[-1] == testString[-2]:
        print "\nRegression Test succeeded SECOND time!!!!!!!!!\n"
    else:
        print "Regression Test Failure: ===================== LEVEL 1:"
        print testString[1]
        print "Regression Test Failure: ===================== LEVEL 2:"
        print testString[2]
        print "\n============================================= END"

    testString.append(reformat(testString[-1], thisDoc))
    if testString[-1] == testString[-2]:
        print "\nRegression Test succeeded THIRD TIME. This is not exciting.\n"

    
                
def reformat(str, thisDoc):
    if 0:
        print "Regression Test: ===================== INPUT:"
        print str
        print "================= ENDs"
    buffer=StringWriter()
    r=SinkParser(SinkToN3(buffer.write, `thisDoc`),
                  'file:notation3.py')
    r.startDoc()
    r.feed(str)
    r.endDoc()
    return buffer.result()
    


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
        pred, subj, obj = tuple
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

	if not isinstance(obj, Literal): 
	    objn = relativeTo(self._thisDoc, obj)
	    self._wr.emptyElement(ln,
				 (('xmlns', ns),
				  ('resource', objn)))
	else:
	    self._wr.startElement(ln,
				 (('xmlns', ns),))
	    self._wr.data(obj)
	    self._wr.endElement()

def relativeTo(here, there):    # algorithm!? @@@@
    nh = `here`
    l = len(nh)
    nt = `there`
    if nt[:l] == nh:
	return nt[l:]
    else:
	return nt



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
	self._outFp.write("</%s\n%s>" % (n, (' ' * (len(self._elts) * 2) )))

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


#   A word about regenerated Ids.
#
# Within the program, the URI of a resource is kept the same, and in fact
# tampering with it would leave risk of all kinds of inconsistencies.
# Hwoever, on output, where there are URIs whose values are irrelevant,
# such as variables and generated IDs from anonymous ndoes, it makes the
# document very much more readable to regenerate the IDs.
#  We use here a convention that underscores at the start of fragment IDs
# are reserved for generated Ids. The caller can change that.

class SinkToN3(RDFSink):
    """keeps track of most recent subject and predicate reuses them

      Adapted from Dan's ToRDFParser(Parser);
    """

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
        self._write(" bind %s: <%s> .\n" % (prefixString, nsPair[1]) )

    def startDoc(self):
 
        self._write("\n#  Start notation3 generation\n")
        self._write("#  $Id$\n\n")
        self._subj = None
        self._nextId = 0

    def endDoc(self):
	self._endStatement()

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

    def startBag(self, context):
        self.indent = self.indent + 1
        self._write(" { \n"+ "    " * self.indent + "    ")

    def endBag(self, subj):    # Remove context
        self._write(" }\n")
        self._subj = subj
        self._pred = None
        self.indent = self.indent - 1
     
    def _makeSubjPred(self, context, subj, pred):
        
	if self._subj != subj:
	    self._endStatement()
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
            return '"' + value + '"'   # @@@@ encoding !!!!!!

        j = string.rfind(value, "#")
        if j>=0:
            str = self.prefixes.get(value[:j], None)
            if str != None : return str + ":" + value[j+1:]
            if j==0: return "<#" + value[j+1:] + ">"
                
        return "<" + value + ">"    # Everything else

    
class StringWriter:

    def __init__(self):
        self.buffer = ""

    def write(self, str):
        self.buffer = self.buffer + str     #  No idea how to make this efficient in python

    def result(self):
        return self.buffer

    def clear(self):
        self.buffer = ""
        



########################################  Storage URI Handling
#
#  In general an RDf resource - here a Thing, has a uriRef rather
# than just a URI.  It has subclasses of Resource and Fragment.
# (libwww equivalent HTParentAnchor and HTChildAnchor IIRC)
#
# Every resource has a symbol table of fragments.
# A resource may (later) have a connection to a bunch of parsed stuff.
#
# We are nesting symbols two deep let's make a symbol table for each resource
#
#  The statement store lists are to reduce the search time
# for triples in some cases. Of course, indexes would be faster.
# but we can figure out what to optimize later.  The target for now
# is being able to find synonyms and so translate documents.

        
class Thing:
    def __init__(self):
      self.occursAs = [], [], [], []  #  List of statements in store by part of speech       
            
    def __repr__(self):   # only used for debugging I think
        return self.representation()

    def representation(self, base=None):
        """ in N3 """
        return "<" + self.uriref(base) + ">"

    def generated(self):
        """  Is this thing a genid - is its name arbitrary? """
        return 0    # unless overridden

    def n3_anonymous(self, context):
        """ Can be output as an anonymous node in N3
        """
        return (self.generated() and  # The URI is irrelevant
            self.occurrences(OBJ,context) == 1 and  # This is only incoming arrow
            self.occurrences(PRED, context) == 0 )    # It is not used as a verb itself

    def asPair(self):
        return (RESOURCE, self.uriref(None))
    
    def occurrences(self, p, context):
        """ Count the times a thing occurs in a statement in given context
        """
        if context == None:   # meaning any
            return len(self.occursAs[p])
        else:
            n = 0
            for s in self.occursAs[p]:
                if s.triple[CONTEXT] is context:
                    n = n+1
            return n

class Resource(Thing):
    """   A Thing which has no fragment
    """
    
    def __init__(self, uri):
        Thing.__init__(self)
        self.uri = uri
        self.fragments = {}

    def uriref(self, base):
        if base is self :  # @@@@@@@ Really should generate relative URI!
            return ""
        else:
            return self.uri

    def internFrag(r,fragid):
            f = r.fragments.get(fragid, None)
            if f: return f
            f = Fragment(r, fragid)
            r.fragments[fragid] = f
            return f
                
    def internAnonymous(r, fragid):
            f = r.fragments.get(fragid, None)
            if f: return f
            f = Anonymous(r, fragid)
            r.fragments[fragid] = f
            return f
                
    def internVariable(r, fragid):
            f = r.fragments.get(fragid, None)
            if f: return f
            f = Variable(r, fragid)
            r.fragments[fragid] = f
            return f
                
    
class Fragment(Thing):
    """    A Thing which DOES have a fragment id in its URI
    """
    def __init__(self, resource, fragid):
        Thing.__init__(self)

        self.resource = resource
        self.fragid = fragid

    def uriref(self, base):
        return self.resource.uriref(base) + "#" + self.fragid

    def representation(self,  base=None):
        """ Optimize output if prefixes available
        """
        return  "<" + self.uriref(base) + ">"

    def generated(self):
         """ A generated identifier?
         This arises when a document is parsed and a arbitrary
         name is made up to represent a node with no known URI.
         It is useful to know that its ID has no use outside that
         context.
         """
         return self.fragid[0] == "_"  # Convention for now @@@@@
                                # parser should use seperate class?


class Anonymous(Fragment):
    def __init__(self, resource, fragid):
        Fragment.__init__(self, resource, fragid)

    def generated(self):
        return 1

    def asPair(self):
        return (ANONYMOUS, self.uriref(None))
        
class Variable(Fragment):
    def __init__(self, resource, fragid):
        Fragment.__init__(self, resource, fragid)

    def asPair(self):
        return (VARIABLE, self.uriref(None))
        
class Literal(Thing):
    """ A Literal is a data resource to make it clean

    really, data:application/n3;%22hello%22 == "hello" but who
    wants to store it that way?  Maybe we do... at least in theory and maybe
    practice but, for now, we keep them in separate subclases of Thing.
    """
    Literal_URI_Prefix = "data:application/n3;"

    def __init__(self, string):
        Thing.__init__(self)
        self.string = string    #  n3 notation EXcluding the "  "

    def __repr__(self):
        return self.string

    def asPair(self):
        return (LITERAL, self.string)

    def representation(self, base=None):
        return '"' + self.string + '"'   # @@@ encode quotes; @@@@ strings containing \n

    def uriref(self, base=None):      # Unused at present but interesting! 2000/10/14
        return  Literal_URI_Prefix + uri_encode(self.representation())

def uri_encode(str):
        """ untested - this must be in a standard library somewhere
        """
        result = ""
        i=0
        while i<len(str) :
            if string.find('"\'><"', str[i]) <0 :   # @@@ etc
                result.append("%%%2x" % (atoi(str[i])))
            else:
                result.append(str[i])
        return result

####################################### Engine
    
class Engine:
    """ The root of the references in the system -a set of things and stores
    """

    def __init__(self):
        self.resources = {}    # Hash table of URIs for interning things
        
        
    def intern(self, pair):
        """  Returns either a Fragment or a Resource as appropriate

    This is the way they are actually made.
    """
        type, uriref = pair
        if type == LITERAL:
            return Literal(uriref)  # No interning for literals (?@@?)

#        print " ... interning <%s>" % `uriref`
        hash = len(uriref)-1
        while (hash >= 0) and not (uriref[hash] == "#"):
            hash = hash-1
        if hash < 0 :     # This is a resource with no fragment
            r = self.resources.get(uriref, None)
            if r: return r
            r = Resource(uriref)
            self.resources[uriref] = r
            return r
        
        else :      # This has a fragment and a resource
            r = self.intern((RESOURCE, uriref[:hash]))
            if type == RESOURCE:  return r.internFrag(uriref[hash+1:])
            if type == ANONYMOUS: return r.internAnonymous(uriref[hash+1:])
            if type == VARIBALE:  return r.internVariable(uriref[hash+1:])


######################################################## Storage
# The store uses an index in the interened resource objects.
#
#   store.occurs[context, thing][partofspeech]   dict, list, ???


class StoredStatement:

    def __init__(self, q):
        self.triple = q
        
class RDFStore(RDFSink) :
    """ Absorbs RDF stream and saves in triple store
    """

    def __init__(self, engine):
        RDFSink.__init__(self)
        self.engine = engine

# Input methods:

    def makeStatement(self, tuple):
        q = ( self.engine.intern(tuple[CONTEXT]),
              self.engine.intern(tuple[PRED]),
              self.engine.intern(tuple[SUBJ]),
              self.engine.intern(tuple[OBJ]) )
        s = StoredStatement(q)
        for p in ALL4: s.triple[p].occursAs[p].append(s)
                    
    def startDoc(self):
        pass

    def endDoc(self):
        pass

    def selectDefaultPrefix(self, context):

        """ Resource whose fragments have the most occurrences
        """
        best = 0
        mp = None
        for r in self.engine.resources.values() :
            total = 0
            for f in r.fragments.values():
                total = total + (f.occurrences(PRED,context)+
                                 f.occurrences(SUBJ,context)+
                                 f.occurrences(OBJ,context))

            if total > 3 and chatty:
                print "#   Resource %s has %i occurrences in %s" % (`r`, total, `context`)
            if total > best :
                best = total
                mp = r
        if chatty: print "# Most popular Namesapce in %s is %s" % (`context`, `mp`)
        defns = self.namespaces.get("", None)
        if defns :
            del self.namespaces[""]
            del self.prefixes[defns]
        if self.prefixes.has_key(mp) :
            oldp = self.prefixes[mp]
            del self.prefixes[mp]
            del self.namespaces[oldp]
        self.prefixes[mp] = ""
        self.namespaces[""] = mp
        
# Manipulation methods:

    def moveContext(self, old, new):
        for s in old.occursAs[CONTEXT] :
            t = s.triple
#            print "Quad:", `s.triple`, "Old, new:",`old`, `new`
            s.triple = new, t[PRED], t[SUBJ], t[OBJ]
            old.occursAs[CONTEXT].remove(s)
            
            
    def copyContext(self, old, new):
        for s in self.statements :
            if s.triple[CONTEXT] == old:
                self.makeStatement((new, s.triple[PRED], s.triple[SUBJ], s.triple[OBJ]))
            
# Output methods:

    def dumpChronological(self, contextURI, sink):
        """ Ignores contexts
        """
        context = self.engine.intern((RESOURCE, contextURI))
        sink.startDoc()
        for c in self.prefixes.items():   #  bind in same way as input did FYI
            sink.bind(c[1], c[0])
        for s in context.occursAs[CONTEXT]:
#        for s in self.statements :
            self._outputStatement(sink, s)
        sink.endDoc()

    def _outputStatement(self, sink, s):
        t = s.triple
        sink.makeStatement(self.extern(t))

    def extern(self, t):
        return(t[CONTEXT].asPair(),
                            t[PRED].asPair(),
                            t[SUBJ].asPair(),
                            t[OBJ].asPair(),
                            )

    def dumpBySubject(self, contextURI, sink):

        context = self.engine.intern((RESOURCE, contextURI))
        self.selectDefaultPrefix(context)        
        sink.startDoc()
        for c in self.prefixes.items() :   #  bind in same way as input did FYI
            sink.bind(c[1], c[0])

        for r in self.engine.resources.values() :  # First the bare resource
            for s in r.occursAs[SUBJ] :
                if context is s.triple[CONTEXT]:
                    self._outputStatement(sink, s)
            for f in r.fragments.values() :  # then anything in its namespace
                for s in f.occursAs[SUBJ] :
#                    print "...dumping %s in context %s" % (`s.triple[CONTEXT]`, `context`)
                    if s.triple[CONTEXT] is context:
                        self._outputStatement(sink, s)
        sink.endDoc()
#
#  Pretty printing
#
    def dumpNested(self, contextURI, sink):
        """ Iterates over all URIs ever seen looking for statements
        """
        context = self.engine.intern((RESOURCE, contextURI))
        self.selectDefaultPrefix(context)        
        sink.startDoc()
        for c in self.prefixes.items() :   #  bind in same way as input did FYI
            sink.bind(c[1], c[0])
        print "# RDFStore: Done bindings, doing arcs:" 
        for r in self.engine.resources.values() :  # First the bare resource
            self._dumpSubject(r, context, sink)
            for f in r.fragments.values() :  # then anything in its namespace
                self._dumpSubject(f, context, sink)
        sink.endDoc()


    def _dumpSubject(self, subj, context, sink):
        """ Take care of top level anonymous nodes
        """
        print "%s occures %i as context, %i as pred, %i as subj, %i as obj" % (
            `subj`, subj.occurrences(CONTEXT, None),
            subj.occurrences(PRED,context), subj.occurrences(SUBJ,context),
            subj.occurrences(OBJ, context))
        if (subj.generated() and  # The URI is irrelevant
                subj.occurrences(OBJ,context) == 0 and  # There is no incoming arrow
                subj.occurrences(PRED,context) == 0 ):    # It is not used as a verb itself
            if subj.occurrences(SUBJ,context) > 0 :   # Ignore if actually no statements for this thing
                sink.startAnonymousNode(subj.asPair())
                for s in subj.occursAs[SUBJ]:
                    if s.triple[CONTEXT] is context:
                        self.coolMakeStatement(sink, s)
                sink.endAnonymousNode()
            if subj.occurrences(CONTEXT, None) > 0:  # @@@ only dumps of no statemenst about it
                sink.startBag(subj)
                raise theRoof
                self.dumpNested(subj, sink)  # dump contents of anonymous bag
                sink.endBag(subj)

        else:
            for s in subj.occursAs[SUBJ]:
                if s.triple[CONTEXT] is context:
                    self.coolMakeStatement(sink, s)

    def coolMakeStatement(self, sink, s):
        triple = s.triple
        if triple[SUBJ] is triple[OBJ]:
            self.outputStatement(s)
        else:
            if not triple[SUBJ].n3_anonymous(triple[CONTEXT]):  # Don't repeat
                self.coolMakeStatement2(sink, s)
                
    def coolMakeStatement2(self, sink, s):
        triple = s.triple
        if triple[OBJ].n3_anonymous(triple[CONTEXT]):  # Can be represented as anonymous node in N3
            sink.startAnonymous( self.extern(triple))
            for t in triple[OBJ].occursAs[SUBJ]:
                if t.triple[CONTEXT] is triple[CONTEXT]:
                    self.coolMakeStatement2(sink, t)
            sink.endAnonymous(triple[SUBJ].asPair(), triple[PRED].asPair) # Restore context
        else:    
            self._outputStatement(sink, s)
                


            
class RDFTriple:
    
    def __init__(self, triple):
        self.triple = triple
        triple[SUBJ].occursAs[SUBJ].append(self)   # Resource index
        triple[PRED].occursAs[PRED].append(self)   # Resource index
        triple[OBJ].occursAs[OBJ].append(self)     # Resource index
        triple[CONTEXT].occursAs[CONTEXT].append(self) #


############################################################## Query engine

# Template matching in a graph

    

INFINITY = 1000000000           # @@ larger than any number occurences
def match (unmatched, action, param, bindings = [], newBindings = [] ):

        """ Apply action(bindings, param) to succussful matches
    bindings      collected matches alreday found
    newBindings  matches found and not yet applied - used in recursion
        """
# Scan terms to see what sort of a problem we have:
#
# We prefer terms with a single variable to those with two.
# (Those with none we immediately check and therafter ignore)
# Secondarily, we prefer short searches to long ones.

        total = 0           # Number of matches found (recursively)
        shortest = INFINITY
        shortest_t = None
        found_single = 0   # Singles are better than doubles
        unmatched2 = unmatched[:] # Copy so we can remove() while iterating :-(

        for pair in newBindings:
            bindings.append(pair)  # Record for posterity
            for t in unmatched:     # Replace variables with values
                for p in SUBJ, PRED, OBJ:
                    if t[p] is pair[0] : t[p] = pair[1]
        
        for t in unmatched:
            vars = []       # Count where variables are
            q = []          # Count where constants are
            short_p = -1
            short = INFINITY
            for p in PRED, SUBJ, OBJ:
                r = t.triple[p]
                if isinstance(r,Variable):
                    vars.append(r)
                else:
                    if r.occurs[p]< short:
                        short_p = p
                        short = r.occurs[p]
                        consts.append(p)

            if short == 0: return 0 # No way we can satisfy that one - quick "no"

            if len(vars) == 0: # This is an independant constant triple
                          # It has to match or the whole thing fails
                 
                for s in r.occursAs[short_p]:
                    if (s.triple[q[0]] is t.triple[q[0]]
                        and s.triple[q[1]] is t.triple[q[1]]):
                            unmatched2.remove(t)  # Ok - we believe it - ignore it
                    else: # no match for a constant term: query fails
                        return 0
                
            elif len(vars) == 1: # We have a single variable.
                if not found_single or short < shortest :
                    shortest = short
                    shortest_p = short_p
                    shortest_t = t
                    found_single = 1
                
            else:   # Has two variables
                if not found_single and short < shortest :
                    shortest = short
                    shortest_p = short_p
                    shortest_t = t

        if len(unmatched2) == 0:
            print "Found for bindings: ", bindings
            action(bindings, param)  # No terms left .. success!
            return 1

        # Now we have identified the best statement to search for
        t = shortest_t
        parts_to_search = [ PRED, SUBJ, OBJ ]
        unmatched2.remove(t)  # We will resolve this one now

        q = []   # Parts of speech to test for match
        v = []   # Parts of speech which are variables
        for p in [PRED, SUBJ, OBJ] :
            if isinstance(t.triple[p], Variable):
                parts_to_search.remove(p)
                v.append(p)
            elif p != shortest_p :
                q.append(p)

        if found_single:        # One variable, two constants - must search
            for s in t.occursAs[shortest_p]:
                if s.triple[q[0]] is t.triple[q[0]]: # Found this one
                    total = total + match(unmatched2, action, param,
                                          bindings, [ s.triple[pv], s.triple[pv] ])
            
        else: # Two variables, one constant. Every one in occurrence list will be good
            for s in t.occursAs[shortest_p]:
                total = total + matches(unmatched2, action, param, bindings,
                                        [ t.triple[v[0]], s.triple[v[0]]],
                                        [ t.triple[v[1]], s.triple[v[1]]])
            
        return total
         
                            
                    
            
        
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
 
 -rdf1out   Output in RDF M&S 1.0 insead of n3
 -pipe      Don't store, just pipe out *
 -ugly      Store input and regurgitate *
 -bySubject Store inpyt and regurgitate in subject order *
            (default is to store and pretty print with anonymous nodes) *
 -help      print this message
 -chatty    Verbose output of questionable use

            * mutually exclusive
 
"""
        
        import urllib
        option_ugly = 0     # Store and regurgitate with genids *
        option_pipe = 0     # Don't store, just pipe though
        option_rdf1out = 0  # Output in RDF M&S 1.0 instead of N3
        option_bySubject= 0 # Store and regurgitate in subject order *
        option_inputs = []
        chatty = 0          # not too verbose please
        hostname = "localhost" # @@@@@@@@@@@ Get real one
        
        for arg in sys.argv[1:]:  # Command line options after script name
            if arg == "-test": return test()
            elif arg == "-ugly": option_ugly = 1
            elif arg == "-pipe": option_pipe = 1
            elif arg == "-bySubject": option_bySubject = 1
            elif arg == "-rdf1out": option_rdf1out = 1
            elif arg == "-chatty": chatty = 1
            elif arg == "-help":
                print doCommand.__doc__
                return
            elif arg[0] == "-": print "Unknown option", arg
            else : option_inputs.append(arg)

        # The base URI for this process - the Web equiv of cwd
#	_baseURI = "file://" + hostname + os.getcwd() + "/"
	_baseURI = "file://" + os.getcwd() + "/"
	print "# Base URI of process is" , _baseURI
	
        _outURI = urlparse.urljoin(_baseURI, "STDOUT")
	if option_rdf1out:
            _outSink = ToRDF(sys.stdout, _outURI)
        else:
            _outSink = SinkToN3(sys.stdout.write, _outURI)

        if option_pipe:
            _sink = _outSink
        else:
            _sink = RDFStore()
        
#  Suck up the input information:

        inputContexts = []
        for i in option_inputs:
            _inputURI = urlparse.urljoin(_baseURI, i) # Make abs from relative
            inputContexts.append(intern(_inputURI))
            print "# Input from ", _inputURI
            netStream = urllib.urlopen(_inputURI)
            p = SinkParser(_sink,  _inputURI)
            p.startDoc()
            p.feed(netStream.read())     # May be big - buffered in memory!
            p.endDoc()
        # note we can't do it in chunks as p stores no state between feed()s
            del(p)
        if option_inputs == []:
            _inputURI = urlparse.urljoin( _baseURI, "STDIN") # Make abs from relative
            inputContexts.append(intern(_inputURI))
            print "# Taking input from standard input"
            p = SinkParser(_sink,  _inputURI)
            p.startDoc()
            p.feed(sys.stdin.read())     # May be big - buffered in memory!
            p.endDoc()
            del(p)

        if option_pipe: return                # everything was done inline

# Manpulate it as directed:

        outputContext = intern(_outURI)
        for i in inputContexts:
            _sink.moveContext(i,outputContext)
            
#@@@@@@@@@@@ problem of deciding which contexts to dump and dumping > 1
                #@@@ or of merging contexts

# Squirt it out again as directed
        
        if not option_pipe:
            if option_ugly:
                _sink.dumpChronological(outputContext, _outSink)
            elif option_bySubject:
                _sink.dumpBySubject(outputContext, _outSink)
            else:
                _sink.dumpNested(outputContext, _outSink)
                

############################################################ Main program
    
if __name__ == '__main__':
    import os
    import urlparse
    if os.environ.has_key('SCRIPT_NAME'):
        serveRequest(os.environ)
    else:
        doCommand()

