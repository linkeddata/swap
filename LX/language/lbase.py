"""

See http://www.w3.org/TR/2003/NOTE-lbase-20030123/#consistency

"""
__version__ = "$Revision$"
# $Id$

tokens = (
    'AND', 'OR', 'IMPLIES', 'IFF', 'NOT',
    'FORALL', 'EXISTS',
    'CONSTANT', 'VARIABLE', 'URIREF',
    'NUMERAL', 'QUOTEDSTRING', 'XMLSTRUCTURE',
    'LPAREN', 'RPAREN', 'COMMA', 'EQUALS', 'PERIOD'
    )

# these need to be functions to check for them first

def t_AND(t):
    "and"
    return t

def t_OR(t):
    "or"
    return t

def t_IMPLIES(t):
    "implies"
    return t

def t_IFF(t):
    "iff"
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

t_EQUALS  = r'\='
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_COMMA   = r','
t_PERIOD   = r'\.'
t_CONSTANT = r'[a-zA-Z_][:a-zA-Z0-9_]*'
t_VARIABLE = r'\?'+t_CONSTANT

def t_NUMERAL(t):
    r'\d+'
    try:
        t.value = int(t.value)
    except ValueError:
        print "Integer value too large", t.value
        t.value = 0
    return t

def t_QUOTEDSTRING(t):
    r"'[^'*]'"   # need \-handling
    t.value = t.value[1:-1]
    return t

# Ignored characters
t_ignore = " \t"

def t_newline(t):
    r'\n+'
    t.lineno += t.value.count("\n")
    
def t_error(t):
    print "Illegal character '%s'" % t.value[0]
    t.skip(1)
    
# Build the lexer
import lex
lex.lex()

# Test it out
data = '''
rdf:type(?x,?y) implies (p or q or s or t or ?y(?x))
'''
longData = '''
rdf:type(?x,?y) implies ?y(?x).
rdf:Property(rdf:type).
rdf:List(rdf:nil).
pair(?x,?y)=pair(?u,?v) iff (?x=?u and ?y=?v) .
Lbase:XMLThing(?x) implies
          L2V(?x,rdf:XMLLiteral)=XMLCanonical(?x).
(Lbase:XMLThing(?x) and LanguageTag(?y)) implies L2V(pair(?x,?y),rdf:XMLLiteral)=XMLCanonical(withLang(?x,?y)).
T(?x).
not F(?x).
rdfs:Class(?y) implies (?y(?x) iff rdf:type(?x,?y)).
(rdfs:range(?x,?y) and ?x(?u,?v)) implies ?y(?v).
(rdfs:domain(?x,?y) and ?x(?u,?v)) implies ?y(?u).
(rdfs:subClassOf(?x,?y) iff
  (rdfs:Class(?x) and rdfs:Class(?y) and (forall
          (?u)(?x(?u) implies ?y(?u)))
).
(rdfs:subPropertyOf(?x,?y) iff
  (rdf:Property(?x) and rdf:Property(?y) and
          (forall (?u ?v)(?x(?u,?v) implies ?y(?u,?v)))
).
rdfs:ContainerMembershipProperty(?x) implies rdfs:subPropertyOf(?x,rdfs:member).
rdf:XMLLiteral(?x) implies rdfs:Literal(?x).
Lbase:String(?y) implies
          rdfs:Literal(?y).
LanguageTag(?x) implies Lbase:String(?x).
(Lbase:String(?x) and LanguageTag(?y))
          implies rdfs:Literal(pair(?x,?y)).
rdfs:Datatype(rdf:XMLLiteral).
Lbase:NatNumber(?x) implies
          rdfs:ContainerMembershipProperty(rdf:member(?x)).
rdfs:Class(T).
rdfs:Class(rdf:Property).
rdfs:Class(rdfs:Class).
rdfs:Class(rdfs:Datatype).
rdfs:Class(rdf:Seq).
rdfs:Class(rdf:Bag).
rdfs:Class(rdf:Alt).
rdfs:Class(rdfs:Container).
rdfs:Class(rdf:List).
rdfs:Class(rdfs:ContainerMembershipProperty).
rdfs:Class(rdf:Statement).
rdf:Property(rdfs:domain).
rdf:Property(rdfs:range).
rdf:Property(rdfs:subClassOf).
rdf:Property(rdfs:subPropertyOf).
rdf:Property(rdfs:comment).
rdf:Property(rdf:predicate).
rdf:Property(rdf:subject).
rdf:Property(rdf:object).
rdf:Property(rdf:first).
rdf:Property(rdf:rest).
rdf:Property(rdfs:seeAlso).
rdf:Property(rdfs:isDefinedBy).
rdf:Property(rdfs:label).
rdf:Property(rdf:value).
rdfs:domain(rdfs:subPropertyOf,rdf:Property).
rdfs:domain(rdfs:subClassOf,rdfs:Class).
rdfs:domain(rdfs:domain,rdf:Property).
rdfs:domain(rdfs:range,rdf:Property).
rdfs:domain(rdf:subject,rdf:Statement).
rdfs:domain(rdf:predicate,rdf:Statement).
rdfs:domain(rdf:object,rdf:Statement).
rdfs:domain(rdf:first,rdf:List).
rdfs:domain(rdf:rest,rdf:List).
rdfs:range(rdfs:subPropertyOf,rdf:Property).
rdfs:range(rdfs:subClassOf,rdfs:Class).
rdfs:range(rdfs:domain,rdfs:Class).
rdfs:range(rdfs:range,rdfs:Class).
rdfs:range(rdf:type,rdfs:Class).
rdfs:range(rdfs:comment,rdfs:Literal).
rdfs:range(rdfs:label,rdfs:Literal).
rdfs:range(rdf:rest,rdf:List).
rdfs:subClassOf(rdfs:Datatype,rdfs:Literal).
rdfs:subClassOf(rdf:Alt,rdfs:Container).
rdfs:subClassOf(rdf:Bag,rdfs:Container).
rdfs:subClassOf(rdf:Seq, rdfs:Container).
rdfs:subClassOf(rdfs:ContainerMembershipProperty,rdf:Property).
rdfs:subPropertyOf(rdfs:isDefinedBy,rdfs:seeAlso).
rdfs:Datatype(?x) implies ( LegalLexicalForm(?y,?x)) iff
          ?x(L2V(?y,?x)) ).
( rdfs:Datatype(?x) and LegalLexicalForm(?y,?x) and ?x(?y))
          implies rdfs:Literal(?y).
Lbase:XMLThing(?x) iff
          LegalLexicalForm(?x,rdf:XMLLiteral).
'''

