"""Use ply to tokenize a SPARQL expression


"""

import re
import sys
#import lex

bufsiz = 3


class Tokens(object):
    #literal strings
    t_IT_SELECT = u'SELECT'
    t_IT_DISTINCT = u'DISTINCT'
    t_IT_CONSTRUCT = u'CONSTRUCT'
    t_IT_DESCRIBE = u'DESCRIBE'
    t_IT_ASK = u'ASK'
    t_IT_BASE = u'BASE'
    t_IT_PREFIX = u'PREFIX'
    t_FROM_NAMED = u'FROM(?:(?:\u0008)|(?:(?:\\n)|(?:(?:\\r)|(?:(?: )|(?:(?:\u00A0)|(?:(?:[\u2000-\u200B])|(?:(?:\u202F)|(?:(?:\u205F)|(?:\u3000)))))))))+NAMED'
    t_IT_FROM = u'FROM'
    t_IT_WHERE = u'WHERE'
    t_IT_ORDER = u'ORDER'
    t_IT_BY = u'BY'
    t_IT_ASC = u'ASC'
    t_IT_DESC = u'DESC'
    t_IT_LIMIT = u'LIMIT'
    t_IT_OFFSET = u'OFFSET'
    t_IT_UNION = u'UNION'
    t_IT_OPTIONAL = u'OPTIONAL'
    t_IT_GRAPH = u'GRAPH'
    t_IT_FILTER = u'FILTER'
    t_IT_STR = u'STR'
    t_IT_LANG = u'LANG'
    t_IT_DATATYPE = u'DATATYPE'
    t_IT_REGEX = u'REGEX'
    t_IT_BOUND = u'BOUND'
    t_IT_isURI = u'isURI'
    t_IT_isBLANK = u'isBLANK'
    t_IT_isLITERAL = u'isLITERAL'
    t_IT_true = u'true'
    t_IT_false = u'false'


    t_QuotedIRIref = u'<[^> ]*>'


    t_FLOATING_POINT = u'(?:[0-9]+\\.[0-9]*(?:[eE][\\+-]?[0-9]+)?)|(?:(?:\\.[0-9]+(?:[eE][\\+-]?[0-9]+)?)|(?:[0-9]+(?:[eE][\\+-]?[0-9]+)))'
    t_DECIMAL = u'(?:[0-9]+\\.[0-9]*)|(?:\\.[0-9]+)'
    t_INTEGER = u'[0-9]+'
    t_STRING_LITERAL_LONG1 = u'"""(?:(?:[^"\\\\])|(?:(?:(?:\\\\[^\\n\\r]))|(?:(?:(?:"[^"]))|(?:(?:""[^"])))))*"""'
    t_STRING_LITERAL_LONG2 = u'\'\'\'(?:(?:[^\'\\\\])|(?:(?:(?:\\\\[^\\n\\r]))|(?:(?:(?:\'[^\']))|(?:(?:\'\'[^\'])))))*\'\'\''
    t_STRING_LITERAL1 = u'\'(?:(?:[^\'\\\\\\n\\r])|(?:(?:\\\\[^\\n\\r])))*\''
    t_STRING_LITERAL2 = u'"(?:(?:[^"\\\\\\n\\r])|(?:(?:\\\\[^\\n\\r])))*"'
    t_LANGTAG = u'@[a-zA-Z]+(?:-[a-zA-Z0-9]+)*'
    t_BNODE_LABEL = u'_:(?:(?:(?:_)|(?:(?:(?:[A-Z])|(?:(?:[a-z])|(?:(?:[\u00C0-\u00D6])|(?:(?:[\u00D8-\u00F6])|(?:(?:[\u00F8-\u02FF])|(?:(?:[\u0370-\u037D])|(?:(?:[\u037F-\u1FFF])|(?:(?:[\u200C-\u200D])|(?:(?:[\u2070-\u218F])|(?:(?:[\u2C00-\u2FEF])|(?:(?:[\u3001-\uD7FF])|(?:[\uF900-\uFFFE]))))))))))))))(?:(?:(?:(?:[A-Z])|(?:(?:[a-z])|(?:(?:[\u00C0-\u00D6])|(?:(?:[\u00D8-\u00F6])|(?:(?:[\u00F8-\u02FF])|(?:(?:[\u0370-\u037D])|(?:(?:[\u037F-\u1FFF])|(?:(?:[\u200C-\u200D])|(?:(?:[\u2070-\u218F])|(?:(?:[\u2C00-\u2FEF])|(?:(?:[\u3001-\uD7FF])|(?:[\uF900-\uFFFE])))))))))))))|(?:(?:_)|(?:(?:-)|(?:(?:\\.)|(?:(?:[0-9])|(?:\u00B7))))))*)'
    t_QNAME = u'(?:(?:(?:[A-Z])|(?:(?:[a-z])|(?:(?:[\u00C0-\u00D6])|(?:(?:[\u00D8-\u00F6])|(?:(?:[\u00F8-\u02FF])|(?:(?:[\u0370-\u037D])|(?:(?:[\u037F-\u1FFF])|(?:(?:[\u200C-\u200D])|(?:(?:[\u2070-\u218F])|(?:(?:[\u2C00-\u2FEF])|(?:(?:[\u3001-\uD7FF])|(?:[\uF900-\uFFFE]))))))))))))(?:(?:(?:(?:[A-Z])|(?:(?:[a-z])|(?:(?:[\u00C0-\u00D6])|(?:(?:[\u00D8-\u00F6])|(?:(?:[\u00F8-\u02FF])|(?:(?:[\u0370-\u037D])|(?:(?:[\u037F-\u1FFF])|(?:(?:[\u200C-\u200D])|(?:(?:[\u2070-\u218F])|(?:(?:[\u2C00-\u2FEF])|(?:(?:[\u3001-\uD7FF])|(?:[\uF900-\uFFFE])))))))))))))|(?:(?:_)|(?:(?:-)|(?:(?:\\.)|(?:(?:[0-9])|(?:\u00B7))))))*)?:(?:(?:(?:_)|(?:(?:(?:[A-Z])|(?:(?:[a-z])|(?:(?:[\u00C0-\u00D6])|(?:(?:[\u00D8-\u00F6])|(?:(?:[\u00F8-\u02FF])|(?:(?:[\u0370-\u037D])|(?:(?:[\u037F-\u1FFF])|(?:(?:[\u200C-\u200D])|(?:(?:[\u2070-\u218F])|(?:(?:[\u2C00-\u2FEF])|(?:(?:[\u3001-\uD7FF])|(?:[\uF900-\uFFFE]))))))))))))))(?:(?:(?:(?:[A-Z])|(?:(?:[a-z])|(?:(?:[\u00C0-\u00D6])|(?:(?:[\u00D8-\u00F6])|(?:(?:[\u00F8-\u02FF])|(?:(?:[\u0370-\u037D])|(?:(?:[\u037F-\u1FFF])|(?:(?:[\u200C-\u200D])|(?:(?:[\u2070-\u218F])|(?:(?:[\u2C00-\u2FEF])|(?:(?:[\u3001-\uD7FF])|(?:[\uF900-\uFFFE])))))))))))))|(?:(?:_)|(?:(?:-)|(?:(?:\\.)|(?:(?:[0-9])|(?:\u00B7))))))*)'
    t_QNAME_NS = u'(?:(?:(?:[A-Z])|(?:(?:[a-z])|(?:(?:[\u00C0-\u00D6])|(?:(?:[\u00D8-\u00F6])|(?:(?:[\u00F8-\u02FF])|(?:(?:[\u0370-\u037D])|(?:(?:[\u037F-\u1FFF])|(?:(?:[\u200C-\u200D])|(?:(?:[\u2070-\u218F])|(?:(?:[\u2C00-\u2FEF])|(?:(?:[\u3001-\uD7FF])|(?:[\uF900-\uFFFE]))))))))))))(?:(?:(?:(?:[A-Z])|(?:(?:[a-z])|(?:(?:[\u00C0-\u00D6])|(?:(?:[\u00D8-\u00F6])|(?:(?:[\u00F8-\u02FF])|(?:(?:[\u0370-\u037D])|(?:(?:[\u037F-\u1FFF])|(?:(?:[\u200C-\u200D])|(?:(?:[\u2070-\u218F])|(?:(?:[\u2C00-\u2FEF])|(?:(?:[\u3001-\uD7FF])|(?:[\uF900-\uFFFE])))))))))))))|(?:(?:_)|(?:(?:-)|(?:(?:\\.)|(?:(?:[0-9])|(?:\u00B7))))))*)?:'
    t_VAR2 = u'\\$(?:(?:(?:(?:(?:[A-Z])|(?:(?:[a-z])|(?:(?:[\u00C0-\u00D6])|(?:(?:[\u00D8-\u00F6])|(?:(?:[\u00F8-\u02FF])|(?:(?:[\u0370-\u037D])|(?:(?:[\u037F-\u1FFF])|(?:(?:[\u200C-\u200D])|(?:(?:[\u2070-\u218F])|(?:(?:[\u2C00-\u2FEF])|(?:(?:[\u3001-\uD7FF])|(?:[\uF900-\uFFFE])))))))))))))|(?:(?:_)|(?:(?:[0-9])|(?:\u00B7))))*)'
    t_VAR1 = u'\\?(?:(?:(?:(?:(?:[A-Z])|(?:(?:[a-z])|(?:(?:[\u00C0-\u00D6])|(?:(?:[\u00D8-\u00F6])|(?:(?:[\u00F8-\u02FF])|(?:(?:[\u0370-\u037D])|(?:(?:[\u037F-\u1FFF])|(?:(?:[\u200C-\u200D])|(?:(?:[\u2070-\u218F])|(?:(?:[\u2C00-\u2FEF])|(?:(?:[\u3001-\uD7FF])|(?:[\uF900-\uFFFE])))))))))))))|(?:(?:_)|(?:(?:[0-9])|(?:\u00B7))))*)'
    t_CloseSquare = u',?(?:(?:\u0008)|(?:(?:\\n)|(?:(?:\\r)|(?:(?: )|(?:(?:\u00A0)|(?:(?:[\u2000-\u200B])|(?:(?:\u202F)|(?:(?:\u205F)|(?:\u3000)))))))))*;?(?:(?:\u0008)|(?:(?:\\n)|(?:(?:\\r)|(?:(?: )|(?:(?:\u00A0)|(?:(?:[\u2000-\u200B])|(?:(?:\u202F)|(?:(?:\u205F)|(?:\u3000)))))))))*\\]'
    t_CloseCurly = u',?(?:(?:\u0008)|(?:(?:\\n)|(?:(?:\\r)|(?:(?: )|(?:(?:\u00A0)|(?:(?:[\u2000-\u200B])|(?:(?:\u202F)|(?:(?:\u205F)|(?:\u3000)))))))))*;?(?:(?:\u0008)|(?:(?:\\n)|(?:(?:\\r)|(?:(?: )|(?:(?:\u00A0)|(?:(?:[\u2000-\u200B])|(?:(?:\u202F)|(?:(?:\u205F)|(?:\u3000)))))))))*\\.?(?:(?:\u0008)|(?:(?:\\n)|(?:(?:\\r)|(?:(?: )|(?:(?:\u00A0)|(?:(?:[\u2000-\u200B])|(?:(?:\u202F)|(?:(?:\u205F)|(?:\u3000)))))))))*\\}'
    t_OptDot = u'\\.(?=((?:(?:(?:\u0008)|(?:(?:\\n)|(?:(?:\\r)|(?:(?: )|(?:(?:\u00A0)|(?:(?:[\u2000-\u200B])|(?:(?:\u202F)|(?:(?:\u205F)|(?:\u3000)))))))))*(?:(?:(?:(?:UNION)|(?:(?:OPTIONAL)|(?:(?:GRAPH)|(?:FILTER))))[^a-z])|(?:\\{)))))'
    t_EmptyPattern = u'\\{(?:(?:\u0008)|(?:(?:\\n)|(?:(?:\\r)|(?:(?: )|(?:(?:\u00A0)|(?:(?:[\u2000-\u200B])|(?:(?:\u202F)|(?:(?:\u205F)|(?:\u3000)))))))))*\\}'

    #ignored
    t_PASSED_TOKENS = u'(?:(?:(?:\u0008)|(?:(?:\\n)|(?:(?:\\r)|(?:(?: )|(?:(?:\u00A0)|(?:(?:[\u2000-\u200B])|(?:(?:\u202F)|(?:(?:\u205F)|(?:\u3000)))))))))+)|(?:(?:#[^\\n]*\\n)|(?:/\\*(?:(?:/[^\\*])|(?:[^/\\*]))*\\*/))'

    #two characters
    t_GT_OR = u'\\|\\|'
    t_GT_AND = u'&&'
    t_GT_NEQUAL = u'!='
    t_GT_LE = u'<='
    t_GT_GE = u'>='
    t_GT_DTYPE = u'\\^\\^'

    #single character
    t_GT_TIMES = u'\\*'
    t_GT_LPAREN = u'\\('
    t_GT_RPAREN = u'\\)'
    t_GT_SEMI = u';'
    t_GT_COMMA = u','
    t_IT_a = u'a'
    t_GT_EQUAL = u'='
    t_GT_LT = u'<'
    t_GT_GT = u'>'
    t_GT_PLUS = u'\\+'
    t_GT_MINUS = u'-'
    t_GT_DIVIDE = u'/'
    t_GT_NOT = u'!'
    t_Dot = u'\\.'
    t_OpenCurly = u'\\{'
    t_OpenSquare = u'\\['


