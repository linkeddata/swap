#!/usr/bin/env python
"""

You can instantiate your own PluginManager or use the default
shared per-process one.  
"""
import sys
import inspect
import re

class Error(RuntimeError):
   pass

class PluginManager:
    """
    """

    def __init__(self, **attrs):
        """Accept arbitrary keyword arguments and just store
        them for later, so subclasses can have their own easily.
        """
        self.__dict__.update(attrs)

    def prepend(self, location):
        pass

    def append(self, location):
        pass

    def remove(self, location):
        pass

    def plugin(self, service, features=None):
        """Return the appropriate service provider.
        
        Return the current instance charged with handling the
        named service, but make sure it can at least handle the given
        features.  This may cause the server to be reinstantiated from
        a new plugin, if the existing one cannot handle the feature,
        or if plugins have changed to make there be a preferred matching
        one.
        """
        pass


defaultPluginManager = PluginManager()

def prepend(location):
   defaultPluginManager.prepend(location)

def append(location):
   defaultPluginManager.append(location)

def remove(location):
   defaultPluginManager.remove(location)

def plugin(*arg1, **arg2):
   return apply(defaultPluginManager.plugin, arg1, arg2)

   
################################################################

if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])

# $Log$
# Revision 1.1  2003-04-02 20:53:13  sandro
# Added skeletal plugin manager
#
