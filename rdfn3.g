# rfdn3.g -- a Yapps grammar for RDF Notation 3
#
# 
# Share and Enjoy. Open Source license:
# Copyright (c) 2001 W3C (MIT, INRIA, Keio)
# http://www.w3.org/Consortium/Legal/copyright-software-19980720
# $Id$
# see log at end
#
# REFERENCES
# Yapps: Yet Another Python Parser System
# http://theory.stanford.edu/~amitp/Yapps/
# Sat, 18 Aug 2001 16:54:32 GMT
# Last modified 13:21 Sun 26 Nov 2000 , Amit Patel 
#
# http://www.w3.org/DesignIssues/Notation3

import string
import urlparse # for urljoin. hmm... @@patch bugs?
import RDFSink # for FORMULA, SYMBOL
import notation3

%%
parser _Parser:
    ignore: r'\s+'         # whitespace. @@count lines?
    ignore: r'#.*\r?\n'    # n3 comments; sh/perl style

    token URIREF:   r'<[^ >]*>'
    token PREFIX:   r'[a-zA-Z0-9_-]*:'
    token QNAME:    r'([a-zA-Z][a-zA-Z0-9_-]*)?:[a-zA-Z0-9_-]+'
    token EXVAR:    r'_:[a-zA-Z0-9_-]+'
    token UVAR:     r'\?[a-zA-Z0-9_-]+'
    token INTLIT:   r'-?\d+'
    token TYPEDLIT: r'(string|boolean|decimal|float|double|duration|dateTime|time|date|gYearMonth|gYear|gMonthDay|gDay|gMonth|hexBinary|base64Binary|anyURI|normalizedString|token|language|Name|NCName|integer|nonPositiveInteger|negativeInteger|long|int|short|byte|nonNegativeInteger|unsignedLong|unsignedInt|unsignedShort|unsignedByte|positiveInteger)"([^\"\\\n]|\\[\\\"nrt])*"'
    token STRLIT1:  r'"([^\"\\\n]|\\[\\\"nrt])*"'
    token STRLIT2:  r"'([^\'\\\n]|\\[\\\'nrt])*'"
    token STRLIT3:  r'"""([^\"\\]|\\[\\\"nrt])*"""' #@@not right
    token END:      r'\Z'

    rule document:
              {{ self.bindListPrefix(); scp = self.docScope() }}
         ( directive | statement<<scp>> ) * END

    rule directive : "@prefix" PREFIX URIREF "\\."
              {{ self.bind(PREFIX[:-1], URIREF) }}

    # foos0 is mnemonic for 0 or more foos
    # foos1      "          1 or more foos

    rule statement<<scp>> : clause_ind<<scp>> "\\."

    rule clause_ind<<scp>>:
         phrase<<scp>>
           [predicate<<scp, phrase>> (";" [predicate<<scp, phrase>>])* ]
       | term<<scp>>
            predicate<<scp, term>> (";" [predicate<<scp, term>>])*

    rule term<<scp>>:
                expr<<scp>>     {{ return expr }}
              | name           {{ return name }}
              
    rule predicate<<scp,subj>>: verb<<scp>> objects1<<scp,subj,verb>>

    rule verb<<scp>> :
          term<<scp>>           {{ return (1, term) }}
        | "is" term<<scp>> "of" {{ return (-1, term) }}
    # earlier N3 specs had more verb sugar...


    # This is the central rule for recognizing a fact.
    rule objects1<<scp,subj,verb>> :
        term<<scp>>  {{ self.gotStatement(scp, subj, verb, term) }}
        ("," term<<scp>>
                     {{ self.gotStatement(scp, subj, verb, term) }}
         )*


    # details about terms...

    rule name:
                URIREF        {{ return self.uriref(URIREF) }}
              | QNAME         {{ return self.qname(QNAME) }}
              | "a"           {{ return self.termA() }}
              | "="           {{ return self.termEq() }}

    rule expr<<scp>>:
                "this"        {{ return scp }}
              | EXVAR         {{ return self.lname(EXVAR) }}
              | UVAR          {{ return self.vname(UVAR) }}
              | INTLIT        {{ return self.intLit(INTLIT) }}
              | TYPEDLIT      {{ return self.typedLit(TYPEDLIT) }}
              | STRLIT3       {{ return self.strlit(STRLIT3, '"""') }}
              | STRLIT1       {{ return self.strlit(STRLIT1, '"') }}
              | STRLIT2       {{ return self.strlit(STRLIT2, "'") }}
              | list<<scp>>   {{ return list }}
              | phrase<<scp>> {{ return phrase }}
              | clause_sub    {{ return clause_sub }}

    rule list<<scp>> : "\\(" {{ items = [] }}
	 item<<scp, items>> *
	 "\\)" {{ return self.mkList(scp, items) }}

    rule item<<scp, items>> : term<<scp>> {{ items.append(term) }}

    rule phrase<<scp>>:
        "\\[" {{ subj = self.something(scp) }}
        [predicate<<scp, subj>> (";" predicate<<scp, subj>>)* [";"] ]
        "\\]" {{ return subj }}

    rule clause_sub:
        "{" {{ scp = self.newScope() }}
        [ clause_ind<<scp>> ("\\." clause_ind<<scp>>)* ["\\."]]
        "}" {{ return scp }}

