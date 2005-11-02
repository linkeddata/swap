#! /usr/bin/python
"""
$Id$

term

This module defines objects correspodning to the basic terms in the RDF
and N3 langauges: Symbols, Literals and Lists.  (The N3 language goes on to
include formuale, which are defined elsewhere)

The code in this module deals with the represnetation of these terms and
in debug form (__repr__)

Interning of URIs and strings for storage in SWAP store.

It also defines th utility Namespace module which makes
using terms in practice both more convenient maybe even
more efficient than carrying full URIs around.

Includes:
 - template classes for builtins
"""


from __future__ import generators  # for yield

import string, sys, types

from set_importer import Set, ImmutableSet


import uripath # DanC's tested and correct one
import md5, binascii  # for building md5 URIs

from uripath import refTo
from RDFSink import runNamespace
from local_decimal import Decimal  # for xsd:decimal

LITERAL_URI_prefix = "data:application/rdf+n3-literal;"


from RDFSink import List_NS
from RDFSink import CONTEXT, PRED, SUBJ, OBJ, PARTS, ALL4
from RDFSink import FORMULA, LITERAL, LITERAL_LANG, LITERAL_DT, ANONYMOUS, \
			    SYMBOL, RDF_type_URI
from RDFSink import Logic_NS

from OrderedSequence import merge, intersection, minus

import diag
from diag import progress

from weakref import WeakValueDictionary


import sys
if sys.hexversion < 0x02030000:
    raise RuntimeError("Sorry, this software requires python2.3 or newer.")

########################################  Storage URI Handling
#
#  In general a Term has a URI which may or may not have
# a "#" and fragment identifier.  This code keeps track of URIs
# which are the same up to the hash, so as to make it easy to discover
# for example whether a term is a local identifier within a document
# which we know about.  This is relevant to the URI-spec related processing
# rather than the RDF-spec related processing.
#
# than just a URI.  It has subclasses of Symbol and Fragment.
#
# (libwww equivalent HTParentAnchor and HTChildAnchor IIRC)
#
# Every resource has a symbol table of fragments.
# A resource may (later) have a connection to a bunch of parsed stuff.
#
# We are nesting symbols two deep let's make a symbol table for each resource
#
#  The statement store lists are to reduce the search time
# for triples in some cases. Of course, indexes would be faster.
# but we can figure out what to optimize later.  The target for now
# is being able to find synonyms and so translate documents.


        
class Term(object):
    """The Term object represents an RDF term.
    
    It is interned for speed of processing by the store.
    Every term has a pointer back to its store.
    """
    def __init__(self, store):
        self.store = store
            
    def __repr__(self):
	"""This method only used for debugging output - it can be ambiguous,
	as it is is deliberately short to make debug printout readable.

        output as XML qnames [http://www.w3.org/TR/REC-xml-names/#NT-QName].
        This could be beefed up to guarantee unambiguity.
        """
        s = self.uriref()
        p = string.rfind(s, "#")
	if p<0:  # No hash, use slash
	    p=s.rfind("/", 0, len(s)-2) 
	    # Allow "/" namespaces as a second best, not a trailing one
        if (p>=0 and s[p+1:].find(".") <0 ):
	    # Can't use prefix if localname includes "."
            prefix = self.store.prefixes.get(s[:p+1], None) # @@ #CONVENTION
            if prefix != None : return prefix + ":" + s[p+1:]
	if s.endswith("#_formula"):
	    return "`"+s[-22:-9]+"`" # Hack - debug notation for formula
        if p >= 0: return s[p+1:]
        return s

    def debugString(self, already=[]):
	return `self`  # unless more eleborate in superclass
	
    def representation(self, base=None):
        """The string represnting this in N3 """
        return "<" + self.uriref(base) + ">"
 
    def generated(self):
        """Boolean Is this thing a genid - is its name arbitrary? """
        return 0    # unless overridden
  
    def compareAnyTerm(self, other):
	"""Compare two langauge items
	    This is a cannoncial ordering in that is designed to allow
	    the same graph always to be printed in the same order.
	    This makes the regression tests possible.
	    The literals are deemed smaller than symbols, which are smaller
	    than formulae.  This puts the rules at the botom of a file where
	    they tend to take a lot of space anyway.
	    Formulae have to be compared as a function of their sorted contents.
	    
	    @@ Anonymous nodes have to, within a given Formula, be compared as
	    a function of the sorted information about them in that context.
	    This is not done yet
	    """
	if self is other: return 0
	diff = cmp(self.classOrder(), other.classOrder())
	if diff != 0: return diff
	return self.compareTerm(other)
    

    def asPair(self):
	"""Representation in an earlier format, being phased out 2002/08
	
	The first part of the pair is a constant number represnting the type
	see RDFSink.py.  the second is the value -- uri for symbols,
	string for literals"""
        return (SYMBOL, self.uriref())
    
    def substitution(self, bindings, why=None):
	"Return this or a version of me with subsitution made"
	return bindings.get(self, self)

    def substituteEquals(self, bindings, newRedirections):
	"Return this or a version of me with substitution made"
	return bindings.get(self, self)

    def occurringIn(self, vars):
	if self in vars:
	    return Set([self])
	return Set()

    def value(self):
	"As a python value - by default, none exists, use self"
	return self
    
    def doesNodeAppear(self, symbol):
        """Does that node appear within this one

        This non-overloaded function will simply return if I'm equal to him
        """
        return self == symbol