tokens = ('IT_SELECT',
        'IT_DISTINCT',
        'IT_CONSTRUCT',
        'IT_DESCRIBE',
        'IT_ASK',
        'IT_BASE',
        'IT_PREFIX',
        'FROM_NAMED',
        'IT_FROM',
        'IT_WHERE',
        'IT_ORDER',
        'IT_BY',
        'IT_ASC',
        'IT_DESC',
        'IT_LIMIT',
        'IT_OFFSET',
        'IT_UNION',
        'IT_OPTIONAL',
        'IT_GRAPH',
        'IT_FILTER',
        'IT_STR',
        'IT_LANG',
        'IT_DATATYPE',
        'IT_REGEX',
        'IT_BOUND',
        'IT_isURI',
        'IT_isBLANK',
        'IT_isLITERAL',
        'IT_true',
        'IT_false',
        'QuotedIRIref',
        'FLOATING_POINT',
        'DECIMAL',
        'INTEGER',
        'STRING_LITERAL_LONG1',
        'STRING_LITERAL_LONG2',
        'STRING_LITERAL1',
        'STRING_LITERAL2',
        'LANGTAG',
        'BNODE_LABEL',
        'QNAME',
        'QNAME_NS',
        'VAR2',
        'VAR1',
        'CloseSquare',
        'CloseCurly',
        'OptDot',
        'EmptyPattern',
        'PASSED_TOKENS',
        'GT_OR',
        'GT_AND',
        'GT_NEQUAL',
        'GT_LE',
        'GT_GE',
        'GT_DTYPE',
        'GT_TIMES',
        'GT_LPAREN',
        'GT_RPAREN',
        'GT_SEMI',
        'GT_COMMA',
        'IT_a',
        'GT_EQUAL',
        'GT_LT',
        'GT_GT',
        'GT_PLUS',
        'GT_MINUS',
        'GT_DIVIDE',
        'GT_NOT',
        'Dot',
        'OpenCurly',
        'OpenSquare' )

