#!/usr/bin/python
"""Print totals in a file

Bug: This iis very simplistic - assumes that only one
arc exists for each distinct thing.
$Id$
"""
import llyn

from diag import verbosity, setVerbosity, progress


import notation3    	# N3 parsers and generators
from term import Literal

# import toXML 		#  RDF generator

#from RDFSink import FORMULA, LITERAL, ANONYMOUS, Logic_NS
import uripath
import string
import sys
from uripath import join
from myStore import  Namespace
from notation3 import RDF_NS_URI


state = Namespace("/devel/WWW/2000/10/swap/test/dbork/data/USRegionState.n3#")
qu = Namespace("http://www.w3.org/2000/10/swap/pim/qif#")
tax = Namespace("http://www.w3.org/2000/10/swap/pim/tax.n3#")
rdf = Namespace(RDF_NS_URI)
rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
cat_ns = Namespace("categories.n3#")
ma = Namespace("http://www.w3.org/2000/10/swap/pim/massachusetts#") # Mass tax specials
contact = Namespace("http://www.w3.org/2000/10/swap/pim/contact#") # Personal contact info

import llyn
from myStore import load
import uripath
import re

cat = cat_ns



def doCommand(inputURI="/dev/stdin"):
        import sys
        global sax2rdf
	global kb
	import os

# Load the data:
	 
	progress("Data from", inputURI)
	kb=load(inputURI)
#	print "# Size of kb: ", len(kb)

	totals = {}
	for s in kb.statements:
	    obj = s.object()
	    if isinstance(obj, Literal):
		try:
		    value = float(obj.string)
		except:
		    continue
		tot = totals.get(s.predicate(), 0) + value
		totals[s.predicate()] = tot

	ko = kb.newFormula()
	for pred in totals.keys():
	    ko.add(subj=pred, pred=qu.total, obj=ko.newLiteral("%7.2f" % totals[pred]))
	print ko.close().n3String()

	
        
############################################################ Main program
    
if __name__ == '__main__':
    import getopt
    testFiles = []
    start = 1
    normal = 0
    chatty = 0
    proofs = 0
    global verbose
    verbose = 0
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvy:i:",
	    ["help",  "verbose", "year=", "input="])
    except getopt.GetoptError:
        # print help information and exit:
        print __doc__
        sys.exit(2)
    output = None
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-v", "--verbose"):
	    verbose = 1
        if o in ("-i", "--input"):
            inputURI = a

    doCommand(inputURI=inputURI)

#end
