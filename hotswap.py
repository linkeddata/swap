#!/usr/bin/env python
"""

This module makes it easy to have hot-swappable software components.

This may be useful if your code needs the services of something
implementing some interface, and you want to be able to change
implementation while running.  If you only wanted to change at the
start of a run, you could just set up your PYTHONPATH (sys.path) to
put the preferred implementations first.  But if you want the user to
have drop-down menu for which algorithm to use, this may simplify your
program.

As an example, consider a long-running program (some kind of agent,
perhaps an IRC bot) which needs a variety of protocol drivers for
speaking to various other agents.  With this hotswap, each time the
program needs to use such a driver after a possible configuration
change, it says something like:

    my_irc_client = hotswap.get(irc.Client)

and it gets an instance of the irc.Client class.  By default,
each time you call "plugins.get(irc.Client)" you will get
the same client instance.

However, you can modify hotswap's list of places to look for drivers.
If you add another place to the front of the list, ...

   hotswap.prepend("/usr/local/irc7/python/irc")

hotswap may return a different instance at the next get() call.  By
default, the constructor for the new instance will be passed a
"copyFrom" parameter so it can extract any useful state from the old
instance.  (This behavior can be controlled with the transferMode
parameter on get()).

A more sophisticated use is to separate the identity of the service
provider from the its features.  Perhaps you need three simultaneous
irc.Client implementations, and one of them has to also be an
irc.DCC_Client.

   client1 = hotswap.get("cl1", interfaces=[irc.Client])
   client2 = hotswap.get("cl2", interfaces=[irc.Client])
   client3 = hotswap.get("cl3", interfaces=[irc.Client, irc.DCC_Client])

Here the service names are arbitrary immutable objects, and interfaces
parameter provides a list of classes which the chosen resulting class
must inherit from.  See get() for all the details on filter featuring,
transferMode control, and passing initialization arguments to new
service providers.

This module offers both a shared interface (as shown above) and also a
HotSwapManager class, which you can use in the unlikely event you want
multiple simultaneous hotswap configurations.


>>> import hotswap
>>> hotswap.prepend("hotswap")
>>> hotswap.prepend("html")
>>> hotswap.prepend("hotswap")
>>> hotswap.prepend("html")
>>> print hotswap.defaultPluginManager.collections
[plugin-collection-module(html), plugin-collection-module(hotswap), plugin-collection-module(html), plugin-collection-module(hotswap)]
>>> hotswap.remove("html")
>>> print hotswap.defaultPluginManager.collections
[plugin-collection-module(hotswap), plugin-collection-module(hotswap)]

>>> hotswap.prepend("html")
>>> print hotswap.get(A, hotswap.A)
>>> print hotswap.get(A, hotswap.B)

"""
import sys
import inspect
import re
from cStringIO import StringIO
from types import ClassType

class Error(RuntimeError):
   pass

class NoMatchFound(RuntimeError):
    def __init__(self, mgr, interfaces):
        self.mgr = mgr
        self.interfaces = interfaces
    def __str__(self):
        s  = StringIO()
        s.write("Nothing in the current hotswap configuration provides the required features.\n")
        nl = "\n   "
        s.write("\nCurrent Locations:"+nl)
        s.write(nl.join(map(str, self.mgr.collections)))
        s.write("\nRequired Interfaces:"+nl)
        s.write(nl.join(map(str, self.interfaces)) + "\n\n")
        return s.getvalue()
    
class CantTransfer(RuntimeError):
    """constructors with copyFrom can throw this, if they want....

    is transferable a feature....  of sorts....?
    """
    pass

