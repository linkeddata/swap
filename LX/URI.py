"""URI Class

"""
__version__ = "$Revision$"
# $Id$

import urlparse

interned = { }

class URI(str):
    """A URI is a string which conforms to RFC 2396 syntax; this
    class gives us easy access to its the syntactic elements.

    It might be nice to have a mutable version, which allowed things
    like u.scheme="https", but for now interning is more important.

    >>> from LX.URI import URI
    >>> u = URI("http://www.w3.org/People/Sandro/#hours")
    >>> print u
    http://www.w3.org/People/Sandro/#hours
    >>> print `u`
    <URI ('http', 'www.w3.org', '/People/Sandro/', '', '', 'hours')>
    >>> u2 = URI("http://www.w3.org/People/Sandro/#hours")
    >>> u2 == u
    1
    >>> u2 is u
    1
    >>> print u[2:4]
    tp
    >>> u.startswith("ht")
    1

    """

    def __new__(cls, uri, base=None):
        if base is not None:
            uri = urlparse.urljoin(base, uri, allow_fragments=1)
        global interned
        try:
            return interned[uri]
        except KeyError:
            self = str.__new__(cls, uri)
            self.tuple = urlparse.urlparse(uri, allow_fragments=1)
            interned[uri] = self
            return self
        
    def __init__(self, uri="", base=None):
        pass

    def __str__(self):
        # return self makes python core dump.   so this is a workaround...
        return intern(self+"")
    
    def __repr__(self):
        return "<"+self.__class__.__name__+" "+str(self.tuple)+">"

    def get_racine(self):
        try:
            pos = index(self.uri, "#")
            return self.uri[0:pos]
        except ValueError:
            return
    racine = property(get_racine)
        
    def get_scheme(self):
        return self.tuple[0]
    scheme = property(get_scheme)

    def get_netloc(self):
        return self.tuple[0]
    netloc = property(get_netloc)
 
    def get_path(self):
        return self.tuple[0]
    path = property(get_path)

    def get_params(self):
        return self.tuple[0]
    params = property(get_params)

    def get_query(self):
        return self.tuple[0]
    query = property(get_query)

    def get_fragment(self):
        return self.tuple[0]
    fragment = property(get_fragment)


    

def _test():
    import doctest, LX.URI
    return doctest.testmod(LX.URI) 

if __name__ == "__main__": _test()

# $Log$
# Revision 1.1  2003-02-21 22:12:33  sandro
# first cut
#
# Revision 1.3  2003/02/14 19:39:03  sandro
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
