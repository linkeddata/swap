"""

Read a KIF axiom set (as used for the DAML+OIL axiomatization) and
add it to the KB.

See http://daml.kestrel.edu/axioms.kif
 or http://www.ai.sri.com/daml/axioms.kif

Or should we just read KIF and then process it???  I dunno.

See http://logic.stanford.edu/kif/dpans.html#Syntax, but I'm not
really following that -- it's more complex than I need.

This code is based on the lbase code, which right now means its
cruftier than needed, since we DONT actually have any precidence
issues, etc.

"""
__version__ = "$Revision$"
# $Id$

import LX.fol
import LX.expr
import LX.kb
import LX.rdf

kb = LX.kb.KB()
holds = [ LX.fol.Predicate("holds0"),
          LX.fol.Predicate("holds1"),
          LX.fol.Predicate("holds2"),
          LX.fol.Predicate("holds3"),
          LX.fol.Predicate("holds4"),
          LX.fol.Predicate("holds5"),
          LX.fol.Predicate("holds6"),
          ]

tokens = (
    'AND', 'OR', 'IMPLIES', 'IFF', 'NOT',
    'FORALL', 'EXISTS',
    'CONSTANT',
    'NUMERAL', 'QUOTEDSTRING',
    'LPAREN', 'RPAREN', 'EQUALS',
    'TAG', 'SEQVAR', 'INDVAR', 'BODY'
    )

# these need to be functions to check for them first

def t_AND(t):
    "and"
    return t

def t_OR(t):
    "or"
    return t

def t_IMPLIES(t):
    "=>"
    return t

def t_IFF(t):
    "<=>"
    return t

def t_NOT(t):
    "not"
    return t

def t_FORALL(t):
    'forall'
    return t

def t_EXISTS(t):
    'exists'
    return t

def t_BODY(t):
    '\:body'
    return t

t_EQUALS  = r'\='
t_LPAREN  = r'\('
t_RPAREN  = r'\)'

# In fact, KIF's notion of WORDS is much more complex, and
# BLOCK is downright scary (length-delimited identifiers),
# ... but this is probably good enough for now.
t_CONSTANT = r'[a-zA-Z_-][a-zA-Z0-9_-]*'
t_INDVAR = r'\?'+t_CONSTANT
t_SEQVAR = r'\@'+t_CONSTANT
t_TAG = r'\:'+t_CONSTANT

#def t_NUMERAL(t):
#    r'\d+'
#    try:
#        t.value = int(t.value)
#    except ValueError:
#        print "Integer value too large", t.value
#        t.value = 0
#    return t

def t_QUOTEDSTRING(t):
    r"""('[^']*')|("[^"]*")"""   # need \-handling
    t.value = t.value[1:-1]
    return t

# Ignored characters
t_ignore = " \t"

def t_newline(t):
    r'''((\#[^\n]*)?)\n+'''
    t.lineno += t.value.count("\n")
    
def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.skip(1)
    
# Build the lexer
import ply.lex
ply.lex.lex()

# Test it out
data = '''
(<=> (Type ?s ?o) (PropertyValue RDF_type ?s ?o)))
'''
longData = '''
(:subject "Type"
 :sentence-type "axiom"
 :identifier "1"
 :description " Relation 'Type' holds for objects S and O if and only if relation 'PropertyValue' holds for objects 'type', S, and O."
 :body (<=> (Type ?s ?o) (PropertyValue RDF_type ?s ?o)))


(:subject "FunctionalProperty"
 :sentence-type "axiom"
 :identifier "1"
 :description " An object FP is 'FunctionalProperty' if and only if FP is type 'Property' and if objects V1 and V2 are both values of FP for some object, then V1 is equal to V2.  (I.e., functional properties are those properties that are functional in their values.)"
 :body (<=> (FunctionalProperty ?fp) (and (Type ?fp RDF_Property) (forall (?s ?v1 ?v2) (=> (and (PropertyValue ?fp ?s ?v1) (PropertyValue ?fp ?s ?v2)) (= ?v1 ?v2))))))

'''
###          ?x(L2V(?y,?x)).

## # Give the lexer some input

## #ply.lex.input(data)
## ply.lex.input(longData)

