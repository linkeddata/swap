#! /usr/bin/python
"""
$Id$

Interning of URIs and strings for storage in SWAP store

Includes:
 - template classes for builtins
"""



import string
#import re
#import StringIO
import sys

# import notation3    # N3 parsers and generators, and RDF generator
# import sax2rdf      # RDF1.0 syntax parser to N3 RDF stream

import urllib # for hasContent
import uripath # DanC's tested and correct one
import md5, binascii  # for building md5 URIs

from uripath import refTo

LITERAL_URI_prefix = "data:application/n3;"


from RDFSink import CONTEXT, PRED, SUBJ, OBJ, PARTS, ALL4
from RDFSink import FORMULA, LITERAL, ANONYMOUS, SYMBOL
from RDFSink import Logic_NS

PARTS =  PRED, SUBJ, OBJ
ALL4 = CONTEXT, PRED, SUBJ, OBJ

# The parser outputs quads where each item is a pair   type, value
# But you should not assume that ... use RDFSink.new*()


INFINITY = 1000000000           # @@ larger than any number occurences


# In the query engine we use tuples as data structure in the queue, offsets as follows:
# Queue elements as follows:

STATE = 0
SHORT = 1
CONSTS = 2
VARS = 3
BOUNDLISTS = 4
QUAD = 5

#  Keep a cache of subcontext closure:
subcontext_cache_context = None
subcontext_cache_subcontexts = None

# Allow a strore provdier to register:

store = None
storeClass = None

def setStoreClass(c):
    """Set the process-global class to be used to generate a new store if needed"""
    global storeClass
    storeClass = c

def setStore(s):
    """Set the process-global default store to be used when an explicit store is not"""
    global store
    store = s

def _checkStore(s=None):
    """Check that an explict or implicit stroe exists"""
    global store, storeClass
    if s != None: return s
    if store != None: return store
    assert storeClass!= None, "Some storage module must register with thing.py before you can use it"
    store = storeClass() # Make new one
    return store



def symbol(uri):
    """Create or reuse, in the default store, an interned version of the given symbol
    and return it for future use"""
    return _checkStore().newSymbol(uri)
    
def literal(str):
    """Create or reuse, in the default store, an interned version of the given literal string
    and return it for future use"""
    return _checkStore().newLiteral(str)

def formula():
    """Create or reuse, in the default store, a new empty formula (triple people think: triple store)
    and return it for future use"""
    return _checkStore().newFormula()

def bNode(str, context):
    """Create or reuse, in the default store, a new unnamed node within the given
    formula as context, and return it for future use"""
    return _checkStore().newLiteral(context)

def existential(str, context, uri):
    """Create or reuse, in the default store, a new named variable
    existentially qualified within the given
    formula as context, and return it for future use"""
    return _checkStore().newLiteral(context)

def universal(str, context, uri):
    """Create or reuse, in the default store, a named variable
    universally qualified within the given
    formula as context, and return it for future use"""
    return _checkStore().newLiteral(context)

def load(uri=None, formulaURI=None, remember=1):
    """Get and parse document.  Guesses format if necessary.

    uri:      if None, load from standard input.
    remember: if 1, store as metadata the relationship between this URI and this formula.
    
    Returns:  top-level formula of the parsed document.
    Raises:   IOError, SyntaxError, DocumentError
    """
    return _checkStore().load(uri, formulaURI, remember)


class Namespace(object):
    """A shortcut for getting a symbols as interned by the default store

      >>> RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
      >>> RDF.type
      'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
      >>> RDF.type is RDF.type
      1

    """
    
    def __init__(self, name):
        if ':' not in name:    #, "must be absolute: %s" % name
	    base = uripath.base()
	    name = uripath.join(base, name)
        self._name = name
        self._seen = {}

#    def name(self):				No, org.name must  be a symol in the namespace!
#        return self._name
    
    def __getattr__(self, lname):
        """get the lname Symbol in this namespace.

        lname -- an XML name (limited to URI characters)
	I hope this is only called *after* the ones defines above have been checked
        """
        return _checkStore().intern((SYMBOL, self._name+lname))


