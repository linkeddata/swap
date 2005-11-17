#!/usr/bin/python
"""
$Id$

by Dan Connolly
copyright (c) 2001 by W3C (MIT, INRIA, Keio)
released under an Open Source License
http://www.w3.org/COPYRIGHT

transcribed from
Id: rdf2dot.xsl,v 1.4 2001/02/26 19:55:00 connolly Exp 
"""

import sys, os
import urlparse

from swap import myStore, Namespace

GV = Namespace('http://www.w3.org/2001/02pd/gv#')
RCSId='$Id$'

def dotTop(text):
    text("/* transformed by " + RCSId + " */\n")

def rdf2dot(text, f):
    props = (GVlabel,
             GV.size,
             GV.rankdir),
             GV.color,
             GV.shape,
             GV.style,
             )
    dotTop(text)
    for s in f.statementsMatching(pred=GV.digraph):
            print "@@digraph", s.quad[cwm.OBJ]
            text("digraph ")
            eachGraph(text, store, s.quad[cwm.OBJ], props)

def eachGraph(text, store, it, props, cluster=''):
    text(cluster + 'N' + `hash(it.uriref('foo@@:'))`) #@@??
    text(" {\n")
    for s in it.occursAs[cwm.SUBJ]:
        p = s.quad[cwm.PRED]
        if p in props:
            text(p.fragid)
            text('="')
            text(s.quad[cwm.OBJ].string) # @@ quoting
            text('";\n')

    for s in it.occursAs[cwm.SUBJ]:
        p = s.quad[cwm.PRED]
        print "@@ graph prop:", p
        if p.uriref('foo@@:') == GV_ns+'hasNode': #@@ intern
            eachNode(text, store, s.quad[cwm.OBJ], props)

    print "@@ carry on with subgraphs"

def eachNode(text, store, gnode, props):
    text('"' + gnode.uriref('foo@@:') + '" [')

    for s in gnode.occursAs[cwm.SUBJ]:
        p = s.quad[cwm.PRED]
        if p in props:
            text(p.fragid)
            text('="')
            text(s.quad[cwm.OBJ].string) # @@ quoting
            text('",\n')
    text("];\n")

    for s in gnode.occursAs[cwm.SUBJ]:
        p = s.quad[cwm.PRED]
        for s2 in p.occursAs[cwm.SUBJ]:
            if s2.quad[cwm.PRED] is store.type \
               and s2.quad[cwm.OJB].uriref('foo@@:') is GV_ns+'EdgeProperty':
                text('"' + gnode.uriref('foo@@:') + " -> "
                     + s2.quad[cwm.OBJ].uriref('foo@@:') + '"')
                print "@@edge attributes..."
                
                
def main(argv):
    f = myStore.load(argv[1])

    rdf2dot(sys.stdout.write, f)
    

if __name__ == '__main__':
    main(sys.argv)
