"""n3absyn.py -- exploring Notation3 (N3) abstract syntax

Part 1: convert to lisp-like JSON structure

"""

__version__ = '$Id$'

import sys

from swap import uripath, llyn, formula, term



def main(argv):
    path = argv[1]

    addr = uripath.join(uripath.base(), path)
    kb = llyn.RDFStore()
    f = kb.load(addr)

    j = json_formula(f)
    
    import pprint
    pprint.pprint(j)

    for s in lisp_form(j):
        sys.stdout.write(s)

def json_formula(fmla):
    exn = {}
    ex = fmla.existentials()

    assert(not(fmla.universals())) # TODO: handle @forAll

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
    vars = exn.values()
    if vars:
        return ['exists', vars,
                ['and'] + parts ]
    else:
        return ['and'] + parts

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

def lisp_form(f):
    if type(f) is type([]):
        head = f[0]

        if ':' in head:
            if '|' in head:
                raise RuntimeError, "quoting | in symbols not yet implemented"
            yield '(|%s|' % head
            assert(len(f) == 1)
            rest = []
        elif head == 'exists':
            yield '('
            yield head
            yield ' ('
            for v in f[1]:
                yield v
                yield ' '
            yield ')\n'
            rest = f[2:]
        elif head in ('and', 'holds', 'list'):
            yield '('
            yield head
            yield ' '
            rest = f[1:]
        else:
            raise RuntimeError, 'unimplemented list head: %s' % head
        
        for clause in rest:
            for s in lisp_form(clause):
                yield s
        yield ')\n'
    elif type(f) is type({}):
        yield f['var']
        yield ' '
    elif type(f) in (type(''), type(u'')):
        if "\\" in f or '"' in f:
            raise RuntimeError, 'commonlisp string quoting TODO: %s' % f
        yield '"%s"' % f
    else:
        raise RuntimeError, 'unimplemented syntactic type: %s' % f
    
if __name__ == '__main__':
    main(sys.argv)

