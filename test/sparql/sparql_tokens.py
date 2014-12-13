"""Use ply to tokenize a SPARQL expression


"""

import re
import sys
import lex

t_IT_SELECT = 'SELECT'
t_IT_DISTINCT = 'DISTINCT'
t_GT_TIMES = '\\*'
t_IT_CONSTRUCT = 'CONSTRUCT'
t_IT_DESCRIBE = 'DESCRIBE'
t_IT_ASK = 'ASK'
t_IT_BASE = 'BASE'
t_IT_PREFIX = 'PREFIX'
t_IT_FROM = 'FROM'
t_IT_WHERE = 'WHERE'
t_GT_LCURLEY = '\\{'
t_GT_RCURLEY = '\\}'
t_GT_DOT = '\\.'
t_IT_ORDER = 'ORDER'
t_IT_BY = 'BY'
t_GT_LPAREN = '\\('
t_GT_RPAREN = '\\)'
t_IT_ASC = 'ASC'
t_IT_DESC = 'DESC'
t_IT_LIMIT = 'LIMIT'
t_IT_OFFSET = 'OFFSET'
t_IT_UNION = 'UNION'
t_IT_OPTIONAL = 'OPTIONAL'
t_IT_GRAPH = 'GRAPH'
t_IT_FILTER = 'FILTER'
t_GT_SEMI = ';'
t_GT_COMMA = ','
t_IT_a = 'a'
t_GT_LBRACKET = '\\['
t_GT_RBRACKET = '\\]'
t_GT_OR = '\\|\\|'
t_GT_AND = '&&'
t_GT_EQUAL = '='
t_GT_NEQUAL = '!='
t_GT_LT = '<'
t_GT_GT = '>'
t_GT_LE = '<='
t_GT_GE = '>='
t_GT_PLUS = '\\+'
t_GT_MINUS = '-'
t_GT_DIVIDE = '/'
t_GT_NOT = '!'
t_IT_STR = 'STR'
t_IT_LANG = 'LANG'
t_IT_DATATYPE = 'DATATYPE'
t_IT_REGEX = 'REGEX'
t_IT_BOUND = 'BOUND'
t_IT_isURI = 'isURI'
t_IT_isBLANK = 'isBLANK'
t_IT_isLITERAL = 'isLITERAL'
t_GT_DTYPE = '\\^\\^'
t_IT_true = 'true'
t_IT_false = 'false'

def t_EmptyPattern(t):
     u'\\{[ \\t\\r\\n]*\\}'
     return t

def t_TrailingDot(t):
     u'\\.(?=((?:[ \\t\\r\\n]*(?:(?:\\})|(?:(?:(?:(?:(?:UNION)|(?:OPTIONAL))|(?:GRAPH))|(?:FILTER))[^a-zA-Z])))))'
     return t

def t_FROM_NAMED(t):
     u'FROM[ \\t\\r\\n]+NAMED'
     return t

def t_QuotedIRIref(t):
     u'<[^> ]*>'
     return t

def t_INTEGER(t):
     u'[0-9]+'
     return t

def t_DECIMAL(t):
     u'(?:[0-9]+\\.[0-9]*)|(?:\\.[0-9]+)'
     return t


def t_FLOATING_POINT(t):
     u'(?:(?:[0-9]+\\.[0-9]*(?:[eE][\\+-]?[0-9]+)?)|(?:\\.[0-9]+(?:[eE][\\+-]?[0-9]+)?))|(?:[0-9]+(?:[eE][\\+-]?[0-9]+))'
     return t


##def t_EXPONENT(t):
##     '[eE][\\+-]?[0-9]+'
##     return t

def t_STRING_LITERAL1(t):
     u'\'(?:(?:[^\'\\\\\\n\\r])|(?:(?:\\\\\\\\[^\\n\\r])))*\''
     return t

def t_STRING_LITERAL2(t):
     u'"(?:(?:[^"\\\\\\n\\r])|(?:(?:\\\\\\\\[^\\n\\r])))*"'
     return t

def t_STRING_LITERAL_LONG1(t):
     u'"""(?:(?:(?:(?:[^"\\\\])|(?:(?:\\\\[^\\n\\r])))|(?:(?:"[^"])))|(?:(?:""[^"])))*"""'
     return t

