"""
   Run some/all of the OWL test suite.

"""
from rdflib.Namespace import Namespace
from rdflib.constants import TYPE
from rdflib.TripleStore import TripleStore

manifest = "http://www.w3.org/2002/03owlt/editors-draft/draft/Manifest.rdf"

FOAF = Namespace("http://xmlns.com/foaf/0.1/")
OTEST = Namespace("http://www.w3.org/2002/03owlt/testOntology#")
RTEST = Namespace("http://www.w3.org/2000/10/rdf-tests/rdfcore/testSchema#")
DC = Namespace("http://purl.org/dc/elements/1.0/")
OWL = Namespace("http://www.w3.org/2002/07/owl#")

store = TripleStore()
store.load(manifest)

def only(iter):
    result = None
    for x in iter:
        if result is None:
            result = x
        else:
            raise RuntimeError("too many")
    return result
            
for testType in ("PositiveEntailmentTest", "InconsistencyTest"):
    print
    print testType
    print
    tests = []
    for s in store.subjects(TYPE, OTEST[testType]):
        tests.append(s)
    tests.sort()
    for s in tests:
        name = str(s)
        if name.startswith("http://www.w3.org/2002/03owlt/"):
            name = name[len("http://www.w3.org/2002/03owlt/"):]
        creator = only(store.objects(s, DC["creator"]))
        status = only(store.objects(s, RTEST["status"]))
        if str(status) == "OBSOLETED":
            continue

        print "%-40s %-20s %s" % (name, creator, status)
            
        if testType == "PositiveEntailmentTest":
            pdoc = only(store.objects(s, RTEST["premiseDocument"]))
            cdoc = only(store.objects(s, RTEST["conclusionDocument"]))
            print "   ", pdoc, cdoc
        elif testType == "InconsistencyTest":
            idoc = only(store.objects(s, RTEST["inputDocument"]))
            print "   ", idoc


        #    <otest:supportedDatatype rdf:resource='http://www.w3.org/2001/XMLSchema#nonNegativeInteger'/>

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
