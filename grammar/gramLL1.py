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
           'tokens': tokens(f, lang) }

    if '--pprint' in argv:
        from pprint import pprint
        pprint(it)
    elif '--yacc' in argv:
        toYacc(it)
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
        if lhs is EBNF.eps: continue

        s = asSymbol(f, lhs)

        alts = f.the(subj=lhs, pred=EBNF.alt)
        seq = f.the(subj=lhs, pred=EBNF.seq)

        if alts is None and seq is None:
            raise ValueError, "no alt nor seq for %s" % lhs

        if alts:
            for alt in alts:
                addRule(rules, s, start, [s, asSymbol(f, alt)])
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
    part = f.the(subj=s, pred=REGEX.rep)
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
        if lhs is EBNF.eps: continue
        fs = []
        for obj in f.each(subj=lhs, pred=pred):
            fs.append(asSymbol(f, obj))
        fi[asSymbol(f, lhs)] = fs
    return fi

                    
def asSymbol(f, x):
    """return grammar symbol x as a JSON string
    We prefix Terminal names by TOK_ and then
    assume disjointness of non-terminals, terminals, and literals
    """
    if isinstance(x, Literal):
        return unicode(x) #hmm...
    elif x is EBNF.eps:
        #or f.the(subj=x, pred=EBNF.seq) == RDF.nil:
        return 'EMPTY'
    elif x == EBNF.eof:
        return 'EOF'
    elif f.each(subj=x, pred=EBNF.nonTerminal):
        if x in f.existentials():
            return 's_%d' % abs(id(x))
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


if __name__ == '__main__':
    import sys
    main(sys.argv)


# $Log$
# Revision 1.8  2006-06-20 23:25:58  connolly
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