##
##    def doNodesAppear(self, symbols):
##        return Set([a for a in symbols if a == self])

    def unify(self, other, vars=Set([]), existentials=Set([]),  bindings={}):
	"""Unify this which may contain variables with the other,
	    which may contain existentials but not variables.
	    
	    vars   are variables we want a binding for if matched
	    existentials are things we don't need a binding returned for
	    bindings are those bindings already made in this unification
	    
	    Return 0 if impossible.
	    return [({}, reason] if no new bindings
	    Return [( {var1: val1, var2: val2,...}, reason), ...] if match
	"""
	assert type(bindings) is types.DictType
	if diag.chatty_flag > 97:
	    progress("Unifying symbol %s with %s vars=%s, so far=%s"%
					(self, other,vars, bindings))
	try:
	    x = bindings[self]
	    return x.unify(other, vars, existentials, bindings)
	except KeyError:	    
	    if self is other: return [ ({}, None)]
	    if self in vars|existentials:
		if diag.chatty_flag > 80:
		    progress("Unifying term MATCHED %s to %s"%(self,other))
		return [ ({self: other}, None) ]
	    return 0
	
class ErrorFlag(TypeError, Term):
    __init__ = TypeError.__init__
    __repr__ = TypeError.__str__
    __str__ = TypeError.__str__
#    uriref = lambda s: ':'
    value = lambda s: s

    def classOrder(self):
	return 99


class Node(Term):
    """A node in the graph
    """
    pass

class LabelledNode(Node):
    "The labelled node is one which has a URI."
        
    def compareTerm(self, other):
	"Assume is also a LabelledNode - see function compareTerm in formula.py"
	_type = RDF_type_URI
	s = self.uriref()
	if self is self.store.type:
		return -1
	o = other.uriref()
	if other is self.store.type:
		return 1
	retVal = cmp(s, o)
	if retVal:
            return retVal
	print "Error with '%s' being the same as '%s'" %(s,o)
	raise RuntimeError(
	"""Internal error: URIref strings should not match if not same object,
	comparing %s and %s""" % (s, o))

    def classOrder(self):
	return	6

class Symbol(LabelledNode):
    """   A Term which has no fragment
    """

    def __init__(self, uri, store):
        Term.__init__(self, store)
        assert string.find(uri, "#") < 0, "no fragments allowed: %s" % uri
        assert ':' in uri, "must be absolute: %s" % uri
        self.uri = uri
        self.fragments = WeakValueDictionary()

    def uriref2(self, base):
        assert ':' in base, "base must be absolute: %s" % base
        return refTo(base, self.uri)

    def uriref(self):
#        assert ':' in self.uri, "oops! must be absolute: %s" % self.uri
        return self.uri

    def internFrag(self, fragid, thetype):   # type was only Fragment before
            f = self.fragments.get(fragid, None)
            if f != None:
                if not isinstance(f, thetype):
                    raise RuntimeError(
		    "Oops.. %s exists already but not with type %s"
			%(f, thetype))
                return f    # (Could check that types match just to be sure)
            f = thetype(self, fragid)
            self.fragments[fragid] = f
            return f
                
    def __getitem__(self, lname):
        """get the lname Symbol in this namespace.

        lname -- an XML name (limited to URI characters)
        """
        if lname.startswith("__"): # python internal
            raise AttributeError, lname
        
        return self.internFrag(lname, Fragment)

     
    def dereference(self, mode="", workingContext=None):
	"""dereference an identifier, finding the semantics of its schema if any
	
	Returns None if it cannot be retreived.
	"""
	if hasattr(self, "_semantics"):
            F = self._semantics
        else:
            inputURI = self.uriref()
            if diag.chatty_flag > 20: progress("Web: Looking up %s" % self)
            if "E" not in mode: F = self.store.load(inputURI)
            else:
                try:
                    F = self.store.load(inputURI)
                except:
                #except (IOError, SyntaxError, DocumentAccessError,
		#    xml.sax._exceptions.SAXParseException):
                    F = None
	if F != None:
	    if "m" in mode:
		workingContext.reopen()
		if diag.chatty_flag > 45:
		    progress("Web: dereferenced %s  added to %s" %(
			    self, workingContext))
		workingContext.store.copyFormula(F, workingContext)
	    if "x" in mode:   # capture experience
		workingContext.add(r, self.store.semantics, F)
	if not hasattr(self, "_semantics"):
            setattr(self, "_semantics", F)
	if diag.chatty_flag > 25:
	    progress("Web: Dereferencing %s gave %s" %(self, F))
	return F
		

