#! /usr/bin/python
"""
$Id$

Interning of URIs and strings for stporage in SWAP store

Includes:
 - template classes for builtins
"""



import string
import urlparse
#import re
#import StringIO
import sys

import notation3    # N3 parsers and generators, and RDF generator
# import sax2rdf      # RDF1.0 syntax parser to N3 RDF stream

import urllib # for hasContent
import md5, binascii  # for building md5 URIs
urlparse.uses_fragment.append("md5") #@@kludge/patch
urlparse.uses_relative.append("md5") #@@kludge/patch


LITERAL_URI_prefix = "data:application/n3;"

# Should the internal representation of lists be with DAML:first and :rest?
DAML_LISTS = notation3.DAML_LISTS    # If not, do the funny compact ones

# Magic resources we know about

RDF_type_URI = notation3.RDF_type_URI # "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
DAML_equivalentTo_URI = notation3.DAML_equivalentTo_URI


Logic_NS = notation3.Logic_NS

N3_forSome_URI = Logic_NS + "forSome"
#N3_subExpression_URI = Logic_NS + "subExpression"
N3_forAll_URI = Logic_NS + "forAll"

STRING_NS_URI = "http://www.w3.org/2000/10/swap/string#"
META_NS_URI = "http://www.w3.org/2000/10/swap/meta#"

META_mergedWith = META_NS_URI + "mergedWith"
META_source = META_NS_URI + "source"
META_run = META_NS_URI + "run"

# The statement is stored as a quad - affectionately known as a triple ;-)

CONTEXT = notation3.CONTEXT
PRED = notation3.PRED  # offsets when a statement is stored as a Python tuple (p, s, o, c)
SUBJ = notation3.SUBJ
OBJ = notation3.OBJ

PARTS =  PRED, SUBJ, OBJ
ALL4 = CONTEXT, PRED, SUBJ, OBJ

# The parser outputs quads where each item is a pair   type, value

RESOURCE = notation3.RESOURCE        # which or may not have a fragment
FORMULA = notation3.FORMULA          # A set of statements    
LITERAL = notation3.LITERAL          # string etc - maps to data:
ANONYMOUS = notation3.ANONYMOUS     # existentially qualified unlabelled resource
VARIABLE = notation3.VARIABLE



doMeta = 0  # wait until we have written the code! :-)

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

########################################  Storage URI Handling
#
#  In general an RDf resource - here a Thing, has a uriRef rather
# than just a URI.  It has subclasses of Resource and Fragment.
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

        
class Thing:
    def __init__(self, store):
      self.store = store
      store.initThing(self)

#      self.occursAs = None    # Store must set this quad up      
#      self.occursAs = [], [], [], []    # These are special cases of indexes
      #  List of statements in store by part of speech       
            
    def __repr__(self):   # only used for debugging - can be ambiguous!  @@ use namespaces
        s = self.uriref()
        p = string.find(s,'#')
        if p >= 0: return s[p+1:]
        p = string.find(s,'/')
        if p >= 0: return s[p+1:]
        return s

    def representation(self, base=None):
        """ in N3 """
        return "<" + self.uriref(base) + ">"

    def generated(self):
        """  Is this thing a genid - is its name arbitrary? """
        return 0    # unless overridden

    def asList(self):  # Is this a list? (override me!)
        return None
  
    def asPair(self):
        return (RESOURCE, self.uriref())
    


class Resource(Thing):
    """   A Thing which has no fragment
    """
    
    def __init__(self, store, uri):
        Thing.__init__(self, store)
        assert string.find(uri, "#") < 0
        self.uri = uri
        self.fragments = {}

    def uriref(self, base=None):
        if base is self :  # @@@@@@@ Really should generate relative URI!
            return ""
        else:
            return self.uri

    def internFrag(self, fragid, thetype):   # type was only Fragment before
            f = self.fragments.get(fragid, None)
            if f:
                if not isinstance(f, thetype):
                    raise RuntimeError("Oops.. %s existsnot with type %s"%(f, thetype))
                return f    # (Could check that types match just to be sure)
            f = thetype(self, fragid)
            self.fragments[fragid] = f
            return f
                
    def internAnonymous(r, fragid):
            f = r.fragments.get(fragid, None)
            if f: return f
            f = Anonymous(r, fragid)
            r.fragments[fragid] = f
            return f
                
                

