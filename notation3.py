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

To DO: See also "@@" in comments

Internationlization:
- Decode incoming N3 file as unicode
- Encode outgoing file
- unicode \u  (??) escapes in parse
- unicode \u  (??) escapes in string output

Note currently unicode strings work in this code
but fail when they are output into the python debugger
interactive window.

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



import types
import string
import codecs # python 2-ism; for writing utf-8 in RDF/xml output
import urllib

import re
import thing

from diag import verbosity, setVerbosity, progress

from uripath import refTo, join

import uripath
import RDFSink
from RDFSink import CONTEXT, PRED, SUBJ, OBJ, PARTS, ALL4
from RDFSink import  LITERAL, ANONYMOUS, SYMBOL
from RDFSink import Logic_NS
import diag

from why import BecauseOfData, FormulaReason

N3_forSome_URI = RDFSink.forSomeSym
N3_forAll_URI = RDFSink.forAllSym

# Magic resources we know about


from RDFSink import RDF_type_URI, RDF_NS_URI, DAML_equivalentTo_URI, parsesTo_URI
from RDFSink import RDF_spec, List_NS

ADDED_HASH = "#"  # Stop where we use this in case we want to remove it!
# This is the hash on namespace URIs

# Should the internal representation of lists be with DAML:first and :rest?
DAML_LISTS = 1    # Else don't do these - do the funny compact ones- not a good idea after all

RDF_type = ( SYMBOL , RDF_type_URI )
DAML_equivalentTo = ( SYMBOL, DAML_equivalentTo_URI )

from RDFSink import N3_first, N3_rest, N3_nil, N3_List, N3_Empty

LOG_implies_URI = "http://www.w3.org/2000/10/swap/log#implies"

INTEGER_DATATYPE = "http://www.w3.org/2001/XMLSchema#integer"
FLOAT_DATATYPE = "http://www.w3.org/2001/XMLSchema#double"

option_noregen = 0   # If set, do not regenerate genids on output

# @@ I18n - the notname chars need extending for well known unicode non-text characters.
# The XML spec switched to assuming unknown things were name characaters.
# _namechars = string.lowercase + string.uppercase + string.digits + '_-'
_notNameChars = "\t\r\n !\"#$%&'()*.,+/;:<=>?@[\\]^`{|}~"  # Assume anything else valid name :-/
_rdfns = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'


N3CommentCharacter = "#"     # For unix script #! compatabilty

########################################## Parse string to sink
#
# Regular expressions:
eol = re.compile(r'[ \t]*(#[^\n]*)?\r?\n')	# end  of line, poss. w/comment
eof = re.compile(r'[ \t]*(#[^\n]*)?$')      	# end  of file, poss. w/comment
ws = re.compile(r'[ \t]*')			# Whitespace not including newline @@(whatabout unicode NL? ask MartinD)
signed_integer = re.compile(r'[-+]?[0-9]+')	# integer
number_syntax = re.compile(r'([-+]?[0-9]+)(.[0-9]+)?(e[-+]?[0-9]+)?')
digitstring = re.compile(r'[0-9]+')		# Unsigned integer	
interesting = re.compile(r'[\\\r\n\"]')
langcode = re.compile(r'[a-zA-Z0-9]+(-[a-zA-Z0-9]+)?')