class Fragment(LabelledNode):
    """    A Term which DOES have a fragment id in its URI
    """
    def __init__(self, resource, fragid):
        Term.__init__(self, resource.store)
        self.resource = resource
        self.fragid = fragid

    def compareTerm(self, other):
        if not isinstance(other, Fragment):
            return LabelledNode.compareTerm(self, other)
        if self is self.resource.store.type:
            return -1
        if other is self.resource.store.type:
            return 1
        if self.resource is other.resource:
            return cmp(self.fragid, other.fragid)
        return self.resource.compareTerm(other.resource)
   
    def uriref(self):
        return self.resource.uri + "#" + self.fragid

    def uriref2(self, base):
        return self.resource.uriref2(base) + "#" + self.fragid

    def representation(self,  base=None):
        """ Optimize output if prefixes available
        """
        return  "<" + self.uriref2(base) + ">"

    def generated(self):
         """ A generated identifier?
         This arises when a document is parsed and a arbitrary
         name is made up to represent a node with no known URI.
         It is useful to know that its ID has no use outside that
         context.
         """
	 return 0   # Use class Anonymous for generated IDs

    def dereference(self, mode="", workingContext=None):
	"""dereference an identifyer, finding the semantics of its schema if any
	
	Returns None if it cannot be retreived.
	"""
	return self.resource.dereference(mode, workingContext)

		
nextId = 0
class AnonymousNode(Node):
    """Has no real URI except when needed for output.
    Goal is to eliminate use of ths URI in the code.
    The URI is however useful as a diagnostic, so we carry it
    when it is given.   It is NOT checked for uniqueness etc.
    This is a superclass of many things, including AnonymousExistential,
    which has a scope."""

    def __init__(self, store, uri=None):
	global nextId
	if uri: assert isinstance(uri, tuple(types.StringTypes))
        Term.__init__(self, store)
	self._diagnosticURI = uri
	nextId += 1
	self.serial = nextId

    def compareTerm(self, other):
	"Assume is also a Formula - see function compareTerm below"
	return cmp(self.serial, other.serial)

    def classOrder(self):
	"""Anonymous ndoes are higher than symbols as the = smushing
	tries to minimize the order rank of the node which it adopts
	as the epresentative node of an equivalence class."""
	return	9

    def uriref(self):
	if self._diagnosticURI: return self._diagnosticURI
	return runNamespace() + "_g" + `self.serial`
#	return runNamespace() + "_b" + `id(self)`
	
    def generated(self):
	return 1

    def asPair(self):
        return (ANONYMOUS, self.uriref())

class AnonymousVariable(AnonymousNode):
    """An anonymous node which is existentially quantified in a given context.
    Also known as a Blank Node, or "bnode" in RDF parlance."""
    def __init__(self, scope, uri=None):
	AnonymousNode.__init__(self, scope.store, uri)
	 
class AnonymousExistential(AnonymousVariable):
    """An anonymous node which is existentially quantified in a given context.
    Also known as a Blank Node, or "bnode" in RDF parlance."""
    pass
	 
class AnonymousUniversal(AnonymousVariable):
    """Nodes which are introduced as universally quantified variables with
    no quotable URI"""
    pass
    
    
##########################################################################
#
#		L I S T S
#
# Lists are interned, so python object comparison works for log:equalTo.
# For this reason, do NOT use a regular init, always use rest.prepend(first)
# to generate a new list form an old, or nil.prepend(first) for a singleton,
# or nil.newList(somePythonList)
# This lists can only hold hashable objects - but we only use hashable objects
#  in statements.
# These don't have much to be said for them, compared with python lists,
# except that (a) they are hashable, and (b) if you do your procesing using
# first and rest a lot, you don't generate n(n+1)/2 list elements when
# traversing (which you probably don't anyway using slices)
#
# Many different implementations are of course possible.
#
_nextList = 0

class CompoundTerm(Term):
    """A compound term has occurrences of terms within it.
    Examples: List, Formula"""
    pass

class N3Set(ImmutableSet, CompoundTerm): #, 
    """There can only be one of every N3Set

    """
    res = {}
    def __init__(self, stuff=[]):
        """something"""
        ImmutableSet.__init__(self, stuff)
    
    def __new__(cls, stuff=[]):
        new_set = ImmutableSet.__new__(cls, stuff)
        new_set.__init__(stuff)
        if new_set in cls.res:
            return cls.res[new_set]
        cls.res[new_set] = new_set
        return new_set