class Fragment(Thing):
    """    A Thing which DOES have a fragment id in its URI
    """
    def __init__(self, resource, fragid):
        Thing.__init__(self, resource.store)
        self.resource = resource
        self.fragid = fragid
        self._asList = None      # This is not a list as far as we know

    def asList(self):  # Is this a list? (override me!)
        return self._asList
  
    def uriref(self, base=None):
        return self.resource.uriref(base) + "#" + self.fragid

    def representation(self,  base=None):
        """ Optimize output if prefixes available
        """
        return  "<" + self.uriref(base) + ">"

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
        
class Formula(Fragment):
    """A formula of a set of RDF statements, triples. these are actually
    instances of StoredStatement.  Other systems such as jena use the term "Model"
    for this.  Cwm and N3 extend RDF to allow a literal formula as an item in a triple.
    """
    def __init__(self, resource, fragid):
        Fragment.__init__(self, resource, fragid)
        self.descendents = None   # Placeholder for list of closure under subcontext
        self.cannonical = None # Set to self if this has been checked for duplicates

    def generated(self):
        return 1

    def asPair(self):
        return (FORMULA, self.uriref())

    def existentials(self):
        "we may move to an internal storage rather than these statements"
        exs = []
        ss = self.store._index.get((self, self.store.forSome, self, None),[])
        for s in ss:
            exs.append(s[OBJ])
        if verbosity() > 90: progress("Existentials in %s: %s" % (self, exs))
        return exs

    def universals(self):
        "we may move to an internal storage rather than these statements"
        exs = []
        ss = self.store._index.get((self, self.store.forAll, self, None),[])
        for s in ss:
            exs.append(s[OBJ])
        if verbosity() > 90: progress("Universals in %s: %s" % (self, exs))
        return exs
    
    def variables(self):
        return self.existentials() + self.universals()

#   TRAP:  If we define __len__, then the "if F" will fail is len(F)==0 !!!
#   Rats .. so much for making it more like a list!
    def size(self):
        """ How many statements? """
        return len(self.store._index.get((self, None, None, None), []))

    def matching(self, triple):
        return self.store._index.get((self, triple[0], triple[1], triple[2]), [])
    
    def add(self, triple):
        return self.store.storeQuad((self, triple[0], triple[1], triple[2]))
    
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

class List(Thing):
    def __init__(self, store, first, rest):  # Do not use directly
        global _nextList
        Thing.__init__(self, store)
        self.first = first
        self.rest = rest
        self._prec = {}
        self._id = _nextList
        _nextList = _nextList + 1

    def uriref(self, base=None):
        return "http://list.example.org/list"+ `self._id` # @@@@@ Temp. Kludge!! Use run id maybe!

    def asList(self):
        return self    # Allows a list to be used as a Thing which is should be really

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
    
    def uriref(self, base=None):
        return notation3.N3_nil


        
class Literal(Thing):
    """ A Literal is a data resource to make it clean

    really, data:application/n3;%22hello%22 == "hello" but who
    wants to store it that way?  Maybe we do... at least in theory and maybe
    practice but, for now, we keep them in separate subclases of Thing.
    """


    def __init__(self, store, string):
        Thing.__init__(self, store)
        self.string = string    #  n3 notation EXcluding the "  "

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

    def uriref(self, base=None):
        # Unused at present but interesting! 2000/10/14
        # used in test/sameThing.n3 testing 2001/07/19
        return self.asHashURI() #something of a kludge?
        #return  LITERAL_URI_prefix + uri_encode(self.representation())


     
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
    """ A binary operator can calculate truth value given 2 arguments"""
    def __init__(self, resource, fragid):
        Fragment.__init__(self, resource, fragid)


class LightBuiltIn(BuiltIn):
    pass

class HeavyBuiltIn(BuiltIn):
    pass

# A function can calculate its object from a given subject.
#  Example: Joe mother Jane .
class Function:
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
    
# Use this with diagnostics so that it can be changed as necessary
# For example, sometimes want on stdout maybe or in a scroll window....
def progress(*args):
    import sys
    global chatty_level  # verbosity indent level
    sys.stderr.write(" "*chatty_level)
    for a in args:
        sys.stderr.write("%s " % (a,))
    sys.stderr.write("\n")
#        sys.stderr.write(  str + "\n")

global chatty_flag   # verbosity debug flag
global chatty_level  # verbosity indent level

chatty_level = 0

def setVerbosity(x):
    global chatty_flag
    chatty_flag = x

def verbosity():
    global chatty_flag
    return chatty_flag

def progressIndent(delta):
    global chatty_level
    chatty_level = chatty_level + delta
    return chatty_level
