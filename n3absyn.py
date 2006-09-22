"""n3absyn.py -- exploring Notation3 (N3) abstract syntax

Part 1: convert to lisp-ish JSON structure
Part 2: generate lisp s-expression from JSON structure

So far, we handle just the N3-rules subset of N3;
we deal with:
  { ... } => { ... }
but not other occurrences of {}.

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
    
    #import pprint
    #pprint.pprint(j)

    for s in lisp_form(j):
        sys.stdout.write(s)

def json_formula(fmla, vars={}):
    varnames = {}
    varnames.update(vars)
    
    # find distinct names for each variable
    for v in fmla.existentials() | fmla.universals():
        try:
            vn = v.uri
            if '#' in vn: vn = vn.split('#')[1]
        except AttributeError:
            vn = "g%d" % v.serial


        i = 0
        while vn in varnames.values():
            i += 1
            vn = vn + `i`
        varnames[v] = vn

    parts = [] # conjuncts
    for s in fmla: # iterate over statements. hmm.

        # this is the N3rules subset, for now...
        # when we get n3-quote figured out, we can take this special-case out.
        if s.predicate().uriref() == 'http://www.w3.org/2000/10/swap/log#implies':
            
            parts.append(['implies',
                          json_formula(s.subject(), varnames), #@@
                          json_formula(s.object(), varnames)])
        else:
            parts.append(['holds',
                          json_term(s.predicate(), varnames),
                          json_term(s.subject(), varnames),
                          json_term(s.object(), varnames)])

    if len(parts) == 1:
        ret = parts[0]
    else:
        ret = ['and'] + parts
    if fmla.universals():
        ret = ['forall', [varnames[v] for v in fmla.universals()],
               ret]
    if fmla.existentials():
        ret = ['exists', [varnames[v] for v in fmla.existentials()],
               ret]
    return ret


def json_term(t, varmap):
    if t in varmap:
        return {'var': varmap[t]}
    elif isinstance(t, term.Literal):
        if t.datatype:
            dt = t.datatype.uriref()
            if dt in('http://www.w3.org/2001/XMLSchema#integer',
                     'http://www.w3.org/2001/XMLSchema#nonNegativeInteger'):
                return int(t.string)
            if dt == 'http://www.w3.org/2001/XMLSchema#double':
                return float(t.string)
            return ['data', [dt], t.string]
        else:
            return t.string

    elif isinstance(t, term.LabelledNode): # ugh.
        return [t.uriref()]

    # hmm... are lists part of the N3 abstract syntax?
    elif isinstance(t, term.List):
        return ['list'] + [json_term(i, varmap) for i in t]
    elif isinstance(t, formula.Formula):
        return ['n3-quote', json_formula(t, varmap)]
    else:
        raise RuntimeError, "huh? + %s %s" % (t, t.__class__)

def lisp_form(f):
    # integer
    if type(f) is type(1):
        yield "%d " % f

    elif type(f) is type(1.1):
        yield "%f " % f

    # string
    elif type(f) in (type(''), type(u'')):
        if "\\" in f or '"' in f:
            raise RuntimeError, 'commonlisp string quoting TODO: %s' % f
        # @@ hmm... non-ascii chars?
        yield '"%s" ' % f

    # variable
    elif type(f) is type({}):
        yield f['var']
        yield ' '

    # compound forms
    elif type(f) is type([]):
        head = f[0]

        # URI, i.e. a 0-ary function symbol
        if ':' in head:
            if '|' in head:
                raise RuntimeError, "quoting | in symbols not yet implemented"
            yield '(URI::|%s|' % head
            assert(len(f) == 1)
            rest = []

        # function symbols
        #@@ interaction of n3-quote with variables needs work.
        elif head in ('holds', 'list', 'data', 'n3-quote'):
            yield '('
            yield head
            yield ' '
            rest = f[1:]

        # connectives
        elif head in ('and', 'implies'):
            yield '('
            yield head
            yield ' '
            rest = f[1:]

        # quantifiers
        elif head in ('exists', 'forall'):
            yield '('
            yield head
            yield ' ('
            for v in f[1]:
                yield v
                yield ' '
            yield ')\n'
            rest = f[2:]

        else:
            raise RuntimeError, 'unimplemented list head: %s' % head
        
        for clause in rest:
            for s in lisp_form(clause):
                yield s
        yield ')\n'

    else:
        raise RuntimeError, 'unimplemented syntactic type: %s %s' % (f, type(f))
    
if __name__ == '__main__':
    main(sys.argv)

