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

I haven't done quoting yet.

idea: migrate toward CSS notation?

idea: use notation3 for wiki record keeping.

"""

import string
import urlparse
import re


class Parser:
    def __init__(self, baseURI, thisDoc, genBase, bindings = {}):
	""" note: namespace names should *not* end in #;
	the # will get added during qname processing """
	self._baseURI = baseURI
	self._genBase = genBase
	self._bindings = bindings
	self._nextID = 0
	self._thisDoc = intern(thisDoc)

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

    def makeStatement(self, subj, pred, obj):
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

	self._bindings[t[0][0]] = `t[1]`
	return j

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


    def genURI(self):
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
			self.makeStatement(subj, sym, obj)
		    else:
			self.makeStatement(obj, sym, subj)

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
		ns = `self._thisDoc`
	    else:
		try:
		    ns = self._bindings[pfx]
		except KeyError:
		    raise BadSyntax(str, i, "prefix not bound")
	    res.append(intern("%s#%s" % (ns, ln)))
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
	def -> ('', 'def')
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
			res.append(str[st:i])
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

def intern(str):
    try:
	return Symbol.symtab[str]
    except KeyError:
	sym = Symbol(str)
	Symbol.symtab[str] = sym
	return sym
#
#####

RDF_type = intern("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
DAML_equivalentTo = intern("http://www.daml.org/2000/10/daml-ont#equivalentTo")

class PrintingParser(Parser):
    def makeStatement(self, subj, pred, obj):
	if isinstance(obj, Symbol):
	    print "** %s(%s, %s)" % (pred, subj, obj)
	else:
	    print "** %s(%s, %s)" % (pred, subj, repr(obj))

def test():
    import sys

    p=PrintingParser('http://example.org/base/', 'file:notation3.py',
		     'data:#')

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

<> a pp:Check; pp:payee :tim; pp:amount "$10.00"; dc:author :dan; dc:date "2000/10/7" ;  is pp:part of [ a pp:Transaction; = :t1 ]
"""


    print "=== testing: ", t0
    p.feed(t0)

    print "=== testing: ", t1
    p.feed(t1)


    print "=== testing: ", t2
    p.feed(t2)

    print "=== testing: ", t3
    p.feed(t3)


    print "--- RDF:"
    r=ToRDFParser(sys.stdout, 'http://example.org/base/', 'file:notation3.py',
		  'data:#')
    r.startDoc()
    r.feed(t0)
    r.feed(t2)
    r.feed(t3)
    r.endDoc()



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


class ToRDFParser(Parser):
    """keeps track of most recent subject, reuses it"""

    def __init__(self, outFp, baseURI, thisDoc, genBase, bindings = {}):
	Parser.__init__(self, baseURI, thisDoc, genBase, bindings)
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

    def makeStatement(self, subj, pred, obj):
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

	if isinstance(obj, Symbol):
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
    else: genspace = thisMessage + '#'

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