def t_STRING_LITERAL_LONG2(t):
     u'\'\'\'(?:(?:(?:(?:[^\'\\\\])|(?:(?:\\\\[^\\n\\r])))|(?:(?:\'[^\'])))|(?:(?:\'\'[^\'])))*\'\'\''
     return t

def t_LANGTAG(t):
     u'@[a-zA-Z]+(?:-[a-zA-Z0-9]+)*'
     return t

##def t_NCCHAR1(t):
##     '(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:[A-Z])|(?:[a-z]))|(?:[\u00C0-\u00D6]))|(?:[\u00D8-\u00F6]))|(?:[\u00F8-\u02FF]))|(?:[\u0370-\u037D]))|(?:[\u037F-\u1FFF]))|(?:[\u200C-\u200D]))|(?:[\u2070-\u218F]))|(?:[\u2C00-\u2FEF]))|(?:[\u3001-\uD7FF]))|(?:[\uF900-\uFFFE])'
##     return t
##
##def t_NCCHAR(t):
##     '(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:[A-Z])|(?:[a-z]))|(?:[\u00C0-\u00D6]))|(?:[\u00D8-\u00F6]))|(?:[\u00F8-\u02FF]))|(?:[\u0370-\u037D]))|(?:[\u037F-\u1FFF]))|(?:[\u200C-\u200D]))|(?:[\u2070-\u218F]))|(?:[\u2C00-\u2FEF]))|(?:[\u3001-\uD7FF]))|(?:[\uF900-\uFFFE])))|(?:_))|(?:-))|(?:\\.))|(?:[0-9]))|(?:\u00B7)'
##     return t
##
##def t_NCNAME_PREFIX(t):
##     '(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:[A-Z])|(?:[a-z]))|(?:[\u00C0-\u00D6]))|(?:[\u00D8-\u00F6]))|(?:[\u00F8-\u02FF]))|(?:[\u0370-\u037D]))|(?:[\u037F-\u1FFF]))|(?:[\u200C-\u200D]))|(?:[\u2070-\u218F]))|(?:[\u2C00-\u2FEF]))|(?:[\u3001-\uD7FF]))|(?:[\uF900-\uFFFE]))(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:[A-Z])|(?:[a-z]))|(?:[\u00C0-\u00D6]))|(?:[\u00D8-\u00F6]))|(?:[\u00F8-\u02FF]))|(?:[\u0370-\u037D]))|(?:[\u037F-\u1FFF]))|(?:[\u200C-\u200D]))|(?:[\u2070-\u218F]))|(?:[\u2C00-\u2FEF]))|(?:[\u3001-\uD7FF]))|(?:[\uF900-\uFFFE])))|(?:_))|(?:-))|(?:\\.))|(?:[0-9]))|(?:\u00B7))*'
##     return t


def t_QNAME(t):
     u'(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:[A-Z])|(?:[a-z]))|(?:[\u00C0-\u00D6]))|(?:[\u00D8-\u00F6]))|(?:[\u00F8-\u02FF]))|(?:[\u0370-\u037D]))|(?:[\u037F-\u1FFF]))|(?:[\u200C-\u200D]))|(?:[\u2070-\u218F]))|(?:[\u2C00-\u2FEF]))|(?:[\u3001-\uD7FF]))|(?:[\uF900-\uFFFE]))(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:[A-Z])|(?:[a-z]))|(?:[\u00C0-\u00D6]))|(?:[\u00D8-\u00F6]))|(?:[\u00F8-\u02FF]))|(?:[\u0370-\u037D]))|(?:[\u037F-\u1FFF]))|(?:[\u200C-\u200D]))|(?:[\u2070-\u218F]))|(?:[\u2C00-\u2FEF]))|(?:[\u3001-\uD7FF]))|(?:[\uF900-\uFFFE])))|(?:_))|(?:-))|(?:\\.))|(?:[0-9]))|(?:\u00B7))*)?:(?:(?:(?:_)|(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:[A-Z])|(?:[a-z]))|(?:[\u00C0-\u00D6]))|(?:[\u00D8-\u00F6]))|(?:[\u00F8-\u02FF]))|(?:[\u0370-\u037D]))|(?:[\u037F-\u1FFF]))|(?:[\u200C-\u200D]))|(?:[\u2070-\u218F]))|(?:[\u2C00-\u2FEF]))|(?:[\u3001-\uD7FF]))|(?:[\uF900-\uFFFE]))))(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:[A-Z])|(?:[a-z]))|(?:[\u00C0-\u00D6]))|(?:[\u00D8-\u00F6]))|(?:[\u00F8-\u02FF]))|(?:[\u0370-\u037D]))|(?:[\u037F-\u1FFF]))|(?:[\u200C-\u200D]))|(?:[\u2070-\u218F]))|(?:[\u2C00-\u2FEF]))|(?:[\u3001-\uD7FF]))|(?:[\uF900-\uFFFE])))|(?:_))|(?:-))|(?:\\.))|(?:[0-9]))|(?:\u00B7))*)?'
     return t