class SinkParser:
    def __init__(self, sink, thisDoc, baseURI=None, bindings = {},
                 genPrefix = "", metaURI=None,
                 formulaURI = None, why=None):
	""" note: namespace names should *not* end in #;
	the # will get added during qname processing """

        assert ':' in thisDoc, "must be absolute: %s" % thisDoc

        self._sink = sink
	if genPrefix: sink.setGenPrefix(genPrefix) # pass it on
	
    	self._bindings = bindings
	self._thisDoc = thisDoc
        self.lines = 0              # for error handling
	self.startOfLine = 0	    # For calculating character number
        self._genPrefix = genPrefix
	self.keywords = ['a', 'this', 'bind', 'has', 'is', 'of' ]
	self.keywordsSet = 0    # When and only when they have been set can others be considerd qnames
        self._anonymousNodes = {}   # Dict of anon nodes already declared  ln : Term
	self._reason = why	# Why the parser w
	self._reason2 = None	# Why these triples
	if diag.tracking: self._reason2 = BecauseOfData(sink.newSymbol(thisDoc), because=self._reason) 

        if baseURI: self._baseURI = baseURI
        else: self._baseURI = thisDoc

        assert ':' in self._baseURI

        if not self._genPrefix: self._genPrefix = self._thisDoc + "#_g"

        if formulaURI == None:
            formulaURI = thisDoc + "#_formula" # Formula node is what the document parses to
        else:
            formulaURI = formulaURI # Formula node is what the document parses to
	self._formula = sink.newFormula(formulaURI)
	if diag.tracking:
	    progress ("@@@@@@ notation3  167 loading ",thisDoc,  why, self._formula)
	    proof = self._formula.collector
	    if proof == None:
		proof = FormulaReason(self._formula)
		progress ("\tAllocating new FormulaReason")
	    progress ("\tNow: 169", why, proof, self._formula)

        self._context = self._formula
	self._parentContext = None
        
        if metaURI:
            self.makeStatement((SYMBOL, metaURI), # relate document to parse tree
                            (SYMBOL, PARSES_TO_URI ), #pred
                            (SYMBOL, thisDoc),  #subj
                            self._context)                      # obj
            self.makeStatement(((SYMBOL, metaURI), # quantifiers - use inverse?
                            (SYMBOL, N3_forSome_URI), #pred
                            self._context,  #subj
                            subj))                      # obj

    def here(self, i):
	"""String generated from position in file
	
	This is for repeatability when refering people to bnodes in a document.
	This has diagnostic uses less formally, as it should point one to which 
	bnode the arbitrary identifier actually is. It gives the
	line and character number of the '[' charcacter or path character
	which introduced the blank node.  The first blank node is boringly _L1C1."""
	if not diag.tracking: return None
	return "%s#_L%iC%i" % (self. _thisDoc , self.lines + 1, i - self.startOfLine + 1) 
        
    def formula(self):
        return self._formula
    
    def load(self, uri, baseURI=""):
	"""Parses a document of the given URI and returns its top level formula"""
        if uri:
            _inputURI = uripath.join(baseURI, uri) # Make abs from relative
	    inputResource = self._sink.newSymbol(_inputURI)
            self._sink.makeComment("Taking input from " + _inputURI)
            stream = urllib.urlopen(_inputURI)
	    if diag.tracking: self._reason2 = BecauseOfData(inputResource, because=self._reason) 
        else:
            self._sink.makeComment("Taking input from standard input")
            _inputURI = uripath.join(baseURI, "STDIN") # Make abs from relative
            stream = sys.stdin     # May be big - buffered in memory!
	    if self._reason: self._reason2 = BecauseOfData("@@standardInput", because=self._reason) 
	return self.loadBuf(stream.read())    # self._formula

    def loadStream(self, stream):
	return self.loadBuf(stream.read())   # Not ideal

    def loadBuf(self, buf):
	"""Parses a buffer and returns its top level formula"""
	self.startDoc()
	self.feed(buf)
	return self.endDoc()    # self._formula


    def feed(self, octets):
	"""Feed an octet stream tothe parser
	
	if BadSyntax is raised, the string
	passed in the exception object is the
	remainder after any statements have been parsed.
	So if there is more data to feed to the
	parser, it should be straightforward to recover."""
	str = octets.decode('utf-8')
        i = 0
	while i >= 0:
	    j = self.skipSpace(str, i)
	    if j<0: return

            i = self.directiveOrStatement(str,j)
            if i<0:
                print "# next char: ", `str[j]` 
                raise BadSyntax(self._thisDoc, self.lines, str, j, "expected directive or statement")

    def directiveOrStatement(self, str,h):
    
	    i = self.skipSpace(str, h)
	    if i<0: return i   # EOF

	    j = self.directive(str, i)
	    if j>=0: return  self.checkDot(str,j)
	    
            j = self.statement(str, i)
            if j>=0: return self.checkDot(str,j)
            
	    return j


    #@@I18N
    global _notNameChars
    #_namechars = string.lowercase + string.uppercase + string.digits + '_-'

    def tok(self, tok, str, i):
        """Check for keyword.  Space must have been stripped on entry and
	we must not be at end of file."""

	if str[i:i+1] == "@":
	    i = i+1
	else:
	    if tok not in self.keywords:
		return -1   # Nope, this has neither keywords declaration nor "@"

	if (str[i:i+len(tok)] == tok
            and (tok[0]  in _notNameChars    # check keyword is not prefix
                or str[i+len(tok)] in string.whitespace )):
	    i = i + len(tok)
	    return i
	else:
	    return -1

    def directive(self, str, i):
	j = self.skipSpace(str, i)
	if j<0: return j # eof

	j = self.tok('bind', str, i)        # implied "#". Obsolete.
	if j>0: raise BadSyntax(self._thisDoc, self.lines, str, i, "keyword bind is obsolete: use @prefix")

	j = self.tok('keywords', str, i)
	if j>0:
	    raise BadSyntax(self._thisDoc, self.lines, str, i, "Sorry, '@keywords' not implemented yet")

	j = self.tok('from', str, i)
	if j>0:
	    raise BadSyntax(self._thisDoc, self.lines, str, i,
		"Sorry, '@from <xxx> @import a, b, c.' not implemented yet")

	j=self.tok('prefix', str, i)   # no implied "#"
	if j<0: return -1
	
	t = []
	i = self.qname(str, j, t)
	if i<0: raise BadSyntax(self._thisDoc, self.lines, str, j, "expected qname after bind or prefix")
	j = self.uri_ref2(str, i, t)
	if j<0: raise BadSyntax(self._thisDoc, self.lines, str, i, "expected <uriref> after bind _qname_")

#	progress("@@@@@", t)
	if isinstance(t[1], types.TupleType): ns = t[1][1] # old system for --pipe
        else:
#	    progress( "@@@@@@@@@@", type(t[1]))
	    ns = t[1].uriref()
#        if string.find(ns,"##")>=0: raise BadSyntax(self._thisDoc, self.lines, str, j-2, "trailing # illegal on bind: use @prefix")
        ns = join(self._baseURI, ns)
        assert ':' in ns # must be absolute
	self._bindings[t[0][0]] = ns
	self.bind(t[0][0], hexify(ns))
	return j

    def bind(self, qn, uri):
	assert isinstance(uri, types.StringType), "Any unicode must be %x-encoded already"
        if qn == "":
            self._sink.setDefaultNamespace(uri)
        else:
            self._sink.bind(qn, uri)

    def startDoc(self):
        self._sink.startDoc()

    def endDoc(self):
	"""Signal end fo document and stop parsing. returns formula"""
        self._sink.endDoc(self._formula)
	return self._formula

    def makeStatement(self, quadruple):
