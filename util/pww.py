#!/usr/bin/python
#
"""Print web URIs for files
	    
To make this work:
Put a .web_base file in the highest directory of a tree exported to the
web giving the web address of the pace that directory is exported to.
(Omit a trailing slash)

e.g echo 'http//www.w3org' > /cvsroot/w3.org/.web_base

"""
import sys
import string
import os
import re

version = "$Id$"[1:-1]


def findbase(abs):
    basedir, tail = os.path.split(abs)
    while basedir:
	wb = basedir + '/.web_base'
	try:
	    f = open(wb)
	    break
	except IOError:
	    basedir, tail = os.path.split(basedir)
	    if basedir != '': continue
	    print "No .web_base file for ", path
	    f = None
    if f:
	base = f.readline()
	while base[-1:] in "\n\r \t": base = base[:-1]



files = []

for arg in sys.argv[1:]:
    if arg[0:1] == "-":
        if arg == "-?" or arg == "--help":
	    print__doc__
        elif arg == "-v": verbose = 1
	else:
            print """Bad option argument.""" + __doc__
            sys.exit(-1)
    else:
        files.append(arg)

cwd = os.getcwd()
if files == []: print cwd.replace(basedir, base) # Default to this directory




for path in files:
    abs = os.path.abspath(path)

	
	print abs.replace(basedir, base)

#ends