def t_BNODE_LABEL(t):
     u'_:(?:(?:(?:_)|(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:[A-Z])|(?:[a-z]))|(?:[\u00C0-\u00D6]))|(?:[\u00D8-\u00F6]))|(?:[\u00F8-\u02FF]))|(?:[\u0370-\u037D]))|(?:[\u037F-\u1FFF]))|(?:[\u200C-\u200D]))|(?:[\u2070-\u218F]))|(?:[\u2C00-\u2FEF]))|(?:[\u3001-\uD7FF]))|(?:[\uF900-\uFFFE]))))(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:[A-Z])|(?:[a-z]))|(?:[\u00C0-\u00D6]))|(?:[\u00D8-\u00F6]))|(?:[\u00F8-\u02FF]))|(?:[\u0370-\u037D]))|(?:[\u037F-\u1FFF]))|(?:[\u200C-\u200D]))|(?:[\u2070-\u218F]))|(?:[\u2C00-\u2FEF]))|(?:[\u3001-\uD7FF]))|(?:[\uF900-\uFFFE])))|(?:_))|(?:-))|(?:\\.))|(?:[0-9]))|(?:\u00B7))*)'
     return t

def t_QNAME_NS(t):
     u'(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:[A-Z])|(?:[a-z]))|(?:[\u00C0-\u00D6]))|(?:[\u00D8-\u00F6]))|(?:[\u00F8-\u02FF]))|(?:[\u0370-\u037D]))|(?:[\u037F-\u1FFF]))|(?:[\u200C-\u200D]))|(?:[\u2070-\u218F]))|(?:[\u2C00-\u2FEF]))|(?:[\u3001-\uD7FF]))|(?:[\uF900-\uFFFE]))(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:[A-Z])|(?:[a-z]))|(?:[\u00C0-\u00D6]))|(?:[\u00D8-\u00F6]))|(?:[\u00F8-\u02FF]))|(?:[\u0370-\u037D]))|(?:[\u037F-\u1FFF]))|(?:[\u200C-\u200D]))|(?:[\u2070-\u218F]))|(?:[\u2C00-\u2FEF]))|(?:[\u3001-\uD7FF]))|(?:[\uF900-\uFFFE])))|(?:_))|(?:-))|(?:\\.))|(?:[0-9]))|(?:\u00B7))*)?:'
     return t

##def t_NCNAME(t):
##     '(?:(?:_)|(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:[A-Z])|(?:[a-z]))|(?:[\u00C0-\u00D6]))|(?:[\u00D8-\u00F6]))|(?:[\u00F8-\u02FF]))|(?:[\u0370-\u037D]))|(?:[\u037F-\u1FFF]))|(?:[\u200C-\u200D]))|(?:[\u2070-\u218F]))|(?:[\u2C00-\u2FEF]))|(?:[\u3001-\uD7FF]))|(?:[\uF900-\uFFFE]))))(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:[A-Z])|(?:[a-z]))|(?:[\u00C0-\u00D6]))|(?:[\u00D8-\u00F6]))|(?:[\u00F8-\u02FF]))|(?:[\u0370-\u037D]))|(?:[\u037F-\u1FFF]))|(?:[\u200C-\u200D]))|(?:[\u2070-\u218F]))|(?:[\u2C00-\u2FEF]))|(?:[\u3001-\uD7FF]))|(?:[\uF900-\uFFFE])))|(?:_))|(?:-))|(?:\\.))|(?:[0-9]))|(?:\u00B7))*'
##     return t