def Collection(location):
    """
    Might be a python module (in the path), or a filename (of a python module),
    or a URI (of a python module), or a directory....   ?

    >>> from hotswap import Collection
    >>> p = Collection("hotswap")
    
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
        return "<Module \""+self.location+"\" found at \""+self.module.__file__+"\">"

    def __repr__(self):
        return "plugin-collection-module("+self.location+")"

    
Module.foo = "bar"

def subclass(sub, super):
    #print "subclass",sub,super
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

    >>> import hotswap
    
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
        self.collections.append(Collection(location))

    def remove(self, location):
        i = 0
        while i < len(self.collections):
            if self.collections[i].location == location:
                del self.collections[i]
            else:
                i += 1

    def get(self, service, interfaces=None, properties={}):
        """Return the appropriate service provider.
        
        Return the current instance charged with handling the
        named service, but make sure it can at least handle the given
        features.  This may cause the server to be reinstantiated from
        a new plugin, if the existing one cannot handle the feature,
        or if hotswap have changed to make there be a preferred matching
        one.
        """

        if (interfaces is None and
            properties == {} and
            type(service) is ClassType):
            interfaces = (service,)

        if interfaces is None:
            interfaces = ()

        # look for the first matching Class
        #
        # (we could keep a cache of features-listings -> class,
        # which we invalidated on prepend/delete...)
        #
        matchingClass = None
        # print self.collections
        for c in self.collections:
            #print "Trying collection", c
            for member in inspect.getmembers(c.module):
                #print "   Trying member", member[0]
                failed = 0
                m = member[1]
                if inspect.isclass(m):

                    #print "       isclass"
                    for cf in interfaces:
                        if subclass(m, cf):
                            #print "       subclass", cf
                            continue      # try next feature
                        # missing class-feature cf
                        #print "       FAILED subclass", cf
                        failed = 1
                        break
                    if failed: continue   # try next member
                    
                    for (prop, val) in properties:
                        try:
                            if getattr(m, prop) == val:
                                #print "       has .%s=%s"%(prop,val)
                                continue  # try next feature
                        except AttributeError:
                            pass
                        # missing property/value match
                        #print "       FAILED .%s=%s"%(prop,val)
                        failed = 1
                        break
                    if failed: continue   # try next member

                    # this member passed all the tests!
                    matchingClass = m
                    break      # check no more members
            if matchingClass is not None:
                break     # check no more collections
        
        if matchingClass is None:
            raise NoMatchFound(self, interfaces)
    
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
    """
    Add the given location (a filename, directory name, module name,
    or maybe even URI) at the front (highest preference) of the places
    to look for classes to satisfy a get.
    """
    defaultPluginManager.prepend(location)

def append(location):
    """
    Like prepend, but it puts this location at the back (lowest preference)
    of the list of places to look.
    """
    defaultPluginManager.append(location)

def remove(location):
    """
    Removes this location from the places to look for classes to use
    to satisfy a get.  Will remove all matching entries.
    """
    defaultPluginManager.remove(location)

def get(*arg1, **arg2):
    """
    Return an instance of a dynamically-loaded class which satisifes
    the given feature requirements and maintains state from the previous
    such call.

          hotswap.get(server="cl1",
                      interfaces=[irc.Client, irc.DCC_Client],
                      filters=[lambda(x: ... )],
                      attrs={"foo":"bar", ...},
                      transferMode= "failover" / "nevertry" / "tryonce"
                                    "startfresh"  <- even if no change?
                      
        features={ "interfaces":[...],
                   lambda( ... ) : return value
                   "foo": "bar" }
        initargs=[a, b, c]
        initkwargs={...}
        
    THIS IS NOT QUITE WHAT IS CURRENTLY IMPLEMENTED!!

    the current version is too clever about using kwargs.
    
    """
    return apply(defaultPluginManager.get, arg1, arg2)

   
################################################################

if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])

# $Log$
# Revision 1.2  2003-04-03 05:14:55  sandro
# passes two simple tests
#
# Revision 1.1  2003/04/03 04:51:49  sandro
# fairly stable in skeletal state
#
# (renamed from plugins.py)
#
# Revision 1.2  2003/04/03 00:03:47  sandro
# mostly done!
#
# Revision 1.1  2003/04/02 20:53:13  sandro
# Added skeletal plugin manager
#


#  hotswap.get(Foo, [Spif, Spaf, Spef=Zapf])

#     * classes, or maybe class names sometimes
#     * or pair of attr, value)

#                [Spif, Spaf,

#         .get(serviceClass, otherclass, otherclass, feature=value,
#              feature=value)