%%

def scanner(text):
    return _ParserScanner(text)

class BadSyntax(SyntaxError):
    pass

# base types of XML Schema datatypes
# this maps types either to the name
# of a base type or to a python
# value whose type can hold the values
# of the XML Schema type.
# e.g. int => 1
#      long => 1L
# hmm.. still thinking about datetime...
base = {'normalizedString': 'string',
        'token': 'string',
        'language': 'string',
        'Name': 'string',
        'NCName': 'string',
        'integer': 1L,
        'nonPositiveInteger': 1L,
        'negativeInteger' : 1L,
        'long': 1L,
        'int': 1,
        'short': 1,
        'byte': 1,
        'nonNegativeInteger': 1L,
	'unsignedLong': 1L,
	'unsignedInt': 1L,
	'unsignedShort': 1,
	'unsignedByte': 1,
	'positiveInteger': 1L}

class Parser(_Parser):
    def __init__(self, scanner, sink, baseURI):
        _Parser.__init__(self, scanner)
        self._sink = sink
        self._baseURI = baseURI
        self._prefixes = {}
        self._serial = 1
        self._lnames = {}
        self._vnames = {}

    def docScope(self):
        return mkFormula(self._baseURI)

    def uriref(self, str):
        return RDFSink.SYMBOL, urlparse.urljoin(self._baseURI, str[1:-1])

    def qname(self, str):
        i = string.find(str, ":")
        pfx = str[:i]
        ln = str[i+1:]
        try:
            ns = self._prefixes[pfx]
        except:
            raise BadSyntax, "prefix %s not bound" % pfx
        else:
            return RDFSink.SYMBOL, ns + ln

    def lname(self, str):
        n = str[2:]
        try:
            return self._lnames[n]
        except KeyError:
            x = self.something(self.docScope(), n)
            self._lnames[n] = x
            return x

    def vname(self, str):
        n = str[1:]
        try:
            return self._vnames[n]
        except KeyError:
            x = self.something(self.docScope(), n,
                               quant=RDFSink.forAllSym)
            self._vnames[n] = x
            return x

    def termA(self):
        return notation3.RDF_type
    
    def termEq(self):
        return notation3.DAML_equivalentTo

    def strlit(self, str, delim):
        return RDFSink.LITERAL, str[1:-1] #@@BROKEN

    def intLit(self, str):
        try:
            v = int(str)
        except ValueError:
            v = long(str)
        return RDFSink.LITERAL, v #@@ other than LITERAL?

    def typedLit(self, str):
	qindex = index(str, '"')
	ty = str[:qindex]
	str = str[qindex+1:-1]
        # convert to primitive type
        ty = base.get(ty, ty)
        if ty == 'string':
            return RDFSink.LITERAL, str
        elif type(ty) is type(''):
            return RDFSink.LITERAL, (ty, str) #@@ other than LITERAL?
        else:
            return self.intLit(str)

    def bindListPrefix(self):
        self._sink.bind("l", (RDFSink.SYMBOL, notation3.N3_nil[1][:-3]))
    
    def bind(self, pfx, ref):
        ref = ref[1:-1] # take of <>'s
        if ref[-1] == '#': # @@work around bug in urljoin...
            sep = '#'
            ref = ref[:-1]
        else: sep = ''
        addr = urlparse.urljoin(self._baseURI, ref) + sep
        #DEBUG("bind", pfx, ref, addr)
        self._sink.bind(pfx, (RDFSink.SYMBOL, addr))
        #@@ check for pfx already bound?
        self._prefixes[pfx] = addr

    def gotStatement(self, scp, subj, verb, obj):
	#DEBUG("gotStatement:", scp, subj, verb, obj)
        
        dir, pred = verb
        if dir<0: subj, obj = obj, subj
        self._sink.makeStatement((scp, pred, subj, obj))

    def newScope(self):
        return self.something(self.docScope(),
                              "clause", RDFSink.FORMULA)

    def something(self, scp, hint="thing",
                  ty=RDFSink.SYMBOL,
                  quant = RDFSink.forSomeSym):
        it = (ty, "%s#%s_%s" % (self._baseURI, hint, self._serial))

        p = (RDFSink.SYMBOL, quant)
        self._sink.makeStatement((scp, p, scp, it))

        self._serial = self._serial + 1
        return it


    def mkList(self, scp, items):
	tail = None
	head = notation3.N3_nil
	say = self._sink.makeStatement
	for term in items:
	    cons = self.something(scp, "cons")
	    say((scp, notation3.N3_first, cons, term))
	    if tail:
	        say((scp, notation3.N3_rest, tail, cons))
	    tail = cons
	    if not head: head = cons
	if tail:
	    say((scp, notation3.N3_rest, tail, notation3.N3_nil))
	return head