## # Tokenize
## while 1:
##     tok = ply.lex.token()
##     if not tok: break      # No more input
##     print tok

## raise RuntimeError, "Done!"
    

# Precedence rules for the arithmetic operators
precedence = (
    ('left', 'IMPLIES'),
    ('left', 'IFF'), 
    ('left', 'OR'),
    ('left', 'AND'),
    ('right','NOT'),
    )

# dictionary of names (for storing variables)
names = { }

def p_unit(t):
    '''unit : chunkList'''
    pass

def p_chunkList_empty(t):
    '''chunkList : '''
    pass

def p_chunkList_more(t):
    '''chunkList : chunkList chunk'''

def p_chunk(t):
    '''chunk : LPAREN tagList BODY sentence RPAREN'''
    print "Adding formula %s\n" % t[4]
    kb.add(t[4])

def p_tagList(t):
    '''tagList :
               | tagList TAG QUOTEDSTRING'''
    # ignore the tags for now
    pass

def p_sentence(t):
    '''sentence : sformula'''
    t[0] = t[1]

constants = {}
variables = {}
## prefixes = {
##     'rdf':'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
##     'rdfs':'http://www.w3.org/2000/01/rdf-schema#',
##     'Lbase':'http://www.w3.org/TR/2003/NOTE-lbase-20030123-ns#',
##     'owl':'http://www.w3.org/2002/07/owl#',
##     }

def p_term_simple1(t):
    '''term : CONSTANT'''
    # It seems like what's actually meant is this:
    # @@@ uri = "http://example.com#"+t[1]
    uri = t[1]
    if constants.has_key(uri):
        t[0] = constants[uri]
    else:
        tt = LX.logic.Constant(uri)
        t[0] = tt
        #kb.interpret(tt, LX.uri.DescribedThing(uri))
        constants[uri] = tt
    # not
    # t[0] = constants.setdefault(t[1], LX.fol.Constant(t[1]))


## def p_term_simple2(t):
##     '''term : URIREF'''      ##  need two productions here?!
##     try:
##         (pre, post) = t[1].split(":", 1)
##     except ValueError:
##         raise RuntimeError, "Can't find the : in %s\n" % t[1]
##     uri = prefixes[pre]+post
##     if constants.has_key(uri):
##         t[0] = constants[uri]
##     else:
##         tt = LX.logic.Constant(uri)
##         t[0] = tt
##         kb.interpret(tt, LX.uri.DescribedThing(uri))
##         constants[uri] = tt

## def p_term_numeral(t):
##     '''term : NUMERAL'''
##     if constants.has_key(t[1]):
##         t[0] = constants[y[1]]
##     else:
##         tt = LX.logic.Constant(str(t[1]))
##         t[0] = tt
##         kb.interpret(tt, t[1])
##         constants[t[1]] = tt

## def p_term_quotedstrin(t):
##     '''term : QUOTEDSTRING'''
##     t[0] = kb.constantFor(t[1])

#            | NUMERAL
#            | QUOTEDSTRING
#            | XMLSTRUCTURE'''

def p_term_var(t):
    'term : INDVAR'
    for frame in varStack:
        if t[1] == frame.name:
            t[0] = frame.variable
            return
    if variables.has_key(t[1]):
        t[0] = variables[t[1]]
    else:
        tt = LX.fol.UniVar(t[1])
        t[0] = tt
        variables[t[1]] = tt
        kb.univars.append(tt)

def p_term_compound(t):        # funterm
    '''term : LPAREN termlist RPAREN '''
    #t[0] = apply(LX.expr.CompoundExpr, [t[1]] + t[3])
    #   for now just read it in as FOL.
    args = t[2]
    if len(args) == 3:
        t[0] = apply(LX.fol.RDF, (args[1], args[0], args[2]))
    else:
        t[0] = apply(holds[len(args)], args)

def p_termlist_empty(t):
    '''termlist : '''
    t[0] = []

def p_termlist_more(t):
    'termlist : term termlist'''
    t[0] = [t[1]] + t[2]

##def p_atomicformula(t):
##   'atomicformula : term'
##    #  assert function is a predicate?
##    t[0] = t[1]

