#! /bin/python
#   Regression test for new versions of cwm
#
# TODO: separate notation3 testing from cwm testing
#
#alias cwm=python ~/swap/cwm.py
# see also: changelog at end of file.

# From standard python library

"""
Options:

--testsFrom=uri -f uri  Take test definitions from these files (in RDF/XML or N3 format)
--normal        -n      Do normal tests
--proof         -p      Do tests generating and cheking a proof
--start=13      -s 13   Skip the first 12 tests
--verbose	-v      Print what you are doing as you go
--help          -h      Print this message and exit

You must specify some test definitions, and normal or proofs or both,
or nothing will happen.

Example:    python retest.py -n -f regression.n3

 $Id$
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

import getopt

def usage():
    print __doc__

def execute(cmd1):
    global verbose
    if verbose: print "    "+cmd1
    result = system(cmd1)
    if result != 0:
	raise RuntimeError("Error %i executing %s" %(result, cmd1))

def diff(case):
    diffcmd = """diff -Bbwu ref/%s ,temp/%s >,diffs/%s""" %(case, case, case)
#    print "  ", diffcmd
    result = system(diffcmd)
    if result < 0:
	raise RuntimeError("Comparison fails: result %i executing %s" %(result, diffcmd))
    if result > 0: print "Files differ, result=", result
    d = urllib.urlopen(",diffs/"+case)
    buf = d.read()
    if len(buf) > 0:
	print "######### Differences from reference output:\n" + buf
	return 1
    return 0

def main():
    testFiles = []
    start = 1
    normal = 0
    proofs = 0
    global verbose
    verbose = 0
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hs:npf:v",
	    ["help", "start=", "testsFrom=", "normal", "proofs", "verbose"])
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
        if o in ("-s", "--start"):
            start = int(a)
	if o in ("-f", "--testsFrom"):
	    testFiles.append(a)
	if o in ("-n", "--normal"):
	    normal = 1
	if o in ("-p", "--proofs"):
	    proofs = 1

    assert system("mkdir -p ,temp") == 0
    assert system("mkdir -p ,temp/dbork") == 0
    assert system("mkdir -p ,diffs") == 0
    assert system("mkdir -p ,diffs/dbork") == 0
    if proofs: assert system("mkdir -p ,proofs") == 0
    
    tests=0
    passes=0
    
    REFWD="file:/devel/WWW/2000/10/swap/test"
    WD = "file:" + os.getcwd()
    
    #def basicTest(case, desc, args)

    testData = []
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

    testData.sort()

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
		print "######### from normal case %s: %scwm %s" %( case, env, arguments)
		sys.exit(-1)

	if proofs:
	    execute("""%spython ../cwm.py --quiet %s --base=a --why  > ,proofs/%s""" %
		(env, arguments, case))
	    execute("""python ../check.py < ,proofs/%s | %s > ,temp/%s""" %
		(case, cleanup , case))	
	    if diff(case):
		print "######### from proof case %s: %scwm %s" %( case, env, arguments)
		sys.exit(-1)
	passes = passes + 1


if __name__ == "__main__":
    main()


# ends
