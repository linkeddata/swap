#!/usr/bin/env python
"""

You can instantiate your own PluginManager or use the default
shared per-process one.  

>>> import plugins
>>> plugins.prepend("plugins")
>>> plugins.prepend("html")
>>> plugins.prepend("plugins")
>>> plugins.prepend("html")
>>> print plugins.defaultPluginManager.collections
[plugin-collection-module(html), plugin-collection-module(plugins), plugin-collection-module(html), plugin-collection-module(plugins)]
>>> plugins.remove("html")
>>> print plugins.defaultPluginManager.collections
[plugin-collection-module(plugins), plugin-collection-module(plugins)]

>>> plugins.prepend("html")
>>> print plugins.get(A, plugins.A)
>>> print plugins.get(A, plugins.B)

"""
import sys
import inspect
import re

class Error(RuntimeError):
   pass

class CantTransfer(RuntimeError):
    """constructors with copyFrom can throw this, if they want....

    is transferable a feature....  of sorts....?
    """
    pass

def Collection(location):
    """
    Might be a python module (in the path), or a filename (of a python module),
    or a URI (of a python module), or a directory....   ?

    >>> from plugins import Collection
    >>> p = Collection("plugins")
    
    """
    if re.match(r"^[a-zA-Z0-9_.]+$", location):
        return Module(location)
    raise Error, "unknown location syntax"

class A: pass
class B: pass
class C(A,B):pass
class D(C, A):pass

class Module:

    baz = "bux"
    
    def __init__(self, location):
        self.location =  location
        self.open()
        for member in inspect.getmembers(self.module):
            if inspect.isclass(member[1]):
                #print "(", member, ")"
                try:
                    #print "***", member[1].__bases__
                    pass
                except AttributeError:
                    #print "no bases for "+str(member)
                    pass
                for m in inspect.getmembers(member[1]):
                    #print m
                    pass
                # print

    def open(self):
        try:
            mod = __import__(self.location)
        except ImportError:
            raise Error, ("Python can't import %s.\nsys.path is currently: %s\n" %
                          ( self.location, sys.path))
        components = self.location.split('.')
        for comp in components[1:]:
            mod = getattr(mod, comp)
        self.module = mod

    def __str__(self):
        return "plugin-collection-module("+self.location+")"
    def __repr__(self):
        return "plugin-collection-module("+self.location+")"

    
Module.foo = "bar"

def subclass(sub, super):
    print "subclass",sub,super
    # class comparison is tricky -- this doesn't seem to match
    # if the same class is imported via two different paths...?
    if sub == super:
        return 1
    for base in sub.__bases__:
        if subclass(base, super):
            return 1
    return 0

class PluginManager:
    """

    >>> import plugins
    
    """

    def __init__(self, **attrs):
        """Accept arbitrary keyword arguments and just store
        them for later, so subclasses can have their own easily ?
        """
        # self.__dict__.update(attrs)
        self.services = { }
        self.collections = [ ]

    def prepend(self, location):
        self.collections.insert(0, Collection(location))

    def append(self, location):
        self.collections.append(0, Collection(location))

    def remove(self, location):
        i = 0
        while i < len(self.collections):
            if self.collections[i].location == location:
                del self.collections[i]
            else:
                i += 1

    def get(self, service, *classFeatures, **propertyFeatures):
        """Return the appropriate service provider.
        
        Return the current instance charged with handling the
        named service, but make sure it can at least handle the given
        features.  This may cause the server to be reinstantiated from
        a new plugin, if the existing one cannot handle the feature,
        or if plugins have changed to make there be a preferred matching
        one.
        """

        # look for the first matching Class
        #
        # (we could keep a cache of features-listings -> class,
        # which we invalidated on prepend/delete...)
        #
        matchingClass = None
        print self.collections
        for c in self.collections:
            print "Trying collection", c
            for member in inspect.getmembers(c.module):
                print "   Trying member", member[0]
                failed = 0
                m = member[1]
                if inspect.isclass(m):

                    print "       isclass"
                    for cf in classFeatures:
                        if subclass(m, cf):
                            print "       subclass", cf
                            continue      # try next feature
                        # missing class-feature cf
                        print "       FAILED subclass", cf
                        failed = 1
                        break
                    if failed: continue   # try next member
                    
                    for (prop, val) in propertyFeatures:
                        try:
                            if getattr(m, prop) == val:
                                print "       has .%s=%s"%(prop,val)
                                continue  # try next feature
                        except AttributeError:
                            pass
                        # missing property/value match
                        print "       FAILED .%s=%s"%(prop,val)
                        failed = 1
                        break
                    if failed: continue   # try next member

                    # this member passed all the tests!
                    matchingClass = m
                    break      # check no more members
            if matchingClass is not None:
                break     # check no more collections
        
        if matchingClass is None:
            raise Error, "no class in any collection matched given features"
    
        # if we have an instance && it is the same Class, return it
        current = self.services.get(service, None)
        if current and current.__class__ is matchingClass:
            return current
        
        # construct a new instance, copied from any existing one
        if current is None:
            new = apply(matchingClass, [])
        else:
            try:
                new = apply(matchingClass, [], { "copyFrom": current })
            except TypeError:
                raise CantTransfer, "Can't switch service '%s' to class %s\nbecause it lacks a copyFrom constructor parameter" % (service, str(matchingClass))

        # save and return it
        self.services[service] = new
        return new


defaultPluginManager = PluginManager()

def prepend(location):
   defaultPluginManager.prepend(location)

def append(location):
   defaultPluginManager.append(location)

def remove(location):
   defaultPluginManager.remove(location)

def get(*arg1, **arg2):
   return apply(defaultPluginManager.get, arg1, arg2)

   
################################################################

if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])

# $Log$
# Revision 1.2  2003-04-03 00:03:47  sandro
# mostly done!
#
# Revision 1.1  2003/04/02 20:53:13  sandro
# Added skeletal plugin manager
#


#  plugins.get(Foo, [Spif, Spaf, Spef=Zapf])

#     * classes, or maybe class names sometimes
#     * or pair of attr, value)

#                [Spif, Spaf,

#         .get(serviceClass, otherclass, otherclass, feature=value,
#              feature=value)



