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
import notation3 # for FORMULA

%%
parser _Parser:
    ignore: r'\s+'         # whitespace. @@count lines?
    ignore: r'#.*\r?\n'    # n3 comments; sh/perl style

    token URIREF:   r'<[^ >]*>'
    token PREFIX:   r'[a-zA-Z0-9_-]*:'
    token QNAME:    r'[a-zA-Z0-9_-]*:[a-zA-Z0-9_-]+'
    token STRLIT1:  r'"([^\"\\\n]|\\[\\\"nrt])*"'
    token STRLIT2:  r"'([^\'\\\n]|\\[\\\'nrt])*'"
    token STRLIT3:  r'"""([^\"\\]|\\[\\\"nrt])*"""' #@@not right
    token THIS:     r'this\b'
    token A:        r'a\b'   #@@matches axy:def?
    token IS:       r'is\b ' #@@matches bxy:def?
    token OF:       r'of\b ' #@@matches bxy:def?
    token STOP:     r'\.'
    token LP:       r'\('
    token RP:       r'\)'
    token LB:       r'\['
    token RB:       r'\]'
    token LC:       r'\{'
    token RC:       r'\}'
    token END:      r'\Z'

    rule document: {{ ctx = self.docContext() }}
         ( directive | statement<<ctx>> ) * END

    rule directive : "@prefix" PREFIX URIREF STOP
    {{ self.bind(PREFIX[:-1], URIREF) }}

    # foos0 is mnemonic for 0 or more foos
    # foos1      "          1 or more foos

    rule statement<<ctx>> : term<<ctx>> predicates0<<ctx, term>> STOP

    rule term<<ctx>>
              : URIREF        {{ return self.uriref(URIREF) }}
              | QNAME         {{ return self.qname(QNAME) }}
              | THIS          {{ return ctx }}
              | shorthand     {{ return shorthand }}
              | STRLIT3       {{ return self.strlit(STRLIT3, '"""') }}
              | STRLIT1       {{ return self.strlit(STRLIT1, '"') }}
              | STRLIT2       {{ return self.strlit(STRLIT2, "'") }}
              | list<<ctx>>   {{ return list }}
              | phrase<<ctx>> {{ return phrase }}
              | clause        {{ return clause }}
              # @@TODO: _:foo
              # @@TODO: ?foo maybe? hmm...
              
    rule predicates0<<ctx,subj>> :
        predicate<<ctx,subj>> predicates_rest<<ctx,subj>>
        | # empty

    rule predicates_rest<<ctx,subj>> :
        ";" predicates0<<ctx,subj>>
        | # empty

    rule predicate<<ctx,subj>>: verb<<ctx>> objects1<<ctx,subj,verb>>

    rule verb<<ctx>> :
          term<<ctx>>          {{ return (1, term) }}
        | IS term<<ctx>> OF    {{ return (-1, term) }}
    # earlier N3 specs had more verb sugar...


    # This is the central rule for recognizing a fact.
    rule objects1<<ctx,subj,verb>> :
        term<<ctx>>  {{ self.gotStatement(ctx, subj, verb, term) }}
        ("," term<<ctx>>
                     {{ self.gotStatement(ctx, subj, verb, term) }}
         )*


    # details about terms...

    rule shorthand :
          A   {{ return self.termA() }}
        | "=" {{ return self.termEq() }}

    rule list<<ctx>> : LP term<<ctx>> * RP #@@TODO: facts to build lists...

    rule phrase<<ctx>>: LB {{ subj = self.something(ctx) }}
                          predicates0<<ctx,subj>>
                        RB
                          {{ return subj }}

    rule clause: LC {{ ctx = self.newClause() }}
                  statements0<<ctx>>
                 RC
                    {{ return ctx }}

    rule statements0<<ctx>>:
       term<<ctx>> predicates0<<ctx,term>> statements_rest<<ctx>>
       | #empty
       
    rule statements_rest<<ctx>> :
        STOP statements0<<ctx>>
        | # empty

%%

def scanner(text):
    return _ParserScanner(text)

class Parser(_Parser):
    def __init__(self, scanner, sink, baseURI):
        _Parser.__init__(self, scanner)
        self._sink = sink
        self._baseURI = baseURI
        self._prefixes = {}
        self._serial = 1

    def docContext(self):
        return mkFormula(self._baseURI)

    def uriref(self, str):
        return notation3.RESOURCE, urlparse.urljoin(self._baseURI, str[1:-1])

    def qname(self, str):
        i = string.find(str, ":")
        pfx = str[:i]
        ln = str[i+1:]
        try:
            ns = self._prefixes[pfx]
        except:
            raise SyntaxError, "prefix %s not bound" % pfx
        else:
            return notation3.RESOURCE, ns + ln

    def termA(self):
        return notation3.RDF_type
    
    def termEq(self):
        return notation3.DAML_equivalentTo

    def strlit(self, str, delim):
        return notation3.LITERAL, str[1:-1] #@@BROKEN

    def bind(self, pfx, ref):
        ref = ref[1:-1] # take of <>'s
        if ref[-1] == '#': # @@work around bug in urljoin...
            sep = '#'
            ref = ref[:-1]
        else: sep = ''
        addr = urlparse.urljoin(self._baseURI, ref) + sep
        #DEBUG("bind", pfx, ref, addr)
        self._sink.bind(pfx, (notation3.RESOURCE, addr))
        #@@ check for pfx already bound?
        self._prefixes[pfx] = addr

    def gotStatement(self, ctx, subj, verb, obj):
        #DEBUG("gotStatement:", ctx, subj, verb, obj)
        
        dir, pred = verb
        if dir<0: subj, obj = obj, subj
        self._sink.makeStatement((ctx, pred, subj, obj))

    def newClause(self):
        return self.something(self.docContext(),
                              "clause", notation3.FORMULA)

    def something(self, ctx, hint="thing", ty=notation3.RESOURCE):
        it = (ty, "%s#%s_%s" % (self._baseURI, hint, self._serial))

        ex = (notation3.RESOURCE, notation3.N3_forSome_URI)
        self._sink.makeStatement((ctx, ex, ctx, it))

        self._serial = self._serial + 1
        return it


def mkFormula(absURI):
    """move this somewhere else?"""
    return notation3.FORMULA, absURI + "#_formula" #@@KLUDGE from notation3.py, cwm.py

def DEBUG(*args):
    import sys
    for a in args:
        sys.stderr.write("%s " % (a,))
    sys.stderr.write("\n")
    
# $Log$
# Revision 1.8  2001-08-31 22:15:44  connolly
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