##    def __setattr__(self, attr, value):
##        print "%s=%s" % (`attr`, `value`)
##        ImmutableSet.__setattr__(self, attr, value)
        
    def uriref(self):
        raise NotImplementedError

    def substitution(self, bindings, why=None):
	"Return this or a version of me with variable substitution made"
	if self.occurringIn(bindings.keys()) == Set():
	    return self # phew!

	return self.__class__([x.substitution(bindings, why=why) for x in self])

    def substituteEquals(self, bindings, newBindings):
	"Return this or a version of me with substitution of equals made"
	if diag.chatty_flag > 100:
	    progress("SubstituteEquals list %s with %s" % (self, bindings))
	if self.occurringIn(bindings.keys()) == Set():
	    return self # phew!

	new = self.__class__([x.substitution(bindings, why=why) for x in self])
	newBindings[self] = new
	return new

    def occurringIn(self, vars):
        union = Set.union
        return reduce(union, [x.occurringIn(vars) for x in self], Set())

    def asSequence(self):
        return self

    def classOrder(self):
        return 10

    def compareTerm(self, other):
        """This is annoying

        """
        def my_max(the_set):
            Max = None
            for a in the_set:
                if Max == None or a.compareAnyTerm(Max) > 0:
                    Max = a
            return Max
        s1 = self - other
        s2 = other - self
        max1 = my_max(s1)
        max2 = my_max(s2)
        if max1 is max2: return 0
        if max1 is None: return -1
        if max2 is None: return 1
        return max1.compareAnyTerm(max2)
    
class List(CompoundTerm):
    def __init__(self, store, first, rest):  # Do not use directly
        global _nextList
        Term.__init__(self, store)
        self.first = first
        self.rest = rest
        self._prec = {}
        self._id = _nextList
        _nextList = _nextList + 1

    def uriref(self):
        return runNamespace() + "li"+ `self._id`

    def prepend(self, first):
        x = self._prec.get(first, None)
        if x != None: return x
        x = NonEmptyList(self.store, first, self)
        self._prec[first] = x
        return x

    def __iter__(self):
	"""The internal method which allows one to iterate over the statements
	as though a formula were a sequence.
	"""
	x = self
	while x is not self.store.nil:
	    yield x.first
	    x = x.rest

    def __len__(self):
	"""The internal method which allows one to count the statements
	as though a formula were a sequence.
	"""
	x = self
	i = 0
	while x is not self.store.nil:
	    i = i + 1
	    x = x.rest
	return i

    def value(self):
	res = []
	for x in self:
	    res.append(x.value())
	return res

    def substitution(self, bindings, why=None):
	"Return this or a version of me with variable substitution made"
	if self.occurringIn(bindings.keys()) == Set():
	    return self # phew!
	s = self.asSequence()
	s.reverse()
	tail = self.store.nil
	for x in s:
	    tail = tail.prepend(x.substitution(bindings, why=why))
	if diag.chatty_flag > 90:
	    progress("Substition of variables %s in list %s" % (bindings, self))
	    progress("...yields NEW %s = %s" % (tail, tail.value()))
	return tail
	    
    def substituteEquals(self, bindings, newBindings):
	"Return this or a version of me with substitution of equals made"
	if diag.chatty_flag > 100:
	    progress("SubstituteEquals list %s with %s" % (self, bindings))
	if self.occurringIn(bindings.keys()) == Set():
	    return self # phew!
	s = self.asSequence()
	s.reverse()
	tail = self.store.nil
	for x in s:
	    tail = tail.prepend(x.substituteEquals(bindings, newBindings))
	newBindings[self] = tail # record a new equality
	self.generated = lambda : True
	if diag.chatty_flag > 90:
	    progress("SubstitueEquals list CHANGED %s -> %s" % (self, tail))
	return tail
	    

    def occurringIn(self, vars):
	"Which variables in the list occur in this list?"
	set = Set()
	x = self
	while not isinstance(x, EmptyList):
	    y = x.first
	    x = x.rest
	    import types
	    set = set | y.occurringIn(vars)
	if self in vars:
            set.add(self)
	return set

    def asSequence(self):
	"Convert to a python sequence - NOT recursive"
	res = []
	x = self
	while x is not self.store.nil:
	    res.append(x.first)
	    x = x.rest
	return res
    
    def doesNodeAppear(self, symbol):
        """Does that particular node appear anywhere in this list

        This function is necessarily recursive, and is useful for the pretty
	printer. It will also be useful for the flattener, when we write it.
        """
        for elt in self:
            val = 0
            if isinstance(elt, CompoundTerm):
                val = val or elt.doesNodeAppear(symbol)
            elif elt == symbol:
                val = 1
            else:
                pass
            if val == 1:
                print 'I won!'
                return 1
        return 0
##            
##    def doNodesAppear(self, symbols):
##        val = Set()
##        for elt in self:
##            val.update(elt.doNodesAppear(symbols))
##        return val

class NonEmptyList(List):

    def classOrder(self):
	return	3

    def compareTerm(self, other):
	"Assume is also a NonEmptyList - see function compareTerm in formula.py"
	s = self
	o = other
	while 1:
	    if isinstance(o, EmptyList): return -1
	    if isinstance(s, EmptyList): return 1
	    diff = s.first.compareAnyTerm(o.first)
	    if diff != 0: return diff
	    s = s.rest
	    o = o.rest

    def unify(self, other, vars=Set([]), existentials=Set([]),  bindings={}):
	"""See Term.unify()"""
	if diag.chatty_flag > 90:
	    progress("Unifying list %s with %s vars=%s, so far=%s"%
		    (self.value(), other.value(),vars, bindings))
	if not isinstance(other, NonEmptyList): return 0
	if other is self: return [ ({}, None)]

	# Using the sequence-like properties of lists:
	return unifySequence(self, other, vars, existentials,  bindings)
	