## # Give the lexer some input

## lex.input(data)

## # Tokenize
## while 1:
##     tok = lex.token()
##     if not tok: break      # No more input
##     print tok

    

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
    '''unit : formula PERIOD'''

    return t

def p_term_simple(t):
    '''term : CONSTANT
            | VARIABLE
            | URIREF
            | NUMERAL
            | QUOTEDSTRING
            | XMLSTRUCTURE'''
    return t

def p_term_compound(t):
    '''term : term LPAREN termlist RPAREN '''
    return t

def p_termlist(t):
    '''termlist : term
                | term COMMA termlist'''
    return t

def p_atomicformula(t):
    '''atomicformula : term
                     | term EQUALS term'''
    return t

def p_varlist(t):
    '''varlist : VARIABLE
               | VARIABLE varlist'''
    return t

def p_formula(t):
    '''formula : atomicformula
               | formula PERIOD formula
               | formula AND formula
               | formula OR formula
               | formula IMPLIES formula
               | formula IFF formula
               | NOT formula
               | FORALL LPAREN varlist RPAREN formula
               | EXISTS LPAREN varlist RPAREN formula
               | LPAREN formula RPAREN
               '''
    return t
    
## def p_statement_assign(t):
##     'statement : NAME EQUALS expression'
##     names[t[1]] = t[3]

## def p_statement_expr(t):
##     'statement : expression'
##     print t[1]

## def p_expression_binop(t):
##     '''expression : expression PLUS expression
##                   | expression MINUS expression
##                   | expression TIMES expression
##                   | expression DIVIDE expression'''
##     if t[2] == '+'  : t[0] = t[1] + t[3]
##     elif t[2] == '-': t[0] = t[1] - t[3]
##     elif t[2] == '*': t[0] = t[1] * t[3]
##     elif t[2] == '/': t[0] = t[1] / t[3]

## def p_expression_uminus(t):
##     'expression : MINUS expression %prec UMINUS'
##     t[0] = -t[2]

## def p_expression_group(t):
##     'expression : LPAREN expression RPAREN'
##     t[0] = t[2]

## def p_expression_number(t):
##     'expression : NUMBER'
##     t[0] = t[1]

## def p_expression_name(t):
##     'expression : NAME'
##     try:
##         t[0] = names[t[1]]
##     except LookupError:
##         print "Undefined name '%s'" % t[1]
##         t[0] = 0

def p_error(t):
    print "Syntax error at '%s'" % t.value

import yacc
yacc.yacc()

#while 1:
#    try:
#        s = raw_input('calc > ')
#    except EOFError:
#        break
#    yacc.parse(s)

yacc.parse(longData, debug=1)

#yacc.parse('p', debug=1)
#yacc.parse('not not not not p', debug=1)
#yacc.parse('p or or or q', debug=1)
#yacc.parse('''p q r''', debug=1)

# $Log$
# Revision 1.1  2003-01-30 22:11:52  sandro
# handles syntax now, I think; needs to build LX AST
#