##def t_VARNAME(t):
##     '(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:[A-Z])|(?:[a-z]))|(?:[\u00C0-\u00D6]))|(?:[\u00D8-\u00F6]))|(?:[\u00F8-\u02FF]))|(?:[\u0370-\u037D]))|(?:[\u037F-\u1FFF]))|(?:[\u200C-\u200D]))|(?:[\u2070-\u218F]))|(?:[\u2C00-\u2FEF]))|(?:[\u3001-\uD7FF]))|(?:[\uF900-\uFFFE])))|(?:_))|(?:[0-9]))|(?:\u00B7))*'
##     return t

def t_VAR2(t):
     u'\\$(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:[A-Z])|(?:[a-z]))|(?:[\u00C0-\u00D6]))|(?:[\u00D8-\u00F6]))|(?:[\u00F8-\u02FF]))|(?:[\u0370-\u037D]))|(?:[\u037F-\u1FFF]))|(?:[\u200C-\u200D]))|(?:[\u2070-\u218F]))|(?:[\u2C00-\u2FEF]))|(?:[\u3001-\uD7FF]))|(?:[\uF900-\uFFFE])))|(?:_))|(?:[0-9]))|(?:\u00B7))*)'
     return t

def t_VAR1(t):
     u'\\?(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:(?:[A-Z])|(?:[a-z]))|(?:[\u00C0-\u00D6]))|(?:[\u00D8-\u00F6]))|(?:[\u00F8-\u02FF]))|(?:[\u0370-\u037D]))|(?:[\u037F-\u1FFF]))|(?:[\u200C-\u200D]))|(?:[\u2070-\u218F]))|(?:[\u2C00-\u2FEF]))|(?:[\u3001-\uD7FF]))|(?:[\uF900-\uFFFE])))|(?:_))|(?:[0-9]))|(?:\u00B7))*)'
     return t

    
tokens = (
              'IT_SELECT',
              'IT_DISTINCT',
              'GT_TIMES',
              'IT_CONSTRUCT',
              'IT_DESCRIBE',
              'IT_ASK',
              'IT_BASE',
              'IT_PREFIX',
              'IT_FROM',
              'IT_WHERE',
              'GT_LCURLEY',
              'GT_RCURLEY',
              'GT_DOT',
              'IT_ORDER',
              'IT_BY',
              'GT_LPAREN',
              'GT_RPAREN',
              'IT_ASC',
              'IT_DESC',
              'IT_LIMIT',
              'IT_OFFSET',
              'IT_UNION',
              'IT_OPTIONAL',
              'IT_GRAPH',
              'IT_FILTER',
              'GT_SEMI',
              'GT_COMMA',
              'IT_a',
              'GT_LBRACKET',
              'GT_RBRACKET',
              'GT_OR',
              'GT_AND',
              'GT_EQUAL',
              'GT_NEQUAL',
              'GT_LT',
              'GT_GT',
              'GT_LE',
              'GT_GE',
              'GT_PLUS',
              'GT_MINUS',
              'GT_DIVIDE',
              'GT_NOT',
              'IT_STR',
              'IT_LANG',
              'IT_DATATYPE',
              'IT_REGEX',
              'IT_BOUND',
              'IT_isURI',
              'IT_isBLANK',
              'IT_isLITERAL',
              'GT_DTYPE',
              'IT_true',
              'IT_false',
              'EmptyPattern',
              'TrailingDot',
              'FROM_NAMED',
              'QuotedIRIref',
              'QNAME_NS',
              'QNAME',
              'BNODE_LABEL',
              'VAR1',
              'VAR2',
              'INTEGER',
              'FLOATING_POINT',
              'STRING_LITERAL1',
              'STRING_LITERAL2',
              'STRING_LITERAL_LONG1',
              'STRING_LITERAL_LONG2',
              'LANGTAG')


whitespace = re.compile(r'\s+')
t_ignore = ' \t\r'
def t_newline(t):
    r'\n+'
    t.lineno += len(t.value)

# Error handling rule
def t_error(t):
    msg = "Unexpected data in input on line %d: %s"%(t.lineno, t.value)
    raise RuntimeError(msg)
    #print msg
    #t.skip(1)

def runLexer():
    lexer = lex.lex(debug=False)
    lexer.input(file(sys.argv[1]).read())
    while 1:
        tok = lexer.token()
        if not tok: break      # No more input
        print tok

if __name__ == '__main__':
    runLexer()
