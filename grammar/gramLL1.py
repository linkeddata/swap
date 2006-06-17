# $Id$
from swap import myStore, term
from swap.RDFSink import RDF_NS_URI
from swap.term import Literal

EBNF = myStore.Namespace('http://www.w3.org/2000/10/swap/grammar/ebnf#')
RDF = myStore.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')

def main(argv):
    from pprint import pprint
    data = argv[1]
    f = myStore.load(data)
    pprint({ 'rules': asGrammar(f),
             'first': sets(f, EBNF.first),
             'follow': sets(f, EBNF.follow)})



def asGrammar(f):
    """find BNF grammar in f and return {rhs: [lhs, lhs, ...]} grammar
    """
    rules = {}
    for lhs in f.each(pred=RDF.type, obj=EBNF.NonTerminal):
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
        fs = []
        for obj in f.each(subj=lhs, pred=pred):
            fs.append(asSymbol(f, obj))
        fi[lhs] = fs
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
    elif f.the(subj=x, pred=EBNF.seq) == RDF.nil:
        return ('eps',)
    elif x == EBNF.eof:
        return ('EOF',)
    elif EBNF.NonTerminal in f.each(subj=x, pred=RDF.type):
        return x.fragid
    elif EBNF.Terminal in f.each(subj=x, pred=RDF.type):
        return ('terminal', x.fragid)
    else:
        return id(x)

if __name__ == '__main__':
    import sys
    main(sys.argv)


# $Log$
# Revision 1.1  2006-06-17 03:12:42  connolly
# finds grammar rules, first sets, follow sets following EBNF ontology;
# prints JSON-happy structure
#