#        print "# Parser output: ", `triple`
        self._sink.makeStatement(quadruple, why=self._reason2)



    def statement(self, str, i):
	r = []

	i = self.object(str, i, r)       #  Allow literal for subject - This extends RDF model
	if i<0: return i

	j = self.property_list(str, i, r[0])

	if j<0: raise BadSyntax(self._thisDoc, self.lines, str, i, "expected propertylist")
	return j

    def subject(self, str, i, res):
	return self.item(str, i, res)

    def verb(self, str, i, res):
	""" has _prop_
	is _prop_ of
	a
	=
	_prop_
	>- prop ->
	<- prop -<
	_operator_"""

	j = self.skipSpace(str, i)
	if j<0:return j # eof
	
	r = []

	j = self.tok('has', str, i)
	if j>=0:
	    i = self.prop(str, j, r)
	    if i < 0: raise BadSyntax(self._thisDoc, self.lines, str, j, "expected property after 'has'")
	    res.append(('->', r[0]))
	    return i

	j = self.tok('is', str, i)
	if j>=0:
	    i = self.prop(str, j, r)
	    if i < 0: raise BadSyntax(self._thisDoc, self.lines, str, j, "expected <property> after 'is'")
	    j = self.skipSpace(str, i)
	    if j<0:
		raise BadSyntax(self._thisDoc, self.lines, str, i, "EOF found, expected property after 'is'")
		return j # eof
	    i=j
	    j = self.tok('of', str, i)
	    if j<0: raise BadSyntax(self._thisDoc, self.lines, str, i, "expected 'of' after 'is' <prop>")
	    res.append(('<-', r[0]))
	    return j

	j = self.tok('a', str, i)
	if j>=0:
	    res.append(('->', RDF_type))
	    return j

	    
	if str[i:i+2] == "<=":
	    res.append(('<-', self._sink.newSymbol(Logic_NS+"implies")))
	    return i+2

	if str[i:i+1] == "=":
	    if str[i+1:i+2] == ">":
		res.append(('->', self._sink.newSymbol(Logic_NS+"implies")))
		return i+2
	    res.append(('->', DAML_equivalentTo))
	    return i+1

	if str[i:i+2] == ":=":
	    res.append(('->', Logic_NS+"becomes"))   # patch file relates two formulae, uses this
	    return i+2

	j = self.prop(str, i, r)
	if j >= 0:
	    res.append(('->', r[0]))
	    return j

	if str[i:i+2] == ">-" or str[i:i+2] == "<-":
	    raise BadSyntax(self._thisDoc, self.lines, str, j, ">- ... -> syntax is obsolete.")

	return -1

    def prop(self, str, i, res):
	return self.item(str, i, res)

    def item(self, str, i, res):
	return self.path(str, i, res)
	
    def path(self, str, i, res):
	"""Parse the path production.
	"""
	j = self.nodeOrLiteral(str, i, res)
	if j<0: return j  # nope

	while str[j:j+1] in "!^.":  # no spaces, must follow exactly (?)
	    ch = str[j:j+1]		# @@ Allow "." followed IMMEDIATELY by a node.
	    if ch == ".":
		ahead = str[j+1:j+2]
		if not ahead or ahead in _notNameChars + "[{(":
		    break
	    subj = res.pop()
	    obj = self._sink.newBlankNode(self._context, uri=self.here(j), why=self._reason2)
	    j = self.node(str, j+1, res)
	    if j<0: raise BadSyntax(self._thisDoc, self.lines, str, j, "EOF found in middle of path syntax")
	    pred = res.pop()
	    if ch == "^": # Reverse traverse
		self.makeStatement((self._context, pred, obj, subj)) 
	    else:
		self.makeStatement((self._context, pred, subj, obj)) 
	    res.append(obj)
	return j

    def anonymousNode(self, ln):
	"""Remember or generate a term for one of these _: anonymous nodes"""
	term = self._anonymousNodes.get(ln, None)
	if term != None: return term
	term = self._sink.newExistential(self._context, self._genPrefix + ln, why=self._reason2)
	self._anonymousNodes[ln] = term
	return term

    def node(self, str, i, res, subjectAlready=None):
	"""Parse the <node> production.
	Space is now skipped once at the beginning
	instead of in multipe calls to self.skipSpace().
	"""
        subj = subjectAlready

	j = self.skipSpace(str,i)
	if j<0: return j #eof
	i=j
	ch = str[i:i+1]  # Quick 1-character checks first:

        if ch == "[":
	    bnodeID = self.here(i)
	    j=self.skipSpace(str,i+1)
	    if j<0: raise BadSyntax(self._thisDoc, self.lines, str, i, "EOF after '['")
	    if str[j:j+1] == "=":     #   Hack for "is"  binding name to anon node
		i = j+1
                objs = []
                j = self.object_list(str, i, objs);
                if j>=0:
                    subj = objs[0]
                    if len(objs)>1:
                        for obj in objs:
                            self.makeStatement((self._context,
                                                DAML_equivalentTo, subj, obj))
		    j = self.skipSpace(str, j)
		    if j<0: raise BadSyntax(self._thisDoc, self.lines, str, i,
			"EOF when object_list expected after [ = ")
		    if str[j:j+1] == ";":
			j=j+1
                else:
                    raise BadSyntax(self._thisDoc, self.lines, str, i, "object_list expected after [= ")

            if subj is None: subj=self._sink.newBlankNode(self._context,uri= bnodeID, why=self._reason2)

            i = self.property_list(str, j, subj)
            if i<0: raise BadSyntax(self._thisDoc, self.lines, str, j, "property_list expected")

	    j = self.skipSpace(str, i)
	    if j<0: raise BadSyntax(self._thisDoc, self.lines, str, i,
		"EOF when ']' expected after [ <propertyList>")
	    if str[j:j+1] != "]":
		raise BadSyntax(self._thisDoc, self.lines, str, j, "']' expected")
            res.append(subj)
            return j+1

        if ch == "{":
	    j=i+1
            oldParentContext = self._parentContext
	    self._parentContext = self._context
            if subj is None: subj = self._sink.newFormula()
            self._context = subj
            
            while 1:
                i = self.skipSpace(str, j)
                if i<0: raise BadSyntax(self._thisDoc, self.lines, str, i, "needed '}', found end.")
                
		if str[i:i+1] == "}":
		    j = i+1
		    break
                
                j = self.directiveOrStatement(str,i)
                if j<0: raise BadSyntax(self._thisDoc, self.lines, str, i, "expected statement or '}'")

            self._context = self._parentContext
	    self._parentContext = oldParentContext
            res.append(subj.close())   # Must not actually use the formula until it has been closed
            return j

        if ch == "(":
	    j=i+1
            previous = None  # remember value to return
            while 1:
                i = self.skipSpace(str, j)
                if i<0: raise BadSyntax(self._thisDoc, self.lines, str, i, "needed ')', found end.")                    
                if str[i:i+1] == ')':
		    j = i+1
		    break

                item = []
                j = self.object(str,i, item)
                if j<0: raise BadSyntax(self._thisDoc, self.lines, str, i, "expected item in list or ')'")
                this = self._sink.newExistential(self._context, why=self._reason2)
                if DAML_LISTS:
                    if previous:
                        self.makeStatement((self._context, N3_rest, previous, this ))
                    else:
                        head = this
                    self.makeStatement((self._context, N3_first, this, item[0]))
                else:  # compact lists
                    if previous:
                        self.makeStatement((self._context, this, previous, previousvalue ))
                    else: # First time though
                        head = this
                previous = this
                previousvalue = item[0]

            if not previous:
                res.append(N3_nil)
                return j
            if DAML_LISTS:
                self.makeStatement((self._context, N3_rest, previous, N3_nil ))           # obj
            else:
                self.makeStatement((self._context, N3_nil, previous, previousvalue ))           # obj                
            res.append(head)
            return j

        j = self.tok('this', str, i)   # This context
        if j>=0:
            res.append(self._context)
            return j

	if subj is None:   # If this can be a named node, then check for a name.
            j = self.uri_ref2(str, i, res)
            if j >= 0:
                return j

        return -1
        
    def property_list(self, str, i, subj):
	"""Parse property list
	Leaves the terminating punctuation in the buffer
	"""
	while 1:
	    j = self.skipSpace(str, i)
	    if j<0:
		raise BadSyntax(self._thisDoc, self.lines, str, i, "EOF found when expected verb in property list")
		return j #eof

            if str[j:j+2] ==":-":
		i = j + 2
                res = []
                j = self.node(str, i, res, subj)
                if j<0: raise BadSyntax(self._thisDoc, self.lines, str, i, "bad {} or () or [] node after :- ")
		i=j
                continue
	    i=j
	    v = []
	    j = self.verb(str, i, v)
            if j<=0:
		return i # void but valid

	    objs = []
	    i = self.object_list(str, j, objs)
	    if i<0: raise BadSyntax(self._thisDoc, self.lines, str, j, "object_list expected")
	    for obj in objs:
		dir, sym = v[0]
		if dir == '->':
		    self.makeStatement((self._context, sym, subj, obj))
		else:
		    self.makeStatement((self._context, sym, obj, subj))

	    j = self.skipSpace(str, i)
	    if j<0:
		raise BadSyntax(self._thisDoc, self.lines, str, j, "EOF found in list of objects")
		return j #eof
	    if str[i:i+1] != ";":
		return i
	    i = i+1 # skip semicolon and continue

    def object_list(self, str, i, res):
	i = self.object(str, i, res)
	if i<0: return -1
	while 1:
	    j = self.skipSpace(str, i)
	    if j<0:
		raise BadSyntax(self._thisDoc, self.lines, str, j, "EOF found after object")
		return j #eof
	    if str[j:j+1] != ",":
		return j    # Found something else!
            i = self.object(str, j+1, res)
	    if i<0: return i

    def checkDot(self, str, i):
	    j = self.skipSpace(str, i)
	    if j<0: return j #eof
	    if str[j:j+1] == ".":
		return j+1  # skip
	    if str[j:j+1] == "}":
		return j     # don't skip it
	    if str[j:j+1] == "]":
		return j
            raise BadSyntax(self._thisDoc, self.lines, str, j, "expected '.' or '}' or ']' at end of statement")
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
                    if pfx == "_":   # Magic prefix added 2001/05/30, can be overridden
                        res.append(self.anonymousNode(ln))
			# progress("@@@@@@@ uri_ref2 res", res)
                        return j
		    raise BadSyntax(self._thisDoc, self.lines, str, i, "Prefix %s not bound" % (pfx))
            res.append(self._sink.newSymbol(ns + ln)) # @@@ "#" CONVENTION
            if not string.find(ns, "#"):progress("Warning: no # on NS %s," % ns)
	    return j

        v = []
        j = self.variable(str,i,v)
        if j>0:                    #Forget varibles as a class, only in context.
            res.append(v[0])
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
                    uref = uripath.join(self._baseURI, str[st:i])
                    if str[i-1:i]=="#" and not uref[-1:]=="#":
                        uref = uref + "#"  # She meant it! Weirdness in urlparse?
                    res.append(self._sink.newSymbol(uref))
                    return i+1
                i = i + 1
            raise BadSyntax(self._thisDoc, self.lines, str, j, "unterminated URI reference")
        else:
            return -1

    def skipSpace(self, str, i):
	"""Skip white space, newlines and comments.
	return -1 if EOF, else position of first non-ws character"""
	while 1:
            m = eol.match(str, i)
	    if m == None: break
	    self.lines = self.lines + 1
	    i = m.end()   # Point to first character unmatched
	    self.startOfLine = i
	m = ws.match(str, i)
	if m != None:
	    i = m.end()
	m = eof.match(str, i)
	if m != None: return -1
	return i

    def variable(self, str, i, res):
	"""	?abc -> variable(:abc)
  	"""

	j = self.skipSpace(str, i)
	if j<0: return -1

        if str[j:j+1] != "?": return -1
        j=j+1
        i = j
	while i <len(str) and str[i] not in _notNameChars: #@@ check for intial alpha
            i = i+1
	if self._parentContext == None:
	    raise BadSyntax(self._thisDoc, self.lines, str, j,
			    "Can't use ?xxx syntax for variable in outermost level: %s" % str[j-1:i])
	var = self._sink.newUniversal(self._parentContext, self. _thisDoc +"#"+str[j:i], why=self._reason2)
        res.append(var)
