"""Interface to llyn, the original cwm storage structure and inference engine.

"""
__version__ = "$Revision$"
# $Id$

def _test():
    import doctest, expr
    return doctest.testmod(expr) 

if __name__ == "__main__": _test()

import llyn
from llyn import PRED, SUBJ, OBJ, RDFSink, CONTEXT
import LX


################################################################

def toLX(store, formula, maxDepth=4, kb=None, vars=None):
    """Convert a llyn.formula to an LX.Formula and return it, or
    to one or more LX.Formulas and add them to an LX.KB; also convert
    a non-formula into an LX.Term.

    If a kb is specified, the conjoined parts of the formula (or
    just the formula itself, if there are no conjoined parts) will
    be added to it, instead of being returned.  For document
    top-level formulas this is often the appropriate usage.

    """

    if not isinstance(formula, llyn.Formula):
        try:
            return vars[formula]
        except KeyError:
            return LX.URIRef(formula.uriref())

    if vars is None:
        vars = {}
    # @@ is there a problem with adding vars like this an never
    # taking them away -- something that's a variable in one scope
    # being inappropriately called a variable in another scope;
    # probably!   Need some stacking structure to solve this.
    for v in formula.existentials(): toLXVar(store, v, vars, makeWith=LX.ExiVar)
    for v in formula.universals():   toLXVar(store, v, vars, makeWith=LX.UniVar)
    if kb is None or formula.existentials() or formula.universals():
        deferAddingToKB = 1
    else:
        deferAddingToKB = 0
    result = None
    if maxDepth < 0:
        raise RuntimeError, "Formulas too deeply nested, probably looping"
    for s in formula:
        #print "statement", s
        if s[PRED] is store.forAll or s[PRED] is store.forSome:
            if s[SUBJ] is formula: continue
            # BUG: this construction may be obsolete; it loses var declarations
            # as in   {   } log:forall :x.
            this = toLX(store, s[SUBJ], maxDepth-1, vars=vars)
        elif s[PRED] is store.implies:
            this = LX.Conditional(toLX(store, s[SUBJ], maxDepth-1, vars=vars),
                                  toLX(store, s[OBJ], maxDepth-1, vars=vars))
        elif s[PRED] is store.means:
            this = LX.Biconditional(toLX(store, s[SUBJ], maxDepth-1, vars=vars),
                                  toLX(store, s[OBJ], maxDepth-1, vars=vars))
        elif s[PRED] is store.type and s[OBJ] is store.Truth:
            this = toLX(store, s[SUBJ], maxDepth-1, vars=vars)
        elif s[PRED] is store.type and s[OBJ] is store.Falsehood:
            this = LX.Negation(toLX(store, s[SUBJ], maxDepth-1, vars=vars))
        else:
            this = LX.Triple(toLX(store, s[SUBJ], maxDepth-1, vars=vars),
                             toLX(store, s[PRED], maxDepth-1, vars=vars),
                             toLX(store, s[OBJ], maxDepth-1, vars=vars))
        if deferAddingToKB:
            if result is None:
                result = this
            else:
                result = result & this
        else:
            kb.add(this)
    for v in formula.existentials():
        result = LX.ExistentialQuantification(vars[v], result)
    for v in formula.universals():
        result = LX.UniversalQuantification(vars[v], result)
    if kb is None:
        return result
    elif deferAddingToKB:
        kb.add(result)

def toLXVar(store, term, vars, makeWith=LX.Variable):
    try:
        return vars[term]
    except KeyError:
        v = makeWith(uriref=term.uriref())
        vars[term] = v
        return v

################################################################

def addLXKB(store, context, kb):
    "Add all the formulas in an LX.KB to the store"
    terms = {}
    for term in kb.exivars:
        # Oh, maybe we should use RDFSink.newExistential, I see now.
        # but.... it doesn't allow us to give our own fragment name.
        if term.value:
            n = store.intern((RDFSink.SYMBOL, term.value),)
        else:
            n = store.intern((RDFSink.ANONYMOUS, store._genPrefix+term.name),)
        terms[term] = n
        store.storeQuad([context, store.forSome, context, n])
    for term in kb.univars:
        if term.value:
            n = store.intern((RDFSink.SYMBOL, term.value),)
        else:
            n = store.intern((RDFSink.ANONYMOUS, store._genPrefix+term.name),)
        terms[term] = n
        store.storeQuad([context, store.forAll, context, n])
    for f in kb:
        addLXFormula(store, context, f, terms)

def addLXFormula(store, context, lxFormula, terms={}):
    """Add an LX.Formula to the store.

    terms maps from LX.Term to RDFSink pairs
    """
    if lxFormula.operator is LX.ATOMIC_SENTENCE:
        t = [None, None, None, None]
        t[CONTEXT] = context
        for (index, term) in zip((SUBJ, PRED, OBJ), lxFormula.operands):
            try:
                sym = terms[term]
            except KeyError:
                if isinstance(term, LX.URIRef):
                    sym = store.intern((RDFSink.SYMBOL, term.value),)
                elif isinstance(term, LX.Variable):
                    if term.value is None:
                        #@ Bug, but why do we have Nones here?
                        sym = store.intern((RDFSink.SYMBOL, "foo:bar#baz"),)
                    else:
                        sym = store.intern((RDFSink.SYMBOL, term.value),)
                else:
                    msg = "Conversion of %s's not implemented" % term.__class__
                    raise RuntimeError, msg
            t[index] = sym
        store.storeQuad(t)
    else: 
        raise RuntimeError, "Can only convert atomic formula yet"


# $Log$
# Revision 1.1  2002-10-03 16:15:51  sandro
# code moved out of cwm's llyn.py
#
