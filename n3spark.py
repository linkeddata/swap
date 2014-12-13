#!/usr/bin/python
"""
n3spark.py -- a re-implementation of RDF/n3 syntax using the SPARK tools

Share and Enjoy. Open Source license:
Copyright (c) 2001 W3C (MIT, INRIA, Keio)
http://www.w3.org/Consortium/Legal/copyright-software-19980720

see log at end
"""
rcsId = "$Id$"


from string import find

# SPARK Scanning, Parsing, and Rewriting Kit
# http://www.cpsc.ucalgary.ca/~aycock/spark/
# cf
# Compiling Little Languages in Python
# at the 7th International Python Conference. 
import spark 

# http://www.w3.org/DesignIssues/Notation3


class AutoN3Parser(spark.GenericASTBuilder):
    def __init__(self, AST, start='document'):
        spark.GenericASTBuilder.__init__(self, AST, start)

    def p_document(self, args):
        ''' document ::=
            document ::= directive document
            document ::= statements
            document ::= statements . document
        '''

    def p_directive(self, args):
        ''' directive ::= prefix qname uriref .
        '''

    def p_statements(self, args):
        '''
        statements ::= term
        statements ::= term . statements
        statements ::= term predicates
        statements ::= term predicates .
        statements ::= term predicates . statements
        '''

    def p_term(self, args):
        '''
        term ::= uriref
        term ::= qname
        term ::= this
        term ::= shorthand
        term ::= strlit1
        term ::= strlit2
        term ::= strlit3
        term ::= ( )
        term ::= ( items )
        term ::= [ ]
        term ::= [ predicates ]
        term ::= { }
        term ::= { statements }
        '''

    def p_keyword(self, args):
        '''
        shorthand ::= a
        shorthand ::= =
        '''
        
    def p_predicates(self, args):
        '''
        predicates ::= pred objects
        predicates ::= pred objects ;
        predicates ::= pred objects ; predicates
        '''

    def p_pred(self, args):
        '''
        pred ::= term
        pred ::= is term of
        '''

    def p_objects(self, args):
        '''
        objects ::= term
        objects ::= term , objects
        '''

    def p_items(self, args):
        '''
        items ::= term
        items ::= term items
        '''


    def typestring(self, token):
        """monkey-see-monkey-do from spark/auto/example.py"""
        return token.type

    def error(self, token):
        print "@@parse error at line", token.lineno, ":", token.type, token.attr
        raise SystemExit
    
    def resolve(self, list):
        print "@@resolving ambiguity among:", list
        return list[0]
    
    def terminal(self, token):
        """monkey-see-monkey-do from spark/auto/example.py"""
        #
        #  Homogeneous AST.
        #
        rv = AST(token.type)
        rv.attr = token.attr
        return rv

    def nonterminal(self, type, args):
        """monkey-see-monkey-do from spark/auto/example.py"""
        #
        #  Flatten AST a bit by not making nodes if there's only
        #  one child.
        #
        if len(args) == 1:
            return args[0]
        return spark.GenericASTBuilder.nonterminal(self, type, args)


class AST:
    """monkey-see-monkey-do from spark/auto/ast.py"""
    
    def __init__(self, type):
        self.type = type
        self._kids = []

    #
    #  Not all these may be needed, depending on which classes you use:
    #
    #  __getitem__		GenericASTTraversal, GenericASTMatcher
    #  __len__		GenericASTBuilder
    #  __setslice__		GenericASTBuilder
    #  __cmp__		GenericASTMatcher
    #
    def __getitem__(self, i):
        return self._kids[i]
    def __len__(self):
        return len(self._kids)
    def __setslice__(self, low, high, seq):
        self._kids[low:high] = seq
    def __cmp__(self, o):
        return cmp(self.type, o)

    def dump(self, level=0):
        print level * "  ",
        print self.type
        for k in self._kids:
            k.dump(level+1)



