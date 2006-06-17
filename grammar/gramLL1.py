# $Id$
from swap import myStore, term
from swap.RDFSink import RDF_NS_URI
from swap.term import Literal, Symbol

EBNF = myStore.Namespace('http://www.w3.org/2000/10/swap/grammar/ebnf#')
RDF = myStore.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')

def main(argv):
    data = argv[-1]
    f = myStore.load(data)
    it = { 'rules': asGrammar(f),
             'first': sets(f, EBNF.first),
             'follow': sets(f, EBNF.follow)}

    if '--pprint' in argv:
        from pprint import pprint
        pprint(it)
    else:
        import simplejson #http://cheeseshop.python.org/pypi/simplejson
        import sys
        simplejson.dump(it, sys.stdout)



def asGrammar(f):
    """find BNF grammar in f and return {rhs: [lhs, lhs, ...]} grammar
    """
    rules = {}
    for lhs in f.each(pred=RDF.type, obj=EBNF.NonTerminal):
        if lhs is EBNF.eps: continue
        alts = f.the(subj=lhs, pred=EBNF.alt)
        if not alts: alts = [lhs]
        rhss = []
        for alt in alts:
            seq = f.the(subj=alt, pred=EBNF.seq)
            if seq:
                rhss.append(tuple([asSymbol(f, x) for x in seq]))
        if rhss: rules[asSymbol(f, lhs)] = rhss
    return rules


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

                    
def terminal(x):
    return type(x) is not type(())

def asSymbol(f, x):
    """return grammar symbol x as a JSON item:
    non-terminals become strings
    terminals become ('terminal': name)
    and literals become ('string': str)

    JSON doesn't really have () tuples, but we want something hashable.
    """
    if isinstance(x, Literal):
        return ('string', unicode(x))
    elif x is EBNF.eps:
        #or f.the(subj=x, pred=EBNF.seq) == RDF.nil:
        return ('eps',)
    elif x == EBNF.eof:
        return ('EOF',)
    elif EBNF.NonTerminal in f.each(subj=x, pred=RDF.type):
        if isinstance(x, Symbol):
            return x.fragid
        else:
            return 's_%d' % id(x)
    elif EBNF.Terminal in f.each(subj=x, pred=RDF.type):
        return ('terminal', x.fragid)
    else:
        raise ValueError, x

if __name__ == '__main__':
    import sys
    main(sys.argv)


# $Log$
# Revision 1.2  2006-06-17 06:11:03  connolly
# support JSON output or python pretty-printed output
# fix keys in first/follow sets to be strings
# skip eps when it's not relevant
# turn anonymous nodes into strings rather than ints, since JSON keys are strings
#
# Revision 1.1  2006/06/17 03:12:42  connolly
# finds grammar rules, first sets, follow sets following EBNF ontology;
# prints JSON-happy structure
#