def mkFormula(absURI):
    """move this somewhere else?"""
    return RDFSink.FORMULA, absURI + "#_formula" #@@KLUDGE from notation3.py, cwm.py

def DEBUG(*args):
    import sys
    for a in args:
        sys.stderr.write("%s " % (a,))
    sys.stderr.write("\n")
    
# $Log$
# Revision 1.16  2002-08-07 16:01:23  connolly
# working on datatypes
#
# Revision 1.15  2002/06/21 16:04:02  connolly
# implemented list handling
#
# Revision 1.14  2002/01/12 23:37:14  connolly
# allow . after ;
#
# Revision 1.13  2001/09/06 19:55:13  connolly
# started N3 list semantics. got KIFSink working well enough to discuss
#
# Revision 1.12  2001/09/01 05:56:28  connolly
# the name rule does not need a scope param
#
# Revision 1.11  2001/09/01 05:31:17  connolly
# - gram2html.py generates HTML version of grammar from rdfn3.g
# - make use of [] in rdfn3.g
# - more inline terminals
# - jargon change: scopes rather than contexts
# - term rule split into name, expr; got rid of shorthand
#
# Revision 1.10  2001/08/31 22:59:58  connolly
# ?foo for universally quantified variables; document-scoped, ala _:foo
#
# Revision 1.9  2001/08/31 22:27:57  connolly
# added support for _:foo as per n-triples
#
# Revision 1.8  2001/08/31 22:15:44  connolly
# aha! fixed serious arg-ordering bug; a few other small clean-ups
#
# Revision 1.7  2001/08/31 21:28:39  connolly
# quick release for others to test
#
# Revision 1.6  2001/08/31 21:14:11  connolly
# semantic actions are starting to work;
# anonymous stuff ( {}, [] ) doesn't seem
# to be handled correctly yet.
#
# Revision 1.5  2001/08/31 19:10:58  connolly
# moved term rule for easier reading
#
# Revision 1.4  2001/08/31 19:06:20  connolly
# added END/eof token
#
# Revision 1.3  2001/08/31 18:55:47  connolly
# cosmetic/naming tweaks
#
# Revision 1.2  2001/08/31 18:46:59  connolly
# parses test/vocabCheck.n3
#
# Revision 1.1  2001/08/31 17:51:08  connolly
# starting to work...
#