########################################  Storage URI Handling
#
#  In general an RDf resource - here a Term, has a uriRef rather
# than just a URI.  It has subclasses of Symbol and Fragment.
# (@@ use/mention error -- DWC)
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


        
class Term:
    """The Term object represents an RDF term.
    
    It is interned for speed of processing by the store.
    """
    def __init__(self, store=None):
        self.store = _checkStore(store)
        store.initTerm(self)

            
    def __repr__(self):
	"""This method only used for debugging output - it can be ambiguous,
	as it is is deliberately short to make debug printout readable.
	@@@ It would be better if it used namespace prefixed."""
        s = self.uriref()
        p = string.find(s,'#')
        if p >= 0: return s[p+1:]
        p = string.find(s,'/')
        if p >= 0: return s[p+1:]
        return s

    def representation(self, base=None):
        """The string represnting this in N3 """
        return "<" + self.uriref(base) + ">"

    def generated(self):
        """Boolean Is this thing a genid - is its name arbitrary? """
        return 0    # unless overridden

    def asList(self):
	"""The interned List object if this is in fact a list, else None.
	
	Lists are interned because they are a form of literal in that
	equal lists are identical.
	(override me!)"""
        return None
  
    def asPair(self):
	"""Representation in an earlier format, being phased out 2002/08
	
	The first part of the pair is a constant number represnting the type
	see RDFSink.py.  the second is the value -- uri for symbols, string for literals"""
        return (SYMBOL, self.uriref())
    


class Symbol(Term):
    """   A Term which has no fragment
    """
    
    def __init__(self, uri, store=None):
        Term.__init__(self, store)
        assert string.find(uri, "#") < 0, "no fragments allowed: %s" % uri
        assert ':' in uri, "must be absolute: %s" % uri
        self.uri = uri
        self.fragments = {}

    def uriref2(self, base):
        assert ':' in base, "base must be absolute: %s" % base
        return refTo(base, self.uri)

    def uriref(self):
        assert ':' in self.uri, "oops! must be absolute: %s" % self.uri
        return self.uri

    def internFrag(self, fragid, thetype):   # type was only Fragment before
            f = self.fragments.get(fragid, None)
            if f != None:
                if not isinstance(f, thetype):
                    raise RuntimeError("Oops.. %s exists already but not with type %s"%(f, thetype))
                return f    # (Could check that types match just to be sure)
            f = thetype(self, fragid)
            self.fragments[fragid] = f
            return f
                
    def internAnonymous(r, fragid):
            f = r.fragments.get(fragid, None)
            if f!= None: return f
            f = Anonymous(r, fragid)
            r.fragments[fragid] = f
            return f
                
                

class Fragment(Term):
    """    A Term which DOES have a fragment id in its URI
    """
    def __init__(self, resource, fragid):
        Term.__init__(self, resource.store)
        self.resource = resource
        self.fragid = fragid
        self._asList = None      # This is not a list as far as we know

    def asList(self):  # Is this a list? (override me!)
        return self._asList
  
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
         return self.fragid[0] == "_"  # Convention for now @@@@@
                                # parser should use seperate class?

class FragmentNil(Fragment):
    pass


class Anonymous(Fragment):
    def __init__(self, resource, fragid):
        Fragment.__init__(self, resource, fragid)

    def generated(self):
        return 1

    def asPair(self):
        return (ANONYMOUS, self.uriref())
        
    
#################################### Lists
#
#  The statement  x p l   where l is a list is shorthand for
#  exists g such that x p g. g first; rest r.
#
# Lists are interned, so python object comparison works for log:equalTo.
# For this reason, do NOT use a regular init, always use rest.precededBy(first)
# to generate a new list form an old, or nil.precededBy(first) for a singleton,
# or internList(somePythonList)
# This lists can only hold hashable objects - but we only use hashable objects
#  in statements.
# These don't have much to be said for them, compared with python lists,
# except that (a) they are hashable, and (b) if you do your procesing using
# first and rest a lot, you don't generate n(n+1)/2 lists when traversing.

_nextList = 0

class List(Term):
    def __init__(self, store, first, rest):  # Do not use directly
        global _nextList
        Term.__init__(self, store)
        self.first = first
        self.rest = rest
        self._prec = {}
        self._id = _nextList
        _nextList = _nextList + 1

    def uriref(self):
        return "http://list.example.org/list"+ `self._id` # @@@@@ Temp. Kludge!! Use run id maybe!

    def asList(self):
        return self    # Allows a list to be used as a Term which is should be really

    def precededBy(self, first):
        x = self._prec.get(first, None)
        if x: return x
        x = List(self.store, first, self)
        self._prec[first] = x
        return x

    def value(self):
        return [self.first] + self.rest.value()

class EmptyList(List):
        
    def value(self):
        return []
    
    def uriref(self):
        return notation3.N3_nil


        
