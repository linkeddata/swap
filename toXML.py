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



import string
import codecs # python 2-ism; for writing utf-8 in RDF/xml output
import urlparse
import urllib
import re
import thing
from thing import relativeURI

import RDFSink

from notation3 import relativeURI

from RDFSink import CONTEXT, PRED, SUBJ, OBJ, PARTS, ALL4
from RDFSink import FORMULA, LITERAL, ANONYMOUS, VARIABLE, SYMBOL
from RDFSink import Logic_NS

N3_forSome_URI = RDFSink.forSomeSym
N3_forAll_URI = RDFSink.forAllSym

# Magic resources we know about

RDF_type_URI = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
RDF_NS_URI = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
DAML_NS=DPO_NS = "http://www.daml.org/2001/03/daml+oil#"  # DAML plus oil
DAML_equivalentTo_URI = DPO_NS+"equivalentTo"
parsesTo_URI = Logic_NS + "parsesTo"
RDF_spec = "http://www.w3.org/TR/REC-rdf-syntax/"

ADDED_HASH = "#"  # Stop where we use this in case we want to remove it!
# This is the hash on namespace URIs

# Should the internal representation of lists be with DAML:first and :rest?
DAML_LISTS = 1    # Else don't do these - do the funny compact ones- not a good idea after all

RDF_type = ( SYMBOL , RDF_type_URI )
DAML_equivalentTo = ( SYMBOL, DAML_equivalentTo_URI )

List_NS = DPO_NS     # We have to pick just one all the time

# For lists:
N3_first = (SYMBOL, List_NS + "first")
N3_rest = (SYMBOL, List_NS + "rest")
# N3_only = (SYMBOL, List_NS + "only")
N3_nil = (SYMBOL, List_NS + "nil")
N3_List = (SYMBOL, List_NS + "List")
N3_Empty = (SYMBOL, List_NS + "Empty")



option_noregen = 0   # If set, do not regenerate genids on output


########################## RDF 1.0 Syntax generator

global _namechars	
_namechars = string.lowercase + string.uppercase + string.digits + '_-'
	    
class ToRDF(RDFSink.RDFSink):
    """keeps track of most recent subject, reuses it"""

    _valChars = string.lowercase + string.uppercase + string.digits + "_ !#$%&().,+*/"
    #@ Not actually complete, and can encode anyway
    def __init__(self, outFp, thisURI, base=None, flags=""):
        RDFSink.RDFSink.__init__(self)
        dummyEnc, dummyDec, dummyReader, encWriter = codecs.lookup('utf-8')
	self._wr = XMLWriter(encWriter(outFp))
	self._subj = None
	self._base = base
	if base == None: self._base = thisURI
	self._thisDoc = thisURI
	self._flags = flags
	self._docOpen = 0  # Delay doc open <rdf:RDF .. till after binds

    #@@I18N
    _rdfns = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'

    def startDoc(self):
        pass

    flagDocumentation = """
        Flags to control RDF/XML output (after --rdf=) areas follows:
        
        c  - Don't use elements as class names
        d  - Don't use default namespace

"""

    def endDoc(self, rootFormulaPair=None):
        self.flushStart()  # Note: can't just leave empty doc if not started: bad XML
	if self._subj:
	    self._wr.endElement()  # </rdf:Description>
	self._subj = None
	self._wr.endElement()  # </rdf:RDF>
	self._wr.endDocument()

    def makeComment(self, str):
        self._wr.makeComment(str)

    def flushStart(self):
        if not self._docOpen:
            if self.prefixes.get((SYMBOL, RDF_NS_URI), ":::") == ":::":
                if self.namespaces.get("rdf", ":::") ==":::":
                    self.bind("rdf", (SYMBOL, RDF_NS_URI))
            if self.prefixes.get((SYMBOL, Logic_NS), ":::") == ":::":
                if self.namespaces.get("log", ":::") ==":::":
                    self.bind("log", (SYMBOL, Logic_NS))
            ats = []
            ps = self.prefixes.values()
            ps.sort()    # Cannonicalize output somewhat
            if self.defaultNamespace and "d" not in self._flags:
                ats.append(('xmlns',self.defaultNamespace[1]))
            for pfx in ps:
#                if pfx:
                    ats.append(('xmlns:'+pfx, self.namespaces[pfx][1]))
#                else:
#                    ats.append(('xmlns', self.namespaces[pfx][1]))
            self._wr.startElement(RDF_NS_URI+'RDF', ats, self.prefixes)
            self._subj = None
            self._nextId = 0
            self._docOpen = 1

    def makeStatement(self,  tuple):
        self.flushStart()
        context, pred, subj, obj = tuple # Context is ignored
	predn = relativeURI(self._base, pred[1])
	subjn = relativeURI(self._base, subj[1])

	if self._subj != subj:
	    if self._subj:
		self._wr.endElement()
	    self._subj = subj
            if (pred == (SYMBOL, RDF_type_URI)# Special case starting with rdf:type as element name
                and obj[0] != LITERAL
                and "c" not in self._flags): # "c" flag suppresses class element syntax on RDF output
                 self._wr.startElement(obj[1], [(RDF_NS_URI+" about", subjn),], self.prefixes)
                 return
            self._wr.startElement(RDF_NS_URI+'Description',
				 [(RDF_NS_URI+" about", subjn),], self.prefixes)

	if obj[0] != LITERAL: 
	    objn = relativeURI(self._base, obj[1])
	    self._wr.emptyElement(pred[1], [(RDF_NS_URI+' resource', objn)], self.prefixes)
	    return
