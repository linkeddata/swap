"""Interface to llyn, the original cwm storage structure and inference engine.

"""
__version__ = "$Revision$"
# $Id$

def _test():
    import doctest, expr
    return doctest.testmod(expr) 

if __name__ == "__main__": _test()

import llyn
from llyn import PRED, SUBJ, OBJ, CONTEXT
import RDFSink
import LX.logic
import LX.expr


################################################################

def toLX(store, formula, maxDepth=4, kb=None, kbMode=0, terms={}):
    """Convert a llyn.formula to an LX.Formula and return it, or
    to one or more LX.expr.Expr's and add them to an LX.KB; also convert
    a non-formulas.

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
            toLXVar(store, formula, terms, makeWith=LX.logic.ConstantForURI)
            #kb.interpret(terms[formula],     ### bug:  need to know position in triple!
            #             LX.uri.DescribedThing(formula.uriref()))
            return terms[formula]

    #iTerms = terms.copy()
    iTerms = terms   # need this for proper URI-merging, though maybe its wrong sometimes. 

    if kbMode: assert(kb != None)

    for v in formula.existentials(): toLXVar(store, v, iTerms, makeWith=LX.logic.ExiVar)
    for v in formula.universals():   toLXVar(store, v, iTerms, makeWith=LX.logic.UniVar)

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
            this = LX.logic.IMPLIES(toLX(store, s[SUBJ], maxDepth-1, kb=kb, terms=iTerms),
                                  toLX(store, s[OBJ], maxDepth-1, kb=kb, terms=iTerms))
        elif s[PRED] is store.means:
            this = LX.logic.MEANS(toLX(store, s[SUBJ], maxDepth-1, kb=kb, terms=iTerms),
                                toLX(store, s[OBJ], maxDepth-1, kb=kb, terms=iTerms))
        elif s[PRED] is store.type and s[OBJ] is store.Truth:
            this = toLX(store, s[SUBJ], maxDepth-1, kb=kb, terms=iTerms)
        elif s[PRED] is store.type and s[OBJ] is store.Falsehood:
            this = LX.logic.NOT(toLX(store, s[SUBJ], maxDepth-1, kb=kb, terms=iTerms))
        else:
            # use position for #-smarts here; lower order here....
            this = LX.logic.RDF(toLX(store, s[SUBJ], maxDepth-1, kb=kb, terms=iTerms),
                              toLX(store, s[PRED], maxDepth-1, kb=kb, terms=iTerms),
                              toLX(store, s[OBJ], maxDepth-1, kb=kb, terms=iTerms))
            
        if kbMode:
            kb.add(this)
        else:
            if result is None:
                result = this
            else:
                result = LX.logic.AND(result, this)

    if kbMode:
        for v in formula.existentials():  kb.exivars.append(iTerms[v])
        for v in formula.universals():    kb.univars.append(iTerms[v])
        return None
    else:    
        for v in formula.existentials(): result = LX.logic.EXISTS(iTerms[v], result)
        for v in formula.universals():   result = LX.logic.FORALL(iTerms[v], result)
        return result

def toLXVar(store, term, vars, makeWith=0):
    try:
        return vars[term]
    except KeyError:
        v = makeWith(term.uriref())
        vars[term] = v
        return v

################################################################

import re
scope = {
    ("legal",): re.compile(r"^[a-zA-Z0-9_]+$"),
    ("hint",): re.compile(r"(?:\/|#)([a-zA-Z0-9_]*)/?$")
    }

def addLXKB(store, context, kb):
    "Add all the formulas in an LX.KB to the store"
    terms = {}
    for term in kb.exivars:
        # Oh, maybe we should use RDFSink.newExistential, I see now.
        # but.... it doesn't allow us to give our own name hint.
        n = store.intern((RDFSink.ANONYMOUS, store._genPrefix+term.getNameInScope(scope)),)
        terms[term] = n
        store.storeQuad([context, store.forSome, context, n])
    for term in kb.univars:
        n = store.intern((RDFSink.ANONYMOUS, store._genPrefix+term.getNameInScope(scope)),)
        terms[term] = n
        store.storeQuad([context, store.forAll, context, n])
    for f in kb:
        addLXFormula(store, context, f, terms, kb)

def addLXFormula(store, context, expr, terms={}, kb=None):
    """Add an LX.Formula to the store.

    terms maps from LX.AtomicExpr to RDFSink pairs
    """

    if expr.function is LX.logic.IMPLIES:
        t = [None, None, None, None]
        left = store.newFormula()
        addLXFormula(store, left, expr.args[0], terms, kb)
        left = left.close()
        right = store.newFormula()
        addLXFormula(store, right, expr.args[1], terms, kb)
        right = right.close()
        t[SUBJ] = left
        t[PRED] = store.implies
        t[OBJ] = right
        t[CONTEXT] = context
        store.storeQuad(t)
    elif expr.function is LX.logic.NOT:
        t = [None, None, None, None]
        left = store.newFormula()
        addLXFormula(store, left, expr.args[0], terms, kb)
        left = left.close()
        t[SUBJ] = left
        t[PRED] = store.type
        t[OBJ] = store.Falsehood
        t[CONTEXT] = context
        store.storeQuad(t)
    elif expr.function is LX.logic.RDF:
        t = [None, None, None, None]
        t[CONTEXT] = context
        for (index, term) in zip((SUBJ, PRED, OBJ), expr.args):
            try:
                sym = terms[term]
            except KeyError:
                #print "What llyn tuple to use for", term, "index", index
                try:
                    uri = term.uri
                except AttributeError:
                    pass   # @@@@  No, really, what should we do here?
                sym = store.intern((RDFSink.SYMBOL, uri),)
                    
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
            t[index] = sym
        store.storeQuad(t)
    else: 
        raise RuntimeError, "Can only convert atomic formula yet, not %s" % expr


# $Log$
# Revision 1.6  2003-08-28 11:56:04  sandro
# remove import of LX.uri
#
# Revision 1.5  2003/08/20 09:26:49  sandro
# update --flatten code path to work again, using newer URI strategy
#
# Revision 1.4  2003/02/14 22:21:10  sandro
# Got it mostly working again, so data can roundtrip between
# llyn and lx.Exprs.  Still buggy about uris, rdf(s,p,o) vs p(s,o),
# some logic constructs -> llyn, and multiple interpretations.
# One wonders if it wouldn't make more sense to go via n3.
#
# Revision 1.3  2003/01/29 06:09:18  sandro
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
