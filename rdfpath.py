"""
   rdfpath.py : A Multi-Valued Node-Centric RDF API


   x>>> import rdfpath
   x>>> s = rdfpath.Store()
   x>>> s.ns.bindPrefix("foaf_", "http://xmlns.com/foaf/0.1/")
   x>>> s.ns.bindPrefix("", "http://example.com/")

   alice = s.node(rdf_type=ns.foaf_Person, foaf_nick="Al1ce")

   x>>> alice = s.node(foaf_nick="Al1ce")
   x>>> bob = s.node(foaf_knows=alice)
   x>>> charlie = s.node(foaf_knows=alice)
   x>>> alice.foaf_knows << bob
   x>>> alice.foaf_knows << charlie
   x>>> print s.values(alice.foaf_knows)
   
"""

from cStringIO import StringIO

class NameMapper:

    """Handles the conversion between URIs (external names) and
    shorter, more convenient (internal) names which also fit into the
    Python name syntax.

    Has two API styles: normal and hack.   The hack style takes
    advantage of the fact that internal names look like python
    attributes.   So in the normal style you say

        >>> import rdfpath
        >>> n = rdfpath.NameMapper()
        >>> n.bindPrefix("rdf_", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")

    while in the hack style you say

        >>> n.rdf_ = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"

    Similarly for using it, you say

        >>> print n.externalize("rdf_foo")
        http://www.w3.org/1999/02/22-rdf-syntax-ns#foo
        
    or

        >>> print n.rdf_foo
        http://www.w3.org/1999/02/22-rdf-syntax-ns#foo

    But look -- that's still just the STRING, not the NODE.  It's NOT
    what end users want.

    todo:
      + sanity checking name syntax
      + compile it into a regexp

    x>>> n.bindExact("foo", "http://example.com/foo")
    x>>> print n,
    xExact bindings:
    x-  foo              http://example.com/foo
    xPrefix bindings:
    x-  rdf_             http://www.w3.org/1999/02/22-rdf-syntax-ns#
    x>>> print n.rdf_x
    xhttp://www.w3.org/1999/02/22-rdf-syntax-ns#x
    x>>> print n.internalize("http://www.w3.org/1999/02/22-rdf-syntax-ns#bar")
    xrdf_bar
    
      
    """

    def __getattr__(self, attr):
        return self.externalize(attr)

    def __setattr__(self, attr, value):
        if attr.endswith("_"):
            self.bindPrefix(attr, value)
        else:
            self.bindExact(attr, value)

    def __init__(self):
        # access via __dict__ to bypass __setattr__ hook
        # alternative: could use leading underscore
        self.__dict__["pairs"] = []
        self.__dict__["prefixPairs"] = []
        self.__dict__["re"] = None
    
    def bindPrefix(self, internalNamePrefix, externalNamePrefix):
        self.prefixPairs.append((internalNamePrefix, externalNamePrefix))

    def bindExact(self, internalName, externalName):
        self.pairs.append((internalName, externalName))

    def externalize(self, internalName):
        for (i, e) in self.pairs:
            if i == internalName:
                return e
        for (i, e) in self.prefixPairs:
            if internalName.startswith(i):
                rest=internalName[len(i):]
                return e+rest
        raise RuntimeError

    def internalize(self, externalName):
        for (i, e) in self.pairs:
            if e == externalName:
                return i
        for (i, e) in self.prefixPairs:
            if externalName.startswith(e):
                rest=externalName[len(e):]
                return i+rest
        raise RuntimeError

    def __str__(self):
        s = StringIO()
        s.write("Exact bindings:\n")
        for (i, e) in self.pairs:
            s.write("-  %-16s %s\n" % (i, e))
        s.write("Prefix bindings:\n")
        for (i, e) in self.prefixPairs:
            s.write("-  %-16s %s\n" % (i, e))
        return s.getvalue()

uri = "http://the-uri-predicate.example.com"

