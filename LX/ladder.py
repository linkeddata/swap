"""
An immutable object, for which you define the properties at creation time. 

I find it useful for passing along during recursion, when we want only
the path from the root to the current node to be able to affect our
parameters.  Reduces clutter, and allows recursion though
general-purpose functions: as long as they pass along a ladder, they
don't need to know about our particular parameters.

Is this a software pattern?
"""
__version__ = "$Revision$"
# $Id$


class Ladder:
    """An immutable dictionary-style object that's easy to make
    slightly-modified copies of.

    """  

    def __init__(self, *sources):
        """Any dicts, ladders, or pairs of (key, value) are copied
        here

        TODO: move this to __new__, and just return itself if no
        changes -- because called like   x = Ladder((a,b), x)  when
        x already has a key a.
        """
        for source in sources:
            if isinstance(source, self.__class__):
                self.__dict__.update(source.__dict__)
            elif isinstance(source, dict):
                self.__dict__.update(source)
            elif isinstance(source, tuple):
                self.__dict__[source[0]] = source[1]
            else:
                msg = ("cant handle source of type %s class %s" %
                       (type(source), source.__class__))
                raise RuntimeError, msg
                       
    #def __getattr__(self, key):
    #    return self.__dict__.get(key, None)
    # ? Maybe nah, people should use  g.getattr(key, None) instead
    #   or try/catch 
    
    def setIfAbsent(self, key, value):
        """Add this pair if key is not already present; return
        a new object if changes are made.

        x=x.setIfAbsent(a,b)  is the same as   x=Ladder((a,b), x)

        """
        if key in self.__dict__: return self
        return Ladder(self, (key, value))

    def __setattr__(self, name, value):
        # yes, they could go into __dict__ themselves...
        raise RuntimeError, "Immutable Object"

    def has(self, key):
        return key in self.__dict__

    def missing(self, key):
        return key not in self.__dict__

# $Log$
# Revision 1.1  2002-08-29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#
