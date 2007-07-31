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
dawgt = Namespace("http://www.w3.org/2001/sw/DataAccess/tests/test-dawg#")
rdft = Namespace("http://www.w3.org/2000/10/rdf-tests/rdfcore/testSchema#")
triage = Namespace("http://www.w3.org/2000/10/swap/test/triage#")
mf = Namespace("http://www.w3.org/2001/sw/DataAccess/tests/test-manifest#")
qt = Namespace("http://www.w3.org/2001/sw/DataAccess/tests/test-query#")
earl = Namespace("http://www.w3.org/ns/earl#")

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

testTypes = {mf.PositiveSyntaxTest : 'Positive',
             mf.NegativeSyntaxTest : 'Negative',
             mf.QueryEvaluationTest : 'Query' }


def serial(*iters):
    for i in iters:
        for thing in i:
            yield thing


def gatherDAWGStyleTests(kb):
    manifests = kb.each(pred=rdf.type, obj=mf.Manifest)
    for manifest in manifests:
        testList = kb.the(subj=manifest, pred=mf.entries)
        for test in testList:
            typeURI = kb.the(subj=test, pred=rdf.type)
            try:
                type = testTypes[typeURI]
            except KeyError:
                if kb.contains(subj=test, pred=mf.result):
                    type = 'Query'
                else:
                    raise ValueError(test.uriref())
            name = str(kb.the(subj=test, pred=mf.name))
            description = str(kb.the(subj=test, pred=rdfs.comment))
            action = kb.the(subj=test, pred=mf.action)
            if type == 'Query':
                queryDocument = kb.the(subj=action, pred=qt.query)
                inputDocument = kb.the(subj=action, pred=qt.data)
                outputDocument = kb.any(subj=test, pred=mf.result)
            else:
                queryDocument = action
                inputDocument = None
                outputDocument = None
            if kb.contains(subj=test, pred=dawgt.approval, obj=dawgt.Approved):
                yield test, name, type, description, queryDocument, inputDocument, outputDocument

def testCwmSparql(kb, output, errorFile):
    """The main parser tester


    """
    temp_adder = '_dawg_test'
    commandNode = output.newBlankNode()
    thisProgram = output.newSymbol('http://www.w3.org/2000/10/swap/test/sparql/dawg_tester.py')
    cwmURI = output.newSymbol('http://www.w3.org/2000/10/swap/doc/cwm#')

    
    for test in gatherDAWGStyleTests(kb):
        testURI, name, type, description, queryDocument, inputDocument, outputDocument = test
        print('%s\t%s\t%s\t%s\t%s' % (testURI, name, description, queryDocument.uriref(), type))
        case = (name + temp_adder + ".out").replace(' ',
                '_').replace('\n',
                '_').replace('\t',
                '_').replace('|',
                '_').replace('\\',
                '_').replace('/',
                '_') # Make up temp filename
        tempFile = output.newSymbol(join(base(), ',temp/' + case))


        if type == 'Query':
            thisCommand = ('python ../../cwm.py %s --sparql=%s --filter=%s --filter=%s --ntriples > %s' %
                              (inputDocument.uriref(), queryDocument.uriref(),
                               'filter1.n3', 'filter2.n3',
                                tempFile.uriref()[5:]))
            print thisCommand
            result = system(thisCommand)
            if result != 0:
                result = earl.fail
            else:
                if outputDocument.uriref()[-3:] == 'srx': # sparql results format. how do we deal with that?
                    result = earl['noClue']
                else:
                    result = system('python ../../cwm.py %s --ntriples | python ../../cant.py -d %s' %
                               (outputDocument.uriref(), tempFile.uriref()))
                    if result == 0:
                        result = earl['pass']
                    else:
                        result = earl['fail']
        else:
            thisCommand = ('python ../../cwm.py --language=sparql %s > /dev/null 2> /dev/null' %
                              (queryDocument.uriref(), ))
            result = system(thisCommand)
            if (result == 0 and type == 'Positive') or \
               (result != 0 and type == 'Negative'):
                result = earl['pass']
            else:
                result = earl['fail']
                
        caseURI = output.newBlankNode()
        output.add(caseURI, rdf.type, earl.Assertion)
        output.add(caseURI, earl.assertedBy, thisProgram)
        output.add(caseURI, earl.subject, cwmURI)
        output.add(caseURI, earl.test, testURI)
        resultURI = output.newBlankNode()
        output.add(caseURI, earl.result, resultURI)
        output.add(resultURI, rdf.type, earl.TestResult)
        output.add(resultURI, earl.outcome, result)
        print '\t\t\tresult\t', result


            
