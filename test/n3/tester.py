#!/usr/bin/env python
"""tester.py

run all of the n3 tests given on all

"""
from os import system, popen3, popen4
import os
import sys
import urllib

# From PYTHONPATH equivalent to http://www.w3.org/2000/10

from swap import llyn
from swap.myStore import load, loadMany, Namespace, formula
from swap.uripath import refTo, base
from swap import diag
from swap.diag import progress
from swap.notation3 import ToN3


rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
test = Namespace("http://www.w3.org/2000/10/swap/test.n3#")
n3test = Namespace("http://www.w3.org/2004/11/n3test#")
rdft = Namespace("http://www.w3.org/2000/10/rdf-tests/rdfcore/testSchema#")
triage = Namespace("http://www.w3.org/2000/10/swap/test/triage#")

import getopt
import sys
import re
from htmlentitydefs import codepoint2name


def usage():
    print __doc__

def escapize(char):
    a = codepoint2name.get(ord(char), None)
    if a:
        return '&' + a + ';'
    return char

def testParser(command, kb, output):
    """The main parser tester


    """
    commandNode = output.newBlankNode()
    output.add(commandNode, rdf.type, n3test.N3Parser)
    output.add(commandNode, n3test.command, command)
    
    totalTestList = kb.each(pred=rdf.type, obj=n3test.PositiveParserTest) + \
                    kb.each(pred=rdf.type, obj=n3test.NegativeParserTest) + \
                    kb.each(pred=rdf.type, obj=n3test.UndecidedParserTest)
    
    for t in totalTestList:
	u = t.uriref()
	hash = u.rfind("#")
	slash = u.rfind("/")
	assert hash >0 and slash > 0
	case = u[slash+1:hash] + "_" + u[hash+1:] + ".out" # Make up temp filename
	
	description = str(kb.the(t, n3test.description))
#	    if description == None: description = case + " (no description)"
	inputDocument = kb.the(t, n3test.inputDocument)
        outputDocument = kb.any(t, n3test.outputDocument)
        output.add(inputDocument, rdf.type, n3test.Input)
        #result = 1
        result = system((command + '> %s 2>/dev/null') % (inputDocument.uriref(), case) )
        #print (command + '> %s 2>/dev/null') % (inputDocument.uriref(), case)
        if result != 0:
            output.add(commandNode, n3test.failsParsing, inputDocument)
        else:
            output.add(commandNode, n3test.parses, inputDocument)
            parseResult = output.newBlankNode()
            output.add(inputDocument, commandNode, parseResult)
            output.add(inputDocument, n3test.description, description)
            if outputDocument is None:
                output.add(parseResult, n3test.doesNotMatch, rdf.nil)
            else:
                a = output.newBlankNode()
                child_stdin, child_stdout = popen4("%s %s -f %s -d %s" % \
                              ('python', '../../cant.py', case, outputDocument.uriref()))
                output.add(a, rdf.type, n3test.Diff)
                output.add(a, n3test.diffString, "".join([escapize(ii) for ii in child_stdout.read()]))
                output.add(parseResult, a, outputDocument)
def main():
    """The main function


    """ ### """
    try:
        opts, testFiles = getopt.getopt(sys.argv[1:], "hc:o:",
	    ["help", "command=", "output="])
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-c", "--command"):
            commandFile = a
        if o in ("-o", "--output"):
            outputFile = a
    commands = [w[:-1] for w in file(commandFile, 'r')]

    assert system("mkdir -p ,temp") == 0
    assert system("mkdir -p ,diffs") == 0

    kb = loadMany(testFiles, referer="")
    output = formula()
    for command in commands:
        testParser(command, kb, output)

    output.close()
    output.store.dumpNested(output, ToN3(file(outputFile, 'w').write))
    
if __name__ == "__main__":
    main()