#	nbs = self.first.unify(other.first, vars, existentials, bindings)
#	if nbs == 0: return 0
#	if nbs == [({}, None)]: return self.rest.unify(  #@@   Tail rec to loop
#				other.rest, vars, existentials,  bindings)
#	res = []
#	for nb, reason in nbs:
#	    b2 = bindings.copy()
#	    b2.update(nb)
#	    done = Set(nb.keys())
#	    nbs2 = self.rest.unify(other.rest,
#			vars.difference(done),
#			existentials.difference(done), b2)
#	    if nbs2 == 0: return 0
#	    for nb2, reason2 in nbs2:
#		nb3 = nb2.copy()
#		nb3.update(nb)
#		res.append((nb3, None))
#	return res

    def debugString(self, already=[]):
	s = `self`+" is ("
	for i in self:
	    s = s + i.debugString(already) + " "
	return s + ")"
	
#    def __repr__(self):
#	return "(" + `self.first` + "...)"

    def __getitem__(self, i):
	p = self
	while 1:
	    if i == 0: return p.first
	    p = p.rest
	    if not isinstance(p, NonEmptyList):
		raise ValueError("Index %i exceeds size of list %s"
			% (i, `self`))
	    i = i - 1

class EmptyList(List):
        
    def classOrder(self):
	return	2

    def value(self):
        return []
    
    def uriref(self):
        return List_NS + "nil"

    def substitution(self, bindings, why=None):
	"Return this or a version of me with substitution made"
	return self

    def substituteEquals(self, bindings, newBindings):
	"Return this or a version of me with substitution of equals made"
	return self

    def __repr__(self):
	return "()"
	
    def newList(self, value):
        x = self
        l = len(value)
        if l == 0:
            return x
        try:
            value[0]
        except TypeError:
            for a in value:
                x = x.prepend(a)
        else:
            while l > 0:
                l = l - 1
                x = x.prepend(value[l])
        return x

    def unify(self, other, vars=Set([]), existentials=Set([]),  bindings={}):
	"""Unify the substitution of this using bindings found so far
	    with the other. This may contain variables, the other may contain
	    existentials but not variables.
	    Return 0 if impossible.
	    Return [({}, None)] if no new bindings
	    Return [( {var1: val1, var2: val2, ...}, reason) ...] if match.
	    bindings is a dictionary."""
	assert type(bindings) is type({})
	if self is other: return [({}, None)]
	return 0
	
    def occurringIn(self, vars):
	return Set()

    def __repr__(self):
	return "()"

    def __getitem__(self, i):
	raise ValueError("Index %i exceeds size of empty list %s" % (i, `self`))


class FragmentNil(EmptyList, Fragment):
    " This is unique in being both a symbol and a list"
    def __init__(self, resource, fragid):
	Fragment.__init__(self, resource, fragid)
	EmptyList.__init__(self, self.store, None, None)
	self._asList = self



def unifySequence(self, other, vars=Set([]), existentials=Set([]),  bindings={}, start=0):
    """Utility routine to unify 2 python sequences of things against each other
    Slight optimization to iterate instead of recurse when no binding happens.
    """

    if diag.chatty_flag > 99: progress("Unifying sequence %s with %s" %
	(`self`, `other`))
    i = start
    if len(self) != len(other): return 0
    while 1:
	nbs = unify(self[i], other[i], vars, existentials, bindings)
	if nbs == 0: return 0	 # Match fail
	i = i +1
	if i == len(self): return nbs
	if nbs != [({}, None)]: break   # Multiple bundings
    
    res = []
    for nb, reason in nbs:
	b2 = bindings.copy()
	b2.update(nb)
	done = Set(nb.keys())
	nbs2 = unifySequence(self, other,
		    vars.difference(done),
		    existentials.difference(done), b2, start=i)
	if nbs2 == 0: return 0
	for nb2, reason2 in nbs2:
	    nb3 = nb2.copy()
	    nb3.update(nb)
	    res.append((nb3, None))
    return res
    
def unifySet(self, other, vars=Set([]), existentials=Set([]),  bindings={}):
    """Utility routine to unify 2 python sets of things against each other
    No optimization!  This is of course the graph match function 
    implemented with indexing, and built-in functions, in query.py.
    """
    if diag.chatty_flag > 99: progress("Unifying set %s with %s" %
	(`self`, `other`))
    if len(self) != len(other): return 0    # Match fail
    if self == Set([]): return [ ({}, None) ] # Perfect match
    self2 = self.copy() # Don't mess with parameters
    s = self2.pop()   # Pick one
    for o in other:
	nbs = unify(s, o, vars, existentials, bindings)
	if nbs == 0: continue
	res = []
	other2 = other.copy()
	other2.remove(o)
	for nb, reason in nbs:
	    b2 = bindings.copy()
	    b2.update(nb)
	    done = Set(nb.keys())
	    nbs2 = unifySet(self2, other2,
			vars.difference(done),
			existentials.difference(done), b2)
	    if nbs2 == 0: return 0
	    for nb2, reason2 in nbs2:
		nb3 = nb2.copy()
		nb3.update(nb)
		res.append((nb3, None))
	return res
    return 0
	    
