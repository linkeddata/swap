#!/usr/local/bin/python
"""
$Id$

cf

http://www.w3.org/DesignIssues/Notation3
Date: 2000/07/17 21:46:13  

oops... I'm not doing qname expansion as described
there (i.e. adding a # if it's not already there).

I allow unprefixed qnames, so not all barenames
are keywords.

---- hmmmm ... not expandable - a bit of a trap.

I haven't done quoting yet.

idea: migrate toward CSS notation?

idea: use notation3 for wiki record keeping.

T: more cool things:
 - sucking in the schema (http library?)
 - metaindexes - "to know more about x please see r" - described by
 - equivalence handling inc. equivalence of equivalence
 - @@ regeneration of genids on output.
- regression test! 
 Shakedown:
 - Find all synonyms of synonym
 - Find closure for all synonyms
 - Find superclass closure?
 - Use unambiguous property to infer synomnyms

Validation:  validate domain and range constraints against closuer of classes and
   mutually disjoint classes.

Translation;  Try to represent the space (or a context) using a subset of namespaces

"""

import string
import urlparse
import re


PRED = 0  # offsets when a statement is stored as a Python triple (p, s, o)
SUBJ = 1
OBJ = 2
PARTS = [ PRED, SUBJ, OBJ]

class Parser:
    def __init__(self, baseURI, thisDoc, genBase, bindings = {}):
	""" note: namespace names should *not* end in #;
	the # will get added during qname processing """
	self._baseURI = baseURI
	self._genBase = genBase
	self._bindings = bindings
	self._nextID = 0
	self._thisDoc = intern(thisDoc)
	self.context = self._thisDoc    # For storing with triples


    def feed(self, str):
	"""if BadSyntax is raised, the string
	passed in the exception object is the
	remainder after any statements have been parsed.
	So if there is more data to feed to the
	parser, it should be straightforward to recover."""

	while len(str)>0:
	    i = self.skipSpace(str, 0)
	    if i<0: return

	    j = self.directive(str, i)
	    if j<0:
		j = self.statement(str, i)
		if j<0:
		    raise BadSyntax(str, i, "expected directive or statement")
	    str = str[j:]

    def makeStatement(self, context, triple):
	pass

    #@@I18N
    _namechars = string.lowercase + string.uppercase + string.digits + '_'

    def tok(self, tok, str, i):
	while i<len(str) and str[i] in string.whitespace:
	    i = i + 1
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

	self._bindings[t[0][0]] = t[1]
	self.bind(t[0][0], t[1])
	return j

    def bind(self, qname, resource):
        pass                            # Hook for subclasses

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
	    r = []
	    j = self.tok('[', str, i)
	    if j<0: return -1
	    subj = self.genURI()
	    i = self.property_list(str, j, subj)
	    if i<0: raise BadSyntax(str, j, "property_list expected")
	    j = self.tok(']', str, i)
	    if j<0: raise BadSyntax(str, i, "] expected")
	    res.append(subj)
	    return j


    def genURI(self):  # @@ genids should be regenerated on output
	self._nextID = self._nextID + 1
	return intern(self._genBase + `self._nextID`)


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
			self.makeStatement(self.context, (sym, subj, obj))
		    else:
			self.makeStatement(self.context, (sym, obj, sym))

		j = self.tok(';', str, i)
		if j<0:
		    return i
		i = j

    def object_list(self, str, i, res):
	i = self.object(str, i, res)
	if i<0: return -1
	while 1:
	    j = self.tok(',', str, i)
	    if j<0: return i
	    i = self.object(str, j, res)

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
	    res.append(internFrag(ns, ln))
	    return j
	else:
	    j = self.skipSpace(str, i)
	    if j<0: return -1
	    else: i=j

	    if str[i]=="<":
		i = i + 1
		st = i
		while i < len(str):
		    if str[i] == ">":
			uref = str[st:i]
			if uref == '':
			    sym = self._thisDoc
			else:
			    if self._baseURI:
				uref=urlparse.urljoin(self._baseURI, uref)
			    #@@else: if it's not absolute, BadSyntax
			    sym = intern(uref)
			res.append(sym)
			return i+1
		    i = i + 1
		raise BadSyntax(str, o, "unterminated URI reference")
	    else:
		return -1

    def skipSpace(self, str, i):
	while i<len(str) and str[i] in string.whitespace: i = i + 1
	if i == len(str): return -1
	return i

    def qname(self, str, i, res):
	"""
	xyz:def -> ('xyz', 'def')
	def -> ('', 'def')                   @@@@
	:def -> (None, 'def')
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
	    ln = None

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
			res.append(Literal(str[st:i]))
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

	return "bad syntax (%s) at: %s%s^%s%s" \
	       % (self._why, pre, str[i-30:i], str[i:i+30], post)



class SinkParser(Parser):
    """Parses notation3 and outputs RDF stream to sink"""

    def __init__(self, sink, baseURI, thisDoc, genBase, bindings = {}):
	Parser.__init__(self, baseURI, thisDoc, genBase, bindings)
	self._sink = sink

    def bind(self, qname, uriref):
        self._sink.bind(qname, uriref)                            # Hook for subclasses

    def startDoc(self):
        self._sink.startDoc()

    def endDoc(self):
        self._sink.endDoc()

    def makeStatement(self, context, triple):
        self._sink.makeStatement(context, triple)

#####
# Symbol support
# taken from imap_sort.py
class Symbol:
    symtab = {}

    def __init__(self, name):
	self._name = name

    def __str__(self):
	return self._name

    def __repr__(self):
	return self._name

def intern_old(str):
    try:
	return Symbol.symtab[str]
    except KeyError:
	sym = Symbol(str)
	Symbol.symtab[str] = sym
	return sym


########################################################  URI Handling
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
        self.occursAs = [], [], []  #  List of statements in store by part of speech       
            
    def __repr__(self):   # only used for debugging I think
        return self.representation()

    def representation(self, prefixes = {}, base=None):
        """ in N3 """
        return "<" + self.uriref(base) + ">"

    def generated(self):
        """  Is this thing a genid - is its name arbitrary? """
        return None    # unless overridden

    def n3_anonymous(self):
        """ Can be output as an anonymous node in N3
        """
        return (self.generated() and  # The URI is irrelevant
            len(self.occursAs[OBJ]) == 1 and  # This is only incoming arrow
            len(self.occursAs[PRED]) == 0 )    # It is not used as a verb itself

    def equivalent(self, x):
        """ Find one reason for beliveing them equivalent

        Could search from subject, verb, or object, or find shortest. 
        """
        for s in DAML_equivalentTo.occursAs[PRED].items():
            if ((s.object is self and s.subject is x) or
                (s.subject is self and s.object is x)):
                return s
        return None

class Resource(Thing):
    """   A Thing which has no fragment
    """
    table = {} # Table of resources
    
    def __init__(self, uri):
        Thing.__init__(self)
        self.uri = uri
        self.fragments = {}

    def uriref(self, base):
        if base is self :  # @@@@@@@ Really should generate relative URI!
            return ""
        else:
            return self.uri

def mostPopular():
        """ Resource whose fragments have the most occurrences
        """
        best = 0
        mp = None
        for r in Resource.table.values() :
            total = 0
            for f in r.fragments.values():
                total = total + len(f.occursAs[SUBJ]) + len(f.occursAs[PRED]) + len(f.occursAs[OBJ])
            if total > best :
                best = total
                mp = r
        return mp
        
    
class Fragment(Thing):
    """    A Thing which DOES have a fragment id in its URI
    """
    def __init__(self, resource, fragid):
        Thing.__init__(self)

        self.resource = resource
        self.fragid = fragid

    def uriref(self, base):
        return self.resource.uriref(base) + "#" + self.fragid

    def representation(self, prefixes = {}, base=None):
        """ Optimize output if prefixes available
        """
        try:
            return prefixes[self.resource] + ":" + self.fragid;
        except KeyError:
            return  "<" + self.uriref(base) + ">"

    def generated(self):
         """ A generated identifier?
         This arises when a document is parsed and a arbitrary
         name is made up to represent a node with no known URI.
         It is useful to know that its ID has no use outside that
         context.
         """
         return self.fragid[0] == "_"  # Convention for now @@@
        
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

    def representation(self, prefixes = {}, base=None):
        return '"' + self.string + '"'

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

    
def intern(uriref):
    """  Returns either a Fragment or a Resource as appropriate

