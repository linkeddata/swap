# This is or was http://www.w3.org/2000/10/swap/util/ptsw.py
# see http://pingthesemanticweb.com/api.php

"""Ping the PingTheSemantcicWeb service

PTSW tracks changed sem wb files, as a sevice for bots.
Using this to indicate that a file has changed will suggest a bot re-index it.
It also provides interesting statistics and lists of documents with 
different vocabularies.

Usage example:

alias ptsw='python /devel/WWW/2000/10/swap/util/ptsw.py'
ptsw *.rdf

Note the map file must be salted to taste to tell PTSW where the
files in your system are pubished.

- removes the extension assuming the URI uses content negotiation

Open source W3C licence.
"""
# Map from filenames to URIs
map = { 'file:///devel/WWW/': 'http://www.w3.org/',
        'file:///devel/dig/': 'http://dig.csail.mit.edu/'}
service = 'http://pingthesemanticweb.com/rest/?url='

import os, sys # http://pydoc.org/1.6/os.html
from urllib2 import urlopen


import swap
from swap import uripath # http://www.w3.org/2000/10/swap/uripath.py
from swap.uripath import join, URI_unreserved

cwd = os.getcwd()
base = 'file://' + cwd  + "/"

for arg in sys.argv[1:]:
    uri = join(base, arg)
    for local, web in map.items():
        uri = uri.replace(local, web)
    if uri.endswith('.rdf'): uri = uri[:-4]
    if uri.endswith('.n3'): uri = uri[:-3]
    print "Ping: ",uri
    encoded = ""
    for ch in uri:
        if ch in URI_unreserved: encoded += ch
        else: encoded += "%%%2x" % ord(ch)
#    print "  with ", service+encoded
    x = urlopen(service+encoded)
    buf = x.read()
    if buf.find('Thanks for') < 0: print buf
    x.close()
    
    
    

    
