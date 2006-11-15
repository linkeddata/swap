# $Id$
from swap import myStore, term
from swap.RDFSink import RDF_NS_URI
from swap.term import Literal, Fragment #umm... why not Symbol?

EBNF = myStore.Namespace('http://www.w3.org/2000/10/swap/grammar/ebnf#')
REGEX = myStore.Namespace('http://www.w3.org/2000/10/swap/grammar/regex#')
RDF = myStore.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')

import re

def main(argv):
    data, lang = argv[-2:]
    f = myStore.load(data)
    lang = f.newSymbol(lang)
    it = { 'rules': asGrammar(f, lang),
           'tokens': tokens(f, lang),
           'first': sets(f, lang, EBNF.first),
           'follow': sets(f, lang, EBNF.follow),
           }

    if '--pprint' in argv:
        from pprint import pprint
        pprint(it)
    elif '--yacc' in argv:
        toYacc(it)
    elif '--ply' in argv:
        toPly(it)
    else:
        import simplejson #http://cheeseshop.python.org/pypi/simplejson
        import sys
        start = it['rules'][0][0]
        print "SYNTAX_%s = " % start,
        simplejson.dump(it, sys.stdout)



def asGrammar(f, lang):
    """find BNF grammar in f and return grammar rules array
    as per http://www.navyrain.net/compilergeneratorinjavascript/
    navyrain@navyrain.net
    """
    rules = []
    start = asSymbol(f, f.the(subj=lang, pred=EBNF.start))
    for lhs in f.each(pred=EBNF.nonTerminal, obj=lang):
        s = asSymbol(f, lhs)

        alts = f.the(subj=lhs, pred=EBNF.alt)
        seq = f.the(subj=lhs, pred=EBNF.seq)

        if alts is None and seq is None:
            raise ValueError, "no alt nor seq for %s" % lhs
        elif alts and seq:
            raise ValueError, "both alt and seq for %s" % lhs
        elif alts:
            for alt in alts:
                seq = f.the(subj=alt, pred=EBNF.seq)
                if seq is None:
                    r = [s, asSymbol(f, alt)]
                elif seq is RDF.nil:
                    r = [s]
                elif alt in f.existentials():
                    r = [s] + [asSymbol(f, x) for x in seq]
                else:
                    r = [s, asSymbol(f, alt)]
                addRule(rules, s, start, r)
        else:
            r = [s] + [asSymbol(f, x) for x in seq]
            addRule(rules, s, start, r)

    return rules
                
def addRule(rules, s, start, r):
    if s == start: rules.insert(0, r)
    else: rules.append(r)

def tokens(f, lang):
    """find lexer rules f and return JSON struct
    as per http://www.navyrain.net/compilergeneratorinjavascript/
    navyrain@navyrain.net
    """
    tokens = []
    for lhs in f.each(subj=lang, pred=EBNF.terminal):
        tokens.append([pattern(f, lhs), asSymbol(f, lhs), None])
    return tokens


def pattern(f, s):
    if isinstance(s, Literal):
        return reesc(unicode(s))

    pat = f.the(subj=s, pred=REGEX.matches)
    if pat:
        return '(?:%s)' % unicode(pat)

    parts = f.the(subj=s, pred=REGEX.seq)
    if parts:
        return '(?:%s)' % ''.join([pattern(f, i) for i in parts])
    parts = f.the(subj=s, pred=REGEX.alt)
    if parts:
        return '(?:%s)' % '|'.join([pattern(f, i) for i in parts])
    parts = f.the(subj=s, pred=REGEX.diff)
    if parts:
        return '(?!%s)(%s)' % (pattern(f, parts[1]), pattern(f, parts[0]))
    part = f.the(subj=s, pred=REGEX.star)
    if part:
        return '(?:%s*)' % pattern(f, part)
    part = f.the(subj=s, pred=REGEX.plus)
    if part:
        return '(?:%s+)' % pattern(f, part)
    part = f.the(subj=s, pred=REGEX.opt)
    if part:
        return '(?:%s?)' % pattern(f, part)
    raise ValueError, s
    
def reesc(txt):
    r"""turn a string into a regex string constant for that string
    >>> reesc("(")
    '\\('
    """
    return re.sub("(\W)", r"\\\1", txt)


def sets(f, lang, pred=EBNF.first):
    """get LL(1) first/follow sets
    """
    fi = {}
    for lhs in f.each(pred=EBNF.nonTerminal, obj=lang):
        if lhs is EBNF.empty: continue
        fs = []
        for obj in f.each(subj=lhs, pred=pred):
            fs.append(asSymbol(f, obj))
        fi[asSymbol(f, lhs)] = fs
    return fi

                    
