#!/bin/env python
"""
sitemap -- craw web site, record titles and links

$Id$
see changelog at end.

Share and Enjoy.

design sketch:

1. content = urlopen.urlopen(startAddr)
2. xmlDoc = xmlparse(content)
3. neighbors = xpath.eval(xmlDoc, "//a/@href"); neighbors = map(lambda x: uripath.join(x, startAddr), neighbors)
4. title = xpath.eval(xmlDoc, "//title")
5. kb.addTriple(startAddr, dc.title, title)
6. for n in neighbors: kb.addTriple(startAddr, dc:relation, n)
7. queue unseen neighbors, recur

TODO:
  -- circles/arrows diagram of results
  -- handle img/@src
  -- handle area/@href
  -- handle form action?

LICENSE: Share and Enjoy.
Copyright (c) 2001 W3C (MIT, INRIA, Keio)
Open Source license:
http://www.w3.org/Consortium/Legal/copyright-software-19980720

"""

import urllib2

# eliminate this dependency; use mnot's HtmlDom instead
# http://www.mnot.net/python/HtmlDom.py
# <AaronSw> it lets me do: d = fetch(url); print xml.xpath.Evaluate("//*[@class='rss:item']/text()", d)
import libxml2 # http://xmlsoft.org/python.html , DebianPackage:libxml2-python2.1 won't work because llyn.py uses 2.2isms

import llyn, uripath, toXML # http://www.w3.org/2000/10/swap/
from RDFSink import SYMBOL, LITERAL, FORMULA
import diag
diag.setVerbosity(0)

def DC(n):
    return 'http://purl.org/dc/elements/1.1/' + n


class Crawler:
    def __init__(self, kb, ctx, here):
        self._kb = kb
        self._ctx = ctx

    def crawlFrom(self, addr, prefix, max):
        kb = self._kb
        ctx = self._ctx

        iter = 1
        queue = [addr]
        seen = []
        while queue:
            head = queue.pop()

            progress("crawling at: ", head, " iter ", iter, " of ", max)
            iter = iter + 1
            if iter > max:
                progress("should stop now.")
                break

            seen.append(head)

            try:
                content = urllib2.urlopen(head).read()
            except IOError:
                progress("can't GET", head)
                continue
                #@@ makeStatement(head type NoGood)

            progress("... got content")
            doc = libxml2.htmlParseDoc(content, 'us-ascii')
            try:
                titles = doc.xpathNewContext().xpathEval('//title')
                title = titles[0].getContent()
            except: #@@figure out the right exceptions
                pass
            else:
                progress("... found title:", title)
                #self._fmla.add(DC('title'), head, str(title))
                kb.makeStatement((ctx,
                                  kb.newSymbol(DC('title')),
                                  kb.newSymbol(head),
                                  kb.newLiteral(str(title))))
            
            hrefs = doc.xpathNewContext().xpathEval('//a/@href')
            progress("... found ", len(hrefs), " links")
                     
            for h in hrefs:
                h = h.getContent()
                progress("... found href", h)
                i = uripath.join(head, h)
                progress("... found link", head, ' -> ', i)
                kb.makeStatement((ctx,
                                  kb.newSymbol(DC('relation')),
                                  kb.newSymbol(head),
                                  kb.newSymbol(i)))
                if i[:len(prefix)] == prefix and i not in seen:
                    queue.append(i)


def progress(*args):
    import sys
    for a in args:
        sys.stderr.write('%s ' % a)
    sys.stderr.write("\n")


def main(argv):
    import sys

    site, max = argv[1:3]
    max = int(max)
    kb = llyn.RDFStore()
    here = uripath.base()
    f = kb.intern((FORMULA, here + "#_formula")) #@@ ugly!
    progress("f = ", f)
    c = Crawler(kb, f, here)
    c.crawlFrom(site, site, max)
    sink = toXML.ToRDF(sys.stdout, here)
    sink.bind('dc', DC(''))
    kb.dumpNested(f, sink)
    
if __name__ == '__main__':
    import sys
    main(sys.argv)

# $Log$
# Revision 1.2  2003-01-02 05:32:46  connolly
# some comments about dependencies
#
# Revision 1.1  2003/01/02 05:29:59  connolly
# works on one web site
#