#        print "Variable found: <<%s>>" % str[j:i]
        return i

    def qname(self, str, i, res):
	"""
	xyz:def -> ('xyz', 'def')
	If not in keywords and keywordsSet: def -> ('', 'def')
	:def -> ('', 'def')    
	"""

	j = self.skipSpace(str, i)
	if j<0: return -1
	else: i=j

	c = str[i]
	if c not in _notNameChars:
	    ln = c
	    i = i + 1
	    while i < len(str):
		c = str[i]
		if c not in _notNameChars:
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
		if c not in _notNameChars:
		    ln = ln + c
		    i = i + 1
		else: break

	    res.append((pfx, ln))
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

                j, s = self.strconst(str, i, delim)

                res.append(self._sink.newLiteral(s))
		return j
	    else:
		return -1

    def nodeOrLiteral(self, str, i, res):
	j = self.node(str, i, res)
	if j>= 0:
	    return j
	else:
	    j = self.skipSpace(str, i)
	    if j<0: return -1
	    else: i=j

	    ch = str[i]
	    if ch in "-+0987654321":
		m = number_syntax.match(str, i)
		if m == None:
		    raise BadSyntax(self._thisDoc, startline, str, i,
				"Bad number syntax")
		j = m.end()
		if m.group(2) != None or  m.group(3) != None: # includes decimal exponent
		    res.append(self._sink.newLiteral(str[i:j],
			self._sink.newSymbol(FLOAT_DATATYPE)))
		else:
		    res.append(self._sink.newLiteral(str[i:j],
			self._sink.newSymbol(INTEGER_DATATYPE)))
		return j

	    if str[i]=='"':
		if str[i:i+3] == '"""': delim = '"""'
		else: delim = '"'
                i = i + len(delim)

		dt = None
                j, s = self.strconst(str, i, delim)
		lang = None
		if str[j:j+1] == "@":  # Language?
		    m = langcode.match(str, j+1)
		    if m == None:
			raise BadSyntax(self._thisDoc, startline, str, i,
				    "Bad language code syntax on string literal, after @")
		    i = m.end()
		    lang = str[j+1:i]
		    j = i
		if str[j:j+2] == "^^":
		    res2 = []
		    j = self.uri_ref2(str, j+2, res2) # Read datatype URI
		    dt = res2[0]
                res.append(self._sink.newLiteral(s, dt, lang))
		return j
	    else:
		return -1

    def strconst(self, str, i, delim):
        """parse an N3 string constant delimited by delim.
        return index, val
        """


        j = i
        ustr = u""   # Empty unicode string
        startline = self.lines # Remember where for error messages
        while j<len(str):
            i = j + len(delim)
            if str[j:i] == delim: # done.
                return i, ustr

            if str[j] == '"':
                ustr = ustr + '"'
                j = j + 1
                continue
            m = interesting.search(str, j)  # was str[j:].
	    # Note for pos param to work, MUST be compiled  ... re bug?