def matchSet(pattern, kb, vars=Set([]),  bindings={}):
    """Utility routine to match 2 python sets of things.
    No optimization!  This is of course the graph match function 
    implemented with indexing, and built-in functions, in query.py.
    This only reuires the first to include the second.
    
    vars are things to be regarded as variables in the pattern.
    bindings map from pattern to kb.
    """
    if diag.chatty_flag > 99: progress("Matching pattern %s against %s, vars=%s" %
	(`pattern`, `kb`, `vars`))
    if len(pattern) > len(kb): return 0    # Match fail  @@@discuss corner cases
    if len(pattern) == 0: return [(bindings, None)] # Success
    
    pattern2 = pattern.copy() # Don't mess with parameters
    o = pattern2.pop()   # Pick one
    for s in kb:   # Really slow recursion unaided by indexes
	nbs = unify(o, s, vars, Set([]), bindings)
	if nbs == 0: continue
	res = []
	kb2 = kb.copy()
	kb2.remove(s)
	for nb, reason in nbs:
	    b2 = bindings.copy()
	    b2.update(nb)
	    done = Set(nb.keys())
	    nbs2 = matchSet(pattern2, kb2, vars.difference(done), b2)
	    if nbs2 == 0: return 0
	    for nb2, reason2 in nbs2:
		nb3 = nb2.copy()
		nb3.update(nb)
		res.append((nb3, None))
	return res
    return 0  # Failed to match the one we picked
	    
def unify(self, other, vars=Set([]), existentials=Set([]),  bindings={}):
    """Unify something whatever it is
    See Term.unify
    """
    if diag.chatty_flag > 100: progress("Unifying %s with %s" %(self, other))
    if isinstance(self, (Set, ImmutableSet)):
	return unifySet(self, other, vars, existentials, bindings)
    if type(self) is type([]):
	return unifySequence(self, other, vars, existentials, bindings)
    return self.unify(other, vars, existentials, bindings)


##########################################################################
#
#		L I T E R A L S

typeMap = { "decimal": Decimal,
                "integer": long,
                    "nonPositiveInteger": long,
                        "negativeInteger": long,
                    "long": int,
                        "int": int,
                            "short": int,
                                "byte": int,
                    "nonNegativeInteger": long,
                        "unsignedLong": int,
                            "unsignedInt": int,
                                "unsignedShort": int,
                                    "unsignedByte": int,
                        "positiveInteger": long,
            "boolean": int,
            "double": float,
            "float": float,
            "duration": unicode,
            "dateTime": unicode,
            "time": unicode,
            "date": unicode,
            "gYearMonth": unicode,
            "gYear": unicode,
            "gMonthDay": unicode,
            "gDay": unicode,
            "gMonth": unicode,
            "anyURI": unicode,
            "QName": unicode,
            "NOTATION": unicode,
            "string": unicode,
                "normalizedunicodeing": unicode,
                    "token": unicode,
                        "language": unicode,
                        "Name": unicode,
                            "NCNAME": unicode,
                                "ID": unicode,
                                "IDREF": unicode,
                                    "IDREFS": unicode,
                                "ENTITY": unicode,
                                    "ENTITIES": unicode,
                        "NMTOKEN": unicode,
                            "NMTOKENS": unicode}
##
## We don't support base64Binary or hexBinary
##
class Literal(Term):
    """ A Literal is a representation of an RDF literal

    really, data:text/rdf+n3;%22hello%22 == "hello" but who
    wants to store it that way?  Maybe we do... at least in theory and maybe
    practice but, for now, we keep them in separate subclases of Term.
    An RDF literal has a value - by default a string, and a datattype, and a
    language.
    """


    def __init__(self, store, str, dt=None, lang=None):
        Term.__init__(self, store)
        self.string = str    #  n3 notation EXcluding the "  "
	self.datatype = dt
	assert dt is None or isinstance(dt, Fragment)
	self.lang=lang

    def __str__(self):
        return self.string

    def __int__(self):
	return int(self.string)

    def __float__(self):
	return float(self.string)

    def __decimal__(self):
        return Decimal(self.string)

    def occurringIn(self, vars):
	return Set()

    def __repr__(self):
        return '"' + self.string[0:8] + '"'