def p_atomicformula_2(t):
    'atomicformula : EQUALS term term'
    t[0] = LX.fol.EQUALS(t[2], t[3])

def p_varlist(t):
    '''varlist : INDVAR'''
    t[0] = [t[1]]

def p_varlist_2(t):
    'varlist : INDVAR varlist'
    t[0] = [t[1]] + t[2]

def p_formula(t):
    'formula : atomicformula'
    t[0] = t[1]
    
def p_formula_2(t):
    '''formula : AND formulaList
                | OR formulaList
                | IMPLIES formulaList
                | IFF formulaList '''
    f = { "and": LX.fol.AND,
          "or": LX.fol.OR,
          "=>": LX.fol.IMPLIES,
          "<=>": LX.fol.MEANS}[t[1]]
    #print "APPLYING", f, t[2]
    t[0] = apply(f, t[2])
    # is LX.fol.AND allowed to be n-ary...???

def p_formula_3(t):
     'formula : NOT formula'
     t[0] = LX.fol.NOT(t[2])

def p_formulaList_empty(t):
    'formulaList : '
    t[0] = []

def p_formulaList_more(t):
    'formulaList : formulaList sformula'
    t[0] = t[1] + [t[2]]

class Frame:
    def __init__(self):
        self.name = None; self.variable = None; self.quantifier = None
frameSep = Frame()
varStack = []

def p_quantification(t):
    '''quantification : FORALL LPAREN varlist RPAREN 
                      | EXISTS LPAREN varlist RPAREN '''
    varlist = t[3]
    varStack.insert(0, frameSep)
    quantifier = { "forall": LX.fol.FORALL,
                   "exists": LX.fol.EXISTS }[t[1]]
    varclass =   { "forall": LX.fol.UniVar,
                   "exists": LX.fol.ExiVar }[t[1]]
    for var in varlist:
        frame = Frame()
        frame.name = var
        frame.variable = apply(varclass, (var,))
        frame.quantifier = quantifier
        varStack.insert(0, frame)
    #print "varStack built up to", varStack
            
def p_formula_4(t):
     'formula : quantification sformula'
     f = t[2]
     while 1:
         frame = varStack.pop(0)
         if frame == frameSep: break
         f = apply(frame.quantifier, [frame.variable, f])
         #print "f built up to ", f
     #print "varStack chopped to", varStack, "@@@ forgot to quantify"
     t[0] = f
     
def p_sformula(t):
     'sformula : LPAREN formula RPAREN'
     t[0] = t[2]

def p_sformula_2(t):
     'sformula : term'
     t[0] = t[1]

def p_error(t):
    print "Syntax error at '%s' on line %s" % (t.value, t.lineno)

import ply.yacc
ply.yacc.yacc(tabmodule="lx_language_kifax_tab")

#while 1:
#    try:
#        s = raw_input('calc > ')
#    except EOFError:
#        break
#    yacc.parse(s)

#ply.yacc.parse(longData, debug=0)
#raise RuntimeError, "Done!"

#yacc.parse('p', debug=1)
#yacc.parse('not not not not p', debug=1)
#yacc.parse('p or or or q', debug=1)
#yacc.parse('''p q r''', debug=1)

#yacc.parse('p(x,y,x) or q(x).')
#yacc.parse('p(x,y,x) or q(?x).')
#yacc.parse('forall (?a ?b) exists (?z) p(x,?a, y,x) or q(x).')

#print kb

# print LX.language.otter.serialize(kb)

# @@ need to properly re-init stuff, like being a proper object?
def parse(s, to_kb):
    global kb
    kb = to_kb
    ply.yacc.parse(s)

import urllib

class Parser:

    def __init__(self, sink=None, flags=""):
        self.kb = sink

    def load(self, inputURI):
        stream = urllib.urlopen(inputURI)
        s = stream.read()
        global kb
        kb = self.kb
        ply.yacc.parse(s)

class Serializer:

    def __init__(self, stream, flags=""):
        self.stream = stream

    def makeComment(self, comment):
        self.stream.write("% "+comment+"\n")

    def serializeKB(self, kb):
        pass

# $Log$
# Revision 1.1  2003-07-18 04:35:38  sandro
# first cut, based on lbase.py, parser for DAML+OIL KIF axioms
#
#