#	    print "Matched >>>>", m.group(0), "<<< in string >>>>>", m.string, "<<<<<<"
            assert m # we at least have to find a quote
#	    print "@@@ old i = ",i, " j=",j, "m.start=", m.start(),"m.end=", m.end(), 
#	    print ">>>>>>>", m.string[:j+m.start()], "|||||||", m.string[j+m.start(): j+m.end()], "<<<<<<<"

            i = m.start()
	    try:
		ustr = ustr + str[j:i]
	    except UnicodeError:
		err = ""
		for c in str[j:i]:
		    err = err + (" %02x" % ord(c))
		streason = sys.exc_info()[1].__str__()
		raise BadSyntax(self._thisDoc, startline, str, j,
				"Unicode error appending characters %s to string, because\n\t%s"
				% (err, streason))
		
#	    print "@@@ i = ",i, " j=",j, "m.end=", m.end()

            ch = str[i]
            if ch == '"':
                j = i
                continue
            elif ch == "\r":   # Strip carriage returns
                j = i+1
                continue
            elif ch == "\n":
                if delim == '"':
                    raise BadSyntax(self._thisDoc, startline, str, i,
                                    "newline found in string literal")
                self.lines = self.lines + 1
                ustr = ustr + ch
                j = i + 1
		self.startOfLine = j

            elif ch == "\\":
                j = i + 1
                ch = str[j:j+1]  # Will be empty if string ends
                if not ch:
                    raise BadSyntax(self._thisDoc, startline, str, i,
                                    "unterminated string literal (2)")
                k = string.find('abfrtvn\\"', ch)
                if k >= 0:
                    uch = '\a\b\f\r\t\v\n\\"'[k]
                    ustr = ustr + uch
                    j = j + 1
                elif ch == "u":
                    j, ch = self.uEscape(str, j+1, startline)
                    ustr = ustr + ch
                else:
                    raise BadSyntax(self._thisDoc, self.lines, str, i,
                                    "bad escape")

        raise BadSyntax(self._thisDoc, self.lines, str, i,
                        "unterminated string literal")


    def uEscape(self, str, i, startline):
        j = i
        count = 0
        value = 0
        while count < 4:  # Get 4 more characters
            ch = str[j:j+1].lower()  # sbp http://ilrt.org/discovery/chatlogs/rdfig/2002-07-05
            j = j + 1
            if ch == "":
                raise BadSyntax(self._thisDoc, startline, str, i,
                                "unterminated string literal(3)")
            k = string.find("0123456789abcdef", ch)
            if k < 0:
                raise BadSyntax(self._thisDoc, startline, str, i,
                                "bad string literal hex escape")
            value = value * 16 + k
            count = count + 1
        uch = unichr(value)
        return j, uch


