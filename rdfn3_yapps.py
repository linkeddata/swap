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

import uripath
from ConstTerm import Symbol, StringLiteral, Namespace

RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
LIST = Namespace("http://www.daml.org/2001/03/daml+oil#")
DPO = Namespace("http://www.daml.org/2001/03/daml+oil#")
LOG = Namespace("http://www.w3.org/2000/10/swap/log#")


from string import *
import re
from yappsrt import *

class _ParserScanner(Scanner):
    def __init__(self, str):
        Scanner.__init__(self,[
            ('"}"', '}'),
            ('"{"', '{'),
            ('"\\\\]"', '\\]'),
            ('"\\\\["', '\\['),
            ('"\\\\)"', '\\)'),
            ('"\\\\("', '\\('),
            ('"this"', 'this'),
            ('"="', '='),
            ('"a"', 'a'),
            ('","', ','),
            ('"of"', 'of'),
            ('"is"', 'is'),
            ('"@prefix"', '@prefix'),
            ('\\s+', '\\s+'),
            ('#.*\\r?\\n', '#.*\\r?\\n'),
            ('URIREF', '<[^ \\n>]*>'),
            ('PREFIX', '[a-zA-Z0-9_-]*:'),
            ('QNAME', '([a-zA-Z][a-zA-Z0-9_-]*)?:[a-zA-Z0-9_-]+'),
            ('EXVAR', '_:[a-zA-Z0-9_-]+'),
            ('UVAR', '\\?[a-zA-Z0-9_-]+'),
            ('INTLIT', '-?\\d+'),
            ('STRLIT1', '"([^\\"\\\\\\n]|\\\\[\\\\\\"nrt])*"'),
            ('STRLIT2', "'([^\\'\\\\\\n]|\\\\[\\\\\\'nrt])*'"),
            ('STRLIT3', '"""([^\\"\\\\]|\\\\[\\\\\\"nrt])*"""'),
            ('TERM', '\\.(?=\\s*})'),
            ('SEP', '\\.(?!\\s*})'),
            ('PTERM', ';(?=\\s*[\\.}])'),
            ('PSEP', ';(?!\\s*[\\.}])'),
            ('END', '\\Z'),
            ], ['\\s+', '#.*\\r?\\n'], str)

