"""A convenience for handling RDF-style namespaces

TODO: load names from web?
"""
__version__ = "$Revision$"
# $Id$

import LX

class Namespace:
    """
    


    """
    def __init__(self, uri, initialNames=[], strict=True, shortForm=None):
        """Provide the namespace URI (without the trailing #)

        If "strict", then names must be added (here or with add())
        before being used.   shortForm is the conventional short form,
        which need not be unique.
        """
        self.uri = uri
        self.strict = strict
        self.shortForm = shortForm
        for name in initialNames:
            add(name)

    def add(self, name):
        self.__dict__[name] = LX.URIRef(self.uri + "#" + name)

    def __getattr__(self, name):
        if self.strict:
            msg = ("No name %s declared for namespace %s (in strict mode)" %
                   name, self.uri)
            raise AttributeError, msg
        result = LX.URIRef(self.uri + "#" + name)
        self.__dict__[name] = result
        return result


# $Log$
# Revision 1.1  2002-08-29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

 