# If we are going to do operators then they should generate
#  [  is  operator:plus  of (  \1  \2 ) ]


class BadSyntax(SyntaxError):
    def __init__(self, uri, lines, str, i, why):
	self._str = str.encode('utf-8') # Better go back to strings for errors
	self._i = i
	self._why = why
	self.lines = lines
	self._uri = uri 

    def __str__(self):
	str = self._str
	i = self._i
	st = 0
	if i>60:
	    pre="..."
	    st = i - 60
	else: pre=""
	if len(str)-i > 60: post="..."
	else: post=""

	return 'Line %i of <%s>: Bad syntax (%s) at ^ in:\n"%s%s^%s%s"' \
	       % (self.lines +1, self._uri, self._why, pre, str[st:i], str[i:i+60], post)



def stripCR(str):
    res = ""
    for ch in str:
        if ch != "\r":
            res = res + ch
    return res

############################################################################################
    
class ToN3(RDFSink.RDFSink):
    """Serializer output sink for N3
    
      keeps track of most recent subject and predicate reuses them.
      Adapted from Dan's ToRDFParser(Parser);
    """

    flagDocumentation = """Flags for N3 output are as follows:-
        
a   Anonymous nodes should be output using the _: convention (p flag or not).
d   Don't use default namespace (empty prefix)
i   Use identifiers from store - don't regen on output
l   List syntax suppression. Don't use (..)
n   No numeric syntax - use strings typed with ^^ syntax
p   Prefix suppression - don't use them, always URIs in <> instead of qnames.
q   Quiet - don't make comments about the environment in which processing was done.
r   Relative URI suppression. Always use absolute URIs.
s   Subject must be explicit for every statement. Don't use ";" shorthand.
t   "this" and "()" special syntax should be suppresed.
"""
# "



#   A word about regenerated Ids.
#
# Within the program, the URI of a resource is kept the same, and in fact
# tampering with it would leave risk of all kinds of inconsistencies.
# Hwoever, on output, where there are URIs whose values are irrelevant,
# such as variables and generated IDs from anonymous ndoes, it makes the
# document very much more readable to regenerate the IDs.
#  We use here a convention that underscores at the start of fragment IDs
# are reserved for generated Ids. The caller can change that.
#
# Now there is a new way of generating these, with the "_" prefix for anonymous nodes.

    def __init__(self, write, base=None, genPrefix = None, noLists=0 , quiet=0, flags=""):
	gp = genPrefix
	if gp == None:
	    if base==None: gp = "#_g"
	    else: gp = uripath.join(base, "#_g")
	RDFSink.RDFSink.__init__(self, gp)
	self._write = write
	self._quiet = quiet or "q" in flags
	self._flags = flags
	self._subj = None
	self.prefixes = {}      # Look up prefix conventions
	self.defaultNamespace = None
	self.indent = 1         # Level of nesting of output
	self.base = base
#	self.nextId = 0         # Regenerate Ids on output
	self.regen = {}         # Mapping of regenerated Ids
#	self.genPrefix = genPrefix  # Prefix for generated URIs on output
	self.stack = [ 0 ]      # List mode?
	self.noLists = noLists  # Suppress generation of lists?
	self._anonymousNodes = [] # For "a" flag

        if "l" in self._flags: self.noLists = 1
	
    
#    def newId(self):
#        nextId = nextId + 1
#        return nextId - 1

    def setDefaultNamespace(self, uri):
        return self.bind("", uri)
    
    def bind(self, prefixString, uri):
        """ Just accepting a convention here """
        assert ':' in uri # absolute URI references only
        if "p" in self._flags: return  # Ignore the prefix system completely
        if not prefixString:
            raise RuntimError("Please use setDefaultNamespace instead")
        
        if (uri == self.defaultNamespace
            and "d" not in self._flags): return # don't duplicate ??
        self._endStatement()
        self.prefixes[uri] = prefixString
        self._write(" @prefix %s: <%s> ." % (prefixString, refTo(self.base, uri)) )
        self._newline()

    def setDefaultNamespace(self, uri):
        if "d" in self._flags or "p" in self._flags: return  # Ignore the prefix system completely
        self._endStatement()
        self.defaultNamespace = uri
	if self.base:  # Sometimes there is none, and nowadays refTo is intolerant
	    x = refTo(self.base, uri)
	else:
	    x = uri
        self._write(" @prefix : <%s> ." % x )
        self._newline()
       

    def startDoc(self):
 
        if not self._quiet:  # Suppress stuff which will confuse test diffs
            self._write("\n#  Notation3 generation by\n")
            idstring = "$Id$" # CVS CHANGES THIS
            self._write("#       " + idstring[5:-2] + "\n\n") # Strip $s in case result is checked in
            if self.base: self._write("#   Base was: " + self.base + "\n")
        self._write("    " * self.indent)
        self._subj = None
