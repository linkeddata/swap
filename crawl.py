#!/usr/bin/python
"""

$Id$

Crawler"""


import llyn
from thing import Fragment
import thing

import sys

from thing import load
from uripath import join, base

cvsRevision = "$Revision$"

document = {}
already = []
agenda = []

class Document:
    def __init__(self, x):
	self.item = x
	self.mentions = []

def getDoc(r):
    d = document.get(r, None)
    if d != None: return d
    d = Document(r)
    document[r] = d
    return d
	
def crawl(uriref, level=0):

    uri = join(base(), uriref)
    print " " * level, "Loading ", uriref, uri, base()
    f = load(join(base(), uri))
    this = thing.symbol(uri)
    thisd = getDoc(this)
    for s in f.statements:
	for p in 1,2,3:
	    x = s[p]
	    if isinstance(x, Fragment):
		r = x.resource
		if r not in thisd.mentions:
		    thisd.mentions.append(r)
		    print  " " * level, "Mentions", r.uriref()
		    
		    
	    

    
def doCommand():
    """Command line RDF/N3 crawler
        
 <command> <options> <steps> [--with <more args> ]

options:
 
See http://www.w3.org/2000/10/swap/doc/cwm  for more documentation.
"""
    uri = sys.argv[1]
    crawl(uri)

############################################################ Main program
    
if __name__ == '__main__':
    import os
    doCommand()

