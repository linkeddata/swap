#!/usr/local/bin/python
"""
$Id$

Web access functionality building on urllib

"""

import urllib

def urlopenForRDF(addr):
    """A version of urllib.urlopen() which asks for RDF by preference
    """
    z = urllib.FancyURLopener()
    z.addheaders.append(('Accept', 'application/rdf+xml'))
    return z.open(addr)
