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
from rdflib.BNode import BNode
from rdflib.URIRef import URIRef
from rdflib.Literal import Literal
import OwlAxiomReasoner
import time
import os
import os.path
import re

#import random

resultsPrefix=",results-"

pubUriPrefix=""

FOAF = Namespace("http://xmlns.com/foaf/0.1/")
OTEST = Namespace("http://www.w3.org/2002/03owlt/testOntology#")
TRES = Namespace("http://www.w3.org/2002/03owlt/resultsOntology#")
RTEST = Namespace("http://www.w3.org/2000/10/rdf-tests/rdfcore/testSchema#")
DC = Namespace("http://purl.org/dc/elements/1.0/")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
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
axiomTag['http://www.w3.org/2002/03owlt/oneOf/Manifest003#test']="-oneOf"
axiomTag['http://www.w3.org/2002/03owlt/equivalentProperty/Manifest002#test']="-equivProp"
axiomTag['http://www.w3.org/2002/03owlt/equivalentProperty/Manifest003#test']="-equivProp"
axiomTag['http://www.w3.org/2002/03owlt/equivalentProperty/Manifest004#test']="-equivProp"
#axiomTag['http://www.w3.org/2002/03owlt/FunctionalProperty/Manifest004#test']="-funcProp"
#axiomTag['http://www.w3.org/2002/03owlt/InverseFunctionalProperty/Manifest004#test']="-funcProp"


axiomTag['http://www.w3.org/2002/03owlt/cardinality/Manifest001#test']='-cardeq'
axiomTag['http://www.w3.org/2002/03owlt/cardinality/Manifest002#test']='-cardeq'
axiomTag['http://www.w3.org/2002/03owlt/cardinality/Manifest003#test']='-cardeq'
# axiomTag['http://www.w3.org/2002/03owlt/cardinality/Manifest004#test']='-cardeq'
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
system = URIRef('http://www.w3.org/2003/08/surnia/data/surnia')
    
def run(store, test, name, input, entailed, expected, resultStore):

    global failed

    axiomTags = []
    
    dtlist = []
    for dt in store.objects(test, OTEST["supportedDatatype"]):
        dtlist.append(dt)

    for er in store.objects(test, RTEST["entailmentRules"]):
        if str(er) == "http://www.w3.org/1999/02/22-rdf-syntax-ns":
            tag = "RDF"
        elif str(er) == "http://www.w3.org/2000/01/rdf-schema":
            tag = "RDFS"
        elif str(er) == "http://www.w3.org/2000/10/rdf-tests/rdfcore/datatypes":
            if expected == "Consistent":
                print "skipped; our datatype theories are not complete so we can't check for consistency"
                return
            tag = "RDFDT"
        else:
            print "skipped; uses unsupported entailmentRules", er
            return
        axiomTags.append(tag)

    if 0:
        try:
            axiomTags.append("owlAx"+axiomTag.get(str(test)))
        except TypeError:
            pass
        if not axiomTags:
            axiomTags = ["owlAx"]
    if not axiomTags:
        print "skipped; ** NO ENTAILMENT RULES **"
        return
    

    tag=name
    if tag.endswith("#test"):
        tag = tag[:-5]
    tag = "__".join(tag.split("/"))
    tag = re.sub("__Manifest.rdf#", "-", tag)
    tag = re.sub("__Manifest", "-", tag)

    localMaxSeconds=maxSecondsTable.get(str(test), maxSeconds)

    if localMaxSeconds != maxSeconds:
        print (" [special time limit: %ds]" % localMaxSeconds),
    
    ifn = resultsPrefix+tag+".otter.in.txt"
    ofn = resultsPrefix+tag+".otter.out.txt"

    try:
        start = time.time()
        result = OwlAxiomReasoner.checkConsistency(
                     input,
                     entailedDocument=entailed,
                     requiredDatatypes=dtlist,
                     maxSeconds=localMaxSeconds,
                     axiomTags=axiomTags,
                     inputFileName=ifn,
                     outputFileName=ofn)
        end = time.time()
    except OwlAxiomReasoner.UnsupportedDatatype, dt:
        print "skipped; uses unsupported datatype", dt
        return

    this = BNode()
    resultStore.add((this, RDF["type"], TRES["TestRun"]))
    resultStore.add((this, TRES["test"], test))
    resultStore.add((this, TRES["system"], system))
    resultStore.add((this, TRES["output"], URIRef(pubUriPrefix+os.path.basename(ofn))))
    #resultStore.add((this, TRES["start"],
    #                 Literal("20030203T12:12:12", datatype="xsd:time")))
    
    if result == expected:
        dur = end-start
        print "PASSED %ss" % dur
        resultStore.add((this, RDF["type"], TRES["PassingRun"]))
    else:
        if result == "Unknown":
            print "(...unknown...)"
            resultStore.add((this, RDF["type"], TRES["UndecidedRun"]))
        else:
            print "Failed, '%s' when expecting '%s'" % (result, expected)
            resultStore.add((this, RDF["type"], TRES["FailingRun"]))
        #print "   Input document: ", idoc
        failed += 1
        #print "   failed %d (max %d)" % (failed, maxFailed)
                    
