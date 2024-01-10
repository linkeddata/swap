"""A convenience for handling RDF-style namespaces

Includes the "ns" object which gives you handy names for
commonly-used RDF namespaces.

>>> from LX.namespace import ns
>>> ns.rdf.type.uri
'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
>>> ns.dc.author.uri
'http://purl.org/dc/elements/1.1/author'

TODO: option for loading names from web
TODO: add in details for "strict" for "ns"

"""
__version__ = "$Revision$"
# $Id$

import LX.logic

class TermHasNoURI(RuntimeError):
    pass
class NoShortNameDeclared(RuntimeError):
    pass
class NotInNamespace(RuntimeError):
    pass

class NamespaceCluster:
    """An object whose attributes (eg rdf, rdfs, foaf, dc, ...) are
    short names for Namespace objects.  
    
    >>> from LX.namespace import Namespace, NamespaceCluster
    >>> ns = NamespaceCluster()
    >>> ns.app1 = Namespace("http://example.com/ns1", strict=0)
    >>> ns.app1.foo.uri
    'http://example.com/ns1#foo'

    """
    def inverseLookup(self, term):
        try:
            uri = term.uri
        except AttributeError as e:
            raise TermHasNoURI(term)
        for (key, value) in self.__dict__.items():
            if uri.startswith(value.uri):
                rest = uri[len(value.uri):]
                if not value.strict:
                    return (key, rest)
                if rest in value.__dict__:
                    return (key, rest)
                else:
                    raise NotInNamespace(term)

        raise NoShortNameDeclared(term)
                    
            

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
    raise NotInNamespace, msg
    NotInNamespace: No name sandro declared for namespace http://www.example.com/friends# (in strict mode)
    >>> ns1.add("sandro")
    >>> ns1.sandro.uri
    'http://www.example.com/friends#sandro'
    >>> ns2 = Namespace("http://www.example.com/friends", strict=0)
    >>> ns2.sandro.uri
    'http://www.example.com/friends#sandro'

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
            raise NotInNamespace(msg)
        result = LX.logic.ConstantForURI(self.uri + name)
        self.__dict__[name] = result
        return result

ns = NamespaceCluster()
ns.rdf  = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns",
                   ["type", "nil", "first", "rest", "XMLLiteral",
                    "Property"])
ns.rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema",
                   ["Resource", "Class", "Datatype", "seeAlso",
                    "label", "comment", "subClassOf", "isDefinedBy",
                    "domain", "range", "subPropertyOf",
                    "ContainerMembershipProperty",
                    ])
ns.xsd = Namespace("http://www.w3.org/2001/XMLSchema#", strict=0)
ns.dc10 = Namespace("http://purl.org/dc/elements/1.0/", strict=0)
ns.dc = Namespace("http://purl.org/dc/elements/1.1/", strict=0)
ns.foaf = Namespace("http://xmlns.com/foaf/0.1/", strict=0)
ns.log = Namespace("http://www.w3.org/2000/10/swap/log#", strict=0)
ns.owl = Namespace("http://www.w3.org/2002/07/owl#", strict=0)
ns.lx   = Namespace("http://www.w3.org/2003/02/04/LX", strict=0)
ns.rtest   = Namespace("http://www.w3.org/2000/10/rdf-tests/rdfcore/testSchema#", strict=0)

if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])


# $Log$
# Revision 1.15  2003-11-07 06:53:05  sandro
# support for running RDF Core tests
#
# Revision 1.14  2003/09/10 20:13:25  sandro
# added rdf:Property
#
# Revision 1.13  2003/09/08 17:30:44  sandro
# added missing exception class
#
# Revision 1.12  2003/09/06 04:49:00  sandro
# made inverse lookup use its own errors
#
# Revision 1.11  2003/09/05 04:38:49  sandro
# a few additional ns elements
#
# Revision 1.10  2003/09/04 07:14:12  sandro
# fixed plain literal handling
#
# Revision 1.9  2003/09/03 21:07:10  sandro
# added rdfs:label, change bnode handling a little
#
# Revision 1.8  2003/08/28 11:35:55  sandro
# removed a debuging "print"; added ns.xsd
#
# Revision 1.7  2003/08/25 18:21:44  sandro
# rolled defaultns.py into namespace.py
#
# Revision 1.6  2003/08/22 20:49:07  sandro
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

 