class _Parser(Parser):
    def document(self):
        self.bindListPrefix(); scp = self.docScope()
        while self._peek('END', '"@prefix"', '"\\\\["', '"this"', 'EXVAR', 'UVAR', 'INTLIT', 'STRLIT3', 'STRLIT1', 'STRLIT2', 'URIREF', 'QNAME', '"a"', '"="', '"\\\\("', '"{"') != 'END':
            _token_ = self._peek('"@prefix"', '"\\\\["', '"this"', 'EXVAR', 'UVAR', 'INTLIT', 'STRLIT3', 'STRLIT1', 'STRLIT2', 'URIREF', 'QNAME', '"a"', '"="', '"\\\\("', '"{"')
            if _token_ == '"@prefix"':
                directive = self.directive()
            else:                 statement = self.statement(scp)
        END = self._scan('END')

    def directive(self):
        self._scan('"@prefix"')
        PREFIX = self._scan('PREFIX')
        URIREF = self._scan('URIREF')
        SEP = self._scan('SEP')
        self.bind(PREFIX[:-1], URIREF)

    def statement(self, scp):
        clause_ind = self.clause_ind(scp)
        SEP = self._scan('SEP')

    def clause_ind(self, scp):
        _token_ = self._peek('"\\\\["', '"this"', 'EXVAR', 'UVAR', 'INTLIT', 'STRLIT3', 'STRLIT1', 'STRLIT2', 'URIREF', 'QNAME', '"a"', '"="', '"\\\\("', '"{"')
        if _token_ == '"\\\\["':
            phrase = self.phrase(scp)
            if self._peek('PSEP', 'PTERM', '"is"', '","', '"this"', 'EXVAR', 'UVAR', 'INTLIT', 'STRLIT3', 'STRLIT1', 'STRLIT2', 'URIREF', 'QNAME', '"a"', '"="', 'SEP', '"\\\\("', '"\\\\["', '"{"', 'TERM', '"\\\\]"', '"}"') not in ['PSEP', 'PTERM', '","', 'SEP', 'TERM', '"\\\\]"', '"}"']:
                predicate = self.predicate(scp, phrase)
                while self._peek('PSEP', '","', 'PTERM', 'SEP', '"\\\\]"', 'TERM', '"}"') == 'PSEP':
                    PSEP = self._scan('PSEP')
                    if self._peek('PSEP', '"is"', '","', '"this"', 'EXVAR', 'UVAR', 'INTLIT', 'STRLIT3', 'STRLIT1', 'STRLIT2', 'URIREF', 'QNAME', '"a"', '"="', 'PTERM', '"\\\\("', '"\\\\["', '"{"', 'SEP', '"\\\\]"', 'TERM', '"}"') not in ['PSEP', '","', 'PTERM', 'SEP', '"\\\\]"', 'TERM', '"}"']:
                        predicate = self.predicate(scp, phrase)
            if self._peek('PTERM', 'SEP', 'TERM', '"}"') == 'PTERM':
                PTERM = self._scan('PTERM')
        elif 1:
            term = self.term(scp)
            predicate = self.predicate(scp, term)
            while self._peek('PSEP', 'PTERM', '","', 'SEP', 'TERM', '"\\\\]"', '"}"') == 'PSEP':
                PSEP = self._scan('PSEP')
                if self._peek('PSEP', '"is"', '","', 'PTERM', '"this"', 'EXVAR', 'UVAR', 'INTLIT', 'STRLIT3', 'STRLIT1', 'STRLIT2', 'URIREF', 'QNAME', '"a"', '"="', '"\\\\("', '"\\\\["', '"{"', 'SEP', '"\\\\]"', 'TERM', '"}"') not in ['PSEP', '","', 'PTERM', 'SEP', '"\\\\]"', 'TERM', '"}"']:
                    predicate = self.predicate(scp, term)
            if self._peek('PTERM', 'SEP', 'TERM', '"}"') == 'PTERM':
                PTERM = self._scan('PTERM')

    def term(self, scp):
        _token_ = self._peek('"this"', 'EXVAR', 'UVAR', 'INTLIT', 'STRLIT3', 'STRLIT1', 'STRLIT2', 'URIREF', 'QNAME', '"a"', '"="', '"\\\\("', '"\\\\["', '"{"')
        if _token_ not in ['URIREF', 'QNAME', '"a"', '"="']:
            expr = self.expr(scp)
            return expr
        else: # in ['URIREF', 'QNAME', '"a"', '"="']
            name = self.name()
            return name

    def predicate(self, scp,subj):
        verb = self.verb(scp)
        objects1 = self.objects1(scp,subj,verb)

    def verb(self, scp):
        _token_ = self._peek('"is"', '"this"', 'EXVAR', 'UVAR', 'INTLIT', 'STRLIT3', 'STRLIT1', 'STRLIT2', 'URIREF', 'QNAME', '"a"', '"="', '"\\\\("', '"\\\\["', '"{"')
        if _token_ != '"is"':
            term = self.term(scp)
            return (1, term)
        else: # == '"is"'
            self._scan('"is"')
            term = self.term(scp)
            self._scan('"of"')
            return (-1, term)

    def objects1(self, scp,subj,verb):
        term = self.term(scp)
        self.gotStatement(scp, subj, verb, term)
        while self._peek('","', 'PSEP', 'PTERM', 'SEP', '"\\\\]"', 'TERM', '"}"') == '","':
            self._scan('","')
            term = self.term(scp)
            self.gotStatement(scp, subj, verb, term)

    def name(self):
        _token_ = self._peek('URIREF', 'QNAME', '"a"', '"="')
        if _token_ == 'URIREF':
            URIREF = self._scan('URIREF')
            return self.uriref(URIREF)
        elif _token_ == 'QNAME':
            QNAME = self._scan('QNAME')
            return self.qname(QNAME)
        elif _token_ == '"a"':
            self._scan('"a"')
            return self.termA()
        else: # == '"="'
            self._scan('"="')
            return self.termEq()

    def expr(self, scp):
        _token_ = self._peek('"this"', 'EXVAR', 'UVAR', 'INTLIT', 'STRLIT3', 'STRLIT1', 'STRLIT2', '"\\\\("', '"\\\\["', '"{"')
        if _token_ == '"this"':
            self._scan('"this"')
            return scp
        elif _token_ == 'EXVAR':
            EXVAR = self._scan('EXVAR')
            return self.lname(EXVAR)
        elif _token_ == 'UVAR':
            UVAR = self._scan('UVAR')
            return self.vname(UVAR)
        elif _token_ == 'INTLIT':
            INTLIT = self._scan('INTLIT')
            return self.intLit(INTLIT)
        elif _token_ == 'STRLIT3':
            STRLIT3 = self._scan('STRLIT3')
            return self.strlit(STRLIT3, '"""')
        elif _token_ == 'STRLIT1':
            STRLIT1 = self._scan('STRLIT1')
            return self.strlit(STRLIT1, '"')
        elif _token_ == 'STRLIT2':
            STRLIT2 = self._scan('STRLIT2')
            return self.strlit(STRLIT2, "'")
        elif _token_ == '"\\\\("':
            list = self.list(scp)
            return list
        elif _token_ == '"\\\\["':
            phrase = self.phrase(scp)
            return phrase
        else: # == '"{"'
            clause_sub = self.clause_sub()
            return clause_sub

    def list(self, scp):
        self._scan('"\\\\("')
        items = []
        while self._peek('"\\\\)"', '"this"', 'EXVAR', 'UVAR', 'INTLIT', 'STRLIT3', 'STRLIT1', 'STRLIT2', 'URIREF', 'QNAME', '"a"', '"="', '"\\\\("', '"\\\\["', '"{"') != '"\\\\)"':
            item = self.item(scp, items)
        self._scan('"\\\\)"')
        return self.mkList(scp, items)

    def item(self, scp, items):
        term = self.term(scp)
        items.append(term)

    def phrase(self, scp):
        self._scan('"\\\\["')
        subj = self.something(scp)
        if self._peek('"\\\\]"', '"is"', '"this"', 'EXVAR', 'UVAR', 'INTLIT', 'STRLIT3', 'STRLIT1', 'STRLIT2', 'URIREF', 'QNAME', '"a"', '"="', '"\\\\("', '"\\\\["', '"{"') != '"\\\\]"':
            predicate = self.predicate(scp, subj)
            while self._peek('PSEP', 'PTERM', '","', '"\\\\]"', 'SEP', 'TERM', '"}"') == 'PSEP':
                PSEP = self._scan('PSEP')
                predicate = self.predicate(scp, subj)
            if self._peek('PTERM', '"\\\\]"') == 'PTERM':
                PTERM = self._scan('PTERM')
        self._scan('"\\\\]"')
        return subj

    def clause_sub(self):
        self._scan('"{"')
        scp = self.newScope()
        if self._peek('"}"', '"\\\\["', '"this"', 'EXVAR', 'UVAR', 'INTLIT', 'STRLIT3', 'STRLIT1', 'STRLIT2', 'URIREF', 'QNAME', '"a"', '"="', '"\\\\("', '"{"') != '"}"':
            clause_ind = self.clause_ind(scp)
            while self._peek('SEP', 'TERM', '"}"') == 'SEP':
                SEP = self._scan('SEP')
                clause_ind = self.clause_ind(scp)
            if self._peek('TERM', '"}"') == 'TERM':
                TERM = self._scan('TERM')
        self._scan('"}"')
        return scp


