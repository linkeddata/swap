"""

   An OWL Reasoner which doesn't really do any work itself; it just
   mixes in axioms and hands the job off to some general purpose
   reasoner.

   The other reasoner should match the axioms, eg XSB can be used for
   Horn Axioms, while OTTER is more suitable for FOL axioms.

   This might be subclassed from AxiomReasoner and/or Reasoner some
   day, when there are more sorts of users.

"""

import LX.engine.otter
import LX.kb

##
##  Which axioms to use?   all at once?  Some which are theorems?
##  Horn form?    ...  lots of work to do here.
##
axiomFile = "otter/owlAx%s.otter"    # temp hack path, etc

prefixMap = {

    # OWL
    'http://www.w3.org/2002/07/owl#':
    'file:web-override/owl/',

    # RDFS
    'http://www.w3.org/2000/01/rdf-schema#':
    'file:web-override/rdfs/',

    # RDF
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#':
    'file:web-override/rdf/',

    # OWL TESTS
    'http://www.w3.org/2002/03owlt/':
    None,

    # EXAMPLE.COM
    'http://example.com/':
    None,

    }


################################################################

class UnsupportedDatatype(RuntimeError):
    pass

def checkSyntax(inputDocument):
    """An OWL syntax checker takes a document as input, and returns
    one word being one of Lite, DL, Full, Other.

                 -- from http://www.w3.org/TR/owl-test/#conformance

    *RDF parser for Full/Other
    *Feed to XSB recognizer rules for Lite, DL.
    *Return AbstractSyntax version, just for kicks.
    """
    raise NotImplemented

def checkConsistency(inputDocument,
                     entailedDocument=None,
                     requiredDatatypes=[],    # dt not impl
                     forbiddenDatatypes=[],
                     tag="unnamed", maxSeconds=5,
                     axiomTag=""):
    """An OWL consistency checker takes a document as input, and
       returns one word being Consistent, Inconsistent, or Unknown.

       An OWL consistency checker SHOULD report network errors
       occurring during the computation of the imports closure.

       
          -- from http://www.w3.org/TR/owl-test/#conformance

       Search for an inconsistency & see what we find!

       ...   Meanwhile, if we also have an "entailedDocument",
       add its negation; Inconsistent==Entailed, etc.
    """

    for dt in requiredDatatypes:
        # if not supported, ... but they are ALL not supported right now!
        raise UnsupportedDatatype, dt

    kb = LX.kb.KB()

    try:
        kb.load(inputDocument)

        if entailedDocument:
            kb2 = LX.kb.KB()
            kb2.load(entailedDocument)
            #print "Adding negated:", kb2
            kb.add(LX.logic.NOT(kb2.asFormula()))

        # possible huge performance gains by using subset of axioms (when that's not cheating)
        # possible huge performance gains by puting kb [or just kb2 if present] into SOS
        #kb.gather(prefixMap)

        try:
            LX.engine.otter.run(kb, fileBase=",ot/"+tag,
                                includes=[axiomFile % axiomTag], maxSeconds=maxSeconds)
            return "Inconsistent"
        except LX.engine.otter.SOSEmpty:
            return "Consistent"
        except LX.engine.otter.TimeoutBeforeAnyProof:
            return "Unknown"
    except LX.kb.UnsupportedDatatype, e:
        raise UnsupportedDatatype, e

# but what we want and can test for is
#    isKnownConsistent
#    isKnownInconsistent
#    isKnownEntailed
#    isKnownNotEntailed
#    languageLevel
