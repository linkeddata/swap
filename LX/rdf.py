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

def flatten(kb, toKB):
    """Return a formula which expresses the same knowledge, but using
    only RDF triples and the LX-Layering vocabulary.
    """
    d = LX.CombinedDescriber([FormulaDescriber(), URIRefDescriber(),
                              LX.ListDescriber()])
    ladder = Ladder(("kb", toKB))
    ladder = ladder.set("trace", 1)
    for f in kb:
        term = d.describe(f, ladder)
        toKB.add(Triple(term, rdfns.type, lxns.TrueSentence))

def unflatten(f):
    """Return a formula which expresses the same knowledge, but any
    formulas described as true using RDF triples and the LX-Layering
    vocabulary are extracted and conjoined.

    The triples used to make those descriptions are optionally removed
    from the result, depending on the kind of inference required.
    """
    
    raise RuntimeError, "Not Implemented"


class URIRefDescriber:

    def describe(self, object, ladder):
        if isinstance(object, LX.Operator):
            print "Describing an operator...   Ignoring for now..."
            return ladder.kb.newExistential()
        if not isinstance(object, LX.URIRef):
            raise LX.DescriptionFailed, 'not a uriref term'
        if ladder.has("term"):
            term = ladder.term
        else:
            term = ladder.kb.newExistential()
            
        if ladder.has("verbose"):
            ladder.kb.add(Triple(term, rdfns.type, lxns.Constant))
        ladder.kb.add(Triple(term, lxns.denotation, object))
        return term
    
class FormulaDescriber:

    nameTable = {
        LX.CONDITIONAL:   [ lxns.Conditional,   lxns.condLeft,   lxns.condRight   ],
        LX.BICONDITIONAL: [ lxns.Biconditional, lxns.bicondLeft, lxns.bicondRight ],
        LX.CONJUNCTION:   [ lxns.Conjunction,   lxns.conjLeft,   lxns.conjRight   ],
        LX.DISJUNCTION:   [ lxns.Disjunction,   lxns.disjLeft,   lxns.disjRight   ],
        LX.NEGATION:      [ lxns.Negation,      lxns.negated ],
        # @@@ hrrrm, should the quants be done so class info isn't needed?   .univar, .exivar, quantified
        LX.UNIVERSAL_QUANTIFICATION: [ lxns.UniversalQuantification, lxns.variable, lxns.subformula ],
        LX.EXISTENTIAL_QUANTIFICATION: [ lxns.ExistentialQuantification, lxns.variable, lxns.subformula ],
        LX.ATOMIC_SENTENCE: [ lxns.Triple, lxns.subjectTerm, lxns.predicateTerm, lxns.objectTerm ]
        }
    
    def describe(self, object, ladder):
        if not isinstance(object, LX.Formula):
            raise LX.DescriptionFailed, 'not a formula'
        if ladder.has("term"):
            term = ladder.term
        else:
            term = ladder.kb.newExistential()

        entry = self.nameTable[object.operator]

        if ladder.has("verbose"):
            ladder.kb.add(Triple(term, rdfns.type, entry[0]))

        for (pred, obj) in zip(entry[1:], object.operands):
            ladder.kb.add(Triple(term, pred, ladder.describer.describe(obj, ladder)))


# $Log$
# Revision 1.2  2002-08-29 16:39:55  sandro
# fixed various early typos and ommissions; working on logic bug which is manifesting in description loops
#
# Revision 1.1  2002/08/29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

 
