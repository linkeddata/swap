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

%%
parser RDFN3Parser:
    ignore: r'\s+'         # whitespace. @@count lines?
    ignore: r'#.*\r?\n'    # n3 comments; sh/perl style

    token URIREF:   r'<[^ >]*>'
    token QNAME:    r'[a-zA-Z0-9_-]*:[a-zA-Z0-9_-]*'
    token STRLIT1:  r'"([^\"\\\n]|\\[\\\"nrt])*"'
    token STRLIT2:  r"'([^\'\\\n]|\\[\\\'nrt])*'"
    token STRLIT3:  r'"""([^\"\\]|\\[\\\"nrt])*"""' #@@not right
    token PREFIX:   r'@prefix'
    token THIS:     r'this'
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

    rule document: ( directive | statement ) * END

    rule directive : PREFIX QNAME URIREF STOP

    # foos0 is mnemonic for 0 or more foos
    # foos1      "          1 or more foos

    rule statement : term predicates0 STOP

    rule predicates0 : predicate predicates_rest
                     | # empty

    rule predicates_rest : ";" predicates0
                         | # empty
    rule predicate: verb objects1

    rule verb : term | IS term OF  # earlier N3 specs had more sugar...

    rule objects1 : term ("," term)*

    rule term : URIREF
              | QNAME
              | THIS
              | shorthand
              | STRLIT3 | STRLIT1 | STRLIT2
              | list
              | phrase
              | clause

    rule shorthand : A | "="

    rule list : LP term * RP

    rule phrase: LB predicates0 RB

    rule clause: LC statements0 RC

    rule statements0: term predicates0 statements_rest
                    | #empty
    rule statements_rest : STOP statements0
                         | # empty

# $Log$
# Revision 1.4  2001-08-31 19:06:20  connolly
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