This is the way they are actually made.
"""
    hash = len(uriref)-1
    while (hash >= 0) and not (uriref[hash] == "#"):
        hash = hash-1
    if hash < 0 :     # This is a resource with no fragment
        try:
            return Resource.table[uriref]
        except KeyError:
            r = Resource(uriref)
            Resource.table[uriref] = r  
            return r
  
    else :      # This has a fragment and a resource
        r = intern(uriref[:hash])
        return internFrag(r,uriref[hash+1:])

def internFrag(r,fragid):
        try:
            return r.fragments[fragid]
        except KeyError:
            f = Fragment(r, fragid)
            r.fragments[fragid] = f
            return f
            

RDF_type = intern("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
DAML_equivalentTo = intern("http://www.daml.org/2000/10/daml-ont#equivalentTo")


######################################################### Tests
  
def test():
    import sys
  
    t0 = """bind x: <http://example.org/x-ns/>
	    bind dc: <http://purl.org/dc/elements/1.1/>"""

    t1="""[ >- x:firstname -> "Ora" ] >- dc:wrote -> [ >- dc:title -> "Moby Dick" ]
bind default <http://example.org/default>
<uriPath> :localProp defaultedName
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
]    

<http://www.davelennox.com/residential/furnaces/re_furnaces_content_body_elite90gas.asp>
 >- x:describes -> [ >- x:type -> x:furnace;
 >- x:brand -> "Lennox";
 >- x:model -> "G26Q3-75"
 ]
"""
    t3="""
bind pp: <http://example.org/payPalStuff?>
bind default <http://example.org/payPalStuff?>

<> a pp:Check; pp:payee :tim; pp:amount "$10.00";
dc:author :dan; dc:date "2000/10/7" ;  is pp:part of [ a pp:Transaction; = :t1 ]
"""

