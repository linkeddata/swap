#!/usr/bin/python
"""
$Id$

by Dan Connolly
copyright (c) 2001 by W3C (MIT, INRIA, Keio)
released under an Open Source License
http://www.w3.org/COPYRIGHT

transcribed from
Id: rdf2dot.xsl,v 1.4 2001/02/26 19:55:00 connolly Exp 

cwm API notes:
 Symbol.uriref() vs uriref2()... why not an optional arg?
"""

class Usage(Exception):
    """python rdf2dot.py foo.rdf > foo.dot
    """
    def __init__(self, msg):
	self._msg = msg

    def __str__(self):
	return "%s\nUsage: %s" % (self._msg, self.__doc__)


import sys, os

from swap.myStore import load, Namespace

GV = Namespace('http://www.w3.org/2001/02pd/gv#')
RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns')

RCSId='$Id$'

def dotTop(text):
    text("/* transformed by " + RCSId + " */\n")

def rdf2dot(text, f):
    props = (GV.label,
             GV.size,
             GV.rankdir,
             GV.color,
             GV.shape,
             GV.style,
             )
    dotTop(text)
    for s in f.statementsMatching(pred=GV.digraph):
            text("digraph ")
            eachGraph(text, f, s.object(), props)

def eachGraph(text, store, it, props, cluster=''):
    text(cluster + 'N' + `hash(it.uriref())`)
    text(" {\n")
    for p in props:
	for o in store.each(subj = it, pred = p):
            text(p.fragid)
            text('="')
            text(str(o)) # @@ quoting
            text('";\n')

    for n in store.each(subj=it, pred=GV.hasNode):
	eachNode(text, store, n, props)

    print "@@ carry on with subgraphs"

def eachNode(text, store, gnode, props):
    text('"' + gnode.uriref() + '" [')

    for p in props:
	for o in store.each(subj = gnode, pred = p):
            text(p.fragid)
            text('="')
            text(str(o)) # @@ quoting
            text('",\n')
    text("];\n")

    for p in store.each(pred=RDF.type, obj=GV.EdgeProperty):
	for o in store.each(subj=gnode, pred = p):
	    text('"' + gnode.uriref() + " -> "
		 + o.uriref() + '"')
	    print "@@edge attributes..."

def main(argv):
    try:
	ref = argv[1]
    except:
	raise Usage("missing input file/URI")

    f = load(ref)

    rdf2dot(sys.stdout.write, f)
    

if __name__ == '__main__':
    try:
	main(sys.argv)
    except Usage, e:
	print >>sys.stderr, e
