"""  UNUSED -- JUST PLAYING AROUND.

Classes for Abstracting the Web.

Note: This model does not always mesh perfectly with RFC 2396 (URI)
and 2616 (HTTP), but where they disagree, those documents should IMHO
be improved in light of Semantic Web applications.  -- sandro

A URI string might be used as ResponderAddress, and then you might ask
what kind of responder is addressed, and how you can talk to it.  Or it
might be used as a SubjectIndicator.

IndicatedSubject
AddressedResponser

Subject(indicator="http://....")
Responder(address="http://....")


class URI
class URI_As_Web_Address
     stands for a shared memory location by telling you how to access it
class URI_As_Subject_Indicator
     stands for anything

  Locator vs. Indicator

    eu = "http://www.w3.org/People/Eric/"

===>>>>>    URI_As_Web_Address(eu) lastModifedBy URI_As_Subject_Indicator(eu)

    Location(eu) lastModifiedBy IndicatedSubject(eu)a
    
compare http://www.w3.org/ with
http://annotest.w3.org/algae?w3c_query="(ask '((?p http://www.w3.org/ ?o)) collect '(?p ?o))"


  dcTitle="http://purl.org/dc/title"
  WebLocation(dcTitle) IndicatedSubject(dcTitle) "Dublin Core Title"

    uname uname uname


"""
__version__ = "$Revision$"
# $Id$

import re
from cStringIO import StringIO

uriPattern = re.compile(r"""
   ^
   (?P<scheme>[a-z][a-z0-9+.-]*):
   (?P<schemeSpecificPart>[^ <>\#\"]*)
   (\# (?P<fragmentID>[^ <>\#\"]*))?
   $
   """,  re.IGNORECASE | re.VERBOSE)

def makeAbsolute(uri, base):
    """
    Should implement http://www.ietf.org/rfc/rfc2396.txt section 5.2

    of course there are lots of other versions of this around, like in ".."

    >>> from LX.uri import *
    >>> print makeAbsolute("http://foo.bar", "a:b")
    http://foo.bar
    >>> print makeAbsolute("a/b", "")
    RuntimeError: Neither uri ("a/b") nor base ("")is absolute
    >>> print makeAbsolute("a/b/../c", "http://foo.bar/")
    RuntimeError: not implemented
    """
    u = uriPattern.match(uri)
    if u is not None: return uri

    raise RuntimeError, 'Not an absolute URI: "%s"'%uri

    if base is not None:
        b = uriPattern.match(base)
        if b is None:
            raise RuntimeError, ('Neither uri ("%s") nor base ("%s")is absolute'
                                 % (uri, base))
    raise RuntimeError, "not implemented"

class AssociatedThing:

    def __init__(self, uri, base=None):
        self.__uri = makeAbsolute(uri, base)
        
    def getURI(self):
        return self.__uri

    uri = property(getURI)

    """In general, being associated with a URI does not tell us
    equality.  If the association happens to be N:1, then uri string
    equality implies thing equality, but uri string inequality tells
    us nothing.  We could (like python) report a!=b whenever we don't
    happen to know that a==b, but that's too dangerous here.

    If you know more, take care of it in a subclass."""

    def __eq__(self, other):
        raise RuntimeError, "insufficient data to determine equality"

    associationName = "AssociatedThing"
    
    def __str__(self):
        return self.associationName+"("+self.uri+")"

        
class IndicatedSubject(AssociatedThing):
    """This is an arbitrary thing -- anything you might want to talk
    about.

    >>> from LX.uri import *
    >>> eric = IndicatedSubject("http://www.w3.org/People/Eric")
    >>> print eric
    IndicatedSubject(http://www.w3.org/People/Eric)
    >>> ericsPage = SharedMemoryLocation(eric.uri)
    >>> print ericsPage
    +++ entity = webClient.get(ericsPage)
      or
    +++ entity = ericsPage.get()
    +++ print entity.text[1:20]

    """
    associationName = "IndicatedSubject"

class InformationResource(AssociatedThing):
    associationName = "InformationResource"

class DocumentSeries(InformationResource):
    associationName = "DocumentSeries"

class SharedMemoryLocation(AssociatedThing):
    """This one is 1:1 with the (canonical) uri string.  An
    InformationResource can move from one SharedMemoryLocation to
    another.

    Using 

    >>> from LX.uri import *
    >>> print SharedMemoryLocation("http://foo.bar")
    
    """
    
    associationName = "SharedMemoryLocation"
    
    def __init__(self, uri, base=None):
        expl = ExploadedHTTPLikeURI(makeAbsolute(uri, base))
        uri = str(expl)
        superInit = getattr(AssociatedThing, '__init__', lambda x:None)
        superInit(self, uri, base)

    def __str__(self):
        return "SharedMemoryLocation("+self.uri+")"

    def __eq__(self, other):
        assert(isinstance(other, SharedMemoryLocation))
        return self.uri == other.uri

    def makeCanonical(self, uri):
        m = self.httpPattern.match(uri)
        if m is not None:
            s = StringIO()
            s.write(m.group("scheme").lower())
            return s.getvalue()

        raise BadURI, "Cannot parse URI as valid SharedMemoryLocation identifier"

class BadURI(RuntimeError): pass

class ExploadedURI:

    absolutePattern = re.compile("""
        ^

        (?P<scheme>[a-z][a-z0-9+.-]*)  :

        (// (?P<authority>
                 (?P<host>.+?))
                 (\:   (?P<port>[0-9]+))?
        )?

        (/  ?P<pathString> .*? )?
        
        (\? (?P<query_string> .*? ))?
        
        (\#  (?P<fragment>  .*  ))?
        $
        """,  re.IGNORECASE | re.VERBOSE)

    def __init__(self, uri):
        self.original = uri
        m = absolutePattern.match(uri)
        if m is None:
            raise BadURI
        self.scheme = m.group("scheme")
        self.port = m.group("port")
        self.pathString = m.group("pathString")
        self.path = self.pathString.split("/")
        # unescape each bit
        self.queryString = m.group("queryString")
        # break into bits here, too
        self.fragment = m.group("fragment")

    def __str__(self):
        s = StringIO()
        s.write(self.scheme)
        self.canonical = str(self)

        
def _test():
    import doctest, LX.uri
    return doctest.testmod(LX.uri) 

if __name__ == "__main__": _test()

# $Log$
# Revision 1.1  2003-02-13 17:04:41  sandro
# some draft
#
# Revision 1.7  2003/02/01 05:58:10  sandro
