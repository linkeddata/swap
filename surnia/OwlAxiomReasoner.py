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

##
##  Which axioms to use?   all at once?  Some which are theorems?
##  Horn form?    ...  lots of work to do here.
##
axiomFile = "util/owlAx.otter"    # temp hack path, etc

################################################################

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
                     requiredDatatypes=[],    # dt not impl
                     forbiddenDatatypes=[]):
    """An OWL consistency checker takes a document as input, and
       returns one word being Consistent, Inconsistent, or Unknown.

       An OWL consistency checker SHOULD report network errors
       occurring during the computation of the imports closure.

       
          -- from http://www.w3.org/TR/owl-test/#conformance


       Search for an inconsistency & see what we find!
    """
    kb = LX.kb.KB()
    parser = LX.language.getParser(language="rdflib", sink=kb)
    parser.load(inputDocument)

    # possible huge performance gains by using subset of axioms
    # possible huge performance gains by puting kb into SOS
    # datatype theories...?

    try:
        LX.engine.otter.run(kb, includes=[axiomFile])
        return "Inconsistent"
    except LX.engine.otter.SOSEmpty:
        return "Consistent"

def checkEntailment(premiseDocument, conclusionDocument):
    """Not defined as a peice of software, per se.

    invert conclusion and turn into a consistency check,
    with SOS as inverted conclusions
    
    """
    raise NotImplemented


# but what we want and can test for is
#    isKnownConsistent
#    isKnownInconsistent
#    isKnownEntailed
#    isKnownNotEntailed
#    languageLevel
