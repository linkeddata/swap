#! /bin/python
"""Regression test harness for new versions of cwm

python retrest.py   <options>  <inputURIs>
Options:

--testsFrom=uri -f uri  Take test definitions from these files (in RDF/XML or N3 format)
			Or just by themselves at end of command line after options
--normal        -n      Do normal tests, checking output NOW DEFAULT - NOT NEEDED
--chatty        -c	Do tests with debug --chatty=100 (flag just check doesn't crash)
--proof         -p      Do tests generating and cheking a proof
--start=13      -s 13   Skip the first 12 tests
--verbose	-v      Print what you are doing as you go
--ignoreErrors  -i	Print error message but plough on though more tests if errors found
			(Summary error still raised when all tests ahve been tried)
--cwm=../cwm.py         Cwm command is ../cwm
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
from myStore import load, loadMany, Namespace
from uripath import refTo, base
import diag
from diag import progress


rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
test = Namespace("http://www.w3.org/2000/10/swap/test.n3#")
rdft = Namespace("http://www.w3.org/2000/10/rdf-tests/rdfcore/testSchema#")
triage = Namespace("http://www.w3.org/2000/10/swap/test/triage#")

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
    problems.append(str)
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

def diff(case, ref=None, prog="diff -Bbwu"):
    global verbose
    if ref == None:
	ref = "ref/%s" % case
    if diag.print_all_file_names:  #for use in listing all files used in testing
        a = open('testfilelist','a')
        a.write(ref)
        a.write('\n')
        a.close()
    diffcmd = """%s %s ,temp/%s >,diffs/%s""" %(prog, ref, case, case)
    if verbose: print "  ", diffcmd
    result = system(diffcmd)
    if result < 0:
	raise problem("Comparison fails: result %i executing %s" %(result, diffcmd))
    if result > 0: print "Files differ, result=", result
    d = urllib.urlopen(",diffs/"+case)
    buf = d.read()
    if len(buf) > 0:
	print "#  If this is OK,   cp ,temp/%s %s" %(case, ref)
	print "######### Differences from reference output:\n" + buf
	return 1
    return result

def rdfcompare3(case, ref=None):
    "Compare NTriples fieles using the cant.py"
    global verbose
    if ref == None:
	ref = "ref/%s" % case
    diffcmd = """python ../cant.py -d %s -f ,temp/%s >,diffs/%s""" %(ref, case, case)
    if verbose: print "  ", diffcmd
    result = system(diffcmd)
    if result < 0:
	raise problem("Comparison fails: result %i executing %s" %(result, diffcmd))
    if result > 0: print "Files differ, result=", result
    d = urllib.urlopen(",diffs/"+case)
    buf = d.read()
    if len(buf) > 0:
#	print "#  If this is OK,   cp ,temp/%s %s" %(case, ref)
	print "######### Differences from reference output:\n" + buf
	return 1
    return result

def rdfcompare2(case, ref1):
	"""Comare ntriples files by canonicalizing and comparing text files"""
	cant = "python ../cant.py"
	ref = ",temp/%s.ref" % case
	execute("""cat %s | %s > %s""" % (ref1, cant, ref))
	return diff(case, ref)


def rdfcompare(case, ref=None):
    """   The jena.rdfcompare program writes its results to the standard output stream and sets
	its exit code to 0 if the models are equal, to 1 if they are not and
	to -1 if it encounters an error.</p>
    """
    global verbose
    if ref == None:
	ref = "ref/%s" % case
    diffcmd = """java jena.rdfcompare %s ,temp/%s N-TRIPLE N-TRIPLE  >,diffs/%s""" %(ref, case, case)
    if verbose: print "  ", diffcmd
    result = system(diffcmd)
    if result != 0:
	raise problem("Comparison fails: result %s executing %s" %(result, diffcmd))
    return result

def main():
    start = 1
    normal = 1
    chatty = 0
    proofs = 0
    cwm_command='../cwm.py'
    global ploughOn # even if error
    ploughOn = 0
    global verbose
    verbose = 0
    if diag.print_all_file_names:
        a = file('testfilelist','w')
        a.write('')
        a.close()
    try:
        opts, testFiles = getopt.getopt(sys.argv[1:], "hs:ncipf:v",
	    ["help", "start=", "testsFrom=", "normal", "chatty", "ignoreErrors", "proofs", "verbose","cwm="])
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
	if o in ("--cwm", "--the_end"):
            cwm_command=a

    
    assert system("mkdir -p ,temp") == 0
    assert system("mkdir -p ,diffs") == 0
    if proofs: assert system("mkdir -p ,proofs") == 0
    
    tests=0
    passes=0
    global problems
    problems = []
    
    REFWD="file:/devel/WWW/2000/10/swap/test"
    WD = "file:" + os.getcwd()
    
    #def basicTest(case, desc, args)

    if verbose: progress("Test files:", testFiles)
    
    kb = loadMany(testFiles)
    testData = []
    RDFTestData  = []
#    for fn in testFiles:
#	print "Loading tests from", fn
#	kb=load(fn)
    
    for t in kb.each(pred=rdf.type, obj=test.CwmTest):
	u = t.uriref()
	ref = kb.the(t, test.referenceOutput)
	if ref == None:
	    case = str(kb.the(t, test.shortFileName))
	    refFile = "ref/%s" % case
	else:
	    refFile = refTo(base(), ref.uriref())
	    hash = u.rfind("#")
	    slash = u.rfind("/")
	    assert hash >0 and slash > 0
	    case = u[slash+1:hash] + "_" + u[hash+1:] + ".out" # Make up temp filename
	description = str(kb.the(t, test.description))
	arguments = str(kb.the(t, test.arguments))
	environment = kb.the(t, test.environment)
	if environment == None: env=""
	else: env = str(environment) + " "
	testData.append((t.uriref(), case, refFile, description, env, arguments))

    for t in kb.each(pred=rdf.type, obj=rdft.PositiveParserTest):

	x = t.uriref()
	y = x.find("/rdf-tests/")
	x = x[y+11:] # rest
	for i in range(len(x)):
	    if x[i]in"/#": x = x[:i]+"_"+x[i+1:]
	case = "rdft_" + x + ".nt" # Hack - temp file name
	
	description = str(kb.the(t, rdft.description))
#	    if description == None: description = case + " (no description)"
	inputDocument = kb.the(t, rdft.inputDocument).uriref()
	outputDocument = kb.the(t, rdft.outputDocument).uriref()
	status = kb.the(t, rdft.status).string
	good = 1
	if status != "APPROVED":
	    if verbose: print "\tNot approved: "+ inputDocument[-40:]
	    good = 0
	categories = kb.each(t, rdf.type)
	for cat in categories:
	    if cat is triage.ReificationTest:
		if verbose: print "\tNot supported (reification): "+ inputDocument[-40:]
		good = 0
	    if cat is triage.ParseTypeLiteralTest:
		if verbose: print "\tNot supported (Parse type literal): "+ inputDocument[-40:]
		good = 0
	if good:
	    RDFTestData.append((t.uriref(), case, description,  inputDocument, outputDocument))


    testData.sort()
    cwmTests = len(testData)
    if verbose: print "Cwm tests: %i" % cwmTests
    RDFTestData.sort()
    rdfTests = len(RDFTestData)
    totalTests = cwmTests + rdfTests
    if verbose: print "RDF parser tests: %i" % rdfTests

    for u, case, refFile, description, env, arguments in testData:
	tests = tests + 1
	if tests < start: continue
	
	urel = refTo(base(), u)
    
	print "%3i/%i %-30s  %s" %(tests, totalTests, urel, description)
    #    print "      %scwm %s   giving %s" %(arguments, case)
	assert case and description and arguments
	cleanup = """sed -e 's/\$[I]d.*\$//g' -e "s;%s;%s;g" -e '/@prefix run/d'""" % (WD, REFWD)
	
	if normal:
	    execute("""CWM_RUN_NS="run#" %spython %s --quiet %s | %s > ,temp/%s""" %
		(env, cwm_command, arguments, cleanup , case))	
	    if diff(case, refFile):
		problem("######### from normal case %s: %scwm %s" %( case, env, arguments))
		continue

	if chatty:
	    execute("""%spython %s --chatty=100  %s  &> /dev/null""" %
		(env, cwm_command, arguments))	

	if proofs:
	    execute("""%spython %s --quiet %s --base=a --why  > ,proofs/%s""" %
		(env, cwm_command, arguments, case))
	    execute("""python ../check.py < ,proofs/%s | %s > ,temp/%s""" %
		(case, cleanup , case))	
	    if diff(case, refFile):
		problem("######### from proof case %s: %scwm %s" %( case, env, arguments))
	passes = passes + 1
	
    for u, case, description,  inputDocument, outputDocument in RDFTestData:
	tests = tests + 1
	if tests < start: continue
    
    
	print "%3i/%i)  %s   %s" %(tests, totalTests, case, description)
    #    print "      %scwm %s   giving %s" %(inputDocument, case)
	assert case and description and inputDocument and outputDocument
#	cleanup = """sed -e 's/\$[I]d.*\$//g' -e "s;%s;%s;g" -e '/@prefix run/d' -e '/^#/d' -e '/^ *$/d'""" % (
#			WD, REFWD)
	execute("""python %s --quiet --rdf=RT %s --ntriples  > ,temp/%s""" %
	    (cwm_command, inputDocument, case))
	if rdfcompare3(case, localize(outputDocument)):
	    problem("  from positive parser test %s running\n\tcwm %s\n" %( case,  inputDocument))

	passes = passes + 1

    if problems != []:
	sys.stderr.write("\nProblems:\n")
	for s in problems:
	    sys.stderr.write("  " + s + "\n")
	raise RuntimeError("Total %i errors in %i tests." % (len(problems), tests))

if __name__ == "__main__":
    main()


# ends
