"""

   Surnia is an OWL Reasoner, implemented by using some other reasoner
   and a bunch of axioms (rules).

   Basic operation vision is:
       * each input file is checked for semantic validaty
       * --query options can be given to query over the
         inputs (or some closure of them)
   ....
   
   Run some/all of the OWL test suite.

   index tests by owl vocabulary terms they use, number of triples, type,

   might be nice to know which axioms match which tests...

   try some of the other kinds of tests....

   --maxfail 1
   
"""
import ArgHandler
from rdflib.Namespace import Namespace
from rdflib.constants import TYPE
from rdflib.TripleStore import TripleStore
import OwlAxiomReasoner
import time

#import random

FOAF = Namespace("http://xmlns.com/foaf/0.1/")
OTEST = Namespace("http://www.w3.org/2002/03owlt/testOntology#")
RTEST = Namespace("http://www.w3.org/2000/10/rdf-tests/rdfcore/testSchema#")
DC = Namespace("http://purl.org/dc/elements/1.0/")
OWL = Namespace("http://www.w3.org/2002/07/owl#")


def only(iter):
    result = None
    for x in iter:
        if result is None:
            result = x
        else:
            raise RuntimeError("too many")
    return result


testTypes = [
    "NotOwlFeatureTest",
    "PositiveEntailmentTest",
    "NegativeEntailmentTest",
    "TrueTest",
    "OWLforOWLTest",
    "InconsistencyTest",
#    "ConsistencyTest",
    "ImportEntailmentTest",
    "ImportLevelTest"
    ]

# from some config info, telling us how long we should try on
# some test, ...?
fudge = 10

maxSecondsTable = {
    'http://www.w3.org/2002/03owlt/AllDifferent/Manifest001#test': 3 * fudge,
    'http://www.w3.org/2002/03owlt/FunctionalProperty/Manifest004#test': (5 * fudge),
    'http://www.w3.org/2002/03owlt/InverseFunctionalProperty/Manifest004#test': (5 * fudge),
    'http://www.w3.org/2002/03owlt/maxCardinality/Manifest001#test': (110 * fudge),
    }

axiomTag = { }
#axiomTag['http://www.w3.org/2002/03owlt/unionOf/Manifest002#test']="-unionOf"
#axiomTag['http://www.w3.org/2002/03owlt/oneOf/Manifest003#test']="-oneOf"
axiomTag['http://www.w3.org/2002/03owlt/equivalentProperty/Manifest002#test']="-equivProp"
axiomTag['http://www.w3.org/2002/03owlt/equivalentProperty/Manifest003#test']="-equivProp"
axiomTag['http://www.w3.org/2002/03owlt/equivalentProperty/Manifest004#test']="-equivProp"
#axiomTag['http://www.w3.org/2002/03owlt/FunctionalProperty/Manifest004#test']="-funcProp"
#axiomTag['http://www.w3.org/2002/03owlt/InverseFunctionalProperty/Manifest004#test']="-funcProp"

axiomTag['http://www.w3.org/2002/03owlt/cardinality/Manifest001#test']='-card'
axiomTag['http://www.w3.org/2002/03owlt/cardinality/Manifest002#test']='-card'
axiomTag['http://www.w3.org/2002/03owlt/cardinality/Manifest003#test']='-card'
axiomTag['http://www.w3.org/2002/03owlt/cardinality/Manifest004#test']='-card'
axiomTag['http://www.w3.org/2002/03owlt/maxCardinality/Manifest001#test']='-card'

maxSeconds = 1

skip = {
#    'http://www.w3.org/2002/03owlt/I5.2/Manifest002#test': "no DT theory",
#    'http://www.w3.org/2002/03owlt/equivalentClass/Manifest004#test': "no DT theory",
#    'http://www.w3.org/2002/03owlt/cardinality/Manifest001#test': "no DT theory",
#    'http://www.w3.org/2002/03owlt/cardinality/Manifest002#test': "no DT theory",
#    'http://www.w3.org/2002/03owlt/cardinality/Manifest003#test': "no DT theory",
#    'http://www.w3.org/2002/03owlt/cardinality/Manifest004#test': "no DT theory",
#    'http://www.w3.org/2002/03owlt/description-logic/Manifest903#test': "loop",
    }

maxFailed = 999999
failed = 0