#        return self.string

    def asPair(self):
	if self.datatype:
	    return LITERAL_DT, (self.string, self.datatype.uriref())
	if self.lang:
	    return LITERAL_LANG, (self.string, self.lang)
	return (LITERAL, self.string)
	    
    def classOrder(self):
	return	1

    def compareTerm(self, other):
	"Assume is also a literal - see function compareTerm in formula.py"
	if self.datatype == other.datatype:
	    diff = cmp(self.string, other.string)
	    if diff != 0 : return diff
	    return cmp(self.lang, other.lang)
	else:
	    if self.datatype == None: return -1
	    if other.datatype == None: return 1
	    return self.datatype.compareAnyTerm(other.datatype)

    def asHashURI(self):
        """return a md5: URI for this literal.
        Hmm... encoding... assuming utf8? @@test this.
        Hmm... for a class of literals including this one,
        strictly speaking."""
        x=md5.new()
        x.update(self.string)
        d=x.digest()
        b16=binascii.hexlify(d)
        return "md5:" + b16

    def substitution(self, bindings, why=None):
	"Return this or a version of me with subsitution made"
	return self

    def substituteEquals(self, bindings, newBindings):
	"Return this or a version of me with subsitution made"
	return self

    def representation(self, base=None):
        return '"' + self.string + '"' 
	# @@@ encode quotes; @@@@ strings containing \n

    def value(self):
	"""Datatype conversion XSD to Python
	
	RDF primitive datatypes are XML schema datatypes, in the XSD namespace.
	see http://www.w3.org/TR/xmlschema-2
	"""
	global typeMap
	if self.datatype == None: return self.string
	xsd = self.store.integer.resource
	if self.datatype.resource is xsd:
	    try:
		return typeMap[self.datatype.fragid](self.string)
	    except KeyError:
		raise ValueError(
	  "Attempt to run built-in on unsupported XSD datatype %s of value %s." 
			% (`self.datatype`, self.string))

	raise ValueError("Attempt to run built-in on unknown datatype %s of value %s." 
			% (`self.datatype`, self.string))

    def uriref(self):
        # Unused at present but interesting! 2000/10/14
        # used in test/sameTerm.n3 testing 2001/07/19
        return self.asHashURI() #something of a kludge?
        #return  LITERAL_URI_prefix + uri_encode(self.representation())    # tbl preferred

    def unify(self, other, vars=Set([]), existentials=Set([]),  bindings={}):
	"""Unify this which may contain variables with the other,
	    which may contain existentials but not variables.
	    Return 0 if impossible.
	    Return [(var1, val1), (var2,val2)...] if match"""
	if self is other: return [({}, None)]
	return 0
	

#class Integer(Literal):
#	"""Unused"""
#    def __init__(self, store, str):
#        Term.__init__(self, store)
#	self.datatype = store.integer
#	self.lang=None
#	self._value = int(str)
#
#    def __int__(self):
#	return self._value
#
#    def __str__(self):
#        return str(self._value)
#
#    def __repr__(self):
#        return str(self._value)
#
#    def representation(self, base=None):
#	return str(self._value)
#
#    def value(self):
#	return self._value

#I think I'll replace this with urllib.quote
##def uri_encode(str):
##        """ untested - this must be in a standard library somewhere
##        """
##        result = ""
##        i=0
##        while i<len(str) :
##            if string.find('"\'><"', str[i]) <0 :   # @@@ etc
##                result.append("%%%2x" % (atoi(str[i])))
##            else:
##                result.append(str[i])
##        return result
from urllib import quote as uri_encode



################################################################################
#
#   Built-in master classes
#
# These are resources in the store which have processing capability.
# Each one has to have its own class, and each inherits from various of the
# generic classes below, according to its capabilities.
#
# First, the template classes:
#
class BuiltIn(Fragment):
    """This class is a supercalss to any builtin predicate in cwm.
    
    A binary operator can calculate truth value given 2 arguments"""
    def __new__(cls, *args, **keywords):
        self = Fragment.__new__(cls, *args, **keywords)
        BuiltIn.all.append(self)         # to prevent the forgetting of builtins
        return self
    all = []
    
    def __init__(self, resource, fragid):
        Fragment.__init__(self, resource, fragid)

    def eval(self, subj, obj, queue, bindings, proof, query):
	"""This function which has access to the store, unless overridden,
	calls a simpler one which uses python conventions.
	
	To reduce confusion, the inital ones called with the internals available
	use abreviations "eval", "subj" etc while the python-style ones use
	evaluate, subject, etc."""
	if hasattr(self, "evaluate"):
            if (not isinstance(subj, (Literal, CompoundTerm)) or
			not isinstance(obj, (Literal, CompoundTerm))):
                raise ArgumentNotLiteral(subj, obj)
	    return self.evaluate(subj.value(), obj.value())
	elif isinstance(self, Function):
	    return Function.eval(self, subj, obj, queue, bindings, proof, query)
	elif isinstance(self, ReverseFunction):
	    return ReverseFunction.eval(self, subj, obj, queue, bindings, proof, query)
	raise RuntimeError("Instance %s of built-in has no eval() or subsititue for it" %`self`)

class GenericBuiltIn(BuiltIn):
    def __init__(self, resource, fragid):
        Fragment.__init__(self, resource, fragid)

class ArgumentNotLiteral(TypeError):
    pass
	
class LightBuiltIn(GenericBuiltIn):
    """A light built-in is fast and is calculated immediately before searching the store.
    
    Make your built-in a subclass of either this or HeavyBultIn to tell cwm when to
    run it.  Going out onto the web or net counts as heavy."""
    pass

