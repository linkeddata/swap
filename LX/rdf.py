"""Do RDF stuff with LX.

An RDF Graph is just an LX.KB or Formula which has only existential
quantification and binary predicates.  
"""
__version__ = "$Revision$"
# $Id$

import LX
from LX.ladder import Ladder
from LX.defaultns import rdfns, lxns
from LX.describer import CombinedDescriber, ListDescriber, DescriptionFailed
import LX.logic

def flatten(kb, toKB, indirect=0):
    """Return a formula which expresses the same knowledge, but using
    only RDF triples and the LX-Layering vocabulary.

    if "indirect" then even plain triples get described as true;
    otherwise they just get copied over.
    
    """
    d = CombinedDescriber([FormulaDescriber(), URIRefDescriber(),
                              VariableDescriber(), ListDescriber()])
    ladder = Ladder(("kb", toKB))
    ladder = ladder.set("trace", 1)
    for f in kb:
        if f.function is LX.logic.RDF and not indirect:
            toKB.add(f)
        else:
            term = d.describe(f, ladder)
            toKB.add(term, rdfns.type, lxns.TrueSentence)

def unflatten(f):
    """Return a formula which expresses the same knowledge, but any
    formulas described as true using RDF triples and the LX-Layering
    vocabulary are extracted and conjoined.

    The triples used to make those descriptions are optionally removed
    from the result, depending on the kind of inference required.
    """
    raise RuntimeError, "Not Implemented"

class Reconstructed:
    def __init__(self, fromTerm):
        self.fromTerm=fromTerm
        self.args=[]
        self.op=None

# could construct this from class info...
decode = {
    lxns.condLeft: [ 0, LX.logic.IMPLIES ],
    lxns.condRight:[ 1, LX.logic.IMPLIES ],
    lxns.bicondLeft: [ 0, LX.logic.MEANS],
    lxns.bicondRight:[ 1, LX.logic.MEANS ],
    lxns.conjLeft: [ 0, LX.logic.AND ],
    lxns.conjRight: [ 1, LX.logic.AND ],
    lxns.disjLeft: [ 0, LX.logic.OR ],
    lxns.disjRight: [ 1, LX.logic.OR ],
    lxns.negated:[ 0, LX.logic.NOT ],
    lxns.subformula:[ 1, None ],
    lxns.univar:[ 0, LX.logic.FORALL ],
    lxns.exivar:[ 0, LX.logic.EXISTS ],
    lxns.subjectTerm:[ 0, LX.logic.RDF ],
    lxns.predicateTerm:[ 1, LX.logic.RDF ],
    lxns.objectTerm:[ 2, LX.logic.RDF ],
    lxns.denotation: [ None, None, "uri" ],
    }

def reconstruct(kb, keys, recons):
    for f in kb:
        if f.function != LX.logic.RDF:
            continue
        (subj, pred, obj) = f.args
        try:
            k = keys[pred]
        except KeyError:
            continue
        subjRecon = recons.setdefault(subj, Reconstructed(subj))
        objRecon = recons.setdefault(obj, Reconstructed(obj))
        index = k[0]
        if index is None:
            setattr(subjRecon, k[2], objRecon)
        else:
            if index>=len(subjRecon.args):
                subjRecon.args.extend( (None,) * (1+index-len(subjRecon.args) ))
            subjRecon.args[index] = objRecon
            was = subjRecon.__dict__.get("op",None)
            assert(was is None or was is k[1])
            subjRecon.op = k[1]
    
def dereify(kb):
    """a "remove" flag would be nice, but what about structure sharing?


    (doesn't belong here; this has nothing to do with RDF...   except
    that RDF makes this necessary!)

    To do this with linear time, we need to traverse the KB first,
    constructing python objects for each subject in each triple of
    interest to us.  It should work fine....
"""
    recons = { }
    reconstruct(kb, decode, recons)
    for f in kb:
        if f.function != LX.logic.RDF:
            continue
        (subj, pred, obj) = f.args
        if pred is rdfns.type and obj is lxns.TrueSentence:
            kb.add(asExpr(recons[subj], { }))
    
def asExpr(r, map):
    """Turn a Reconstructed into an Expr, possibly overridden by map (to allow for scoping)
    """
    
    try:
        return map[r]
    except KeyError:
        pass
    
    if r.op:
        if r.op == LX.logic.FORALL:
            t=r.args[0]
            v=LX.logic.UniVar()
            newmap=map.copy()
            newmap[t] = v
            result=LX.expr.CompoundExpr(r.op, v, asExpr(r.args[0], newmap))
            print "Result", result
            return result
        if r.op == LX.logic.EXISTS:
            t=r.args[0]
            v=LX.logic.ExiVar()
            newmap=map.copy()
            newmap[t] = v
            result=LX.expr.CompoundExpr(r.op, v, asExpr(r.args[0], newmap))
            print "Result", result
            return result
        e = [r.op]
        for t in r.args:
            e.append(asExpr(t, map))
        result = apply(LX.expr.CompoundExpr, e)
        print "Result", result
        return result

    if hasattr(r, "uri"):
        uri = str(r.uri.fromTerm)
        print "URI", uri
        result= LX.logic.ConstantForURI(uri)
        print "Result", result
        return result

    result=LX.logic.Constant()         # constant with URI?  Odd for RDF.
    print "Result", result
    return result

