"""Classes for Abstracting URIs and the Web

"""
__version__ = "$Revision$"
# $Id$

class Resource:
    """A Resource is a thing which is directly identified by a URI.
    The term "resource", like the term "mother" has far more meaning
    connoting a relationship than a class.  A Resource can be anything,
    but not via an HTTP URI.

    >>> import LX.uri
    >>> x = LX.uri.Resource("http://example.com")
    >>> print x
    <http://example.com>
    >>> print x.uri
    http://example.com
    >>> print LX.uri.Resource("http://example.com#foo")
    [ lx:uri "http://example.com#foo" ]
    """
    def __init__(self, uri):
        self.uri = uri
    def __str__(self):
        if self.uri.count("#"):
            return '[ lx:uri "%s" ]' % self.uri
        else:
            return '<' + self.uri + '>'

class DescribedThing:
    """A DescribedThing is something which is indirectly associated
    with a URI.  The utility of DescribedThing is that it can be a
    physical object, RDF class, etc, even for HTTP URIs.
    
    >>> import LX.uri
    >>> x = LX.uri.DescribedThing("http://example.com")
    >>> print x
    [ web:uriOfDescription "http://example.com" ]
    >>> print x.uriOfDescription
    http://example.com
    >>> print LX.uri.DescribedThing("http://example.com#foo")
    <http://example.com#foo>
    """
    def __init__(self, uri):
        self.uriOfDescription = uri
    def __str__(self):
        if self.uriOfDescription.count("#"):
            return '<' + self.uriOfDescription + '>'
        else:
            return '[ web:uriOfDescription "%s" ]' % self.uriOfDescription

         
def _test():
    import doctest, LX.uri
    return doctest.testmod(LX.uri) 

if __name__ == "__main__": _test()

# $Log$
# Revision 1.3  2003-02-14 19:39:03  sandro
# adopted smart <...> syntax
#
# Revision 1.2  2003/02/13 17:14:14  sandro
# Dropped all the URI parsing stuff and interesting ideas about
# WebLocations and SharedMemory and stuff; trimmed down to bare
# minimum two-level system.
#
# Revision 1.1  2003/02/13 17:04:41  sandro
# some draft
#
# Revision 1.7  2003/02/01 05:58:10  sandro
