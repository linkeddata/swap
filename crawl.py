#!/usr/bin/python
"""

$Id$

Crawler"""


import llyn
from thing import Fragment
import thing
import diag

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
	
def crawl(this, level=0):

    uri = this.uriref()
    print " " * level, "Loading ", uri
    f = load(uri)
    thisd = getDoc(this)
    for s in f.statements:
	for p in 1,2,3:
	    x = s[p]
	    if isinstance(x, Fragment):
		r = x.resource
		if r not in thisd.mentions:
		    thisd.mentions.append(r)
		    print  " " * level, "Mentions", r.uriref()
		    if r not in agenda and r not in already:
			agenda.append(r)
		    
	    

    
def doCommand():
    """Command line RDF/N3 crawler
        
 crawl <uriref>

options:
 
See http://www.w3.org/2000/10/swap/doc/cwm  for more documentation.
"""
    uriref = sys.argv[1]
    uri = join(base(), uriref)
    r = thing.symbol(uri)
    diag.setVerbosity(25)
    crawl(r)
    while agenda != []:
	r = agenda.pop()
	already.append(r)
	crawl(r)

############################################################ Main program
    
if __name__ == '__main__':
    import os
    doCommand()

