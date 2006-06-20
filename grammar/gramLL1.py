# $Id$
from swap import myStore, term
from swap.RDFSink import RDF_NS_URI
from swap.term import Literal, Fragment #umm... why not Symbol?

EBNF = myStore.Namespace('http://www.w3.org/2000/10/swap/grammar/ebnf#')
REGEX = myStore.Namespace('http://www.w3.org/2000/10/swap/grammar/regex#')
RDF = myStore.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')

import regex

def main(argv):
    data = argv[-1]
    f = myStore.load(data)
    it = { 'rules': asGrammar(f),
           'tokens': tokens(f) }

    if '--pprint' in argv:
        from pprint import pprint
        pprint(it)
    else:
        import simplejson #http://cheeseshop.python.org/pypi/simplejson
        import sys
        start = it['rules'][0][0]
        print "SYNTAX_%s = " % start,
        simplejson.dump(it, sys.stdout)



def asGrammar(f):
    """find BNF grammar in f and return grammar rules array
    as per http://www.navyrain.net/compilergeneratorinjavascript/
    navyrain@navyrain.net
    """
    rules = []
    for lhs in f.each(pred=RDF.type, obj=EBNF.NonTerminal):
        if lhs is EBNF.eps: continue
        alts = f.the(subj=lhs, pred=EBNF.alt)
        if not alts:
            alts = [lhs]
        for alt in alts:
            s = asSymbol(f, lhs)
            seq = f.the(subj=alt, pred=EBNF.seq)
            if seq is not None:
                r = [s] + [asSymbol(f, x) for x in seq]
            else:
                r = [s, asSymbol(f, alt)]
            if s == 'document': #@@ parameterize start symbol
                rules.insert(0, r)
            else:
                rules.append(r)
    return rules


def tokens(f):
    """find lexer rules f and return JSON struct
    as per http://www.navyrain.net/compilergeneratorinjavascript/
    navyrain@navyrain.net
    """
    tokens = []
    for lhs in f.each(pred=RDF.type, obj=EBNF.Terminal):
        tokens.append([pattern(f, lhs), asSymbol(f, lhs), None])
    return tokens


def pattern(f, s):
    if isinstance(s, Literal):
        return regex.escape(unicode(s))

    #@@ matches should move from EBNF to REGEX
    pat = f.the(subj=s, pred=EBNF.matches)
    if pat:
        pat = unicode(pat)
        return pat.replace("#x", "\\x")

    parts = f.the(subj=s, pred=REGEX.seq)
    if parts:
        return ''.join([pattern(f, i) for i in parts])
    parts = f.the(subj=s, pred=REGEX.alt)
    if parts:
        return '|'.join([pattern(f, i) for i in parts])
    parts = f.the(subj=s, pred=REGEX.diff)
    if parts:
        return '(?!%s)(%s)' % (pattern(f, parts[1]), pattern(f, parts[0]))
    part = f.the(subj=s, pred=REGEX.star)
    if part:
        return '(?:%s)*' % pattern(f, part)
    part = f.the(subj=s, pred=REGEX.rep)
    if part:
        #@@ look up non-grouping paren thingy
        return '(?:%s)+' % pattern(f, part)
    part = f.the(subj=s, pred=REGEX.opt)
    if part:
        #@@ look up non-grouping paren thingy
        return '(?:%s)?' % pattern(f, part)
    raise ValueError, s
    
def sets(f, pred=EBNF.first):
    """get LL(1) first/follow sets
    """
    fi = {}
    for lhs in f.each(pred=RDF.type, obj=EBNF.NonTerminal):
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
    elif EBNF.NonTerminal in f.each(subj=x, pred=RDF.type):
        if x in f.existentials():
            return 's_%d' % id(x)
        else:
            return x.fragid
    elif EBNF.Terminal in f.each(subj=x, pred=RDF.type):
        return 'TOK_%s' % x.fragid
    else:
        raise ValueError, x

if __name__ == '__main__':
    import sys
    main(sys.argv)


# $Log$
# Revision 1.4  2006-06-20 04:46:23  connolly
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