sharedNS = NameMapper()
sharedNS.bindPrefix("rdf_", "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
sharedNS.uri = uri
sharedNS.eg_ = "http://example.com/"

class Store(list):
    """A trivial implementation of an RDF store, for testing
    and to define the API we expect from a store.

    """
    def __init__(self, nameMapper=sharedNS):
        self.triples = []
        self.nameMapper = nameMapper
        # self.ns = NameMappingHack(self)   #  s.ns.rdf_type is the node
        self.nodeByURI = { }    # sync with URI predicate???
        
    def node(self, **kwargs):
        """Obtain a Node to stand for something.

        Optional keyword arguments are property/value pairs for the
        something, with the keyword being the internal form (via
        nameMapper) of the actual property URI.

        The URI property is especially commonly used.   If you call
        node twice giving the same URI property, you'll get back the
        same Node.   At some point we might return an existing Node
        do to other inferrable equalities.

           >>> import rdfpath
           >>> s = rdfpath.Store()
           >>> p1 = s.node(uri="http://www.w3.org")
           >>> p2 = s.node(uri="http://www.w3.org", eg_quality="good")
           >>> p1 is p2
           1
           >>> print s
           
        """
        
        myURI = None
        todo = []

        for (key, value) in kwargs.iteritems():
            predicateURI = self.nameMapper.externalize(key)
            if predicateURI == uri:
                myURI = value
            todo.append((predicateURI, value))
        if myURI:
            node = self.nodeWithURI(myURI)
        else:
            node = Node()

        for (p,v) in todo:
            self.add((node, self.nodeWithURI(p), v))


    def nodeWithURI(self, uri):
        """Lower level, roughly equiv to .node(uri="...") but
        that uri keyword is really a python keyword here."""
        try:
            return self.nodeByURI[uri]
        except:
            node = Node()
            self.nodeByURI[uri] = node
            return node

    def add(self, other):
        assert(len(other)==3)
        assert(isinstance(other[0], Node))      # iffy
        assert(isinstance(other[1], Node))      # iffy
        
        # skip it if it's there already?   eh.
        self.append(other)
        
    def __iadd__(self, other):
        return self.add(other)

    # externalize this one?
    def appendToCollection(self, collection, item):
        raise NotImplemented
    

class PathStep:

    def __init__(previous, predicate):
        this._previous = previous
        this._predicate = predicate
        
    def getStore(self):
        pass

    def getValues(self):
        """
        
        " or     sto.getValues(path)  ? "
             x in a.b.getValues()
                   if a.b >> x

        """
        pass
    
nodenumber=0

class Node:

    def __init__(self):
        global nodenumber
        self.nodenumber = nodenumber
        nodenumber += 1
        
    def __getattr__(self, other):
        """
       
        """
        return Tree(prior=self, prop=other)

    def __repr__(self):
        return "n#"+str(self.nodenumber)



## ****************************************************************




## only    getValues()   is special on multinode
##         getStore()
## everything else is run through nameMapper to turn
## into a URI

## class Node:

##     def values(self):
##         yield self
##         ...no
        

## class MultiNode:

##     def __rshift__(self, other):
        

##     def __getattr__(self, other):
##         """
##         return a new multi chained off this one.
##         """
##         return MultiNode(prior=self, prop=other)

##     def __setattr__(self, other):
##         raise RuntimeError, "use << or declare property as single-valued"

##     def getValues(self):
##         for prior in self._prior.getValues():
##             for (s,p,o) in self._store.match(prior, self.prop, None):
##                 yield o


## """





##    >>> eric.friend << sandro
##    >>> eric.friend.name.familyPart << "Hawke"

##    # but that could be a different friend

##    eric.friend = sandro               friend is functional
##  THEN  eric.friend   is a Node
##  otherwise it's a MultiNode

##      eric.friend.name   is then another MultiNode
##                         (containing ?y such that eric friend ?x
##                                                  ?x name ?y)
##       eric.friend.name = foo
##                means friend is functional,
##                name is functional,
##                and the value is foo

##       eric.friend.name << foo     means ?y has another possible value

##       eric.friend.name >> bar     collects the known values into bar.
      

##    Multi
##       <<
##       >>
##       getattr
##          breeds a longer multi
##       setattr
##          collapses, give single value.
##          collapse may cause equalities to be inferred.

##     MAYBE you have to declare which terms are functional
##     and use them that way or not.
   
## """

## class Node:

##     def __init__(self, store, **kwargs):
##         self._store = store
##         for (p, v) in kwargs:
##             self._store << (self, p, v)
    
##     def __rshift__(self, other):
##         self._store.appendToCollection(self, v)

##     def __getattr__(self, prop):
##         nodes = []
##         for (s,p,v) in self._store:    # move this over to store
##             if s is self and p is prop:
##                 nodes.append(v)
##         return MultiNode(nodes)

##     def __setattr__(self, prop):
##         raise RuntimeError, "use << instead"
    
## class MultiNode:

##     def __iter__(self):
##         for x in self.nodes:
##             yield x

##     def __rshift__(self, other):
##         " is this what we want...? "
##         raise NotImplemented
##         #for x in self.nodes:
##         #    self._store.appendToCollection(x, v)


## class MultiPath:

##     def __iter__(self):
##         traverse store, and find all matching nodes.

##     def __rshift__(self, other):
##         add triple...

##     def __getattr__(self, prop):
##         return longer multi-path

if __name__ =='__main__':
    print "Performing doctest..."
    import doctest, sys
    doctest.testmod(sys.modules[__name__])
    print "Done."

# $Log$
# Revision 1.1  2003-05-01 04:34:14  sandro
# first checkin; getting stabler
#