class Scanner0(spark.GenericScanner):
    """the split between Scanner0 and Scanner
    prioritizes triple-quoting... @@more explanation"""
    
    def __init__(self):
        spark.GenericScanner.__init__(self)
        self.ln = 0

    def t_whitespace(self, s):
        r' \s+ '
        self._ln = self._ln + countNewlines(s)

    def t_comment(self, s):
        r' \#.*\n '
        self._ln = self._ln + countNewlines(s)

    def t_prefix(self, s):
        r' @prefix '
        self.rv.append(Token(lineno=self._ln, type='prefix'))

    def t_this(self, s):
        r' this '
        self.rv.append(Token(lineno=self._ln, type=s))

    def t_a(self, s):
        r' a\b ' #@@matches axy:def?
        self.rv.append(Token(lineno=self._ln, type=s))

    def t_is(self, s):
        r' is\b ' #@@matches axy:def?
        self.rv.append(Token(lineno=self._ln, type=s))

    def t_of(self, s):
        r' of\b ' #@@matches axy:def?
        self.rv.append(Token(lineno=self._ln, type=s))

    def t_uriref(self, s):
        r' <[^ >]*> '
        self.rv.append(Token(lineno=self._ln, type='uriref', attr=s[1:-1]))

    def t_strlit1(self, s):
        r' "([^\"\\\n]|\\[\\\"nrt])*" '
        self.rv.append(Token(lineno=self._ln, type='strlit1', attr=s))
        self.ln = self.ln + countNewlines(s)
    
    def t_strlit2(self, s):
        r" '([^\'\\\n]|\\[\\\'nrt])*' "
        self.rv.append(Token(lineno=self._ln, type='strlit2', attr=s))
        self.ln = self.ln + countNewlines(s)
    
    def t_punct(self, s):
        r' [\(\)\[\]=\.{};,] '
        self.rv.append(Token(lineno=self._ln, type=s))
    
    def tokenize(self, input):
        self.rv = []
        self._ln = 1
        spark.GenericScanner.tokenize(self, input)
        return self.rv

    def error(self, s):
        print "syntax error: bad token at line", self._ln
        

class Scanner(Scanner0):
    """higher priority patterns
    """
    def t_qname(self, s):
        r' [a-zA-Z0-9_-]*:[a-zA-Z0-9_-]* '

        # split at :?
        self.rv.append(Token(lineno=self._ln, type='qname', attr=s))

    def t_strlit3(self, s):
        r' """([^\"\\]|\\[\\\"nrt])*""" ' #@@not right
        self.line = self.line + countNewlines(s)
        self.rv.append(Token(lineno=self._ln, type='strlit3', attr=s))


def countNewlines(s):
    i=-1
    l=0
    while 1:
        i = find(s, "\n", i+1)
        if i<0: break
        l = l + 1
    return l

class Token:
    def __init__(self, lineno, type, attr=None):
        self.lineno = lineno
        self.type = type
        self.attr = attr

    def __cmp__(self, o):
        return cmp(self.type, o)

    def __repr__(self):
        if self.attr is None: return self.type
        else: return self.attr



def parse(tokens):
    parser = AutoN3Parser(AST)
    return parser.parse(tokens)

def scan(f):
    input = f.read()
    scanner = Scanner()
    return scanner.tokenize(input)

def test():
    import sys
    f = open(sys.argv[1])
    tokens = scan(f)
    print "TOKENS:", tokens
    t = parse(tokens)
    print "AST:"
    t.dump()


if __name__ == '__main__':
    test()


# $Log$
# Revision 1.3  2005-07-13 22:38:33  syosi
# fix conflicts
#
# Revision 1.2  2001/08/28 21:54:44  connolly
# line numbering, =, run-on fix
#
# Revision 1.1  2001/08/28 05:10:31  connolly
# bijan pointed me to this SPARK toolkit, which is nicely self-contained.
#
# So I've taken another whack at N3 syntax.
#
# So far, it does something reasonable for the test/acl-pf.py test.
#