# Janets chart:
    t4="""
bind q: <http://example.org/>
bind m: <>
bind n: <http://example.org/base/>
bind : <http://void-prefix.example.org/>
bind w3c: <http://www.w3.org/2000/10/org>

<#QA> :includes 
 [  = w3c:internal ; :includes <#TAB> , <#interoperability> ,
     <#validation> , w3c:wai , <#i18n> , <#translation> ,
     <#readability_elegance>, w3c:feedback_accountability ],
 [ = <#conformance>;
     :includes <#products>, <#content>, <#services> ],
 [ = <#support>; :includes
     <#tools>, <#tutorials>, <#workshops>, <#books_materails>,
     <#certification> ] 

<#internal> q:supports <#conformance>  
<#support> q:supports <#conformance>

"""


    testString[0] = t0 + t1 + t2 + t3 + t4

    p=SinkParser(RDFSink(),'http://example.org/base/', 'file:notation3.py',
		     'data:#')

    r=SinkParser(SinkToN3(sys.stdout.write, intern('file:output')), 'http://example.org/base/', 'file:notation3.py',
		  '#_')

    p.startDoc()
    r.startDoc()
    
    print "=== testing: \n ", t0, "\n========="
    p.feed(t0)
    r.feed(t0)

    print "=== testing: ", t1, "\n========="
    p.feed(t1)
    r.feed(t1)


    print "=== testing: ", t2, "\n========="
    p.feed(t2)
    r.feed(t2)

    print "=== testing: ", t3
    p.feed(t3)
    r.feed(t3)

    p.endDoc()
    r.endDoc()

    print "----------------------- Test store:"

    store = RDFStore()
    p = SinkParser(store, 'http://example.org/base/', 'file:notation3.py',
		     'file:notation3.py#_')
    p.startDoc()
    p.feed(testString[0])
    p.endDoc()

    print "\n\n------------------ dumping chronologically:"

    store.dumpChronological(SinkToN3(sys.stdout.write, intern('file://dev/mta0')))

    print "\n\n---------------- dumping in subject order:"

    store.dumpBySubject(SinkToN3(sys.stdout.write))

    print "\n\n---------------- dumping nested:"

    store.dumpNested(SinkToN3(sys.stdout.write, intern('file:notation3.py')))

    print "Regression test"
    
    buffer=StringWriter()
    r=SinkParser(SinkToN3(buffer.write, intern('file:output')),
                 'http://example.org/base/', 'file:notation3.py',)))

    store.dumpNested(SinkToN3(buffer.write, intern('file:notation3.py')))
    testString[1]=buffer.result()
    buffer.clear()
    
                 
                