def run(store, test, name, input, entailed, expected):

    global failed
    dtlist = []
    for dt in store.objects(test, OTEST["supportedDatatype"]):
        dtlist.append(dt)

    tag=name
    if tag.endswith("#test"):
        tag = tag[:-5]
    tag = "__".join(tag.split("/"))

    localMaxSeconds=maxSecondsTable.get(str(test), maxSeconds)

    if localMaxSeconds != maxSeconds:
        print (" [special time limit: %ds]" % localMaxSeconds),
    
    try:
        start = time.time()
        result = OwlAxiomReasoner.checkConsistency(
                     input,
                     entailedDocument=entailed,
                     tag=tag,
                     requiredDatatypes=dtlist,
                     maxSeconds=localMaxSeconds,
                     axiomTag=axiomTag.get(str(test), ""))
        end = time.time()
    except OwlAxiomReasoner.UnsupportedDatatype, dt:
        print "skipped; uses unsupported datatype", dt
        return

    if result == expected:
        dur = end-start
        print "PASSED %ss" % dur
    else:
        if result == "Unknown":
            print "(...unknown...)"
        else:
            print "Failed, '%s' when expecting '%s'" % (result, expected)
        #print "   Input document: ", idoc
        failed += 1
        #print "   failed %d (max %d)" % (failed, maxFailed)
                    
def runTests(store):
    for testType in (testTypes):
        print
        print "Trying each",testType,"..."
        print
        tests = []
        for s in store.subjects(TYPE, OTEST[testType]):
            tests.append(s)
        tests.sort()
        for s in tests:

            if failed > maxFailed:
                print
                print "maxFailed reached; testing aborted."
                return

            name = str(s)
            if name.startswith("http://www.w3.org/2002/03owlt/"):
                name = name[len("http://www.w3.org/2002/03owlt/"):]
            creator = only(store.objects(s, DC["creator"]))
            status = only(store.objects(s, RTEST["status"]))

            if str(status) == "OBSOLETED":
                continue
            if str(status) != "APPROVED":
                continue


            #print "%-40s %-20s %s" % (name, creator, status)

            print s,

            if str(s) in skip:
                print "skipping because '%s'" % skip[str(s)]
                continue

            if testType == "PositiveEntailmentTest":
                pdoc = only(store.objects(s, RTEST["premiseDocument"]))
                cdoc = only(store.objects(s, RTEST["conclusionDocument"]))
                run(store, s, name, pdoc, cdoc, "Inconsistent")
            elif testType == "NegativeEntailmentTest":
                pdoc = only(store.objects(s, RTEST["premiseDocument"]))
                cdoc = only(store.objects(s, RTEST["conclusionDocument"]))
                run(store, s, name, pdoc, cdoc, "Consistent")
            elif testType == "InconsistencyTest":
                idoc = only(store.objects(s, RTEST["inputDocument"]))
                run(store, s, name, idoc, None, "Inconsistent")
            elif testType == "ConsistencyTest":
                idoc = only(store.objects(s, RTEST["inputDocument"]))
                run(store, s, name, idoc, None, "Consistent")
            else:
                print "skipped, unsupported test type"


            # rtest:description, otest:level, otest:issuette,
            # rtest:inputDocument
        
# write results in html & rdf
#
# [  a test:Run;
#         :TestPassingRun;
#   test:system [ ... ]
#   test:timing [ ... ]
#   test:tester [ ... ]
#   test:test
#   test:output
# ...
# ]


class MyArgHandler(ArgHandler.ArgHandler):

    def __init__(self, *args, **kwargs):
        #apply(super(MyArgHandler, self).__init__, args, kwargs)
        apply(ArgHandler.ArgHandler.__init__, [self]+list(args), kwargs)

    def handle__t__test(self, testURI="http://www.w3.org/TR/owl-test/Manifest.rdf"):
        """Load a test description (manifest) and run the tests.

        Testing is done in a manner set by previous options.  (such as...?)

        Reasonable options include all the various RDF and OWL tests, such as
        in http://www.w3.org/2002/03owlt/editors-draft/draft/Manifest.rdf
        """
        store = TripleStore()
        print "Loading %s..." % testURI,
        store.load(testURI)
        print "  Done."
        try:
            runTests(store)
        except KeyboardInterrupt, k:
            print "KeyboardInterrupt"

    def handle__maxSeconds(self, timeLimit=1):
        """Time limit for each run of the underlying reasoner.

        Affects future --test option.
        """
        global maxSeconds
        maxSeconds = float(timeLimit)

    # --reach ...      include data from the web
    # --nolookup       don't fetch stuff to validate....  ?
    # --query          a pattern to lookup / prove
    
    def handleNoArgs(self):
        raise ArgHandler.Error, "no options or parameters specified."

    def handleExtraArgument(self, arg):
        # This is supposed to be "semantic validation" some day,
        # and/or inputs to --query
        print "Plain argument (\"%s\") not implemented, ignored." % arg
 
if __name__ == "__main__":
    a = MyArgHandler(program="surnia",
                     version="$Id$",
                     uri="http://www.w3.org/2003/07/surnia")

    a.run()


