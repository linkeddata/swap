"""Do RDF stuff with LX.

An RDF Graph is just an LX.KB or Formula which has only existential
quantification and binary predicates.  
"""
__version__ = "$Revision$"
# $Id$

import re

import LX
from LX.ladder import Ladder
from LX.namespace import ns
from LX.describer import CombinedDescriber, ListDescriber, DescriptionFailed
import LX.logic

def flatten(kb, toKB, indirect=0):
    """Return a formula which expresses the same knowledge, but using
    only RDF triples and the LX-Layering vocabulary.

    if "indirect" then even plain triples get described as true;
    otherwise they just get copied over.
    
    """
    d = CombinedDescriber([FormulaDescriber(),
                           VariableDescriber(),  # must be before uriref
                           URIRefDescriber(),
                           ListDescriber()])
    ladder = Ladder(("kb", toKB))
    ladder = ladder.set("trace", 1)
    # ladder = ladder.set("verbose", 1)
    if kb.univars:
        term = d.describe(kb.asFormula(), ladder)
        toKB.add(term, ns.rdf.type, ns.lx.TrueSentence)
        return
    for f in kb:
        if f.function is LX.logic.RDF and not indirect:
            toKB.add(f)
        else:
            term = d.describe(f, ladder)
            toKB.add(term, ns.rdf.type, ns.lx.TrueSentence)

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
    def dump(self, done):
        if done.has_key(self):
            print "[loop]"
            return
        done[self] = 1
        print "[ ",
        for (key, value) in self.__dict__.iteritems():
            if key is "fromTerm": continue
            if key is "args": continue
            if key is "op": continue
            print key,
            if isinstance(value, Reconstructed):
                value.dump(done)
            else:
                print "<"+str(value)+">"
        try:
            print '"'+'"^^<'.join(LX.logic.valuesForConstants[self.fromTerm])+'>',
        except KeyError:
            pass
        print " ]",

# could construct this from class info...
decode = {
    ns.lx.condLeft: [ 0, LX.logic.IMPLIES ],
    ns.lx.condRight:[ 1, LX.logic.IMPLIES ],
    ns.lx.bicondLeft: [ 0, LX.logic.MEANS],
    ns.lx.bicondRight:[ 1, LX.logic.MEANS ],
    ns.lx.conjLeft: [ 0, LX.logic.AND ],
    ns.lx.conjRight: [ 1, LX.logic.AND ],
    ns.lx.disjLeft: [ 0, LX.logic.OR ],
    ns.lx.disjRight: [ 1, LX.logic.OR ],
    ns.lx.negated:[ 0, LX.logic.NOT ],
    ns.lx.subformula:[ 1, None ],
    ns.lx.univar:[ 0, LX.logic.FORALL ],
    ns.lx.exivar:[ 0, LX.logic.EXISTS ],
    ns.lx.subjectTerm:[ 0, LX.logic.RDF ],
    ns.lx.predicateTerm:[ 1, LX.logic.RDF ],
    ns.lx.objectTerm:[ 2, LX.logic.RDF ],
    ns.lx.denotation: "uri",
    }

def reconstruct(kb, keys, recons, byClass=None, class_=Reconstructed, cluster=None):
    """

    keys is a map from predicates to something which says how to handle
    triples using that predicate during reconstruction.  Specifically:
       - a string means: use that string as the property name
       - a pair of (number, object) means set the reconstructed object's
         arg[number] to the value, and set its "op" to the object.
    """

    localKeys = {}
    nameTable = {
        ("legal",): re.compile(r"^[a-zA-Z0-9_]+$"),
        ("hint",): re.compile(r"(?:\/|#)([a-zA-Z0-9_]*)/?$")
        }
    
    for f in kb:
        if f.function != LX.logic.RDF:
            raise RuntimeError, "Not pure-RDF KB!"
            continue
        (subj, pred, obj) = f.args
        subjRecon = recons.setdefault(subj, apply(class_,[subj]))
        if pred == ns.rdf.type and byClass is not None:
            byClass.setdefault(obj, []).append(subjRecon)
        if keys is not None:
            try:
                k = keys[pred]
            except KeyError:
                print "ignoring triple, pred", pred
                continue
        elif cluster is not None:
            try:
                k = "_".join(cluster.inverseLookup(pred))
            except KeyError:
                print "ignoring triple, pred not in any NS", pred
                continue
        else:
            k = localKeys.setdefault(pred, pred.getNameInScope(nameTable))
            
        objRecon = recons.setdefault(obj, apply(class_,[obj]))
        if isinstance(k, type("x")) or k[0] is None:
            setattr(subjRecon, k, objRecon)
        else:
            index = k[0]
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
        if pred is ns.rdf.type and obj is ns.lx.TrueSentence:
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

vars = { }
class VariableDescriber:

    def describe(self, object, ladder):
        if not isinstance(object, LX.logic.Variable):
            raise DescriptionFailed, 'not a variable term'
        if ladder.has("term"):
            raise (DescriptionFailed,
                       'Cannot describe variable as some term w/out eq')
        else:
            #@@@   keep a global map to exivars?
            global vars
            try:
                term=vars[object]
            except KeyError:
                if isinstance(object, LX.logic.ExiVar):
                    type = ns.lx.exivar
                elif isinstance(object, LX.logic.UniVar):
                    type = ns.lx.exivar
                term=vars.setdefault(object, ladder.kb.newExistential())
                # ladder.kb.add(term, ns.rdf
            
        if ladder.has("verbose"):
            ladder.kb.add(term, ns.rdf.type, ns.lx.Variable)
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
            ladder.kb.add(term, ns.rdf.type, ns.lx.Constant)
        ladder.kb.add(term, ns.lx.denotation, object)
        return term
    
class FormulaDescriber:

    nameTable = {
        LX.logic.IMPLIES:   [ ns.lx.Conditional,   ns.lx.condLeft,   ns.lx.condRight   ],
        LX.logic.MEANS: [ ns.lx.Biconditional, ns.lx.bicondLeft, ns.lx.bicondRight ],
        LX.logic.AND:   [ ns.lx.Conjunction,   ns.lx.conjLeft,   ns.lx.conjRight   ],
        LX.logic.OR:   [ ns.lx.Disjunction,   ns.lx.disjLeft,   ns.lx.disjRight   ],
        LX.logic.NOT:      [ ns.lx.Negation,      ns.lx.negated ],
        LX.logic.FORALL: [ ns.lx.UniversalQuantification, ns.lx.univar, ns.lx.subformula ],
        LX.logic.EXISTS: [ ns.lx.ExistentialQuantification, ns.lx.exivar, ns.lx.subformula ],
        LX.logic.RDF: [ ns.lx.Triple, ns.lx.subjectTerm, ns.lx.predicateTerm, ns.lx.objectTerm ]
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
            ladder.kb.add(term, ns.rdf.type, entry[0])

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
# Revision 1.12  2003-08-28 11:47:07  sandro
# change from defaultns to namespace.ns
#
# Revision 1.11  2003/08/22 20:49:07  sandro
# generalized ns and reconstructor, for second use (2003/08/owl-systems)
#
# Revision 1.10  2003/08/20 11:50:58  sandro
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

 
