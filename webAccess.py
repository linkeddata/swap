#!/usr/local/bin/python
"""
$Id$

Web access functionality building on urllib

"""



import types
import string
import codecs # python 2-ism; for writing utf-8 in RDF/xml output
import urllib

from diag import verbosity, setVerbosity, progress

from uripath import refTo, join

import uripath
import diag

def urlopenForRDF(addr):
    """A version of urllib.urlopen() which asks for RDF by preference
    """
    z = urllib.FancyURLopener()
#    z.addheaders.append(('Accept', 'application/rdf+xml, application/n3'))
#    z.addheaders.append(('Accept', 'application/n3'))
    z.addheaders.append(('Accept', 'application/rdf+xml'))
#    progress("HTTP Headers are now:", z.addheaders)
    return z.open(addr)


#ends
