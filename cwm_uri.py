#
#  URI path extraction routines
#
#  These are just convenience routines, for people who want
# to give metadata about things as a function of their URI
#
#  Eg:
#
#  { ?X log:uri [ uri:scheme "http"; uri:host "w3.org"]} => { ?X a :Cool }
#

"""
The time built-ins concern dates and times expressed in a specific
version of ISO date-time format.  These functions allow the various
parts of the date and time to be compared, and converted
into interger second GMT era format for arithmetic.

Be aware that ISo times carry timezone offset information:  they cannot be
converted to integer second times without a valid timezone offset, such as "Z".
"""

import string
import re

import notation3    # N3 parsers and generators, and RDF generator
import isodate	    # Local, by mnot. implements <http://www.w3.org/TR/NOTE-datetime>
from diag import progress, verbosity
from term import LightBuiltIn, Function, ReverseFunction


URI_NS_URI = "http://www.w3.org/2000/10/swap/uri#"


__version__ = "$Id$"[1:-1]


class BI_uri_canon(LightBuiltIn, Function):
    """The schem part of a URI, without the colon.
    """
    def evaluateObject(self, subj_py):
        try:
            return uripath.canon(subj_py)
        except ValueError, AssertionError:
	    progress("Warning: Failed to parse uri string '%s'" % subj_py)
            return None

class BI_uri_scheme(LightBuiltIn, Function):
    """The schem part of a URI, without the colon.
    """
    def evaluateObject(self, subj_py):
        try:
            return uripath.scheme(subj_py)
        except ValueError, AssertionError:
	    progress("Warning: Failed to parse uri string '%s'" % subj_py)
            return None

class BI_uri_host(LightBuiltIn, Function):
    """The schem part of a URI, without the colon.
    """
    def evaluateObject(self, subj_py):
        try:
            return uripath.host(subj_py)
        except ValueError, AssertionError:
	    progress("Warning: Failed to parse uri string '%s'" % subj_py)
            return None



#  Register the string built-ins with the store
def register(store):
    str = store.symbol(TIME_NS_URI[:-1])
    str.internFrag("canon", BI_uri_canon)
    str.internFrag("scheme", BI_uri_scheme)
    str.internFrag("host", BI_uri_host)


# ends