################################################################### Sinks

class RDFSink:

    """  Dummy RDF sink prints calls

    This is a superclass for other RDF processors which accept RDF events
    -- maybe later Swell events.  Adapted from printParser
    """
#  Keeps track of prefixes
	    

    def __init__(self):
        self.prefixes = { }     # Convention only - human friendly
        self.namespaces = {}    # Both ways

    def bind(self, prefix, ns):
        if not self.prefixes.get(ns, None):  # If
            if not self.namespaces.get(prefix,None):   # For conventions
                self.prefixes[ns] = prefix
                self.namespaces[prefix] = ns
                print "RDFSink: Bound %s to %s" % (prefix, `ns`)
            else:
                self.bind(prefix+"1", ns)
        
    def makeStatement(self, context, tuple):
        pass

    def startDoc(self):
        print "sink: start.\n"

    def endDoc(self):
        print "sink: end.\n"


########################## RDF 1.0 Syntax generator
	    
class ToRDF(RDFSink):
    """keeps track of most recent subject, reuses it"""

    def __init__(self, outFp):
	self._wr = XMLWriter(outFp)
	self._subj = None

    #@@I18N
    _namechars = string.lowercase + string.uppercase + string.digits + '_'
    _rdfns = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
    _myns = 'http://www.w3.org/2000/10/n3/notation3.py#'

    def startDoc(self):
	self._wr.startElement('web:RDF',
			      (('xmlns:web', self._rdfns),
			       ('xmlns:g', self._myns),
			       ('g:genbase', self._genBase)))
	self._subj = None

    def endDoc(self):
	if self._subj:
	    self._wr.endElement()
	self._subj = None
	self._wr.endElement()

    def makeStatement(self, context, tuple):
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

def relativeTo(here, there):
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


class SinkToN3(RDFSink):
    """keeps track of most recent subject and predicate reuses them

      Adapted from ToRDFParser(Parser);
    """

    def __init__(self, write, base=None):
	self._write = write
	self._subj = None
	self.prefixes = {}      # Look up prefix conventions
	self.indent = 1         # Level of nesting of output
	self.base = base

    #@@I18N
    _namechars = string.lowercase + string.uppercase + string.digits + '_'
    _rdfns = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
    _myns = 'http://www.w3.org/2000/10/n3/notation3.py#'

    def bind(self, prefix, ns):
        """ Just accepting a convention here """
        self.prefixes[ns] = prefix
        if prefix == "" :
            self._write(" bind default %s .\n" % (`ns`) )
        else :
            self._write(" bind %s: %s .\n" % (prefix, `ns`) )

    def startDoc(self):
 
      self._write("\n#   Start notation3 generation\n")
      self._subj = None

    def endDoc(self):
	if self._subj:
	    self._write(" .\n\n")
	self._subj = None

    def makeStatement(self, context, subj, pred, obj):
        self._makeSubjPred(context, subj, pred)        
        self._write(obj.representation(self.prefixes, self.base));
        
