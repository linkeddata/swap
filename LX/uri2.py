"""URI Class

"""
__version__ = "$Revision$"
# $Id$

import urlparse
import urllib

interned = { }

class URI(object):      #inherit from object so __new__ can be used

    # This implementation is overdone

    #   use    .intern    to access interned versions
    #   and dont rely on "is", but == and hash okay

    #  ParsedURI
    
    
    """A URI (aka URL) is a structure used to identify something in a
    global, standard way.

    URIs are serialized as strings, with a structure defined by
    RFC 2396, but for convenience here we break them apart into
    unserialized form as well.

    URIs are immutable, interned objects.  You can rely on the fact
    that for any string x, "URI(x) is URI(x)", and use URI(x) as a
    dictionary key.

    See MutableURI for the complementary class allowing the parts to
    be changed around.    m=MutableURI(u), m.scheme="https", etc

    Note on Inheritance: we could inherit from "str" or "unicode",
    since a URI (eg http://www.w3.org) is in fact a sequence of
    characters, but in some sense the URI is more abstract than the
    string.  Since it would be easier to add this inheritance later
    than to remove it, we'll avoid it for now and say if you want the
    string text, use u.text.  That may also give us more flexibility
    in dealing with IRI issues.

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
    >>> print u.text[2:4]
    tp
    >>> u.text.startswith("ht")
    1
    >>> u.fragment
    'hours'

    Use __slots__ instead of propert()?
    Use getattr or getattribute ?
    
    """

    # use __new__ instead of __init__ so we can do automatic interning
    def __new__(cls, text, base=None):   
        if base is not None:
            text = urlparse.urljoin(base, text, allow_fragments=1)
        global interned
        try:
            return interned[text]
        except KeyError:
            self = object.__new__(cls)
            self.__text = text
            self.__tuple = urlparse.urlparse(text, allow_fragments=1)
            interned[text] = self
            return self
        
    def __init__(self, text="", base=None):
        pass

    def __str__(self):
        return self.__text
    
    def __repr__(self):
        return "<"+self.__class__.__name__+" "+str(self.__tuple)+">"

    # http://www.textuality.com/tag/uri-comp-4.html
    #    def equiv1(self, other):
    #def equiv2(self, other):
    #def equiv3(self, other):       query parms
    #   vs   normalized....
    #

    # do this, or just have   wc = WebClient();   wc.get(URI(x))
    #     using URI() makes sense in avoiding reparsing, etc.
    #     this is where we could load scheme-specific handlers, too.
    #def GET(self, cookies=None, accept="*/*"):
    #    pass
    
    
    def getText(self):
        return self.__text
    text = property(getText)

    def get_racine(self):
        # should racine be a URI?      "defrag"?    prefrag ?
        try:
            pos = index(self.__, "#")
            return self.uri[0:pos]
        except ValueError:
            return
    racine = property(get_racine)
        
    def get_scheme(self):
        return self.__tuple[0]
    scheme = property(get_scheme)

    def get_netloc(self):
        return self.__tuple[1]
    netloc = property(get_netloc)
 
    def getPathText(self):
        """
        >>> from URI import URI
        >>> print URI("http://www.w3.org/People/Sandro").pathText
        /People/Sandro
        >>> print URI("http://www.w3.org/People/Sandro/").pathText
        /People/Sandro/
        """
        return self.__tuple[2]
    pathText = property(getPathText)

    def getPath(self):
        """Gives you a tuple of the path parts, with URI-unquoting
        done, since we no longer need it.

        >>> from URI import URI
        >>> print URI("http://www.w3.org/People/Sandro").path
        ('People', 'Sandro')
        >>> print URI("http://www.w3.org/People/Sandro/").path
        ('People', 'Sandro', '')
        >>> print URI("http://www.w3.org/People/Sandro%2f").path
        ('People', 'Sandro/')
        >>> print URI("http://www.w3.org/People/Sandro%252f").path
        ('People', 'Sandro%2f')

        """
        try:
            return self.__path_parts
        except AttributeError:
            pp = self.__tuple[2]
            if pp == "" or pp == "/":
                p = ()
            else:
                assert(pp[0:1] == "/")
                p = pp[1:].split("/")
                p = tuple(map(urllib.unquote, p))
                self.__path_parts = p
            return p
            
    path = property(getPath)

    def get_params(self):
        return self.__tuple[3]
    paramsText = property(get_params)

    def get_query_text(self):
        return self.__tuple[4]
    queryText = property(get_query_text)

    def getQuery(self):
        """Gives you a tuple of the path parts, with URI-unquoting
        done, since we no longer need it.

        >>> from URI import URI
        >>> print URI("http://example.com").query
        {}
        >>> print URI("http://example.com/?").query
        {}
        >>> m = URI("http://example.com/?color=blue&size=extra+large").query
        >>> print m == {'color': 'blue', 'size': 'extra large'}
        1

        Is this a but in urlparse, or how it should be?
        >>> print `URI("http://example.com?color=blue&size=extra+large")`
        <URI ('http', 'example.com?color=blue&size=extra+large', '', '', '', '')>

        NOTE: should return immutable dict, but I don't know an easy
        way to do that.
        """

        try:
            return self.__query_parts
        except AttributeError:
            pp = self.queryText
            if pp == "": 
                m = {}
            else:
                p = pp.split("&")
                m = {}
                for pair in p:
                    (t,v) = pair.split('=')
                    t = urllib.unquote_plus(t)
                    v = urllib.unquote_plus(v)
                    m[t] = v
                self.__query_parts = m
            return m

    """The query stuff.  Does this text appear anywhere?"""
    query = property(getQuery)

    def get_fragment(self):
        return self.__tuple[5]
    fragment = property(get_fragment)


    

def _test():
    import doctest, LX.URI
    return doctest.testmod(LX.URI) 

if __name__ == "__main__": _test()

# $Log$
# Revision 1.1  2003-03-21 02:24:54  sandro
# moving URI.py to uri.py
#
# Revision 1.1  2003/02/21 22:12:33  sandro
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