class Literal(Term):
    """ A Literal is a representation of an RDF literal

    really, data:application/n3;%22hello%22 == "hello" but who
    wants to store it that way?  Maybe we do... at least in theory and maybe
    practice but, for now, we keep them in separate subclases of Term.
    """


    def __init__(self, store, string):
        Term.__init__(self, store)
        self.string = string    #  n3 notation EXcluding the "  "

    def __str__(self):
        return self.string

    def __int__(self):
	return int(self.string)

    def __repr__(self):
        return '"' + self.string[0:8] + '"'
#        return self.string

    def asPair(self):
        return (LITERAL, self.string)

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

    def representation(self, base=None):
        return '"' + self.string + '"'   # @@@ encode quotes; @@@@ strings containing \n

    def uriref(self):
        # Unused at present but interesting! 2000/10/14
        # used in test/sameTerm.n3 testing 2001/07/19
        return self.asHashURI() #something of a kludge?
        #return  LITERAL_URI_prefix + uri_encode(self.representation())    # tbl preferred


     
def uri_encode(str):
        """ untested - this must be in a standard library somewhere
        """
        result = ""
        i=0
        while i<len(str) :
            if string.find('"\'><"', str[i]) <0 :   # @@@ etc
                result.append("%%%2x" % (atoi(str[i])))
            else:
                result.append(str[i])
        return result



##################################################################################
#
#   Built-in master classes
#
# These are resources in the store which have processing capability.
# Each one has to have its own class, and eachinherits from various of the generic
# classes below, according to its capabilities.
#
# First, the template classes:
#
class BuiltIn(Fragment):
    """This class is a supercalss to any builtin predicate in cwm.
    
    A binary operator can calculate truth value given 2 arguments"""
    def __init__(self, resource, fragid):
        Fragment.__init__(self, resource, fragid)


class LightBuiltIn(BuiltIn):
    """A light built-in is fast and is calculated immediately before searching the store.
    
    Make your built-in a subclass of either this or HeavyBultIn to tell cwm when to
    run it.  Going out onto the web or net counts as heavy."""
    pass

class HeavyBuiltIn(BuiltIn):
    """A heavy built-in is fast and is calculated late, after searching the store
    to see if the answer is already in it.
    
    Make your built-in a subclass of either this or LightBultIn to tell cwm when to
    run it.  Going out onto the web or net counts as Heavy."""
    pass

# A function can calculate its object from a given subject.
#  Example: Joe mother Jane .
class Function:
    """A function is a builtin which can calculate its object given its subject.
    
    To get cwm to invoke it this way, your built-in must be a subclass of Function.
    I may make changes to clean up the parameters of these methods below some day. -tbl"""
    def __init__(self):
        pass
    
    def evaluate(self, store, context,  subj, subj_py, obj, obj_py):    # For inheritance only
        x = self.evaluateObject( store, context, subj, subj_py)
        return (obj is x)

    def evaluateObject(self, store, context, subj, subj_py):
        raise function_has_no_evaluate_object_method #  Ooops - you can't inherit this.

# This version is used by heavy functions:

    def evaluate2(self, subj, obj, bindings):
        F = self.evaluateObject2(subj)
        return (F is obj) # @@@@@@@@@@@@@@@@@@@@@@@@@@@@ do structual equivalnce thing


# A function can calculate its object from a given subject
class ReverseFunction:
    """A reverse function is a builtin which can calculate its subject given its object.
    
    To get cwm to invoke it this way, your built-in must be a subclass of ReverseFunction.
    If a function (like log:uri for example) is a two-way  (1:1) builtin, it should be declared
    a subclass of Function and ReverseFunction. Then, cwm will call it either way as needed
    in trying to resolve a query.
    
    I may make changes to clean up the parameters of these methods below some day. -tbl"""
    def __init__(self):
        pass

    def evaluate(self, store, context, subj, subj_py, obj, obj_py):    # For inheritance only
        return (subj is self.evaluateSubject(store, context, obj, obj_py))

    def evaluate2(self, subj, obj, bindings):
        F = self.evaluateObject2(obj)
        return (F is subj) # @@@@@@@@@@@@@@@@@@@@@@@@@@@@ do structual equivalnce thing

    def evaluateSubject(self, store, context, obj, obj_py):
        raise reverse_function_has_no_evaluate_subject_method #  Ooops - you can't inherit this.

#  For examples of use, see, for example, cwm_string.py