# Below is for writing an anonymous node which is the object of only one arc        
    def startAnonymous(self, context, subj, pred, obj):
        self._makeSubjPred(context, subj, pred)
        self.indent = self.indent + 1
        self._write(" [ \n"+ "    " * self.indent + "    ")
        self._subj = obj    # The object is not the subject context
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
        if `subj` == "<#_1>" : raise theroof

    def endAnonymousNode(self):    # Remove context
        self._write(" ].\n")
        self._subj = None
        self._pred = None

    def _makeSubjPred(self, context, subj, pred):
        
	if self._subj is not subj:
	    if self._subj:
		  self._write(" .\n")
		  self._write("    " * self.indent)
	    self._write(subj.representation(self.prefixes, self.base))
	    self._subj = subj
	    self._pred = None

	if self._pred is not pred:
	    if self._pred:
		  self._write(";\n" + "    " * self.indent+ "    ")

            if pred is DAML_equivalentTo :
                self._write(" = ")
            elif pred is RDF_type :
                self._write(" a ")
            else :
#	        self._write( " >- %s -> " % (pred.representation(self.prefixes,base)))
                self._write( " %s : " % (pred.representation(self.prefixes,self.base)))

	    self._pred = pred
	else:
	    self._write(",\n" + "    " * (self.indent+3))    # Same subject and pred => object list

class StringWriter:

    def __init__(self)
        buffer = ""

    def write(self, str)
        buffer = buffer + str     #  No idea how to make this efficient in python

    def result()
        return buffer

######################################################## Storage
# The store uses an index in the actual resource objects.
#

class RDFStore(RDFSink) :
    """ Absorbs RDF stream and saves in triple store
    """

    def __init__(self):
        self.statements = []    # Unordered
        RDFSink.__init__(self)

    def startDoc(self):
        pass

    def endDoc(self):
        mp = mostPopular()
        print "*********** Most popular Namesapce is " , `mp`
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
        

    def makeStatement(self, context, tuple):
        s = RDFTriple(context, tuple) # @@ duplicate check?
        self.statements.append(s)

# Output methods:

    def dumpChronological(self, sink):
        for c in self.prefixes.items():   #  bind in same way as input did FYI
            sink.bind(c[1], c[0])
        for s in self.statements :
            sink.makeStatement(s.context, s.triple)

    def dumpBySubject(self, sink):
        for c in self.prefixes.items() :   #  bind in same way as input did FYI
            sink.bind(c[1], c[0])

        for r in Resource.table.values() :  # First the bare resource
            for s in r.occursAs[SUBJ] :
                sink.makeStatement(s.context, s.triple)
            for f in r.fragments.values() :  # then anything in its namespace
                for s in f.occursAs[SUBJ] :
                    sink.makeStatement(s.context, s.triple)

    def dumpNested(self, sink):
        """ Iterates over all URIs ever seen looking for statements
        """
        for c in self.prefixes.items() :   #  bind in same way as input did FYI
            sink.bind(c[1], c[0])

        for r in Resource.table.values() :  # First the bare resource
            self.dumpSubject(r, sink)
            for f in r.fragments.values() :  # then anything in its namespace
                self.dumpSubject(f, sink)


    def dumpSubject(self, subj, sink):
        """ Take care of top level anonymous nodes
        """
        if (subj.generated() and  # The URI is irrelevant
                len(subj.occursAs[OBJ]) == 0 and  # There is no incoming arrow
                len(subj.occursAs[PRED]) == 0 ):    # It is not used as a verb itself
            if len(subj.occursAs[SUBJ]) > 0 :   # Ignore if actually no statements for this thing
                sink.startAnonymousNode(subj)
                for s in subj.occursAs[SUBJ] :
                    self.coolMakeStatement(sink, s.triple)
                sink.endAnonymousNode()
        else:
            for s in subj.occursAs[SUBJ] :
                self.coolMakeStatement(sink, s.triple)

    def coolMakeStatement(self, sink, context, triple):
     
        if subject is object:
            sink.makeStatement(context, triple)
        else:
            if not subject.n3_anonymous():
                self.coolMakeStatement2(sink, context, triple)
                
    def coolMakeStatement2(self, sink, context, triple):
     
        if object.n3_anonymous():  # Can be represented as anonymous node in N3
            sink.startAnonymous(context, triple)
            for t in object.asSubject:
                self.coolMakeStatement2(sink, t.context, triple)
            sink.endAnonymous(subject, verb) # Restore context
        else:    
            sink.makeStatement(context, triple)
                


            
