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
import LX.fol


################################################################

def toLX(store, formula, maxDepth=4, kb=None, kbMode=0, terms={}):
    """Convert a llyn.formula to an LX.Formula and return it, or
    to one or more LX.Formulas and add them to an LX.KB; also convert
    a non-formula into an LX.Term.

    If a kb is specified, the conjoined parts of the formula (or
    just the formula itself, if there are no conjoined parts) will
    be added to it, instead of being returned.  For document
    top-level formulas this is often the appropriate usage.

    kbMode means we DONT return a formula, we just add the formulas to the KB.
    
    """

    if not isinstance(formula, llyn.Formula):
        # if it's not a formula
        try:
            # and its not a scoped variable
            return terms[formula]
        except KeyError:
            # then it's a constant!
            toLXVar(store, formula, terms, makeWith=LX.fol.Constant)
            kb.interpret(terms[formula], LX.URIRef2(formula.uriref()))
            return terms[formula]

    #iTerms = terms.copy()
    iTerms = terms   # need this for proper URI-merging, though maybe its wrong sometimes. 

    if kbMode: assert(kb != None)

    for v in formula.existentials(): toLXVar(store, v, iTerms, makeWith=LX.fol.ExiVar)
    for v in formula.universals():   toLXVar(store, v, iTerms, makeWith=LX.fol.UniVar)

    result = None
    if maxDepth < 0:
        raise RuntimeError, "Formulas too deeply nested, probably looping"
    for s in formula:
        #print "statement", s
        if s[PRED] is store.forAll or s[PRED] is store.forSome:
            if s[SUBJ] is formula: continue
            # BUG: this construction may be obsolete; it loses var declarations
            # as in   {   } log:forall :x.
            this = toLX(store, s[SUBJ], maxDepth-1, kb=kb, terms=iTerms)
        elif s[PRED] is store.implies:
            this = LX.fol.IMPLIES(toLX(store, s[SUBJ], maxDepth-1, kb=kb, terms=iTerms),
                                  toLX(store, s[OBJ], maxDepth-1, kb=kb, terms=iTerms))
        elif s[PRED] is store.means:
            this = LX.fol.MEANS(toLX(store, s[SUBJ], maxDepth-1, kb=kb, terms=iTerms),
                                toLX(store, s[OBJ], maxDepth-1, kb=kb, terms=iTerms))
        elif s[PRED] is store.type and s[OBJ] is store.Truth:
            this = toLX(store, s[SUBJ], maxDepth-1, kb=kb, terms=iTerms)
        elif s[PRED] is store.type and s[OBJ] is store.Falsehood:
            this = LX.fol.NOT(toLX(store, s[SUBJ], maxDepth-1, kb=kb, terms=iTerms))
        else:
            this = LX.fol.RDF(toLX(store, s[SUBJ], maxDepth-1, kb=kb, terms=iTerms),
                              toLX(store, s[PRED], maxDepth-1, kb=kb, terms=iTerms),
                              toLX(store, s[OBJ], maxDepth-1, kb=kb, terms=iTerms))
            
        if kbMode:
            kb.add(this)
        else:
            if result is None:
                result = this
            else:
                result = LX.fol.AND(result, this)

    if kbMode:
        for v in formula.existentials():  kb.exivars.append(iTerms[v])
        for v in formula.universals():    kb.univars.append(iTerms[v])
        return None
    else:    
        for v in formula.existentials(): result = LX.fol.EXISTS(iTerms[v], result)
        for v in formula.universals():   result = LX.fol.FORALL(iTerms[v], result)
        return result

def toLXVar(store, term, vars, makeWith=0):
    try:
        return vars[term]
    except KeyError:
        v = makeWith(suggestedName=term.uriref())
        vars[term] = v
        return v

################################################################

## def addLXKB(store, context, kb):
##     "Add all the formulas in an LX.KB to the store"
##     terms = {}
##     for term in kb.exivars:
##         # Oh, maybe we should use RDFSink.newExistential, I see now.
##         # but.... it doesn't allow us to give our own fragment name.
##         if term.value:
##             n = store.intern((RDFSink.SYMBOL, term.value),)
##         else:
##             n = store.intern((RDFSink.ANONYMOUS, store._genPrefix+term.name),)
##         terms[term] = n
##         store.storeQuad([context, store.forSome, context, n])
##     for term in kb.univars:
##         if term.value:
##             n = store.intern((RDFSink.SYMBOL, term.value),)
##         else:
##             n = store.intern((RDFSink.ANONYMOUS, store._genPrefix+term.name),)
##         terms[term] = n
##         store.storeQuad([context, store.forAll, context, n])
##     for f in kb:
##         addLXFormula(store, context, f, terms)

## def addLXFormula(store, context, lxFormula, terms={}):
##     """Add an LX.Formula to the store.

##     terms maps from LX.Term to RDFSink pairs
##     """
##     if lxFormula.operator is LX.ATOMIC_SENTENCE:
##         t = [None, None, None, None]
##         t[CONTEXT] = context
##         for (index, term) in zip((SUBJ, PRED, OBJ), lxFormula.operands):
##             try:
##                 sym = terms[term]
##             except KeyError:
##                 if isinstance(term, LX.URIRef):
##                     sym = store.intern((RDFSink.SYMBOL, term.value),)
##                 elif isinstance(term, LX.Variable):
##                     if term.value is None:
##                         #@ Bug, but why do we have Nones here?
##                         sym = store.intern((RDFSink.SYMBOL, "foo:bar#baz"),)
##                     else:
##                         sym = store.intern((RDFSink.SYMBOL, term.value),)
##                 else:
##                     msg = "Conversion of %s's not implemented" % term.__class__
##                     raise RuntimeError, msg
##             t[index] = sym
##         store.storeQuad(t)
##     else: 
##         raise RuntimeError, "Can only convert atomic formula yet"


# $Log$
# Revision 1.3  2003-01-29 06:09:18  sandro
# Major shift in style of LX towards using expr.py.  Added some access
# to otter, via --check.  Works as described in
# http://lists.w3.org/Archives/Public/www-archive/2003Jan/0024
# I don't like this UI; I imagine something more like --engine=otter
# --think, and --language=otter (instead of --otterDump).
# No tests for any of this.
#
# Revision 1.1  2002/10/03 16:15:51  sandro
# code moved out of cwm's llyn.py
#