################################################################

class VariableDescriber:

    def describe(self, object, ladder):
        if not isinstance(object, LX.logic.Variable):
            raise DescriptionFailed, 'not a variable term'
        if ladder.has("term"):
            raise (DescriptionFailed,
                       'Cannot describe variable as some term w/out eq')
        else:
            #@@@   keep a global map to exivars?
            term = ladder.kb.newExistential()
            # term = object
            
        if ladder.has("verbose"):
            ladder.kb.add(term, rdfns.type, lxns.Variable)
        return term
        
    
class URIRefDescriber:

    def describe(self, object, ladder):
        #if isinstance(object, LX.Operator):
        #    print "Describing an operator...   Ignoring for now..."
        #    return ladder.kb.newExistential()
        try:
            uri=object.uri
        except AttributeError:
            raise DescriptionFailed, 'not a uriref term'
        if ladder.has("term"):
            term = ladder.term
        else:
            term = ladder.kb.newExistential()
            
        if ladder.has("verbose"):
            ladder.kb.add(term, rdfns.type, lxns.Constant)
        ladder.kb.add(term, lxns.denotation, object)
        return term
    
class FormulaDescriber:

    nameTable = {
        LX.logic.IMPLIES:   [ lxns.Conditional,   lxns.condLeft,   lxns.condRight   ],
        LX.logic.MEANS: [ lxns.Biconditional, lxns.bicondLeft, lxns.bicondRight ],
        LX.logic.AND:   [ lxns.Conjunction,   lxns.conjLeft,   lxns.conjRight   ],
        LX.logic.OR:   [ lxns.Disjunction,   lxns.disjLeft,   lxns.disjRight   ],
        LX.logic.NOT:      [ lxns.Negation,      lxns.negated ],
        LX.logic.FORALL: [ lxns.UniversalQuantification, lxns.univar, lxns.subformula ],
        LX.logic.EXISTS: [ lxns.ExistentialQuantification, lxns.exivar, lxns.subformula ],
        LX.logic.RDF: [ lxns.Triple, lxns.subjectTerm, lxns.predicateTerm, lxns.objectTerm ]
        }
    
    def describe(self, object, ladder):
        if object.isAtomic():
            raise DescriptionFailed, "atomic (can't be formula)"
        if ladder.has("term"):
            term = ladder.term
        else:
            term = ladder.kb.newExistential()

        entry = self.nameTable[object.function]

        if ladder.has("verbose"):
            ladder.kb.add(term, rdfns.type, entry[0])

        for (pred, obj) in zip(entry[1:], object.args):
            ladder.kb.add(term, pred, ladder.describer.describe(obj, ladder))

        return term

# This implements http://www.w3.org/2002/12/rdf-identifiers/
def denotation(triple, index):
    """
    Return the object denoted by triple[index], where string
    elements of the triple are taken to be URIRef node/arc labels.
    Literals, etc, need to be handled elsewhere.
    
    We need the whole triple because of the disambiguating rules from
    http://www.w3.org/2002/12/rdf-identifiers/
    """
    u = triple[index]
    if index == 1: return LX.uri.DescribedThing(u)
    if u.find("#") >= 0:
        return LX.uri.DescribedThing(u)
    if index == 2 and hasattr(triple[1], "uriOfDescription"):
        if triple[1].uriOfDescription == LX.ns.rdf.type.uriOfDescription:
            return LX.uri.DescribedThing(u)
    return LX.uri.Resource(u)
    
# $Log$
# Revision 1.10  2003-08-20 11:50:58  sandro
# --dereify implemented (linear time algorithm)
#
# Revision 1.9  2003/08/20 09:26:48  sandro
# update --flatten code path to work again, using newer URI strategy
#
# Revision 1.8  2003/02/14 17:21:59  sandro
# Switched to import-as-needed for LX languages and engines
#
# Revision 1.7  2003/02/13 19:49:30  sandro
# changed some names to match other reorg; probably broken
#
# Revision 1.6  2003/02/01 05:58:10  sandro
# intermediate lbase support; getting there but buggy; commented out
# some fol checks 
#
# Revision 1.5  2003/01/29 06:09:18  sandro
# Major shift in style of LX towards using expr.py.  Added some access
# to otter, via --check.  Works as described in
# http://lists.w3.org/Archives/Public/www-archive/2003Jan/0024
# I don't like this UI; I imagine something more like --engine=otter
# --think, and --language=otter (instead of --otterDump).
# No tests for any of this.
#
# Revision 1.4  2002/08/29 21:02:13  sandro
# passes many more tests, esp handling of variables
#
# Revision 1.3  2002/08/29 17:10:38  sandro
# fixed description bug; flatten runs and may even be correct
#
# Revision 1.2  2002/08/29 16:39:55  sandro
# fixed various early typos and ommissions; working on logic bug which is manifesting in description loops
#
# Revision 1.1  2002/08/29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

 
