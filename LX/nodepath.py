"""Home for Node and Path.

This is rarely needed directly; just use attributes off a KB, as with
kb.getNode().


WISDOM:

   - it's nice to have versions of Terms which are attached to
     a particular KB
   - a Path is really just a kind of Query
   - it's unclear whether preFilling, even if we prefilled
     __dict__, would be any faster than generic Query.  The
     difference depends on python internals, and whether lookup
     in a large hash table is really slower than in a small one.
     TRY IT.

"""
__version__ = "$Revision$"
# $Id$


import re
import LX


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
            raise AttributeError("no %s attribute" % name)
        ns = getattr(self.kb.ns, pre)
        term = getattr(ns, post)
        result = Path(self, term, invert)
        setattr(self, name, result)   # save the path, don't come to __getattr_ again!
        # assert(getattr(self, name) is result)
        return result

    def __str__(self):
        try:
            name =  self.kb.nickname(self.fromTerm)
        except LX.namespace.NoShortNameDeclared as error:
            name = "Node("+str(self.fromTerm)+")"
        except LX.namespace.TermHasNoURI as error:
            name = "Node("+str(self.fromTerm)+")"
        done = {}
        return name+" -- "+self.dump(done)

    def __repr__(self):
        return "Node"+"("+repr(self.kb)+","+repr(self.fromTerm)+")"

    
    def preFill(self, attr, value, term, invert):
        #print "preFill", self, attr, value, term, invert
        self.arcLists.setdefault((term,invert), []).append(value)
        #l = self.arcLists[(term,invert)]
        # assert(value == l[len(l)-1])
        #print "preFilled to: ", self.arcLists[(term,invert)]
        #print 

    def dump(self, done):
        """needs shorter names, maybe line breaking, is-of handling, ..."""
        if self in done:
            return "[loop]"
        done[self] = 1
        result = "[ "
        try:
            result += "= "+self.kb.nickname(self.fromTerm)+"; "
        except: pass
        keytexts = []
        # keytexts.append("**"+str(self.arcLists))
        for (key, values) in self.arcLists.items():
            
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
                    valuetexts.append("<"+repr(v)+">")
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


        if name == "data": return self.dataGetOnly()
        if name == "uri": return self.uriGetOnly()

        # is it a namespace-underscore-name name?
        if name.startswith("is_"):
            name = name[3:]
            invert=1
        else:
            invert=0
        try:
            (pre, post) = name.split("_", 2)
        except ValueError:
            raise AttributeError("no %s attribute" % name)
        ns = getattr(self.kb.ns, pre)

        return self.stepTo(getattr(ns, post), invert)

    def stepTo(self, term, invert=0):
        return Path(self, term, invert)

    def __str__(self):
        return str(self.from_)+"."+self.kb.nickname(self.via)

    def __repr__(self):
        if self.invert:
            return "Path"+"("+repr(self.from_)+","+repr(self.via)+", invert=1)"
        else:
            return "Path"+"("+repr(self.from_)+","+repr(self.via)+")"

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
                #    if there are none, we shouldn't have gotten here?
                #for n in self.from_.arcLists[key]:
                yield n
        else:
            for m in self.from_:
                for n in m.arcLists.setdefault(key, []):
                    #for n in m.arcLists[key]:
                    yield n

    def only(self):
        i = self.__iter__()
        try:
            a = next(i);
        except StopIteration:
            raise KeyError(repr(self)+" 'only' violation, too few")
        try:
            b = next(i);
            raise KeyError(repr(self)+" 'only' violation, too many")
        except StopIteration:
            pass
        return a

    def any(self):
        return self.preFilled[0]

    def uriGetOnly(self):
        uri = None
        for node in self:
            if uri is None:
                uri = node.fromTerm.uri
            else:
                if uri != node.fromTerm.uri:
                    raise KeyError('more than one value for URI')
        if uri is None:
            raise KeyError('no value for URI')
        return uri

    # this doesnt work because we have a __getattr_ defined
    #uri = property(uriGetOnly)
        
    def dataGetOnly(self):
        data = None
        for node in self:
            if data is None:
                data = node.fromTerm.data
            else:
                if data != node.fromTerm.data:
                    raise KeyError('more than one value for DATA')
        if data is None:
            raise KeyError('no value for DATA')
        return data

    def x(self):
        """test"""
        print("---------------")
        print("I am: ",repr(self))
        print("I have:",self.preFilled)
        self.from_.x()

    def dump(self, done):
        """broken"""
        if self in done:
            print("[loop]")
            return
        done[self] = 1
        print("[ ", end=' ')
        for sub in self.preFilled:
            print(key, end=' ')
            if isinstance(value, Path):
                value.dump(done)
            else:
                print("<"+repr(value)+">")
        try:
            print('"'+'"^^<'.join(LX.logic.valuesForConstants[self.fromTerm])+'>', end=' ')
        except KeyError:
            pass
        print(" ]", end=' ')

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
# Revision 1.6  2003-09-17 17:19:37  sandro
# remove really really slow asserts
#
# Revision 1.5  2003/09/06 04:48:08  sandro
# added some "wisdom" comments
#
# Revision 1.4  2003/09/06 04:45:04  sandro
# nicer (?  longer at least) printing, arcList assertion
#
# Revision 1.3  2003/08/28 11:44:43  sandro
# * added nickname-based __str__ functions
# * added .uri and .data to paths, as a smarter only().uri, etc.
#
# Revision 1.2  2003/08/25 21:10:01  sandro
# general nodepath support
#
# Revision 1.1  2003/08/25 20:29:05  sandro
# broken draft
#