#           if description == None: description = case + " (no description)"
##        output.add(inputDocument, rdf.type, n3test.Input)
##        output.add(inputDocument, n3test.expected, type)
##        output.add(inputDocument, n3test.description, description)
##        #result = 1
##
##        thisCommand = ((command + ' > %s 2>>%s') % \
##            (inputDocument.uriref(), tempFile.uriref()[5:], errorFile))
##
##        result = system(thisCommand)
##        print thisCommand
##        if result != 0: # Error case:
##            output.add(commandNode, n3test.failsParsing, inputDocument)
##            parseResult = output.newBlankNode()
##            output.add(inputDocument, commandNode, parseResult)
##            output.add(parseResult, n3test.isFile, rdf.nil)
##            ef = open(errorFile, "r")
##            output.add(parseResult, n3test.errorMessage, ef.read())
##            ef.close()
##        else:
##            output.add(commandNode, n3test.parses, inputDocument)
##            parseResult = output.newBlankNode()
##            output.add(inputDocument, commandNode, parseResult)
##            output.add(parseResult, n3test.isFile, tempFile)
##            if outputDocument is None:
##                output.add(parseResult, n3test.doesNotMatch, rdf.nil)
##            else:
##                a = output.newBlankNode()
##                child_stdin, child_stdout = popen4("%s %s -f %s -d %s" % \
##                              ('python', '$SWAP/cant.py', tempFile.uriref(), outputDocument.uriref()))
##                output.add(a, rdf.type, n3test.Diff)
##                output.add(a, n3test.diffString, "".join([escapize(ii) for ii in child_stdout.read()]))
##                output.add(parseResult, a, outputDocument)
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

    assert system("mkdir -p ,temp") == 0
    assert system("mkdir -p ,diffs") == 0

    testFiles = testFiles + [
        'http://www.w3.org/2001/sw/DataAccess/tests/data-r2/syntax-sparql1/manifest.ttl',
        'http://www.w3.org/2001/sw/DataAccess/tests/data-r2/syntax-sparql2/manifest.ttl',
        'http://www.w3.org/2001/sw/DataAccess/tests/data-r2/syntax-sparql3/manifest.ttl',
        'http://www.w3.org/2001/sw/DataAccess/tests/data-r2/syntax-sparql4/manifest.ttl',
        'http://www.w3.org/2001/sw/DataAccess/tests/data-r2/algebra/manifest.ttl',
        'http://www.w3.org/2001/sw/DataAccess/tests/data-r2/bnode-coreference/manifest.ttl',
        'http://www.w3.org/2001/sw/DataAccess/tests/data-r2/boolean-effective-value/manifest.ttl',
        'http://www.w3.org/2001/sw/DataAccess/tests/data-r2/bound/manifest.ttl',
        'http://www.w3.org/2001/sw/DataAccess/tests/data-r2/construct/manifest.ttl',
        'http://www.w3.org/2001/sw/DataAccess/tests/data-r2/distinct/manifest.ttl',
        'http://www.w3.org/2001/sw/DataAccess/tests/data-r2/expr-builtin/manifest.ttl',
        'http://www.w3.org/2001/sw/DataAccess/tests/data-r2/graph/manifest.ttl',
        'http://www.w3.org/2001/sw/DataAccess/tests/data-r2/open-world/manifest.ttl',
        'http://www.w3.org/2001/sw/DataAccess/tests/data-r2/optional-filter/manifest.ttl',
        'http://www.w3.org/2001/sw/DataAccess/tests/data-r2/optional/manifest.ttl',
        'http://www.w3.org/2001/sw/DataAccess/tests/data-r2/regex/manifest.ttl',
        'http://www.w3.org/2001/sw/DataAccess/tests/data-r2/sort/manifest.ttl',
        'http://www.w3.org/2001/sw/DataAccess/tests/data-r2/triple-match/manifest.ttl',
        'http://www.w3.org/2001/sw/DataAccess/tests/data-r2/type-promotion/manifest.ttl']
    kb = loadMany(testFiles, referer="")
    output = formula()
    testCwmSparql(kb, output, errorFile)
    output.close()
    output.store.dumpNested(output, ToN3(file(outputFile, 'w').write))
    
if __name__ == "__main__":
    main()