class RDFTriple:
    
    def __init__(self, context, triple):
        self.context = context
        self.triple = triple
        triple[SUBJ].occursAs[SUBJ].append(self)   # Resource index
        triple[PRED].occursAs[PRED].append(self)   # Resource index
        triple[OBJ].occursAs[OBJ].append(self)     # Resource index
        

############################################################## Query engine

# Template matching in a graph

    

INFINITY = 1000000000           # @@ larger than any number occurences
def match (unmatched, action, param )

# Scan terms to see what sort of a problem we have:
#
# We prefer terms with a single variable to those with two.
# (Those with none we immediately check and therafter ignore)
# Secondarily, we prefer short searches to long ones.

        total = 0           # Number of matches found (recursively)
        shortest = INFINITY
        shortest_t = None
        found_single = 0   # Singles are better than doubles
        unmatched2 = unmatched[:] # Copy
        
        for t in unmatched:
            vars = []       # Count where variables are
            q = []          # Count where constants are
            short_p = -1
            short = INFINITY
            for p in PRED, SUBJ, OBJ:
                r = t.triple[p]
                if r isInstanceOf(Variable):
                    vars.append(r)
                else:
                    if r.occurs[p]< short:
                        short_p = p
                        short = r.occurs[p]
                        consts.append(p)

            if short == 0 return 0 # No way we can satisfy that one - quick "no"

            if len(vars) == 0: # This is an independant constant triple
                          # It has to match or the whole thing fails
                 
                for s in r.occursAs[short_p]:
                    if (s.triple[q[0]] is t.triple[q[0]]
                        and s.triple[q[1]] is t.triple[q[1]]:
                            unmatched2.remove(t)  # Ok - we believe it - ignore it
                    else: # no match for a constant term: query fails
                        return 0
                
            elif len(vars) == 1: # We have a single variable.
            if if not found_single or short < shortest :
                shortest = short
                shortest_p = short_p
                shortest_t = t
                found_single = 1
                
            else:   # Has two variables
            if not found_single and short < shortest :
                shortest = short
                shortest_p = short_p
                shortest_t = t

        if len(unmatched) == 0:
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
            if isInstanceOf(t.triple[p], Variable):
                parts_to_search.remove(p)
                v.append(p)
            elif p != shortest_p :
                q.append(p) = p

        if found_single:        # One variable, two constants - must search
            for s in t.occursAs[shortest_p]:
                if s.triple[q[0]] is t.triple[q[0]]: # Found this one
                    unmatched3 = unmatched2[:]
                    replace_variable(s.triple[pv], s.triple[pv],unmatched2)
                    bindings = bindings + [ s.triple[pv], s.triple[pv] ] 
                    total = total + match(unmatched3, bindings, action)
            
        else: # Two variables, one constant. Every one in occurrence list will be good
            for s in t.occursAs[shortest_p]:
                unmatched3 = unmatched2[:]
                for v1 in v:
                    replace_variable(t.triple[v1], s.triple[v1],unmatched3)
                    bindings = bindings + [ t.triple[v1], s.triple[v1]]
                total = total + matches(unmatched3, bindings, action, param)
            
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

    
if __name__ == '__main__':
    import os
    if os.environ.has_key('SCRIPT_NAME'):
	serveRequest(os.environ)
    else:
	test()

