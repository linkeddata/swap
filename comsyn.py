"""
An RDF Compact Syntax, suitable for transmitting an
RDF graph (optionally with variables) inside a URI.

Or using inside as URI itself, see
http://lists.w3.org/Archives/Public/uri/2003May/0007.html

x-rdfn1:foaf_mbox='sandro@w3.org';ns(foaf_,'http://xmlns.org/FOAF/0.1/')
x-rdfn1:mbox='sandro@w3.org';ns('http://xmlns.org/FOAF/0.1/')
x-rdfn1:(uri='http://xmlns.org/FOAF/0.1/mbox')='sandro@w3.org'
x-rdfn1:=x;x.foaf_mbox='sandro@w3.org';ns(foaf_,'http://xmlns.org/FOAF/0.1/')

an expr denotes an object....
all shortnames are local (bnodes) except
      when a .uri for them is known
      .uri itself?    ick.    hasURI('xxxx')
      the ns(...) function is used

        NS()    1 and 2 place
        hasURI()  to bring in long names without NS()

            [ we reserve all function names;
              we never use SHORTNAMES ]

        version(0.1);
        typed(xsd_date,'2003-02-02')
              x-rdfn1:1,2,3
            denotes an RDF collection with
            a first of 1, etc.
               x-rdfn1:1,2,3,...
            does NOT close the list.
                1,2,3|x;x=foo    ?

x-rdfn1:foaf_mbox='sandro@w3.org';NS(foaf_,'http://xmlns.org/FOAF/0.1/')
x-rdfn1:mbox='sandro@w3.org';NS('http://xmlns.org/FOAF/0.1/')
x-rdfn1:hasURI('http://xmlns.org/FOAF/0.1/mbox')='sandro@w3.org'
x-rdfn1:=x;x.foaf_mbox='sandro@w3.org';NS(foaf_,'http://xmlns.org/FOAF/0.1/')
x-rdfn1:(=x;x.foaf_mbox='sandro@w3.org';NS(foaf_,'http://xmlns.org/FOAF/0.1/'))

dt lits:      'dsfsdf'^^type
               typed(xsd_int,'34')

lists?
        colors=1,2,3
        colors=(1,)

    parens are for precidence

         ,    makes lists, trailing ignored
         =    (infix) makes sentences, trailing ignored,
              sometimes involving current subject
         =    (prefix) relates to current subject ...?
                  [ or is that a null path?   can you
                  say   (self=) to say x.self=x ?
                  or (=) to say x=x ?
         ;    makes compound sentences, drops directives
         xxx()  reserved function or directive

         

why apostrophe?   it's allowed in URI
when to undo %?    after parsing for ' ; = ...


query?

   http://server.com?=x,y,z;x.y=z

does that =x,y,z really make sense....  the matched
object is a list....

   http://server.com?mustbind=x,y,z&pattern=(x.y=z)

do cgi's split on a second "="?   I doubt it.

can bnodes default to maybind or dontbind?   Sure, they're
just existentials; a good proof of existence would bind them.

mustbind means must-bind to a URI or something.

default ?x to mustbind, _x to dontbind, ??x to maybind.





nesting / parsetype=quote?
    easy with    quote(expr)


"""
__version__ = "$Revision$"
# $Id$

import rdfpath
import hotswap
import pluggable


#class Serializer(pluggable.Serializer):
#    pass

tokens = (
    'LPAREN', 'RPAREN', 'SEMI', 'EQUALS', 'PERIOD',
    'SHORTNAME', 'NUMERAL', 'QUOTEDSTRING'
    )

# these need to be functions to check for them first

t_EQUALS  = r'\='
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_SEMI    = r';'
t_PERIOD  = r'\.'
t_SHORTNAME    = r'[-_a-zA-Z0-9:?]+' 

def t_NUMERAL(t):
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print "Integer value too large", t.value
        t.value = 0
    return t

def t_QUOTEDSTRING(t):
    r"'[^']*'"   # need \-handling
    t.value = t.value[1:-1]
    return t

# Ignored characters
# t_ignore = " \t"

def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.skip(1)
    
# Build the lexer
import ply.lex
ply.lex.lex()

# Test it out
data = '''abc.def'''

## lex.input(data)

## # Tokenize
## while 1:
##     tok = lex.token()
##     if not tok: break      # No more input
##     print tok


# Precedence rules for the arithmetic operators
#precedence = (
#    ('left', 'IMPLIES'),
#    ('left', 'IFF'), 
#    ('left', 'OR'),
#    ('left', 'AND'),
#    ('right','NOT'),
#    )


