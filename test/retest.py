#! /bin/python
"""Regression test harness for new versions of cwm

Options:

--testsFrom=uri -f uri  Take test definitions from these files (in RDF/XML or N3 format)
--normal        -n      Do normal tests, checking output
--chatty        -c	Do tests with debug --chatty=100 (flag just check doesn't crash)
--proof         -p      Do tests generating and cheking a proof
--start=13      -s 13   Skip the first 12 tests
--verbose	-v      Print what you are doing as you go
--ignoreErrors  -i	Print error message but plough on though more tests if errors found
			(Summary error still raised when all tests ahve been tried)
--help          -h      Print this message and exit

You must specify some test definitions, and normal or proofs or both,
or nothing will happen.

Example:    python retest.py -n -f regression.n3

 $Id$
This is or was http://www.w3.org/2000/10/swap/test/retest.py
W3C open source licence <http://www.w3.org/Consortium/Legal/copyright-software.html>.

"""
from os import system
import os
import sys
import urllib

# From PYTHONPATH equivalent to http://www.w3.org/2000/10/swap

import llyn
from thing import load, Namespace

rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
test = Namespace("http://www.w3.org/2000/10/swap/test.n3#")
rdft = Namespace("http://www.w3.org/2000/10/rdf-tests/rdfcore/testSchema#")

import getopt
import sys

def localize(uri):
    """Get URI relative to where this lives"""
    import uripath
    return uripath.refTo("http://www.w3.org/2000/10/swap/test/retest.py", uri)

def problem(str):
    global ploughOn
    global problems
    sys.stderr.write(str + "\n")
    problems = problems + 1
    if not ploughOn:
	sys.exit(-1)

#	raise RuntimeError(str)

def usage():
    print __doc__

def execute(cmd1):
    global verbose
    if verbose: print "    "+cmd1
    result = system(cmd1)
    if result != 0:
	raise RuntimeError("Error %i executing %s" %(result, cmd1))

def diff(case, ref=None):
    global verbose
    if ref == None:
	ref = "ref/%s" % case
    diffcmd = """diff -Bbwu %s ,temp/%s >,diffs/%s""" %(ref, case, case)
    if verbose: print "  ", diffcmd
    result = system(diffcmd)
    if result < 0:
	raise problem("Comparison fails: result %i executing %s" %(result, diffcmd))
    if result > 0: print "Files differ, result=", result
    d = urllib.urlopen(",diffs/"+case)
    buf = d.read()
    if len(buf) > 0:
	print "######### Differences from reference output:\n" + buf
	return 1
    return result

def main():
    testFiles = []
    start = 1
    normal = 0
    chatty = 0
    proofs = 0
    global ploughOn # even if error
    ploughOn = 0
    global verbose
    verbose = 0
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hs:ncipf:v",
	    ["help", "start=", "testsFrom=", "normal", "chatty", "ignoreErrors", "proofs", "verbose"])
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)
    output = None
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-v", "--verbose"):
	    verbose = 1
        if o in ("-i", "--ignoreErrors"):
	    ploughOn = 1
        if o in ("-s", "--start"):
            start = int(a)
	if o in ("-f", "--testsFrom"):
	    testFiles.append(a)
	if o in ("-n", "--normal"):
	    normal = 1
	if o in ("-c", "--chatty"):
	    chatty = 1
	if o in ("-p", "--proofs"):
	    proofs = 1

    assert system("mkdir -p ,temp") == 0
    assert system("mkdir -p ,diffs") == 0
    if proofs: assert system("mkdir -p ,proofs") == 0
    
    tests=0
    passes=0
    global problems
    problems = 0
    
    REFWD="file:/devel/WWW/2000/10/swap/test"
    WD = "file:" + os.getcwd()
    
    #def basicTest(case, desc, args)

    testData = []
    RDFTestData  = []
    for fn in testFiles:
	print "Loading tests from", fn
	kb=load(fn)
    
	for t in kb.each(pred=rdf.type, obj=test.CwmTest):
	    case = str(kb.the(t, test.shortFileName))
	    description = str(kb.the(t, test.description))
	    arguments = str(kb.the(t, test.arguments))
	    environment = kb.the(t, test.environment)
	    if environment == None: env=""
	    else: env = str(environment) + " "
	    testData.append((t.uriref(), case, description, env, arguments))

	for t in kb.each(pred=rdf.type, obj=rdft.PositiveParserTest):
	    case = "rdft_" + t.fragid + ".nt" # Hack - temp file name
	    description = str(kb.the(t, rdft.description))
#	    if description == None: description = case + " (no description)"
	    inputDocument = kb.the(t, rdft.inputDocument).uriref()
	    outputDocument = kb.the(t, rdft.outputDocument).uriref()
	    status = kb.the(t, rdft.status).string
	    if status != "APPROVED":
		print "@@@ Not approved: "+ inputDocument
		continue
	    RDFTestData.append((t.uriref(), case, description,  inputDocument, outputDocument))


    testData.sort()
    if verbose: print "Cwm tests: %i" % len(testData)
    RDFTestData.sort()
    if verbose: print "RDF parser tests: %i" % len(RDFTestData)

    for u, case, description, env, arguments in testData:
	tests = tests + 1
	if tests < start: continue
    
    
	print "%3i)  %s" %(tests, description)
    #    print "      %scwm %s   giving %s" %(arguments, case)
	assert case and description and arguments
	cleanup = """sed -e 's/\$[I]d.*\$//g' -e "s;%s;%s;g" -e '/@prefix run/d'""" % (WD, REFWD)
	
	if normal:
	    execute("""%spython ../cwm.py --quiet %s | %s > ,temp/%s""" %
		(env, arguments, cleanup , case))	
	    if diff(case):
		problem("######### from normal case %s: %scwm %s" %( case, env, arguments))
		continue

	if chatty:
	    execute("""%spython ../cwm.py --chatty=100  %s  &> /dev/null""" %
		(env, arguments))	

	if proofs:
	    execute("""%spython ../cwm.py --quiet %s --base=a --why  > ,proofs/%s""" %
		(env, arguments, case))
	    execute("""python ../check.py < ,proofs/%s | %s > ,temp/%s""" %
		(case, cleanup , case))	
	    if diff(case):
		problem("######### from proof case %s: %scwm %s" %( case, env, arguments))
	passes = passes + 1

    for u, case, description,  inputDocument, outputDocument in RDFTestData:
	tests = tests + 1
	if tests < start: continue
    
    
	print "%3i)  %s   %s" %(tests, case, description)
    #    print "      %scwm %s   giving %s" %(inputDocument, case)
	assert case and description and inputDocument and outputDocument
	cleanup = """sed -e 's/\$[I]d.*\$//g' -e "s;%s;%s;g" -e '/@prefix run/d' -e '/^#/d' -e '/^ *$/d'""" % (
			WD, REFWD)
	
	if 1:
	    execute("""python ../cwm.py --quiet --rdf %s --ntriples | %s > ,temp/%s""" %
		(inputDocument, cleanup , case))
	    ref = ",temp/%s.ref" % case
	    execute("""cat %s | %s > %s""" % (localize(outputDocument), cleanup, ref))
	    if diff(case, ref):
		problem("######### from positive parser test %s: cwm %s" %( case,  inputDocument))

	passes = passes + 1

    if problems > 0:
	raise RuntimeError("Total %i errors in %i tests." % (problems, tests))

if __name__ == "__main__":
    main()


# ends
