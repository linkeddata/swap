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
RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')

RCSId='$Id$'

def dotTop(text):
    text("/* transformed by %s */\n" % RCSId)


EdgeAttributes = (
    GV.label,
    GV.color,
    GV.shape,
    GV.style,
    GV.fontcolor,
    GV.fontname,
    GV.fontsize,
    GV.height,
    GV.width,
    GV.layer,
    GV.URL,
    GV.sides,
    GV.shapefile,
    )

# graph attributes see Graphviz spec table 3
# hmm... needs update w.r.t http://www.graphviz.org/doc/info/attrs.html
GraphAttributes = (
    GV.center,
    GV.clusterrank,
    GV.color,
    GV.compound,
    GV.concentrate,
    GV.fontcolor,
    GV.fontname,
    GV.fontsize,
    GV.label,
    GV.layerseq,
    GV.margin,
    GV.mclimit,
    GV.nodesep,
    GV.nslimit,
    GV.ordering,
    GV.orientation,
    GV.page,
    GV.rank,
    GV.rankdir,
    GV.ranksep,
    GV.ratio,
    GV.size,
    GV.shape,
    GV.style,
    )

def rdf2dot(text, f):
    dotTop(text)
    for s in f.statementsMatching(pred=GV.digraph):
            text("digraph ")
            eachGraph(text, f, s.object(), GraphAttributes)

def eachGraph(text, store, it, props, cluster=''):
    text("%s N%d" % (cluster, abs(hash(it.uriref()))))
    text(" {\n")
    for p in props:
        for o in store.each(subj = it, pred = p):
            text('%s="%s";\n' % (p.fragid, o)) # @@ quoting o

    for n in store.each(subj=it, pred=GV.hasNode):
        eachNode(text, store, n, props) #@@hmm... node props = graph props?

    for sub in store.each(subj=it, pred=GV.subgraph):
        raise RuntimeError, "subgraph not yet implemented@@"
    text("}\n")

def eachNode(text, store, gnode, props):
    text('"%s" [' % gnode.uriref())

    for p in props:
        for o in store.each(subj = gnode, pred = p):
            text('%s="%s",\n' % (p.fragid, o)) # @@ quoting o
    text("];\n")

    for p in store.each(pred=RDF.type, obj=GV.EdgeProperty):
        for o in store.each(subj=gnode, pred = p):
            text('"%s" -> "%s"' % (gnode.uriref(), o.uriref()))

            text(" [\n")
            for attr in EdgeAttributes:
                for o in store.each(subj=p, pred=attr):
                    text('%s="%s",\n' % (attr.fragid, o)) # @@ quoting o
            text("];\n")
                    

def progress(*args):
    import sys
    for a in args:
        sys.stderr.write(str(a))
    sys.stderr.write("\n")

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
