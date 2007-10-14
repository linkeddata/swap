#!/usr/bin/env python
"""tester.py

run all of the n3 tests given on all parsers given

"""
from os import system, popen3, popen4
##from subprocess import Popen, PIPE, STDOUT, CalledProcessError  #Use this instead?
import os, os.path
import sys
import urllib
import time

swap = os.environ.get("SWAP", None)
if swap is None:
    realcwd = os.getcwd()
    os.chdir(os.path.split(__file__)[0] or '.')
    os.chdir('..')
    os.chdir('..')
    swap = os.getcwd()
    os.chdir(realcwd)
    os.environ['SWAP'] = swap

# From PYTHONPATH equivalent to http://www.w3.org/2000/10

from swap import llyn
from swap.myStore import load, loadMany, Namespace, formula
from swap.uripath import refTo, base, join
from swap import diag
from swap.diag import progress
from swap.notation3 import ToN3


rdf = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
xsd = Namespace("http://www.w3.org/2001/XMLSchema#")
owl = Namespace("http://www.w3.org/2002/07/owl#")
test = Namespace("http://www.w3.org/2000/10/swap/test.n3#")
n3test = Namespace("http://www.w3.org/2004/11/n3test#")
rdft = Namespace("http://www.w3.org/2000/10/rdf-tests/rdfcore/testSchema#")
triage = Namespace("http://www.w3.org/2000/10/swap/test/triage#")
mf = Namespace("http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#")
qt = Namespace("http://www.w3.org/2001/sw/DataAccess/tests/test-query#")

import getopt
import sys
import re
from htmlentitydefs import codepoint2name
import md5, binascii


def usage():
    print __doc__

def md5it(x):
    m = md5.new(x).digest() 
    return  binascii.hexlify(m)


def escapize(char):
    a = codepoint2name.get(ord(char), None)
    if a:
        return '&' + a + ';'
    return char

testTypes = {n3test.PositiveParserTest : 'Positive',
             n3test.NegativeParserTest : 'Negative',
             n3test.UndecidedParserTest : 'Undecided' }


def serial(*iters):
    for i in iters:
        for thing in i:
            yield thing

def gatherCwmStyleTests(kb):
    """Gather parser tests as specified in the n3parser.tests file

    """
    totalTestList = kb.each(pred=rdf.type, obj=n3test.PositiveParserTest) + \
                    kb.each(pred=rdf.type, obj=n3test.NegativeParserTest) + \
                    kb.each(pred=rdf.type, obj=n3test.UndecidedParserTest)
    

    for t in totalTestList:
        u = t.uriref()
        hash = u.rfind("#")
        slash = u.rfind("/")
        assert hash >0 and slash > 0
        name = u[slash+1:hash] + "_" + u[hash+1:]
        type = testTypes[kb.the(t, rdf.type)]
        description = str(kb.the(t, n3test.description))
        inputDocument = kb.the(t, n3test.inputDocument)
        outputDocument = kb.any(t, n3test.outputDocument)
        yield name, type, description, inputDocument, outputDocument

def gatherDAWGStyleTests(kb):
    manifests = kb.each(pred=rdf.type, obj=mf.Manifest)
    for manifest in manifests:
        s = manifest.uriref()
        if 'bad' in s:
            type= 'Negative'
        else:
            type = 'Positive'
        testList = kb.the(subj=manifest, pred=mf.entries)
        for test in testList:
            name = str(kb.the(subj=test, pred=mf.name))
            description = str(kb.the(subj=test, pred=rdfs.comment))
            action = kb.the(subj=test, pred=mf.action)
            inputDocument = kb.the(subj=action, pred=qt.data)
            outputDocument = kb.any(subj=test, pred=mf.result)
            yield name, type, description, inputDocument, outputDocument

def testParser(command, kb, output, errorFile):
    """The main parser tester


    """
    temp_adder = md5it(command)
    commandNode = output.newBlankNode()
    output.add(commandNode, rdf.type, n3test.N3Parser)
    output.add(commandNode, n3test.command, command)

    
    for test in serial(gatherDAWGStyleTests(kb), gatherCwmStyleTests(kb)):
        name, type, description, inputDocument, outputDocument = test
        case = name + temp_adder + ".out" # Make up temp filename
        tempFile = output.newSymbol(join(base(), ',temp/' + case))

#           if description == None: description = case + " (no description)"
        output.add(inputDocument, rdf.type, n3test.Input)
        output.add(inputDocument, n3test.expected, type)
        output.add(inputDocument, n3test.description, description)
        #result = 1

        thisCommand = ((command + ' > %s 2>>%s') % \
            (inputDocument.uriref(), tempFile.uriref()[5:], errorFile))

        result = system(thisCommand)
        print thisCommand
        if result != 0: # Error case:
            output.add(commandNode, n3test.failsParsing, inputDocument)
            parseResult = output.newBlankNode()
            output.add(inputDocument, commandNode, parseResult)
            output.add(parseResult, n3test.isFile, rdf.nil)
            ef = open(errorFile, "r")
            output.add(parseResult, n3test.errorMessage, ef.read())
            ef.close()
        else:
            output.add(commandNode, n3test.parses, inputDocument)
            parseResult = output.newBlankNode()
            output.add(inputDocument, commandNode, parseResult)
            output.add(parseResult, n3test.isFile, tempFile)
            if outputDocument is None:
                output.add(parseResult, n3test.doesNotMatch, rdf.nil)
            else:
                a = output.newBlankNode()
                child_stdin, child_stdout = popen4("%s %s -f %s -d %s" % \
                              ('python', '$SWAP/cant.py', tempFile.uriref(), outputDocument.uriref()))
                output.add(a, rdf.type, n3test.Diff)
                output.add(a, n3test.diffString, "".join([escapize(ii) for ii in child_stdout.read()]))
                output.add(parseResult, a, outputDocument)
def main():
    """The main function


    """ ### """
    try:
        opts, testFiles = getopt.getopt(sys.argv[1:], "hc:o:e:",
            ["help", "command=", "output=", "error="])
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)
    errorFile = ',temp/__error.txt'   # was "/dev/null"
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-c", "--command"):
            commandFile = a
        if o in ("-o", "--output"):
            outputFile = a
        if o in ("-e", "--error"):
            errorFile = a
    commands = [w[:-1] for w in file(commandFile, 'r')]

    assert system("mkdir -p ,temp") == 0
    assert system("mkdir -p ,diffs") == 0

    kb = loadMany(testFiles, referer="")
    z = 0
    for command in commands:
        output = formula()
        testParser(command, kb, output, errorFile)

        output.close()
        output.store.dumpNested(output, ToN3(file(outputFile+`z`, 'w').write))
        z = z+1
    
if __name__ == "__main__":
    main()