def parse(rule, text):
    P = _Parser(_ParserScanner(text))
    return wrap_error_reporter(P, rule)




def scanner(text):
    return _ParserScanner(text)

class BadSyntax(SyntaxError):
    pass


class Parser(_Parser):
    def __init__(self, scanner, sink, baseURI):
        _Parser.__init__(self, scanner)
        self._sink = sink
	self._docScope = sink.newFormula()
        self._baseURI = baseURI
        self._prefixes = {}
        self._serial = 1
        self._lnames = {}
        self._vnames = {}

    def docScope(self):
	return self._docScope

    def uriref(self, str):
        return Symbol(uripath.join(self._baseURI, str[1:-1]))

    def qname(self, str):
        i = string.find(str, ":")
        pfx = str[:i]
        ln = str[i+1:]
        try:
            ns = self._prefixes[pfx]
        except:
            raise BadSyntax, "prefix %s not bound" % pfx
        else:
            return Symbol(ns + ln)

    def lname(self, str):
        n = str[2:]
        try:
            return self._lnames[n]
        except KeyError:
            x = self.docScope().mkVar(n)
            self._lnames[n] = x
            return x

    def vname(self, str):
        n = str[1:]
        try:
            return self._vnames[n]
        except KeyError:
            x = self.docScope().mkVar(n, 1)
            self._vnames[n] = x
            return x

    def termA(self):
        return RDF['type']
    
    def termEq(self):
        return DAML['equivalentTo']

    def strlit(self, str, delim):
        return StringLiteral(str[1:-1]) #@@BROKEN un-escaping

    def intLit(self, str):
        try:
            v = int(str)
        except ValueError:
            v = long(str)
        return IntegerLiteral(v) #@@

    def bindListPrefix(self):
        self._sink.bind("l", LIST.name())
        self._sink.bind("r", RDF.name())
    
    def bind(self, pfx, ref):
        ref = ref[1:-1] # take of <>'s
        addr = uripath.join(self._baseURI, ref)
        #DEBUG("bind", pfx, ref, addr)
        self._sink.bind(pfx, addr)
        #@@ check for pfx already bound?
        self._prefixes[pfx] = addr

    def gotStatement(self, scp, subj, verb, obj):
	#DEBUG("gotStatement:", scp, subj, verb, obj)
        
        dir, pred = verb
        if dir<0: subj, obj = obj, subj
	if scp is subj and pred is LOG['forAll']:
	    DEBUG("@@bogus forAll", obj)
	elif scp is subj and pred is LOG['forSome']:
	    DEBUG("@@bogus forSome", obj)
	else:
	    scp.add(pred, subj, obj)

    def newScope(self):
        return self._sink.newFormula()

    def something(self, scp, hint="thing",
                  univ = 0):
	return scp.mkVar(hint, univ)


    def mkList(self, scp, items):
	tail = None
	head = LIST['nil']
	say = scp.add
	for term in items:
	    cons = scp.mkVar("cons")
	    say(LIST['first'], cons, term)
	    if tail:
	        say(LIST['rest'], tail, cons)
	    tail = cons
	    if not head: head = cons
	if tail:
	    say(LIST['rest'], tail, LIST['nil'])
	return head


def DEBUG(*args):
    import sys
    for a in args:
        sys.stderr.write("%s " % (a,))
    sys.stderr.write("\n")
    
# $Log$
# Revision 1.5  2002-08-16 22:30:48  timbl
# Add two tests for  quick variable ?x syntax. Passes text/retest.sh.
#
# Revision 1.18  2002/08/15 23:20:36  connolly
# fixed . separater/terminator grammar problem
#
# Revision 1.17  2002/08/13 07:55:15  connolly
# playing with a new parser/sink interface
#
# Revision 1.16  2002/08/07 16:01:23  connolly
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
