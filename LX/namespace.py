"""A convenience for handling RDF-style namespaces

TODO: load names from web?

See modules defaultns.py for some uses.

"""
__version__ = "$Revision$"
# $Id$

#import LX.uri
import LX.logic

class NamespaceCluster:
    """
    Use like ns.rdf.type 
    """
    def inverseLookup(self, term):
        uri = term.uri
        for (key, value) in self.__dict__.iteritems():
            if uri.startswith(value.uri):
                rest = uri[len(value.uri):]
                if not value.strict:
                    return (key, rest)
                print "REST", rest
                if rest in value.__dict__:
                    return (key, rest)
                else:
                    print "NamespaceCluster inverselookup not-matched due to strict"
        raise KeyError
                    
            

class Namespace:
    """
    
    >>> from LX.namespace import *
    >>> ns1 = Namespace("http://www.example.com/friends")
    >>> print ns1.sandro
    Traceback (most recent call last):
    File "/usr/local/lib/python2.2/doctest.py", line 430, in _run_examples_inner
    compileflags, 1) in globs
    File "<string>", line 1, in ?
    File "/home/sandro/0/10/swap/LX/namespace.py", line 46, in __getattr__
    raise AttributeError, msg
    AttributeError: No name sandro declared for namespace http://www.example.com/friends (in strict mode)
    >>> ns1.add("sandro")
    >>> print ns1.sandro
    <http://www.example.com/friends#sandro>
    >>> ns2 = Namespace("http://www.example.com/friends", strict=0)
    >>> print ns2.sandro
    <http://www.example.com/friends#sandro>

    """
    def __init__(self, uri, initialNames=[], strict=1, shortForm=None):
        """Provide the namespace URI (without the trailing #)

        If "strict", then names must be added (here or with add())
        before being used.   shortForm is the conventional short form,
        which need not be unique.
        """
        if uri.endswith("#") or uri.endswith("/") or uri.endswith("?"):
            self.uri = uri
        else:
            self.uri = uri+"#"
        self.strict = strict
        self.shortForm = shortForm
        for name in initialNames:
            self.add(name)

    def add(self, name):
        self.__dict__[name] = LX.logic.ConstantForURI(self.uri + name)

    def __getattr__(self, name):
        if self.strict:
            msg = ("No name %s declared for namespace %s (in strict mode)" %
                   (name, self.uri))
            raise AttributeError, msg
        result = LX.logic.ConstantForURI(self.uri + name)
        self.__dict__[name] = result
        return result


# $Log$
# Revision 1.6  2003-08-22 20:49:07  sandro
# generalized ns and reconstructor, for second use (2003/08/owl-systems)
#
# Revision 1.5  2003/08/20 09:26:48  sandro
# update --flatten code path to work again, using newer URI strategy
#
# Revision 1.4  2003/02/14 19:39:03  sandro
# adopted smart <...> syntax
#
# Revision 1.3  2003/02/13 19:28:10  sandro
# Changed URI dependency a bit, added some tests
#
# Revision 1.2  2002/08/29 16:39:55  sandro
# fixed various early typos and ommissions; working on logic bug which is manifesting in description loops
#
# Revision 1.1  2002/08/29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

 
