"""n3absyn.py -- exploring Notation3 (N3) abstract syntax

Part 1: convert to lisp-like JSON structure

"""

__version__ = '$Id$'

from swap import uripath, llyn, formula, term

def main(argv):
    path = argv[1]

    addr = uripath.join(uripath.base(), path)
    kb = llyn.RDFStore()
    f = kb.load(addr)

    j = json_fmla(f)
    
    import pprint
    pprint.pprint(j)


def json_fmla(fmla):
    exn = {}
    ex = fmla.existentials()

    # find distinct names for each variable
    for v in fmla.existentials():
        try:
            vn = v.fragid
        except AttributeError:
            vn = "g%d" % v.serial

        i = 0
        while vn in exn.values():
            i += 1
            vn = vn + `i`
        exn[v] = vn

    parts = [] # conjuncts
    for s in fmla: # iterate over statements. hmm.
        parts.append(['holds',
                      json_term(s.predicate(), exn),
                      json_term(s.subject(), exn),
                      json_term(s.object(), exn)])
    return ['exists', exn.values(),
            ['and'] + parts ]

def json_term(t, varmap):
    if t in varmap:
        return {'var': varmap[t]}
    elif isinstance(t, term.Literal):
        if t.datatype:
            dt = t.datatype.uriref()
            if dt == 'http://www.w3.org/2001/XMLSchema#integer':
                return int(t.string)
            return ['data', dt, t.string]
        else:
            return t.string

    elif isinstance(t, term.LabelledNode): # ugh.
        return [t.uriref()]

    # hmm... are lists part of the N3 abstract syntax?
    elif isinstance(t, term.List):
        return ['list'] + [json_term(i, varmap) for i in t]
    else:
        raise RuntimeError, "huh? + %s" % t
                    
if __name__ == '__main__':
    import sys
    main(sys.argv)

