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
import xml2rdf, cwm, notation3

GV_ns='http://www.w3.org/2001/02pd/gv#'
RCSId='$Id$'

def dotTop(text):
    text("/* transformed by " + RCSId + " */\n")

def rdf2dot(text, store, docAddr):
    engine = store.engine
    digraph = engine.internURI(GV_ns + 'digraph')

    docRes = engine.internURI(docAddr)

    props = (engine.internURI(GV_ns + 'label'),
             engine.internURI(GV_ns + 'size'),
             engine.internURI(GV_ns + 'rankdir'),
             engine.internURI(GV_ns + 'color'),
             engine.internURI(GV_ns + 'shape'),
             engine.internURI(GV_ns + 'style'),
             )
    dotTop(text)
    for s in docRes.occursAs[cwm.SUBJ]:
        if s.triple[cwm.PRED] is digraph:
            print "@@digraph", s.triple[cwm.OBJ]
            text("digraph ")
            eachGraph(text, store, s.triple[cwm.OBJ], props)

def eachGraph(text, store, it, props, cluster=''):
    text(cluster + 'N' + `hash(it.uriref('foo@@:'))`) #@@??
    text(" {\n")
    for s in it.occursAs[cwm.SUBJ]:
        p = s.triple[cwm.PRED]
        if p in props:
            text(p.fragid)
            text('="')
            text(s.triple[cwm.OBJ].string) # @@ quoting
            text('";\n')

    for s in it.occursAs[cwm.SUBJ]:
        p = s.triple[cwm.PRED]
        print "@@ graph prop:", p
        if p.uriref('foo@@:') == GV_ns+'hasNode': #@@ intern
            eachNode(text, store, s.triple[cwm.OBJ], props)

    print "@@ carry on with subgraphs"

def eachNode(text, store, gnode, props):
    text('"' + gnode.uriref('foo@@:') + '" [')

    for s in gnode.occursAs[cwm.SUBJ]:
        p = s.triple[cwm.PRED]
        if p in props:
            text(p.fragid)
            text('="')
            text(s.triple[cwm.OBJ].string) # @@ quoting
            text('",\n')
    text("];\n")

    for s in gnode.occursAs[cwm.SUBJ]:
        p = s.triple[cwm.PRED]
        for s2 in p.occursAs[cwm.SUBJ]:
            if s2.triple[cwm.PRED] is store.type \
               and s2.triple[cwm.OJB].uriref('foo@@:') is GV_ns+'EdgeProperty':
                text('"' + gnode.uriref('foo@@:') + " -> "
                     + s2.triple[cwm.OBJ].uriref('foo@@:') + '"')
                print "@@edge attributes..."
                
                
def main(argv):
    baseURI = "file:" + cwm.fixslash(os.getcwd()) + "/"

    rdfAddr = urlparse.urljoin(baseURI, argv[1])

    engine = cwm.Engine()
    store = cwm.RDFStore(engine, "#_gs") #@@??


    p = xml2rdf.RDFXMLParser(store, rdfAddr)
    #@@p = notation3.SinkParser(store,  rdfAddr)
    p.load(rdfAddr)

    rdf2dot(sys.stdout.write, store, rdfAddr)
    

if __name__ == '__main__':
    main(sys.argv)
