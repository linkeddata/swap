"""Home for Node and Path.

This is rarely needed directly; just use attributes off a KB, as with
kb.getNode().

"""
__version__ = "$Revision$"
# $Id$

from __future__ import generators
import re

import LX

            
if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])
 
# $Log$
# Revision 1.2  2003-08-25 21:10:01  sandro
# general nodepath support
#
# Revision 1.1  2003/08/25 20:29:05  sandro
# broken draft
#

class Node:
    """
         step into multi-path...
         get value

    """

    def __init__(self, kb, term):
        self.kb = kb
        self.fromTerm = term
        self.arcLists = { }

    def __getattr__(self, name):

        # is it a namespace-underscore-name name?
        if name.startswith("is_"):
            name2 = name[3:]
            invert=1
        else:
            name2 = name
            invert=0
        try:
            (pre, post) = name2.split("_", 2)
        except ValueError:
            raise AttributeError, ("no %s attribute" % name)
        ns = getattr(self.kb.ns, pre)
        term = getattr(ns, post)
        result = Path(self, term, invert)
        setattr(self, name, result)   # save the path, don't come to __getattr_ again!
        assert(getattr(self, name) is result)
        return result

    def __repr__(self):
        return "Node"+"("+`self.kb`+","+`self.fromTerm`+")"

    
    def preFill(self, attr, value, term, invert):
        self.arcLists.setdefault((term,invert), []).append(value)

    def dump(self, done):
        """needs shorter names, maybe line breaking, is-of handling, ..."""
        if done.has_key(self):
            return "[loop]"
        done[self] = 1
        result = "[ "
        try:
            result += "= "+self.kb.nickname(self.fromTerm)+"; "
        except: pass
        keytexts = []
        for (key, values) in self.arcLists.iteritems():
            
            try:
                nick = self.kb.nickname(key[0])
                if key[1]:
                    continue
                    nick = "is "+nick+" of"
            except:
                nick = str(key)
            keytext = nick + " "
            valuetexts = []
            for v in values:
                if isinstance(v, Node):
                    valuetexts.append(v.dump(done))
                else:
                    valuetexts.append("<"+`v`+">")
            keytext += ", ".join(valuetexts)
            keytexts.append(keytext)
        result += "; ".join(keytexts)
        result += " ]"

        #print '"'+'"^^<'.join(LX.logic.valuesForConstants[self.fromTerm])+'>',

        return result

    def getValue(self):
        return self.fromTerm

class Path:
    def __init__(self, from_, via, invert):
        self.from_=from_
        self.kb=from_.kb
        self.via=via
        self.invert=invert

    def __getattr__(self, name):

        # is it a namespace-underscore-name name?
        if name.startswith("is_"):
            name = name[3:]
            invert=1
        else:
            invert=0
        try:
            (pre, post) = name.split("_", 2)
        except ValueError:
            raise AttributeError, ("no %s attribute" % name)
        ns = getattr(self.kb.ns, pre)

        return self.stepTo(getattr(ns, post), invert)

    def stepTo(self, term, invert=0):
        return Path(self, term, invert)

    def __repr__(self):
        if self.invert:
            return "Path"+"("+`self.from_`+","+`self.via`+", invert=1)"
        else:
            return "Path"+"("+`self.from_`+","+`self.via`+")"

    def first(self):
        if isinstance(self.from_, Path):
            return self.from_.first()
        return self
    
    def __iter__(self):
        
        # for [the node that is my from_] / [each node in my from_],
        # yield all the nodes at my key (via,invert)....  

        key = (self.via, self.invert)
        
        if isinstance(self.from_, Node):
            for n in self.from_.arcLists.setdefault(key, []):
                yield n
        else:
            for m in self.from_:
                for n in m.arcLists.setdefault(key, []):
                    yield n

    def only(self):
        i = self.__iter__()
        try:
            a = i.next();
        except StopIteration:
            raise KeyError, `self`+" 'only' violation, too few"
        try:
            b = i.next();
            raise KeyError, `self`+" 'only' violation, too many"
        except StopIteration:
            pass
        return a

    def any(self):
        return self.preFilled[0]

    def x(self):
        print "---------------"
        print "I am: ",`self`
        print "I have:",self.preFilled
        self.from_.x()

    def dump(self, done):
        if done.has_key(self):
            print "[loop]"
            return
        done[self] = 1
        print "[ ",
        for sub in self.preFilled:
            print key,
            if isinstance(value, Path):
                value.dump(done)
            else:
                print "<"+`value`+">"
        try:
            print '"'+'"^^<'.join(LX.logic.valuesForConstants[self.fromTerm])+'>',
        except KeyError:
            pass
        print " ]",

#class PathResultIterator:
#    def __init__(self, path):
#        self.path=path
#        
#    def next(self):
#        """Find the next matching node here,..."""
#        raise StopIteration
    
if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])

# $Log$
# Revision 1.2  2003-08-25 21:10:01  sandro
# general nodepath support
#
