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
            
    def __repr__(self):   # only used for debugging I think
        return self.representation()

    def representation(self, base=None):
        """ in N3 """
        return "<" + self.uriref(base) + ">"

    def generated(self):
        """  Is this thing a genid - is its name arbitrary? """
        return 0    # unless overridden

    def definedAsListIn(self):  # Is this a list? (override me!)
        return None
  
    def asPair(self):
        return (RESOURCE, self.uriref(None))
    

    # Use the URI to allow sorted listings - for cannonnicalization if nothing else
    #  Put a type declaration before anything else except for strings
    
def compareURI(self, other):
        if self is other: return 0
        if isinstance(self, Literal):
            if isinstance(other, Literal):
                return cmp(self.string, other.string)
            else:
                return -1
        if isinstance(other, Literal):
            return 1
        # Both regular URIs
        _type = "<" + notation3.RDF_type_URI + ">"
        s = self.representation()
        if s == _type:
            return -1
        o = other.representation()
        if o == _type:
            return 1
        if s < o :
#            print s,  "LESS THAN", o
            return -1
        if s > o :
#            print s, "GREATER THAN", o
            return 1
        print "Error with '%s' being the same as '%s'" %(s,o)
        raise internalError # Strings should not match if not same object

def compareFormulae(self, other):
    """ This algorithm checks for equality in the sense of structural equivalence, and
    also provides an ordering which allows is to render a graph in a canonical way.
    This is a form of unification.

    The steps are as follows:
    1. If one forumula has more statments than the other, it is greater.
    2. The variables of each are found. If they have different number of variables,
       then the ine with the most is "greater".
    3. The statements of both formulae are ordered, and the formulae compared statement
       for statement ignoring variables. If this produced a difference, then
       the one with the first largest statement is greater.
       Note that this may involve a recursive comparison of subformulae.
    3. If the formulae are still the same, then for each variable, a list
       of appearances is created.  Note that because we are comparing statements without
       variables, two may be equal, in which case the same (first) statement number
       is used whichever statement the variable was in fact in. Ooops
    """
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
        self._defAsListIn = None      # This is not a list as far as we know

    def definedAsListIn(self):  # Is this a list? (override me!)
        return self._defAsListIn
  
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

    def definedAsListIn(self):  # Is this a list? (override me!)
        return self  # YEs, though a special one


class Anonymous(Fragment):
    def __init__(self, resource, fragid):
        Fragment.__init__(self, resource, fragid)

    def generated(self):
        return 1

    def asPair(self):
        return (ANONYMOUS, self.uriref())
        
class Formula(Fragment):

    def generated(self):
        return 1

    def asPair(self):
        return (FORMULA, self.uriref())
        
        
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
        return self.string

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

    def evaluate2(self, store, subj, obj, variables, bindings):
        F = self.evaluateObject2(store, subj)
        return (F is obj) # @@@@@@@@@@@@@@@@@@@@@@@@@@@@ do structual equivalnce thing


# A function can calculate its object from a given subject
class ReverseFunction:
    def __init__(self):
        pass

    def evaluate(self, store, context, subj, subj_py, obj, obj_py):    # For inheritance only
        return (subj is self.evaluateSubject(store, context, obj, obj_py))

    def evaluate2(self, store, subj, obj, variables, bindings):
        F = self.evaluateObject2(store, obj)
        return (F is subj) # @@@@@@@@@@@@@@@@@@@@@@@@@@@@ do structual equivalnce thing

    def evaluateSubject(self, store, context, obj, obj_py):
        raise reverse_function_has_no_evaluate_subject_method #  Ooops - you can't inherit this.

#  For examples of use, see, for example, cwm_string.py
    
# Use this with diagnostics so that it can be changed as necessary
# For example, sometimes want on stdout maybe or in a scroll window....
def progress(*args):
    import sys
    for a in args:
        sys.stderr.write("%s " % (a,))
    sys.stderr.write("\n")
#        sys.stderr.write(  str + "\n")

global chatty_flag   # verbosity debug flag

def setVerbosity(x):
    global chatty_flag
    chatty_flag = x

def verbosity():
    global chatty_flag
    return chatty_flag
