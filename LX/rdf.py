"""Do RDF stuff with LX.

An RDF Graph is just an LX.KB or Formula which has only existential
quantification and binary predicates.  
"""
__version__ = "$Revision$"
# $Id$

import LX
from LX.ladder import Ladder
from LX.defaultns import rdfns, lxns

def flatten(kb, toKB, indirect=0):
    """Return a formula which expresses the same knowledge, but using
    only RDF triples and the LX-Layering vocabulary.

    if "indirect" then even plain triples get described as true;
    otherwise they just get copied over.
    
    """
    d = LX.CombinedDescriber([FormulaDescriber(), URIRefDescriber(),
                              VariableDescriber(), LX.ListDescriber()])
    ladder = Ladder(("kb", toKB))
    ladder = ladder.set("trace", 1)
    for f in kb:
        if f.function is LX.RDF and not indirect:
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


class VariableDescriber:

    def describe(self, object, ladder):
        if not isinstance(object, LX.Variable):
            raise LX.DescriptionFailed, 'not a variable term'
        if ladder.has("term"):
            raise (DescriptionFailed,
                       'Cannot describe variable as some term w/out eq')
        else:
            #@@@   keep a global map to exivars?
            #term = ladder.kb.newExistential()
            term = object
            
        if ladder.has("verbose"):
            ladder.kb.add(term, rdfns.type, lxns.Variable)
        return term
        
    
class URIRefDescriber:

    def describe(self, object, ladder):
        #if isinstance(object, LX.Operator):
        #    print "Describing an operator...   Ignoring for now..."
        #    return ladder.kb.newExistential()
        if not isinstance(object, LX.URIRef):
            raise LX.DescriptionFailed, 'not a uriref term'
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
        if not isinstance(object, LX.expr.Expr):
            raise LX.DescriptionFailed, 'not a formula'
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
# Revision 1.8  2003-02-14 17:21:59  sandro
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

 