# Actually this "value=" shorthand notation is *not* RDF! It was my misunderstanding! rats...
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
	    subjn = relativeURI(self._base, subj[1])
	    self._wr.startElement(RDF_NS_URI + 'Description',
				 ((RDF_NS_URI+' about', subjn),), self.prefixes)
	    self._subj = subj

        self._wr.startElement(pred[1], [(RDF_NS_URI+' parseType','Resource')], self.prefixes)  # @@? Parsetype RDF

        self._subj = obj    # The object is now the current subject


    def endAnonymous(self, subject, verb):    # Remind me where we are

        self._wr.endElement()
#        self._subj = subject
        self._subj = subject       # @@@ This all needs to be thought about!


# Below we do anonymous top level node - arrows only leave this circle

    def startAnonymousNode(self, subj, li=0):
        self.flushStart()
        if self._subj:
            self._wr.endElement()
            self._subj = None
        self._wr.startElement(RDF_NS_URI+'Description', [], self.prefixes)
        self._subj = subj    # The object is not the subject context
#        self._pred = None

    def endAnonymousNode(self, subj=None):    # Remove context
    	self._wr.endElement()
	self._subj = None
#        self._pred = None

# Below we notate a nested bag of statements - a context

    def startBagSubject(self, context):  # Doesn't work with RDF sorry ILLEGAL
        self.flushStart()
        self._wr.startElement(RDF_NS_URI+'Description', 
			      [],
#			      [(RDF_NS_URI+' about', relativeURI(self._base,context[1]))],
                              self.prefixes)
#        print "# @@@@@@@@@@@@@ ", self.prefixes
        log_quote = self.prefixes[(SYMBOL, Logic_NS)] + ":Quote"  # Qname yuk
        
        self._wr.startElement(Logic_NS+"is", [(RDF_NS_URI+' parseType', log_quote)], self.prefixes)
        self._subj = None
#        self._pred = None


    def endBagSubject(self, subj):    # Remove context
        if self._subj:
            self._wr.endElement()   # End description if any
            self._subj = 0
        self._wr.endElement()     # End quote
        self._subj = subj
#       self._pred = None

    def startBagObject(self, tuple):
        self.flushStart()
        context, pred, subj, obj = tuple 
	if self._subj != subj:
	    if self._subj:
		self._wr.endElement()
	    subjn = relativeURI(self._base, subj[1])
	    self._wr.startElement(RDF_NS_URI + 'Description',
				 ((RDF_NS_URI+' about', subjn),), self.prefixes)
	    self._subj = subj

        log_quote = self.prefixes[(SYMBOL, Logic_NS)] + ":Quote"  # Qname yuk
        self._wr.startElement(pred[1], [(RDF_NS_URI+' parseType',log_quote)], self.prefixes)  # @@? Parsetype RDF
        self._subj = None
#        self._pred = None


    def endBagObject(self, pred, subj):    # Remove context
        if self._subj:
            self._wr.endElement()        #  </description> if any
            self._subj = None
        self._wr.endElement()           # end quote
        self._subj = pred   #@@@@@?
#        print "\nEnd bag object, pred=", `pred`[-12:]
#        self._pred = subj     

def relativeTo(here, there):
    print "### Relative to ", here[1], there[1]
    return relativeURI(here[1], there[1])
    

            
    
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

    _namechars = string.lowercase + string.uppercase + string.digits + '_-'


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
        prefix = prefixes.get((SYMBOL, ns), ":::")
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
            prefix = prefixes.get((SYMBOL, ans),":::")
            if prefix == ":::":
                print ("#@@@@@ tag %s: atr %s has no prefiex :-(" %
                       (uriref, at, `prefixes`))
                raise NoPrefixForAttributeError
            attrs.append(( prefix+":"+lan, val))    

	self.newline(3-len(self._elts))    # Newlines separate higher levels
	self._wr("<%s" % (ln,))

        needNL = 0
	for n, v in attrs:
            if needNL:
                self.newline()
                self._wr("   ")
	    self._wr(" %s=\"" % (n, ))
            xmldata(self._wr, v, self.attrEsc)
            self._wr("\"")
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


    dataEsc = re.compile(r"[\r<>&]")  # timbl removed \n as can be in data
    attrEsc = re.compile(r"[\r<>&'\"\n]")

    def data(self, str):
	#@@ throw an exception if the element stack is empty
	o = self._outFp
        self.flushClose()
        xmldata(o.write, str, self.dataEsc)
	self.noWS = 1  # Suppress whitespace - we are in data

    def endDocument(self):
        while len(self._elts) > 0:
            self.endElement()
        self.flushClose()
        self._wr("\n")


def xmldata(write, str, markupChars):
    i = 0
    while i < len(str):
        m = markupChars.search(str, i)
        if not m:
            write(str[i:])
            break
        j = m.start()
        write(str[i:j])
        write("&#%d;" % (ord(str[j]),))
        i = j + 1
    

#ends