class Lexer(object):
    def __init__(self):
        self.uri = None
        self.buffer = None
        self.tokenStream = None
        self.chunk = ''
        self.was = ''
        self.line = 0
        self.fixTokens()

    def input(self, buf):
        self.buffer = buf
        self.line = 0
        self.tokenStream = self.parse()
        #print [m for m in self.parse()]

    def parse(self):
        while True: 
            self.chunk += self.buffer.read().decode('utf_8')
            if not self.chunk: break
            for token in self.tokenize(): 
                yield token

    def tokenize(self): 
        """Tokenize the current chunk."""
        while True: 
            if not self.chunk: break
            waslen = len(self.was)
            (name, m) = self.match(self.was + self.chunk, waslen)
            if m:
                token = (self.was + self.chunk)[m.start():m.end()]
                self.was = token
                self.line += len(token.split('\n')) - 1
                if name != "PASSED_TOKENS":
                    yield (name, token, self.line)
                endpos = (m.end() - waslen)
                if not endpos: 
                   raise ValueError, "Got zero-length token"
                self.chunk = self.chunk[endpos:]
            else: break

    def token(self):
        if not self.tokenStream: return None
        try:
            return self.tokenStream.next()
        except:
            return None

    def fixTokens(self):
        for f_name in dir(Tokens):
            if f_name[:2] == 't_':
                setattr(Tokens, 'c_' + f_name[2:], re.compile(getattr(Tokens, f_name)))
        #print dir(Tokens)

    def match(self, string, offset):
        """try everything in the list ``tokens''

        """
        #print "Trying to match: " + string[offset:]
        for name in tokens:
            #print "trying " + name
            pattern = getattr(Tokens, 'c_' + name)
            r = pattern.match(string, offset)
            if r:
                #print "success with: " + name + " matching ``" + string[r.start():r.end()] + "''"
                return (name, r)
        return None

def runLexer():
    lexer = Lexer()
    lexer.input(file(sys.argv[1]))
    while 1:
        tok = lexer.token()
        if not tok: break      # No more input
        print tok

if __name__ == '__main__':
    runLexer()