def runTests(store, resultStore):

    resultStore.add((system, RDFS["label"], Literal("Surnia")))
    resultStore.add((system, RDFS["comment"], Literal("""Surnia is an OWL Full reasoner using Python (including librdf) for language translation, OTTER for inference, and custom axioms.
    """)))
    
    for testType in (testTypes):
        print
        print "Trying each",testType,"..."
        print
        tests = []
        for s in store.subjects(TYPE, OTEST[testType]):
            tests.append(s)
        for s in store.subjects(TYPE, RTEST[testType]):
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
            if name.startswith("http://www.w3.org/2000/10/rdf-tests/rdfcore/"):
                name = "rdfcore-" + name[len("http://www.w3.org/2000/10/rdf-tests/rdfcore/"):]
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
                if (cdoc, RDF["type"], RTEST["False-Document"]) in store:
                    # concluding a False-Document is the same as just
                    # being inconsistent
                    cdoc = None
                run(store, s, name, pdoc, cdoc, "Inconsistent", resultStore)
            elif testType == "NegativeEntailmentTest":
                pdoc = only(store.objects(s, RTEST["premiseDocument"]))
                cdoc = only(store.objects(s, RTEST["conclusionDocument"]))
                if (cdoc, RDF["type"], RTEST["False-Document"]) in store:
                    # concluding a False-Document is the same as just
                    # being inconsistent
                    cdoc = None
                run(store, s, name, pdoc, cdoc, "Consistent", resultStore)
            elif testType == "InconsistencyTest":
                idoc = only(store.objects(s, RTEST["inputDocument"]))
                run(store, s, name, idoc, None, "Inconsistent", resultStore)
            elif testType == "ConsistencyTest":
                idoc = only(store.objects(s, RTEST["inputDocument"]))
                run(store, s, name, idoc, None, "Consistent", resultStore)
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

def getDirectoryName(pattern):
    try:
        filled = pattern % 0
    except TypeError, e:
        return pattern
    dirName = os.path.dirname(pattern)   #  [0:pattern.rindex("/")]
    try:
        counterFile = file(dirName+"/.counter", "r+")
        count = int(counterFile.readline())
        counterFile.seek(0)
    except IOError, e:
        os.makedirs(dirName)
        counterFile = file(dirName+"/.counter", "w")
        count=0
    counterFile.write(str(count+1))
    counterFile.close()
    return pattern % count
    
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
        resultStore = TripleStore()
        try:
            runTests(store, resultStore)
        except KeyboardInterrupt, k:
            print "KeyboardInterrupt"
        if resultsPrefix:
            f = resultsPrefix + "results.rdf"
            print "\n*** Writing test results to %s ..." % f,
            resultStore.save(f)
            print " done.\n"

    def handle__maxSeconds(self, timeLimit=1):
        """Time limit for each run of the underlying reasoner.

        Affects future --test option.
        """
        global maxSeconds
        maxSeconds = float(timeLimit)

    # --reach ...      include data from the web
    # --nolookup       don't fetch stuff to validate....  ?
    # --query          a pattern to lookup / prove

    def handle__results(self, prefixPattern="./test-results/%05d/"):
        """File name prefix pattern, where test results should be stored.

        Something like: /home/sandro/3/08/surnia/test-results/foo
        or              /home/sandro/3/08/surnia/test-results/%08d/

        If it contains a %-part, then a number will be put there, using
        file ".counter" in that directory to story the count.   (This
        hack means that if you store two sets in the same directory,
        they'll still use distinct numbers.  A bug, you might say.)

        prefix+"results.rdf" will store the general test results,
        while other names linked from it will store the output for
        that particular test.
        """
        global resultsPrefix
        resultsPrefix = getDirectoryName(prefixPattern)
        if resultsPrefix.endswith("/"):
            try:
                os.makedirs(resultsPrefix)
            except OSError, err:
                pass    # @@@ assume OSError: [Errno 17] File exists

    def handle__pubPrefix(self, pubPrefix=""):
        """Beginning of a URI where results files will live,
        as seen from the outside."""
        global pubUriPrefix
        pubUriPrefix = pubPrefix
        
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