#        self._nextId = 0

    def endDoc(self, rootFormulaPair=None):
	self._endStatement()
	self._write("\n")
	if not self._quiet: self._write("#ENDS\n")
	return  # No formula returned - this is not a store

    def makeComment(self, str):
        for line in string.split(str, "\n"):
            self._write("#" + line + "\n")  # Newline order??@@
        self._write("    " * self.indent + "    ")


    def _newline(self, extra=0):
        self._write("\n"+ "    " * (self.indent+extra))

    def makeStatement(self, triple, why=None):
        if self.stack[-1]:
            if 1:  # DAML_LISTS
                if triple[PRED] == N3_first:
                    self._write(self.representationOf(triple[CONTEXT], triple[OBJ])+" ")
                elif triple[PRED] == RDF_type and triple[OBJ] == N3_List:
                    pass  # We knew
                elif triple[PRED] == RDF_type and triple[OBJ] == N3_Empty:
                    pass  # not how we would have put it but never mind
                elif triple[PRED] != N3_rest:
                    raise RuntimeError ("Should only see first and rest in list mode", triple)
            else: # compact lists
                self._write(self.representationOf(triple[CONTEXT], triple[OBJ])+" ")
            return
        
        if ("a" in self._flags and
            triple[PRED] == (SYMBOL, N3_forSome_URI) and
            triple[CONTEXT] == triple[SUBJ]):   # We assume the output is flat @@@
            self._anonymousNodes.append(triple[OBJ])
            return

        self._makeSubjPred(triple[CONTEXT], triple[SUBJ], triple[PRED])        
        self._write(self.representationOf(triple[CONTEXT], triple[OBJ]))
        
# Below is for writing an anonymous node which is the object of only one arc        
    def startAnonymous(self,  triple, isList=0):
        if isList and not self.noLists:
            wasList = self.stack[-1]
            if wasList and (triple[PRED]==N3_rest) :   # rest p of existing list
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

    def startAnonymousNode(self, subj, isList=0):
        self.stack.append(isList)
        if self._subj:
            self._write(" .")
        self._newline()
        self.indent = self.indent + 1
        if isList: self._write("  ( ")
        else: self._write("  [ ")
        self._subj = subj    # The object is not the subject context
        self._pred = None


    def endAnonymousNode(self, subj=None):    # Remove default subject
        isList = self.stack.pop()
        if isList: self._write(" )")
        else: self._write(" ]")
        if not subj: self._write(".")
        self.indent = self.indent - 1
        self._newline()
        self._subj = subj
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
        self.indent = self.indent - 1
        self._write("}")
        self._subj = subj
        self._pred = None
     
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
 #       self._makeSubjPred(somecontext, subj, ( SYMBOL,  DAML_equivalentTo_URI ))
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
        
        if self._subj != subj or "s" in self._flags:
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

            if pred == ( SYMBOL,  DAML_equivalentTo_URI ) and "t" not in self._flags:
                self._write(" = ")
#            elif pred == ( SYMBOL,  LOG_implies_URI ) and "t" not in self._flags:
#                self._write(" => ")
            elif pred == ( SYMBOL, RDF_type_URI )  and "t" not in self._flags:
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

        Regenerates genids if required.
        Uses prefix dictionary to use qname syntax if possible.
        """

        if "t" not in self._flags:
            if pair == context:
                return "this"
            if pair == N3_nil and not self.noLists:
                return"()"

        ty, value = pair

        if ty == LITERAL:
	    if type(value) is not types.TupleType:  # simple old-fashioned string
		return stringToN3(value)
	    s, dt, lang = value
	    if dt != None:
		dt_uri = dt.uriref()		 
		if (dt_uri == INTEGER_DATATYPE or
		    dt_uri == FLOAT_DATATYPE) and "n" not in self._flags:
		    return s    # Naked numeric value
	    str = stringToN3(s)
	    if lang != None: str = str + "@" + lang
	    if dt != None: str = str + "^^" + self.representationOf(context, dt.asPair())
	    return str

        if pair in self._anonymousNodes:   # "a" flags only
            i = value.find(self._genPrefix + "g")  # One of our conversions?
            if i >= 0:
                str = value[i+len(self._genPrefix)+1:]
            else:
                if verbosity()>10: progress("#@@@@@ Ooops ---  anon "+
		    value+"\n with genPrefix "+self._genPrefix+"\n")
                i = len(value)
                while i > 0 and value[i-1] not in _notNameChars: i = i - 1
                str = value[i:]
	    while str.startswith("_"): str = str[1:] # Strip that leading "_" which ntriples doesn't allow
            return "_:a" + str    # Must start with alpha as per NTriples spec.

        if ((ty == ANONYMOUS)
            and not option_noregen and "i" not in self._flags ):
                x = self.regen.get(value, None)
                if x == None:
		    x = self.genId()
                    self.regen[value] = x
		value = x
#                return "<"+x+">"


        j = string.rfind(value, "#")
	if j<0: j=string.rfind(value, "/")   # Allow "/" namespaces as a second best
        if (j>=0
            and "p" not in self._flags   # Suppress use of prefixes?
            and value[j+1:].find(".") <0 ): # Can't use prefix if localname includes "."
#            print "|%s|%s|"%(self.defaultNamespace, value[:j+1])
            if (self.defaultNamespace
                and self.defaultNamespace == value[:j+1]
                and "d" not in self._flags):
                return ":"+value[j+1:]
            prefix = self.prefixes.get(value[:j+1], None) # @@ #CONVENTION
            if prefix != None : return prefix + ":" + value[j+1:]
        
            if value[:j] == self.base:   # If local to output stream,
                return "<#" + value[j+1:] + ">" #   use local frag id (@@ lone word?)
            
        if "r" in self._flags: return "<" + hexify(value) + ">"    # Suppress relative URIs?

        return "<" + refTo(self.base, value) + ">"    # Everything else

###################################################
#
#   Utilities
#

Escapes = {'a':  '\a',
           'b':  '\b',
           'f':  '\f',
           'r':  '\r',
           't':  '\t',
           'v':  '\v',
           'n':  '\n',
           '\\': '\\',
           '"':  '"'}

forbidden1 = re.compile(ur'[\\\"\a\b\f\r\v\u0080-\uffff]')
forbidden2 = re.compile(ur'[\\\"\a\b\f\r\v\t\n\u0080-\uffff]')
#"
def stringToN3(str):
    res = ''
    if (len(str) > 20 and
        str[-1] <> '"' and
        (string.find(str, "\n") >=0 
         or string.find(str, '"') >=0)):
        delim= '"""'
        forbidden = forbidden1   # (allow tabs too now)
    else:
        delim = '"'
        forbidden = forbidden2
        
    i = 0
    while i < len(str):
        m = forbidden.search(str, i)
        if not m:
            break

        j = m.start()
        res = res + str[i:j]
        ch = m.group(0)
        if ch == '"' and delim == '"""' and str[j:j+3] != '"""':
            res = res + ch
        else:
            k = string.find('\a\b\f\r\t\v\n\\"', ch)
            if k >= 0: res = res + "\\" + 'abfrtvn\\"'[k]
            else:
#                res = res + ('\\u%04x' % ord(ch))
                res = res + ('\\u%04X' % ord(ch))  # http://www.w3.org/TR/rdf-testcases/#ntriples
        i = j + 1

    return delim + res + str[i:] + delim

def hexify(ustr):
    """Use URL encoding to return an ASCII string corresponding to the given unicode"""
#    progress("String is "+`ustr`)
#    s1=ustr.encode('utf-8')
    str  = ""
    for ch in ustr:  # .encode('utf-8'):
	if ord(ch) > 126:
	    ch = "%%%02X" % ord(ch)
	else:
	    ch = "%c" % ord(ch)
	str = str + ch
    return str
    
def dummy():
        res = ""
        if len(str) > 20 and (string.find(str, "\n") >=0 or string.find(str, '"') >=0):
                delim= '"""'
                forbidden = "\\\"\a\b\f\r\v"    # (allow tabs too now)
        else:
                delim = '"'
                forbidden = "\\\"\a\b\f\r\v\t\n"
        for i in range(len(str)):
                ch = str[i]
                j = string.find(forbidden, ch)
                if ch == '"' and delim == '"""' and i+1 < len(str) and str[i+1] != '"':
                    j=-1   # Single quotes don't need escaping in long format
                if j>=0: ch = "\\" + '\\"abfrvtn'[j]
                elif ch not in "\n\t" and (ch < " " or ch > "}"):
                    ch = "[[" + `ch` + "]]" #[2:-1] # Use python
                res = res + ch
        return delim + res + delim


#########################################################
#
#    Reifier
#
# Use:
#   sink = notation3.Reifier(sink, outputContextURI, flat)


class Reifier(RDFSink.RDFSink):

    def __init__(self, sink, inputContextURI, flat=0, genPrefix=None):
        RDFSink.RDFSink.__init__(self)
        self._sink = sink
        self._ns = "http://www.w3.org/2000/10/swap/model.n3#"
        self._sink.bind("n3", self._ns)
#        self._nextId = 1
#        self._genPrefix = genPrefix
        self._flat = flat      # Just flatten things not in this context
	contextURI = inputContextURI + "__reified"
	self._formula = sink.newFormula(contextURI) # Formula node is what the document parses to @@kludge
        self._context = self._formula

        if self._genPrefix == None:
            self._genPrefix = string.split(contextURI,"#")[0] + "#_rei"
        
    def bind(self, prefix, uri):
        self._sink.bind(prefix, uri)
               
    def makeStatement(self, tuple, why=None):  # Quad of (type, value) pairs
        _statementURI = self._genPrefix + `self._nextId`
        self._nextId = self._nextId + 1
        N3_NS = "http://www.w3.org/2000/10/swap/model.n3#"
        name = "context", "predicate", "subject", "object"

        if verbosity() > 50: progress("Reifying in  contexts stg with context %s."%(self._context,tuple[CONTEXT]))
        if self._flat and tuple[CONTEXT] == self._context:
            return self._sink.makeStatement(tuple)   # In same context: does not need reifying

        self._sink.makeStatement(( self._context, # quantifiers - use inverse?
                                  (SYMBOL, N3_forSome_URI),
                                  self._context,
                                  (SYMBOL, _statementURI) )) #  Note this is anonymous
        
        self._sink.makeStatement(( self._context, # Context
                              (SYMBOL, self._ns+"statement"), #Predicate
                              tuple[CONTEXT], # Subject
                              (SYMBOL, _statementURI) ))  # Object

        for i in PARTS:
            self._sink.makeStatement((
                self._context, # Context
                (SYMBOL, self._ns+name[i]), #Predicate
                (SYMBOL, _statementURI), # Subject
                tuple[i] ))  # Object


    def makeComment(self, str):
        return self._sink.makeComment(str) 

    def startDoc(self):
        return self._sink.startDoc()

    def endDoc(self, rootFormulaPair=None):
        return self._sink.endDoc(self._formula)

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

    r=SinkParser(ToN3(sys.stdout.write, base=thisURI),
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
        thing.setVerbosity(0)          # not too verbose please
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
	
        _outURI = uripath.join(_baseURI, "STDOUT")
	if option_rdf1out:
            _sink = ToRDF(sys.stdout, _outURI)
        else:
            _sink = ToN3(sys.stdout.write, base=_outURI)
        _sink.makeComment("# Base URI of process is " + _baseURI)
        
#  Parse and regenerate RDF in whatever notation:

        inputContexts = []
        for i in option_inputs:
            _inputURI = uripath.join(_baseURI, i) # Make abs from relative
            p = SinkParser(_sink,  _inputURI)
            p.load(_inputURI)
            del(p)

        if option_inputs == []:
            _inputURI = uripath.join( _baseURI, "STDIN") # Make abs from relative
            p = SinkParser(_sink,  _inputURI)
            p.load("")
            del(p)

        return




############################################################ Main program
    
if __name__ == '__main__':
    import os
    if os.environ.has_key('SCRIPT_NAME'):
        serveRequest(os.environ)
    else:
        doCommand()

#ends
