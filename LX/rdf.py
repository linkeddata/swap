"""Do RDF stuff with LX.

An RDF Graph is just an LX.KB or Formula which has only existential
quantification and binary predicates.  
"""
__version__ = "$Revision$"
# $Id$

import LX
from LX.ladder import Ladder
from LX import rdfns, lxns
from LX import Triple
import LX.fol

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
        if f.function is LX.fol.RDF and not indirect:
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
        if not isinstance(object, LX.fol.Variable):
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
        LX.fol.IMPLIES:   [ lxns.Conditional,   lxns.condLeft,   lxns.condRight   ],
        LX.fol.MEANS: [ lxns.Biconditional, lxns.bicondLeft, lxns.bicondRight ],
        LX.fol.AND:   [ lxns.Conjunction,   lxns.conjLeft,   lxns.conjRight   ],
        LX.fol.OR:   [ lxns.Disjunction,   lxns.disjLeft,   lxns.disjRight   ],
        LX.fol.NOT:      [ lxns.Negation,      lxns.negated ],
        LX.fol.FORALL: [ lxns.UniversalQuantification, lxns.univar, lxns.subformula ],
        LX.fol.EXISTS: [ lxns.ExistentialQuantification, lxns.exivar, lxns.subformula ],
        LX.fol.RDF: [ lxns.Triple, lxns.subjectTerm, lxns.predicateTerm, lxns.objectTerm ]
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

# $Log$
# Revision 1.5  2003-01-29 06:09:18  sandro
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

 
