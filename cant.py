#! /bin/python
"""CAnonicalize N-Triples

Options:

--verbose	-v      Print what you are doing as you go
--help          -h      Print this message and exit
--from=	uri	-f uri	Specify an input file (or web resource)

Can have any number of --from <file> parameters, in which case files are
merged. If none are given, /dev/stdin is used.

This is an independent n-triples cannonicalizer. It uses heuristics, and
will not work on all graphs. It is designed for testing:  the output and
the reference output are both canonicalized and compared.

It uses the very simple NTriples format. It is designed to be independent
of the SWAP code so that it can be used to test the SWAP code. It doesn't
boast any fancy algorithms - just tries to get the job done for the small
files in the test datasets.

The algorithm to generate a "signature" for each bnode. This is just found by looking in its immediate viscinity, treating any local bnode as a blank.
Bnodes which have signatures
unique within the graph can be allocated cannonical identifiers as a function
of the ordering of the signatures. These are then treated as fixed nodes.
If another pass is done of the new graph, the signatures are more distinct.

This works for well-labelled graphs, and graphs which don't have large areas
of interconnected bnodes or large duplicate areas. A particular failing
is complete lack of treatment of symmetry between bnodes.

References:
 .google graph isomorphism
 
 $Id$
This is or was http://www.w3.org/2000/10/swap/cant.py
W3C open source licence <http://www.w3.org/Consortium/Legal/copyright-software.html>.

NTriples http://www.w3.org/TR/rdf-testcases/#ntriples
"""
import os
import sys
import urllib
import uripath  # http://www.w3.org/2000/10/swap/
from sys import stderr, exit
import uripath



import getopt
import re

name = "[A-Za-z][A-Za-z0-9]*" #http://www.w3.org/TR/rdf-testcases/#ntriples
nodeID = '_:' + name
uriref = r'<[^>]*>'
language = r'[a-z0-9]+(?:-[a-z0-9]+)?'
string_pattern = r'"[^"]*"'
langString = string_pattern + r'(?:@' + language + r')?'
datatypeString = langString + '(?:\^\^' + uriref + r')?' 
#literal = langString + "|" + datatypeString
object =  r'(' + nodeID + "|" + datatypeString + "|" + uriref + r')'
ws = r'[ \t]*'
com = ws + r'(#.*)?' 
comment = re.compile("^"+com+"$")
statement = re.compile( ws + object + ws + object + ws + object  + com) # 


#"

def usage():
    print __doc__
    
def main():
    testFiles = []
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
	if o in ("-f", "--from"):
	    testFiles.append(a)

    
    WD = "file:///" + os.getcwd()
    graph = []
    if testFiles == []: testFiles = [ "/dev/stdin" ]
    for fn in testFiles:
	if verbose: print "Loading data from", fn

	uri = uripath.join(WD, fn)
	inStream = urllib.urlopen(uri)
	while 1:
	    line = inStream.readline()
	    if line == "": break
	    if verbose: print line
	    m = comment.match(line)
	    if m != None: continue
	    m = statement.match(line)
	    if m == None:
		stderr.write("Syntax error: "+line+"\n")
		exit(-1)
	    triple = m.group(1), m.group(2), m.group(3)
	    if verbose: print "-> %s  %s  %s ." % (triple[0], triple[1], triple[2])
	    graph.append(triple)
    if verbose: print "%i statements in graph" % (len(graph))
    g = canonicalize(graph)
    serialize(g)
    
def canonicalize(g):
    "Do our best with this algo"
    dups, graph, c = canon(g)
    while dups != 0:
	newDups, graph, c = canon(graph, c)
	if newDups == dups:
	    exit(-2) # give up
	dups = newDups
    return graph

def serialize(graph):
    graph.sort()
    if verbose: print "# Canonicalized:"
    for t in graph:
	for x in t:
	    if x.startswith: x = x[1:]
	    print x,
	print "."

def canon(graph, c0=0):
    "Try one pass at canonicalizing this using 1 step sigs"
    nextBnode = 0
    bnodes = {}
    pattern = []
    signature = []
    canonical = {}
    for j in range(len(graph)):
	triple = graph[j]
	pat = []
	for i in range(3):
	    if triple[i].startswith("_:"):
		b = bnodes.get(triple[i], None)
		if b == None:
		    b = nextBnode
		    nextBnode = nextBnode + 1
		    bnodes[triple[i]] = b
		    signature.append([])
		pat.append(None)
	    else:
		pat.append(triple[i])
	pattern.append(pat)
	for i in range(3):
	    if triple[i].startswith("_:"):
		b = bnodes[triple[i]]
		signature[b].append((i, pat))

    n = nextBnode
    s = []
    for i in range(n):
	signature[i].sort()   # Signature is now intrinsic to the local environment of that bnode.
	if verbose: print " %3i) %s" % (i, signature[i])
	s.append((signature[i], i))
    s.sort()
    
    dups = 0
    c = c0
    for i in range(n):
	if i != n-1 and s[i][0] == s[i+1][0]:
	    if verbose: print "@@@ %3i]  %i and %i have same signature: \n\t%s\nand\t%s\n" % (
		    i, s[i][1], s[i+1][1], s[i][0], s[i+1][0])
	    dups = dups + 1
	elif i != 1 and s[i][0] == s[i-1][0]:
	    if verbose: print "@@@ %3i]  %i and %i have same signature: \n\t%s\nand\t%s\n" % (
		    i, s[i][1], s[i-1][1], s[i][0], s[i-1][0])
	else:
	    canonical[i] = c
	    c = c + 1
	    
    if verbose: print "@@@ %i duplicate sigs out of %i" %(dups, n)

#    if dups > 0:
#	exit(-2)

    newGraph = []
    for j in range(len(graph)):
	triple = graph[j]
	newTriple = []
	for i in range(3):
	    x = triple[i]
	    if x.startswith("_:"):
		b = bnodes[x]
		c1 = canonical.get(b, None)
		if c1 != None:
		    x = "__:c" + str(c1) # New name
	    newTriple.append(x)
	newGraph.append((newTriple[0], newTriple[1], newTriple[2]))
    return dups, newGraph, c



if __name__ == "__main__":
    main()



# ends