def asSymbol(f, x):
    """return grammar symbol x as a JSON string
    We prefix Terminal names by TOK_ and then
    assume disjointness of non-terminals, terminals, and literals.
    And we assume no non-terminal fragids start with '_'.
    """
    if isinstance(x, Literal):
        return tokid(unicode(x)) #hmm...
    elif x is EBNF.empty or f.the(subj=x, pred=EBNF.seq) == RDF.nil:
        return 'EMPTY'
    elif x == EBNF.eof:
        return 'EOF'
    elif f.each(subj=x, pred=EBNF.nonTerminal):
        if x in f.existentials():

            # try to pin down an exact path
            y = f.the(subj=x, pred=EBNF.plus)
            if y: return "_%s_plus" % asSymbol(f, y)
            y = f.the(subj=x, pred=EBNF.star)
            if y: return "_%s_star" % asSymbol(f, y)
            y = f.the(subj=x, pred=EBNF.opt)
            if y: return "_%s_opt" % asSymbol(f, y)

            # just say whether it's a seq or alt
            y = f.the(subj=x, pred=EBNF.alt)
            if y: return '_alt_%d' % abs(id(x))
            y = f.the(subj=x, pred=EBNF.seq)
            if y: return '_seq_%d' % abs(id(x))

            raise ValueError, "umm...@@"
        else:
            return x.fragid
    elif f.each(pred=EBNF.terminal, obj=x):
        return 'TOK_%s' % x.fragid
    else:
        raise ValueError, x

def toYacc(it):
    print """
%{
int yylex (void);
void yyerror (char const *);
%}
"""
    
    tokens = {}
    for pat, tok, dummy in it['tokens']:
        tokens[tok] = 1
        if tok.startswith("TOK"):
            print "%%token %s" % tok

    print "%%"
    
    for rule in it['rules']:
        lhs = rule[0]
        rhs = rule[1:]
        print "%s: " % lhs,
        for sym in rhs:
            if tokens.has_key(sym):
                if sym.startswith("TOK"):
                    print sym,
                else:
                    print '"%s"' % sym,
            else:
                print sym,
        print ";"
    print "%%"


def toPly(it):
    t2r = dict([(tokid(tok), pat) for pat, tok, func in it['tokens']])
    t2t = dict([(tok, tokid(tok)) for pat, tok, func in it['tokens']])
    print "tokens = ", `tuple(t2r.keys())`

    print "# Tokens "

    for t, pat in t2r.iteritems():
        print "t_%s = %s" % (t, `pat`)

    print
    print "import lex"
    print "lex.lex()"
    print

    # collect all the rules about one symbol...
    rules = {}
    for rule in it['rules']:
        lhs = rule[0]
        rhs = rule[1:]
        rhss = rules.get(lhs, None)
        if not rhss: rules[lhs] = rhss = []
        rhss.append(rhs)

    # find all the non-terminals; make sure the start symbol is 1st
    start = it['rules'][0][0]
    nts = rules.keys()
    del nts[nts.index(start)]
    nts.insert(0, start)
    
    for lhs in nts:
        rhss = rules[lhs]
        print "def p_%s(t):" % lhs
        for rhs in rhss:
            rhs = ' '.join([t2t.get(s, s) for s in rhs])
            if lhs:
                print '    """%s : %s' % (lhs, rhs)
                lhs = None
            else:
                print '          | %s' % rhs
        print '    """'
        print "    pass"
        print
        
    print
    print "import yacc"
    print "yacc.yacc()"
    print
    print """
if __name__ == '__main__':
    import sys
    yacc.parse(file(sys.argv[1]).read())
"""
    
    
def tokid(s):
    """turn a string into a python identifier

    >>> tokid(u'TOK_STRING_LITERAL_2')
    u'STRING_LITERAL_2'

    >>> tokid(u'@a')
    u'x40a'
    """
    r = ''
    if s.startswith("TOK_"): s = s[4:]
    for c in s:
        if c == '_' or (r == '' and c.isalpha()) or c.isalnum():
            r = r + c
        else:
            r = r + 'x%x' % ord(c)
    return r.encode('us-ascii')

def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    import sys
    if '--test' in sys.argv:
        _test()
    else:
        main(sys.argv)


# $Log$
# Revision 1.10  2006-11-15 19:59:25  connolly
# change rep to plus, eps to empty
#
# Revision 1.9  2006/06/22 22:08:37  connolly
# trying to generate python ply module to test grammars
# reworked asGrammar; not sure if it's got more or less bugs now...
# use python-happy token names rather than literals
# use more mnemonic symbol names for some bnodes
# include first/follow stuff (usually empty... hmm...)
#
# Revision 1.8  2006/06/20 23:25:58  connolly
# regex escaping details. ugh!
#
# Revision 1.7  2006/06/20 21:13:08  connolly
# add an arg for the URI of the language
# change NonTerminal, Terminal from class to relationship to language
# move matches to regex
#
# Revision 1.6  2006/06/20 08:10:35  connolly
# added --yacc option
# discovered asGrammar was talking the alt/seq tree all wrong; fixed it
# removed '-' from symbol names
#
# Revision 1.5  2006/06/20 05:59:31  connolly
# parameterize start symbol
#
# Revision 1.4  2006/06/20 04:46:23  connolly
# json version of turtle grammar from Andy Mon, 19 Jun 2006 16:12:03 +0100
#
# Revision 1.3  2006/06/17 08:32:20  connolly
# found a javascript parser generator that implements SLR table generation
# so we don't need first/follow.
#
# Got some terminal regex's working, e.g. uriref
#
# Revision 1.2  2006/06/17 06:11:03  connolly
# support JSON output or python pretty-printed output
# fix keys in first/follow sets to be strings
# skip eps when it's not relevant
# turn anonymous nodes into strings rather than ints, since JSON keys are strings
#
# Revision 1.1  2006/06/17 03:12:42  connolly
# finds grammar rules, first sets, follow sets following EBNF ontology;
# prints JSON-happy structure
#