def p_expr_single(t):
    '''expr : part'''
    t[0] = [t[1]]

def p_expr(t):
    '''expr : expr SEMI part'''
    t[0] = t[1] + [t[3]]

def p_part(t):
    '''part : left EQUALS right'''
    t[0] = ("=", t[1], t[3])

def p_part_2(t):
    '''part : EQUALS right'''
    t[0] = ("=", t[2])

def p_left(t):
    '''left : path'''
    t[0] = t[1]

def p_right_string(t):
    '''right : QUOTEDSTRING'''
    t[0] = ('STR', t[1])

def p_right_numeral(t):
    '''right : NUMERAL'''
    t[0] = ('NUM', t[1])

def p_right_word(t):
    '''right : path'''
    t[0] = ('PATH', t[1])

def p_right_p(t):
    '''right : LPAREN expr RPAREN'''
    t[0] = t[2]

def p_path(t):
    '''path : name'''
    t[0] = (t[1],)

def p_path_more(t):
    '''path : path PERIOD name'''
    t[0] = t[1]+(t[3],)

def p_name(t):
    '''name : SHORTNAME'''
    t[0] = ('SHORTNAME', t[1])

def p_name_2(t):
    '''name : LPAREN expr RPAREN'''
    t[0] = t[2]
    
def p_error(t):
    print "Syntax error at '%s'" % (t.value)
    raise RuntimeError

import ply.yacc
ply.yacc.yacc(tabmodule="comsyn_ply_tab")

debug=0
print ply.yacc.parse("hello='world'", debug=debug)
print ply.yacc.parse("hello=35", debug=debug)
print ply.yacc.parse("hello=35;foo=bar;baz='Bux'", debug=debug)
print ply.yacc.parse("a=(b='c')", debug=debug)
print ply.yacc.parse("a=(x.b='c')", debug=debug)
print ply.yacc.parse("a=(x.b.x.q='c');a.b=c.d", debug=debug)
print ply.yacc.parse("=x;x.y=z", debug=debug)
# the left is always a path
#    if it has only one element, the subject is implied
#    if it has 2 or more, the subject is given, and the others
#       are property names
#    if it has ZERO, then it's equating the resulting thing

#  xxprint ply.yacc.parse("a=ext(http'))", debug=debug)

#     (uri='http://www.w3.org/')
#     ns(foaf_, 'http://....')

import sys
sys.exit()


class Parser(pluggable.Parser):

    def parse(self, stream, host):
        self.sink = host.pluginManager.get("store", rdfpath.Store)
        x = ply.yacc.parse(stream)
        print "Result:", x


class xxxParser:

    def __init__(self, sink=None, flags=""):
        self.kb = sink

    def load(self, inputURI):
        stream = urllib.urlopen(inputURI)
        s = stream.read()
        global kb
        kb = self.kb
        ply.yacc.parse(s)

    def parse(self, s):
        global kb
        kb = self.kb
        ply.yacc.parse(s)

    def parseToFormula(self, s):
        global kb
        kb = newkb.KB()
        ply.yacc.parse(s)
        f = kb.asFormula()
        kb = None
    
class xxxSerializer:

    def __init__(self, stream, flags=""):
        self.stream = stream

    def makeComment(self, comment):
        self.stream.write("% "+comment+"\n")

    def serializeKB(self, kb):
        pass

# $Log$
# Revision 1.1  2003-05-02 06:06:58  sandro
# compact syntax for rdf; notes and partial impl
#
# Revision 1.8  2003/02/14 19:40:32  sandro
# working lbase -> otter translation, with regression test
#
# Revision 1.7  2003/02/14 17:21:59  sandro
# Switched to import-as-needed for LX languages and engines
#
# Revision 1.6  2003/02/14 14:47:24  sandro
# possible fix to yacc warning
#
# Revision 1.5  2003/02/14 00:52:03  sandro
# added literals, some tweaks in URI handling
#
# Revision 1.4  2003/02/13 19:50:55  sandro
# better support for "holds", changed parser API a little
#
# Revision 1.3  2003/02/01 06:23:55  sandro
# intermediate lbase support; getting even better
#
# Revision 1.2  2003/02/01 05:58:12  sandro
# intermediate lbase support; getting there but buggy; commented out some fol chreccks
#
# Revision 1.1  2003/01/30 22:11:52  sandro
# handles syntax now, I think; needs to build LX AST
#