class RDFBuiltIn(LightBuiltIn):
    """An RDF built-in is a light built-in which is inherent in the RDF model.
    
    The only examples are (I think) rdf:first and rdf:rest which in the RDF model
    are arcs but in cwm have to be builtins as Lists a a first class data type.
."""
    pass

class HeavyBuiltIn(GenericBuiltIn):
    """A heavy built-in is fast and is calculated late, after searching the store
    to see if the answer is already in it.
    
    Make your built-in a subclass of either this or LightBultIn to tell cwm when to
    run it.  Going out onto the web or net counts as Heavy."""
    pass

# A function can calculate its object from a given subject.
#  Example: Joe mother Jane .
class Function(BuiltIn):
    """A function is a builtin which can calculate its object given its subject.
    
    To get cwm to invoke it this way, your built-in must be a subclass of Function.
    I may make changes to clean up the parameters of these methods below some day. -tbl"""
    def __init__(self):
        pass
    

    def evalObj(self, subj, queue, bindings, proof, query):
	"""This function which has access to the store, unless overridden,
	calls a simpler one which uses python conventions.

	To reduce confusion, the inital ones called with the internals available
	use abreviations "eval", "subj" etc while the python-style ones use "evaluate", "subject", etc."""
        if not isinstance(subj, (Literal, CompoundTerm)):
            raise ArgumentNotLiteral
        return self.store._fromPython(self.evaluateObject(subj.value()))


# This version is used by functions by default:

    def eval(self, subj, obj, queue, bindings, proof, query):
	F = self.evalObj(subj, queue, bindings, proof, query)
	return F is obj

class ReverseFunction(BuiltIn):
    """A reverse function is a builtin which can calculate its subject given its object.
    
    To get cwm to invoke it this way, your built-in must be a subclass of ReverseFunction.
    If a function (like log:uri for example) is a two-way  (1:1) builtin, it should be declared
    a subclass of Function and ReverseFunction. Then, cwm will call it either way as needed
    in trying to resolve a query.
    """
    def __init__(self):
        pass

    def eval(self, subj, obj, queue, bindings, proof, query):
	F = self.evalSubj(obj, queue, bindings, proof, query)
	return F is subj

    def evalSubj(self, obj,  queue, bindings, proof, query):
        """This function which has access to the store, unless overridden,
        calls a simpler one which uses python conventions"""
        if not isinstance(obj, (Literal, CompoundTerm)):
            raise ArgumentNotLiteral(obj)
        return self.store._fromPython(self.evaluateSubject(obj.value()))

class MultipleFunction(Function):
    """Multiple return values.
    The preconditions are the same as for Function, that the subject must be bound.
    The result is different, as multiple versions are returned. Example: member of list.
    """
    def evalSubj(self, obj,  queue, bindings, proof, query):
	"""This function which has access to the store, unless overridden,
	calls a simpler one which uses python conventions.
	The python one returns a list of function values.
	This returns a 'new bindings' structure (nbs) which is a sequence of
	(bindings, reason) pairs."""
        if not isinstance(obj, (Literal, CompoundTerm)):
            raise ArgumentNotLiteral(obj)
        return self.store._fromPython(self.evaluateSubject(subj.value()))
#	results = self.store._fromPython(self.evaluateSubject(obj.value()))
#	return [ ({subj: x}, None) for x in results]
    
class MultipleReverseFunction(ReverseFunction):
    """Multiple return values"""
    def evalObj(self, subj,  queue, bindings, proof, query):
        if not isinstance(subj, (Literal, CompoundTerm)):
            raise ArgumentNotLiteral(subj)
        return self.store._fromPython(self.evaluateObject(obj.value()))
#	results = self.store._fromPython(self.evaluateObject(obj.value()))
#	return [ ({subj: x}, None) for x in results]
    
class FiniteProperty(GenericBuiltIn, Function, ReverseFunction):
    """A finite property has a finite set of pairs of (subj, object) values
    
    The built-in finite property can ennumerate them all if necessary.
    Argv is the only useful example I can think of right now.
    """
#    def __init__(self, resource, fragid):
#        Fragment.__init__(self, resource, fragid)
    
    def enn(self):
	" Return list of pairs [(subj, obj)]"
	for s, o in self.ennumerate():
	    yield self.store._fromPython(s), self.store._fromPython(o)
	    
    def ennumerate(self):
	raise RuntimeError("Not implemented fbuilt-in")


    def evalSubj(self, obj,  queue, bindings, proof, query):
	"""This is of course   very inefficient except for really small ones like argv."""
	for s, o in self.ennum():
	    if o is obj: return s
	return None

    def evalObj(self, subj,  queue, bindings, proof, query):
	"""This is of course   very inefficient except for really small ones like argv."""
	for s, o in self.ennum():
	    if s is subj: return o
	return None

    def eval(self, subj, obj, queue, bindings, proof, query):
	"""This is of course   very inefficient except for really small ones like argv."""
	for s, o in self.ennum():
	    if s is subj: return o
	return (subj, obj) in self.ennum()


#  For examples of use, see, for example, cwm_*.py


