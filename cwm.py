#! /usr/bin/python /devel/WWW/2000/10/swap/cwm.py
"""

$Id$

Closed World Machine

(also, in Wales, a valley  - topologiclly a partially closed world perhaps?)

This is an engine which knows a certian amount of stuff and can manipulate it.
It is a (forward chaining) query engine, not an (backward chaining) inference engine:
that is, it will apply all rules it can
but won't figure out which ones to apply to prove something.  It is not
optimized particularly.


http://www.w3.org/DesignIssues/Notation3
Date: 2000/07/17 21:46:13  

Agenda:
=======

 - get rid of other globals (DWC 30Aug2001)
 - split out separate modules: CGI interface, command-line stuff,
   built-ins (DWC 30Aug2001)
 - split Query engine out as subclass of RDFStore? (DWC)
 - implement a back-chaining reasoner (ala Euler/Algernon) on this store? (DWC)
 - run http daemon/client sending changes to database
 - act as client/server for distributed system
 - Bultins - says
 - postgress, mySQl underlying database?
 -    
 -    standard mappping of SQL database into the web in N3/RDF
 -    
 - logic API as requested DC 2000/12/10
 - Jena-like API x=model.createResource(); addProperty(DC.creator, "Brian", "en")
 - sucking in the schema (http library?) --schemas ;
 - to know about r1 see r2; daml:import
 - schema validation - done partly but no "no schema for xx predicate".
 -   syntax for "all she wrote" - schema is complete and definitive
 - metaindexes - "to know more about x please see r" - described by
 - general python URI access with catalog!
 - equivalence handling inc. equivalence of equivalence?
 Shakedown:
 - Find all synonyms of synonym
 - Find closure for all synonyms
 - Find superclass closure?
- represent URIs bound to same equivalence closuse object?

BULTINS WE NEED
    - usesNamespace(x,y)   # find transitive closure for validation  - awful function in reality
    - delegation of query to remote database (cwm or rdbms)
    - F impliesUnderThink G.  (entails? leadsTo? conclusion?)

- Translation;  Try to represent the space (or a context) using a subset of namespaces

- Other forms of context - explanation of derivation by rule or merging of contexts
- operators on numbers
- operators (union, intersection, subtraction) of context
- cwm -diff using above! for test result comparison

- Optimizations:
    - Remember previous bindings found for this rule(?)
    - Notice disjoint graphs & explicitly form cross-product of subresults

- test rdf praser against Dave Becket's test suite http://ilrt.org/people/cmdjb/
- Introduce this or $ to indicate the current context
- Introduce a difference between <> and $  in that <> log:parsesTo $ .
    serialised subPropertyOf serialisedAs

Done
====
(test/retest.sh is another/better list of completed functionality --DWC)
 - BUG: a [ b c ] d.   gets improperly output. See anon-pred
 - Separate the store hash table from the parser. - DONE
 - regeneration of genids on output. - DONE
 - repreentation of genids and foralls in model
- regression test - DONE (once!)
 Manipulation:
  { } as notation for bag of statements - DONE
  - filter -DONE
  - graph match -DONE
  - recursive dump of nested bags - DONE
 - semi-reification - reifying only subexpressions - DONE
 - Bug  :x :y :z as data should match [ :y :z ] as query. Fixed by stripping forSomes from top of query.
 - BUG: {} is a context but that is lost on output!!!
     occursAs[CONTEXT] not enough. See foo2.n3 - change existential representation :-( to make context a real conjunction again?
    (the forSome triple is special in that you can't remove it and reduce info)
 - filter out duplicate conclusions - BUG! - DONE
 - Validation:  validate domain and range constraints against closuer of classes and
   mutually disjoint classes.
 - Use unambiguous property to infer synomnyms
   (see sameDan.n3 test case in test/retest.sh)
BULTINS WE HAVE DONE
    - includes(expr1, expr2)      (cf >= ,  dixitInterAlia )
    - indirectlyImplies(expr1, expr2)   
    - startsWith(x,y)
    - uri(x, str)
    - usesNamespace(x,y)   # find transitive closure for validation  - awful function in reality

NOTES

This is slow - Parka [guiFrontend PIQ] for example is faster but is propritary (patent pending). Jim Hendler owsns the
research version. Written in C. Of te order of 30k lines
"""



import string
import urlparse
import re
import StringIO

import notation3    # N3 parsers and generators, and RDF generator
# import sax2rdf      # RDF1.0 syntax parser to N3 RDF stream

import urllib # for hasContent
import md5, binascii  # for building md5 URIs
urlparse.uses_fragment.append("md5") #@@kludge/patch
urlparse.uses_relative.append("md5") #@@kludge/patch

from thing import *

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


######################################################## Storage
# The store uses an index in the interned resource objects.
#
#   store.occurs[context, thing][partofspeech]   dict, list, ???


class StoredStatement:

    def __init__(self, q):
        self.triple = q

    def __getitem__(self, i):   # So that we can index the stored thing directly
        return self.triple[i]

#   The order of statements is only for cannonical output
    def __cmp__(self, other):
        if self is other: return 0
        for p in [CONTEXT, SUBJ, PRED, OBJ]: # Note NOT internal order
            if self.triple[p] is not other.triple[p]:
                return compareURI(self.triple[p],other.triple[p])
        progress("Problem with duplicates: '%s' and '%s'" % (quadToString(self.triple),quadToString(other.triple)))
        raise internalerror # SHould never have two identical distinct

    
###############################################################################################
#
#                       C W M - S P E C I A L   B U I L T - I N s
#
###########################################################################
    
# Equivalence relations

class BI_EqualTo(LightBuiltIn,Function, ReverseFunction):
    def evaluate(self, store, context, subj, subj_py, obj, obj_py):
        return (subj is obj)   # Assumes interning

    def evaluateObject(self, store, context, subj, subj_py):
        return subj

    def evaluateSubject(self, store, context, obj, obj_py):
        return obj

class BI_notEqualTo(LightBuiltIn):
    def evaluate(self, store, context, subj, subj_py, obj, obj_py):
        return (subj is not obj)   # Assumes interning


# Functions 
    
class BI_uri(LightBuiltIn, Function, ReverseFunction):

    def evaluateObject(self, store, context, subj, subj_py):
        return store.intern((LITERAL, subj.uriref()))

    def evaluateSubject(self, store, context, obj, obj_py):
        if type(obj_py) == type(""):
            return store.intern((RESOURCE, obj_py))

class BI_rawType(LightBuiltIn, Function):
    """
    The raw type is a type from the point of view of the langauge: is
    it a forumla, list, and so on. Needed for test for formula in finding subformulae
    eg see test/includes/check.n3 
    """

    def evaluateObject(self, store, context, subj, subj_py):
        if isinstance(subj, Literal): y = store.Literal
        elif isinstance(subj, Formula): y = store.Formula
        elif subj.definedAsListIn(): y = store.List
        else: y = store.Other  #  None?  store.Other?
        if chatty > 91:
            progress("%s  rawType %s." %(`subj`, y))
        return y
        

class BI_racine(LightBuiltIn, Function):    # The resource whose URI is the same up to the "#" 

    def evaluateObject(self, store, context, subj, subj_py):
        if isinstance(subj, Fragment):
            return subj.resource
        else:
            return subj

# Heavy Built-ins


class BI_directlyIncludes(HeavyBuiltIn):
    def evaluate2(self, store, subj, obj, variables, bindings):
        return store.testIncludes(subj, obj, variables, bindings=bindings)
    
class BI_notDirectlyIncludes(HeavyBuiltIn):
    def evaluate2(self, store, subj, obj, variables, bindings):
        return not store.testIncludes(subj, obj, variables, bindings=bindings)
    

class BI_includes(HeavyBuiltIn):
    pass    # Implemented specially inline in the code below by query queue expansion.

#class BI_statement(BI_includes):
#    """ A constructor which enumerates the statements in a formula:  F includes f."""
# @@ No machinery for returning multiple values as yet.
#    def evaluate2(self, store, subj, obj, variables):
#        list = obj.occursAs[PRED]
#        if len(list) != 1 return 0  # f2 is not a statement
#        return BI_includes.evaluate2(self, store, subj, obj, variables) 
#
#    def evaluateObject2(self, store, subj):
#        list = obj.occursAs[PRED]
#        for s in list:
#            con, pred, subj, obj = s.triple
#            bindings = []
#            for p in PARTS:  # s o p not c
#                if quad[p] in variables:
                
            
    
class BI_notIncludes(HeavyBuiltIn):
    def evaluate2(self, store, subj, obj, variables, bindings):
        if isinstance(subj, Formula) and isinstance(obj, Formula):
            return not store.testIncludes(subj, obj, variables, bindings=bindings)
        return 0   # Can't say it *doesn't* include it if it ain't a formula

class BI_resolvesTo(HeavyBuiltIn, Function):
    def evaluateObject2(self, store, subj):
        if isinstance(subj, Fragment): doc = subj.resource
        else: doc = subj
        F = store.any((store._experience, store.resolvesTo, doc, None))
        if F: return F
        
        if chatty > 10: progress("Reading and parsing " + `doc`)
        inputURI = doc.uriref()
        loadToStore(store, inputURI)
        if chatty>10: progress("resolvesTo FORMULA addr: %s" % (inputURI+ "#_formula"))
        F = store.intern((FORMULA, inputURI+ "#_formula"))
        return F
    
class BI_resolvesToIfPossible(HeavyBuiltIn, Function):
    def evaluateObject2(self, store, subj):
        try:
            return BI_resolvesTo.evaluateObject2(self, store, subj)
        except (IOError, SyntaxError):
            if chatty > 0: progress("Error trying to resolve <" + inputURI + ">") 
            return None
    

HTTP_Content_Type = 'content-type' #@@ belongs elsewhere?

def loadToStore(store, addr):
    """raises IOError, SyntaxError
    """
    
    netStream = urllib.urlopen(addr)
    ct=netStream.headers.get(HTTP_Content_Type, None)
#    if chatty > 19: progress("HTTP Headers:" +`netStream.headers`)
#    @@How to get at all headers??
#    @@ Get sensible net errors and produce dignostics

    guess = ct
    if chatty > 29: progress("Content-type: " + ct)
    if ct.find('text/plain') >=0 :   # Rats - nothing to go on
        buffer = netStream.read(500)
        netStream.close()
        netStream = urllib.urlopen(addr)
        if buffer.find('xmlns') >=0:
            guess = 'application/xml'
        elif buffer[0] == "#" or buffer[0:7] == "@prefix":
            guess = 'application/n3'
        if chatty > 29: progress("    guess " + guess)
            
    # Hmmm ... what about application/rdf; n3 or vice versa?
    if guess.find('xml') >= 0 or guess.find('rdf') >= 0:
        if chatty > 49: progress("Parsing as RDF")
        import sax2rdf, xml.sax._exceptions
        p = sax2rdf.RDFXMLParser(store, addr)
        p.loadStream(netStream)
    else:
        if chatty > 49: progress("Parsing as N3")
        p = notation3.SinkParser(store, addr)
        p.startDoc()
        p.feed(netStream.read())
        p.endDoc()

    
class BI_hasContent(HeavyBuiltIn, Function): #@@DWC: Function?
    def evaluateObject2(self, store, subj):
        if isinstance(subj, Fragment): doc = subj.resource
        else: doc = subj
        C = store.any((store._experience, store.hasContent, doc, None))
        if C: return C
        if chatty > 10: progress("Reading " + `doc`)
        inputURI = doc.uriref()
        netStream = urllib.urlopen(inputURI)
        str = netStream.read() # May be big - buffered in memory!
        C = store.intern((LITERAL, str))
        return C


class BI_n3ExprFor(HeavyBuiltIn, Function):
    def evaluateObject2(self, store, subj):
        if isinstance(subj, Literal):
            F = store.any((store._experience, store.n3ExprFor, subj, None))
            if F: return F
            if chatty > 10: progress("parsing " + subj.string[:30] + "...")
            inputURI = subj.asHashURI() # iffy/bogus... rather asDataURI? yes! but make more efficient
            p = notation3.SinkParser(store, inputURI)
            p.startDoc()
            p.feed(subj.string) #@@ catch parse errors
            p.endDoc()
            del(p)
            F = store.intern((FORMULA, inputURI+ "#_formula"))
            return F
    

    
###################################################################################        
class RDFStore(notation3.RDFSink) :
    """ Absorbs RDF stream and saves in triple store
    """

    def __init__(self, genPrefix=None, metaURI=None):
        notation3.RDFSink.__init__(self)

        self.resources = {}    # Hash table of URIs for interning things
        self._experience = None

        self.size = 0
        self._nextId = 0
        if genPrefix: self._genPrefix = genPrefix
        else: self._genPrefix = "#_gs"

        # Constants, as interned:
        
        self.forSome = self.internURI(Logic_NS + "forSome")
#        self.subExpression = self.internURI(Logic_NS + "subExpression")
        self.forAll  = self.internURI(Logic_NS + "forAll")
        self.implies = self.internURI(Logic_NS + "implies")
        self.asserts = self.internURI(Logic_NS + "asserts")
        
# Register Light Builtins:
        log = self.internURI(Logic_NS[:-1])   # The resource without the hash
        daml = self.internURI(notation3.DAML_NS[:-1])   # The resource without the hash

#        self.greaterThan =      log.internFrag("greaterThan", BI_GreaterThan)
#        self.notGreaterThan =   log.internFrag("notGreaterThan", BI_NotGreaterThan)
#        self.lessThan =         log.internFrag("lessThan", BI_LessThan)
#        self.notLessThan =      log.internFrag("notLessThan", BI_NotLessThan)
#        log.internFrag("startsWith", BI_StartsWith)
#        log.internFrag("concat", BI_concat)

# Functions:        

        log.internFrag("racine", BI_racine)  # Strip fragment identifier from string

        self.rawType =          log.internFrag("rawType", BI_rawType) # syntactic type, oneOf:
        self.Literal =          log.internFrag("Literal", Fragment) # syntactic type possible value - a class
        self.List =             log.internFrag("List", Fragment) # syntactic type possible value - a class
        self.Formula =          log.internFrag("Formula", Fragment) # syntactic type possible value - a class
        self.Other =            log.internFrag("Other", Fragment) # syntactic type possible value - a class (Use?)

# Bidirectional things:
        log.internFrag("uri", BI_uri)
        log.internFrag("equalTo", BI_EqualTo)
        log.internFrag("notEqualTo", BI_notEqualTo)

# Heavy relational operators:

        self.includes =         log.internFrag( "includes", BI_includes)
        log.internFrag("directlyIncludes", BI_directlyIncludes)
        log.internFrag("notIncludes", BI_notIncludes)
        log.internFrag("notDirectlyIncludes", BI_notDirectlyIncludes)

#Heavy functions:

        self.resolvesTo = log.internFrag("resolvesTo", BI_resolvesTo)
        log.internFrag("resolvesToIfPossible", BI_resolvesToIfPossible)
        log.internFrag("hasContent", BI_hasContent)
        log.internFrag("n3ExprFor",  BI_n3ExprFor)
        
# Constants:

        self.Truth = self.internURI(Logic_NS + "Truth")
        self.type = self.internURI(notation3.RDF_type_URI)
        self.Chaff = self.internURI(Logic_NS + "Chaff")


# List stuff - beware of namespace changes! :-(

        self.first = self.intern(notation3.N3_first)
        self.rest = self.intern(notation3.N3_rest)
        self.nil = self.intern(notation3.N3_nil)
#        self.only = self.intern(notation3.N3_only)
        self.Empty = self.intern(notation3.N3_Empty)
        self.List = self.intern(notation3.N3_List)

        import cwm_string  # String builtins
        import cwm_os      # OS builtins
        cwm_string.register(self)
        cwm_os.register(self)
        
        if metaURI != None:
            self.reset(metaURI)

# Internment of URIs and strings (was in Engine).

# We ought to intern formulae too but it ain't as simple as that.
# - comparing foumale is graph isomorphism complete.
# - formulae grow with addStatement() and would have to be re-interned

    def reset(self, metaURI): # Set the metaURI
        self._experience = self.intern((FORMULA, metaURI + "_forumla"))

    def internURI(self, str):
        return self.intern((RESOURCE,str))
    
    def intern(self, pair):
        """  Returns either a Fragment or a Resource or Literal as appropriate

    This is the way they are actually made.
    """
        type, urirefString = pair
        if type == LITERAL:
            uriref2 = LITERAL_URI_prefix + urirefString # @@@ encoding at least hashes!!
            r = self.resources.get(uriref2, None)
            if r: return r
            r = Literal(urirefString)
            self.resources[uriref2] = r
            return r
        
#        print " ... interning <%s>" % `uriref`
        hash = len(urirefString)-1
        while (hash >= 0) and not (urirefString[hash] == "#"):
            hash = hash-1
        if hash < 0 :     # This is a resource with no fragment
            r = self.resources.get(urirefString, None)
            if r: return r
            r = Resource(urirefString)
            self.resources[urirefString] = r
            return r
        
        else :      # This has a fragment and a resource
            r = self.internURI(urirefString[:hash])
            if type == RESOURCE:
                if urirefString == notation3.N3_nil[1]:  # Hack - easier if we have a different classs
                    return r.internFrag(urirefString[hash+1:], FragmentNil)
                else:
                    return r.internFrag(urirefString[hash+1:], Fragment)
            if type == FORMULA: return r.internFrag(urirefString[hash+1:], Formula)
            else: raise shouldntBeHere    # Source code did not expect other type


# Input methods:

    def loadURI(self, uri):
        p = notation3.SinkParser(self,  uri)
        p.load(uri)
        del(p)


    def bind(self, prefix, nsPair):
        if prefix:   #  Ignore binding to empty prefix
            return notation3.RDFSink.bind(self, prefix, nsPair) # Otherwise, do as usual.
    
    def makeStatement(self, tuple):
        q = ( self.intern(tuple[CONTEXT]),
              self.intern(tuple[PRED]),
              self.intern(tuple[SUBJ]),
              self.intern(tuple[OBJ]) )
        self.storeQuad(q)
                    
    def makeComment(self, str):
        pass        # Can't store comments

    def contains(self, q):
        """  Check whether this quad  exists in the store
	"""
        short = 1000000 #@@
	for p in ALL4:
            l = len(q[p].occursAs[p])
            if l < short:
                short = l
                p_short = p
        for t in q[p_short].occursAs[p_short]:
            if t.triple == q: return t
        return None

    def any(self, q):
        """  Quad contains one None as wildcard. Returns first value
        matching in that position.
	"""
        short = 1000000 #@@
	for p in ALL4:
            if q[p] != None:
                l = len(q[p].occursAs[p])
                if l < short:
                    short = l
                    p_short = p
        for t in q[p_short].occursAs[p_short]:
            for p in ALL4:
                if q[p] != None and q[p] is not t.triple[p]:
                    break
                else:
                    for p in ALL4:
                        if q[p] == None:
                            return t.triple[p]
        return None

    def storeQuad(self, q):
        """ Effectively intern quads, in that dupliates are eliminated.
        """
        #  Check whether this quad already exists
	if self.contains(q): return 0  # Return no change in size of store

        # Compress string constructors within store:
        # The first, rest pair becomes a single dotted-pair-like compact list element
        # These are extended in the output routine back to first and rest.
        
        context, pred, subj, obj = q        
        if pred is self.first:  # If first, and rest already known, combine:
            for s in subj.occursAs[SUBJ]:
                if s[PRED] is self.rest and s[CONTEXT] is context:
                    q = (context, s[OBJ], subj, obj)
                    context, pred, subj, obj = q
                    self.removeStatement(s)
                    if chatty > 80: progress("Found list:" + quadToStr(q))
                    break
        elif pred is self.rest:  # And vice versa
            for s in subj.occursAs[SUBJ]:
                if s[PRED] is self.first and s[CONTEXT] is context:
                    q = (context, obj, subj, s[OBJ])
                    context, pred, subj, obj = q
                    self.removeStatement(s)
                    if chatty > 80: progress("Found list:" + quadToStr(q))
                    break

	s = StoredStatement(q)
        for p in ALL4: q[p].occursAs[p].append(s)
        self.size = self.size+1

        if pred.definedAsListIn():
            subj = q[SUBJ]
            if (not isinstance(subj, Fragment)) or subj._defAsListIn:
                progress("??? ")
                raise internalError #should only once
            subj._defAsListIn = s
            self.newList(subj)
        return 1  # One statement has been added

    def newList(self, x):  # Note, for speed, that this is a list
        for s in x.occursAs[PRED]:  # For every one which tis list gen'd
            y = s.triple[SUBJ]
            if not y._defAsListIn:
                y._defAsListIn = s
                self.newList(y)
        return

    def deList(self, x):
        for s in x.occursAs[PRED]:
            y = s.triple[SUBJ]
            y._defAsListIn = None
            self.deList(y)
        return

    def startDoc(self):
        pass

    def endDoc(self):
        pass

##########################################################################
#
# Output methods:
#
    def selectDefaultPrefix(self, context):

        """ Resource whose fragments have the most occurrences.
        """

        best = 0
        mp = None
        counts = {}   # Dictionary of how many times each
        closure = self.subContexts(context)    # This context and all subcontexts
        for con in closure:
            for s in con.occursAs[CONTEXT]:
                for p in PRED, SUBJ, OBJ:
                    x = s[p]
                    if isinstance(x, Fragment):
                        anon, inc, se = self._topology(x, con)
                        if not anon and not isinstance(x, Formula):
                            r = x.resource
                            total = counts.get(r, 0) + 1
                            counts[r] = total
                            if total > best or (total == best and `mp` > `r`) :  # Must be repeatable for retests
                                best = total
                                mp = r

        if chatty > 25:
            for r, count in counts.items():
                if count > 4:
                    progress("    Count is %3i for %s" %(count, `r`))

        if chatty > 20:
            progress("# Most popular Namesapce in %s is %s with %i" % (`context`, `mp`, best))

        if mp is None: return
        
        mpPair = (RESOURCE, mp.uriref(None)+"#")
        defns = self.namespaces.get("", None)
        if defns :
            del self.namespaces[""]
            del self.prefixes[defns]
        if self.prefixes.has_key(mpPair) :
            oldp = self.prefixes[mpPair]
            del self.prefixes[mpPair]
            del self.namespaces[oldp]
        self.prefixes[mpPair] = ""
        self.namespaces[""] = mpPair


    def dumpPrefixes(self, sink):
        prefixes = self.namespaces.keys()   #  bind in same way as input did FYI
        prefixes.sort()
        for pfx in prefixes:
            sink.bind(pfx, self.namespaces[pfx])

    def dumpChronological(self, context, sink):
        sink.startDoc()
        self.dumpPrefixes(sink)
#        print "# There are %i statements in %s" % (len(context.occursAs[CONTEXT]), `context` )
        for s in context.occursAs[CONTEXT]:
            self._outputStatement(sink, s.triple)
        sink.endDoc()

    def _outputStatement(self, sink, triple):
        sink.makeStatement(self.extern(triple))

    def extern(self, t):
        return(t[CONTEXT].asPair(),
                            t[PRED].asPair(),
                            t[SUBJ].asPair(),
                            t[OBJ].asPair(),
                            )

    def dumpBySubject(self, context, sink, sorting=1):
        """ Dump by order of subject except forSome's first for n3=a mode"""
        
        self.selectDefaultPrefix(context)        
        sink.startDoc()
        self.dumpPrefixes(sink)

        if sorting: context.occursAs[SUBJ].sort()
        for s in context.occursAs[SUBJ] :
            if context is s.triple[CONTEXT]and s.triple[PRED] is self.forSome:
                self._outputStatement(sink, s.triple)

        rs = self.resources.values()
        if sorting: rs.sort()
        for r in rs :  # First the bare resource
            if sorting: r.occursAs[SUBJ].sort()
            for s in r.occursAs[SUBJ] :
                if context is s.triple[CONTEXT]:
                    if not(context is s.triple[SUBJ]and s.triple[PRED] is self.forSome):
                        self._outputStatement(sink, s.triple)
            if not isinstance(r, Literal):
                fs = r.fragments.values()
                if sorting: fs.sort
                for f in fs :  # then anything in its namespace
                    for s in f.occursAs[SUBJ] :
#                        print "...dumping %s in context %s" % (`s.triple[CONTEXT]`, `context`)
                        if s.triple[CONTEXT] is context:
                            self._outputStatement(sink, s.triple)
        sink.endDoc()
#
#  Pretty printing
#
#   x is an existential if there is in the context C we are printing
# is a statement  (C log:forSome x). If so, the anonymous syntaxes follow.
# c is 1 if x is a subexpression of the current context else c=0
# r s and o are the number  times x occurs within context as p,s or o
# o excludes the statements making it an existential and maybe subexp.
#
#   c  p  s  o   Syntax
#   0  0  0  0   (won't occur.)
#   0  0  ?  1   y p [ ... ] .
#   0  0  y  0   [] p z, ....     or  [ p y,z ... ] .  or a combination
#   0  0  y  1   y q [ p y z ... ] .
#   0  1  ?  0   y  [ ... ] w .
#   ?  1  ?  1   can't be pred and obj.
#   y  0  y  0   { ... } p y z,... .
#   y  0  y  1   y q [ p y z ...; = { ... } ] .
#   ?  ?  ?  >1  can't without using revese <- p -< notation
#   ?  >1 ?  ?   can't UNLESS all occurrences for same subject
#   y  0  0  0   { ... } .     Does this have any meaning? Void meaning I think.
#   y  0  0  1   y q { ... } .
#   y  1  0  0   x  { .... }  y .   Illegal because statementlist and property disjoint????
#   y  1  y  0   x  [ ... ; ={ ...} ]  (illegal - same reason?)
# simplified rules:
#  If it occurs > once as a (predicate or object), forget it.
#  If it occurs as a predicate or object at all
#       Wait for it to turn up
#
#  If it is not as a subject but is as a context use {}
#  Else use [ ..] with optionally a = { ... } inside. 
#
#  Exception: when the subject, and when 
#  If it occurs both as predicate and object, forget it.
#  If it occurs as context and subject in the SAME STATEMENT, forget it.
#  Else
#      If it does not occur as a subject use { ... } form
#      Else use [ ... ] form optionally with  = { ... } if both
#  Exception:  if subject and not pred or obj then use  [] p z... form to cut down nesting?

# An intersting alternative is to use the reverse syntax to the max, which
# makes the DLG an undirected labelled graph. s and o above merge. The only think which
# then prevents us from dumping the graph without genids is the presence of cycles.

# Contexts
#
# These are in some way like literal strings, in that they are defined completely
# by their contents. They are sets of statements. (To say a statement occurs
# twice has no menaing).  Can they be given an id?  You can assert that any
# object is equivalent to (=) a given context. However, it is the contexts which
# define a context. If one could label it in one place then one would want to
# be able to label it in more than one.  I'm not sure whether this is wise.
# Let's try it with no IDs on contexts as in the N3 syntax.  There would be
# the question of in which context the assertion wa made that the URI was
# a label for the expression. You couldn't just treat it as part of the
# machinery as we do for URI of a regular thing.


    def _topology(self, x, context): 
        """ Can be output as an anonymous node in N3. Also counts incoming links.

        1. True iff can be represented as anonymous node in N3
        2. Number of incoming links: >0 means occurs as object or pred, 0 means as only as subject.
        3. Is this a literal context? forSome and exists as context.
            Literal contexts are represented wherever they occur by braces expression
        
        Returns  number of incoming links (1 or 2) including forSome link
        or zero if self can NOT be represented as an anonymous node.
        Paired with this is whether this is a subexpression.
        """
        # @@@@ This is NOT a proper test - we should test that the statement
        # is an assumed one.
        # @@@ what about nested contexts? @@@@@@@@@@@@@@@@@@@@@@@@@@

        subcontexts = self.subContexts(context)   #  @@ Cache these on the formula for speed?         
        _asPred = x.occurrences(PRED, context)
        
        _isSubExp = 0
        _asObj = 0       # Times occurs as object NOT counting the subExpression or ForSome
        _isExistential = 0  # Is there a forSome?
        _elsewhere = 0
        for s in x.occursAs[OBJ]:  # Checking all statements about x
            con, pred, subj, obj = s.triple
            # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ HACK - error - check context is ancestor
            if subj is con and pred is self.forSome :
                _isExistential = 1
            else:
                if con is context:
                    _asObj = _asObj + 1  # Regular object
                elif con in subcontexts:
                    _elsewhere = _elsewhere + 1  # Occurs in a subformula - can't be anonymous!
                else:
                    pass    # Irrelevant occurrence in some other formula


#        _anon = (_op < 2) and _isExistential
        _anon = (_asObj < 2) and ( _asPred == 0) and _isExistential and not _elsewhere
        if x.definedAsListIn():
            _asObj = _asObj + _asPred  # List links are like obj (daml:rest)
            _asPred = 0
            _anon = 1    # Always represent it as anonymous
        _isSubExp = _isExistential and (isinstance(x, Formula) and x is not context) # subExpression removal

        if chatty > 98: progress( "\nTopology <%s in <%sanon=%i ob=%i,pr=%i se=%i exl=%i"%(
            `x`[-8:], `context`[-8:], _anon, _asObj, _asPred, _isSubExp, _isExistential))
        return ( _anon, _asObj+_asPred, _isSubExp)  

    def isList(self, x, context):
        """ Does this look like a list?
        This should check that this is a node which can be represented in N3
        without loss of information as a list.
        This does not check whether the node is anonymous - check that first.
        It does check whether there is more info about the node which
            can't be represented in ()
        
        """
        if x is self.nil: return 1  # Yes, nil is the list ()

        if not DAML_LISTS:
            if x is self.nil: return 1  # Yes, only is actually the list ()
            ld = x.definedAsListIn()
            if not ld: return None
            first = ld.triple[OBJ]     # first
            rest = ld.triple[PRED]    # rest
            empty = 0
            left = []
            right = []
            for s in x.occursAs[SUBJ]:
                con, pred, subj, obj = s.triple
                if con == context and s is not ld: 
                    #print "     ",quadToString(s.triple), `self.first`
                    if pred is self.first and obj is first:
                        pass
                    elif pred is self.rest and obj is rest:
                        pass
                    elif pred is self.type:
                        if obj is self.Empty: empty = 1
                        if obj is not self.List and obj is not self.Empty : return 0
                    else:
                        #print "     Unacceptable: ",quadToString(s.triple), `self.rest`, `pred`
                        return 0  # Can't have anything else - wouldn't print.
            #print "# ", `x`[-8:], "left:", left, "right", right
            return self.isList(rest, context)
        else:  # DAML_LISTS
            empty = 0
            left = []
            right = []
            for s in x.occursAs[SUBJ]:
                con, pred, subj, obj = s.triple
                if con == context:
                    #print "     ",quadToString(s.triple), `self.first`
                    if pred is self.first: left.append(obj)
                    elif pred is self.rest: right.append(obj)
                    elif pred is self.type:
                        if obj is self.Empty: empty = 1
                        if obj is not self.List and obj is not self.Empty : return 0
                    else:
                        #print "     Unacceptable: ",quadToString(s.triple), `self.rest`, `pred`
                        return 0  # Can't have anything else - wouldn't print.
            #print "# ", `x`[-8:], "left:", left, "right", right
            if left == [] and right == [] and empty: return 1
            if len(left) != 1 or len(right)!=1: return 0 # Invalid
            return self.isList(right[0], context)
    
#  Convert a data item with no unbound variables into a python equivalent 
#  Given the entries in a queue template, find the value of a list.
#  @@ slow
#   These mthods are at the disposal of built-ins.

    def _toPython(self, x, hypothetical, queue):
        if chatty > 85: progress("#### Converting to python "+ x2s(x))
        """ Returns an N3 list as a Python sequence"""
        if x is self.nil: return []  # Yes, nil is the list ()
        ld = x.definedAsListIn()
        if not ld:
            if isinstance(x, Literal):
                return x.string
            return x    # If not a list, return unchanged
        if hypothetical: # This is a hypothetical list in the query
            for i in range(len(queue)):  # @@ slow
                c2, p2, s2, o2 = queue[i][QUAD]
                if s2 is x and p2.definedAsListIn():
                    object_hypothetical = OBJ in queue[i][BOUNDLISTS]
                    predicate_hypothetical = PRED in queue[i][BOUNDLISTS]
                    return [ self._toPython(o2, object_hypothetical, queue) ] + self._toPython(p2, predicate_hypothetical, queue)
            else:
                raise noendtolist  # oops -bug
        else:  #  A stored list - get it from the store
            ld = x.definedAsListIn()
            return  [ self._toPython(ld[OBJ], 0, queue) ] + self._toPython(ld[PRED], 0, queue) 

    def _fromPython(self, x):
        if type(x) == type('"'):
            return self.intern((LITERAL, x))
        if type(x) == type(2):
            return self.intern((LITERAL, `x`))
#        if type(x, []): # @@@@@@@@@@@@@ return list
#            return self.intern(LITERAL, x)
        return x

    def dumpNested(self, context, sink):
        """ Iterates over all URIs ever seen looking for statements
        """
        self.selectDefaultPrefix(context)        
        sink.startDoc()
        self.dumpPrefixes(sink)
        self.dumpNestedStatements(context, sink)
        sink.endDoc()

    def dumpNestedStatements(self, context, sink, sorting=1):
        """ Iterates over statements in 
        """
        if sorting: context.occursAs[CONTEXT].sort()
        currentSubject = None
        statements = []
        for s in context.occursAs[CONTEXT]:
            con, pred, subj, obj =  s.triple
            if not currentSubject: currentSubject = subj
            if subj != currentSubject:
                self._dumpSubject(currentSubject, context, sink, sorting, statements)
                statements = []
                currentSubject = subj
            statements.append(s)
        if currentSubject:
            self._dumpSubject(currentSubject, context, sink, sorting, statements)

    def dumpNestedStatements_old(self, context, sink, sorting=1):
        """ Iterates over all URIs ever seen looking for statements
        """
        rs = self.resources.values()[:]
        if sorting: rs.sort(compareURI)
        for r in rs :  # First the bare resource
            #print "# sorted?" ,`r`
            self._dumpSubject(r, context, sink, sorting)
            fs = r.fragments.values()[:]
            if sorting: fs.sort(compareURI) 
            for f in fs :  # then anything in its namespace
                self._dumpSubject(f, context, sink, sorting)

# This outputs arcs leading away from a node, and where appropriate
# recursively descends the tree, by dumping the object nodes
# (and in the case of a compact list, the predicate (rest) node).

    def _dumpSubject(self, subj, context, sink, sorting=1, statements=[]):
        """ Take care of top level anonymous nodes
        """
        if 0: print "...%s occurs %i as context, %i as pred, %i as subj, %i as obj" % (
            `subj`, len(subj.occurrsAs[CONTEXT, None]),
            subj.occurrences(PRED,context), subj.occurrences(SUBJ,context),
            subj.occurrences(OBJ, context))
        _anon, _incoming, _se = self._topology(subj, context)    # Is anonymous?

       
        if 0: sink.makeComment("DEBUG: %s incoming=%i, se=%i, anon=%i" % (
            `subj`[-8:], _incoming, _se, _anon))
        if _anon and  _incoming == 1: return           # Forget it - will be dealt with in recursion

    
        if _anon and _incoming == 0:    # Will be root anonymous node - {} or []
            if _se > 0:  # Is subexpression of this context
                sink.startBagSubject(subj.asPair())
                self.dumpNestedStatements(subj, sink)  # dump contents of anonymous bag
                sink.endBagSubject(subj.asPair())       # Subject is now set up
                # continue to do arcs

            elif subj is context:
                pass
            else:     #  Could have alternative syntax here

                for s in statements:  # Find at least one we will print
                    context, pre, sub, obj = s.triple
                    if sub is obj: break  # Ok, we will do it
                    _anon, _incoming, _se = self._topology(obj, context)
                    if not((pre is self.forSome) and sub is context and _anon):
                        break # We will print it
                else: return # Nothing to print - so avoid printing [].

                sink.startAnonymousNode(subj.asPair())
                if sorting: statements.sort()    # Order only for output
                for s in statements:
                    self.dumpStatement(sink, s.triple)
                    next = s[PRED].definedAsListIn()    # List?
                    if next:
                        self.dumpStatement(sink, next.triple) # If so, unweave now
                        
                sink.endAnonymousNode()
                return  # arcs as subject done

        if not _anon and isinstance(subj, Formula) and subj is not context:
            sink.startBagNamed(context.asPair(), subj.asPair())
            self.dumpNestedStatements(subj, sink)  # dump contents of anonymous bag
            sink.endBagNamed(subj.asPair())       # Subject is now set up

        if sorting: statements.sort()
        for s in statements:
            self.dumpStatement(sink, s.triple)

                
    def dumpStatement(self, sink, triple, sorting=0):
        # triple = s.triple
        context, pre, sub, obj = triple
        if sub is obj:
            self._outputStatement(sink, triple) # Do 1-loops simply
            return
        # Expand lists to DAML lists on output - its easier
        if pre.definedAsListIn():
            self.dumpStatement(sink, (context, self.first, sub, obj), sorting)
#            if pre is not self.nil:
            self.dumpStatement(sink, (context, self.rest,  sub, pre), sorting)
            return
        _anon, _incoming, _se = self._topology(obj, context)
        if 0: sink.makeComment("...%s anon=%i, incoming=%i, se=%i" % (
            `obj`[-8:], _anon, _incoming, _se))
        
        if ((pre is self.forSome) and sub is context and _anon):
#            print "# @@@@ implicit ", quadToString(s.triple)  
            return # implicit forSome - may leave [] empty :-(

        if _anon and _incoming == 1:  # Embedded anonymous node in N3
            _isSubject = obj.occurrences(SUBJ,context) # Has properties in this context?

#            if _isContext > 0 and _isSubject > 0: raise CantDoThat # Syntax problem!@@@
            
            if _isSubject > 0 or not _se :   #   Do [ ] if nothing else as placeholder.
                li = _anon and self.isList(obj,context)
                if chatty>49 and li:
                    progress("List found in " + x2s(obj))
                sink.startAnonymous(self.extern(triple), li)
                if sorting: obj.occursAs[SUBJ].sort()
                for t in obj.occursAs[SUBJ]:
                    if t.triple[CONTEXT] is context:
                        self.dumpStatement(sink, t.triple)

                ld = pre.definedAsListIn()
                if ld: #@@@@
                    self.dumpStatement(sink, ld.triple)
  
                if _se > 0:
                    sink.startBagNamed(context.asPair(),obj.asPair()) # @@@@@@@@@  missing "="
                    self.dumpNestedStatements(obj, sink)  # dump contents of anonymous bag
                    sink.endBagObject(pre.asPair(), sub.asPair())
                    
                sink.endAnonymous(sub.asPair(), pre.asPair()) # Restore parse state
            else:  # _isSubject == 0 and _se
                sink.startBagObject(self.extern(triple))
                self.dumpNestedStatements(obj, sink)  # dump contents of anonymous bag
                sink.endBagObject(pre.asPair(), sub.asPair())
            return # Arc is done

        if _se:
            sink.startBagObject(self.extern(triple))
            self.dumpNestedStatements(obj, sink)  # dump contents of anonymous bag
            sink.endBagObject(pre.asPair(), sub.asPair())
            return

        self._outputStatement(sink, triple)
                


########1#########################  Manipulation methods:
#
#  Note when we move things, then the store may shrink as they may
# move on top of existing entries and we don't allow duplicates.
#
    def moveContext(self, old, new):
        for s in old.occursAs[CONTEXT][:] :   # Copy list!
            self.removeStatement(s)
            for p in CONTEXT, PRED, SUBJ, OBJ:
                x = s.triple[p]
                if x is old:
                    s.triple = s.triple[:p] + (new,) + s.triple[p+1:]
            self.storeQuad(s.triple)
                
#  Clean up intermediate results:
#
# Statements in the given context that a term is a Chaff cause
# any mentions of that term to be removed from the context.

    def purge(self, context, boringClass=None):
        if not boringClass:
            boringClass = self.Chaff
        for s in boringClass.occursAs[OBJ][:]:
            con, pred, subj, obj = s.triple
            if con is context and  pred is self.type:
                total = 0
                for p in (PRED, SUBJ, OBJ):
                    for t in subj.occursAs[p][:]:  # Take copy as list changes
                        if t.triple[CONTEXT] is context:
                            self.removeStatement(t)
                            total = total + 1

                if chatty > 30: progress("Purged %i statements with...%s" % (total,`subj`[-20:]))


    def removeStatement(self, s):
        for p in ALL4:
            i=0
            l=s.triple[p].occursAs[p]
            while l[i] is not s:
                i = i + 1
            l[i:i+1] = []  # Remove one element
            # s.triple[p].occursAs[p].remove(s)  # uses slow __cmp__
        pred = s.triple[PRED]
        if pred.definedAsListIn():
            subj = s.triple[SUBJ]
            if not subj._defAsListIn: raise internalError #should only once
            subj._defAsListIn = None
            self.deList(subj)

        self.size = self.size-1
        del s

#  Apply rules from one context to another
                
    def applyRules(self, workingContext,    # Data we assume 
                   filterContext = None,    # Where to find the rules
                   targetContext = None,    # Where to put the conclusions
                   universals = []):        # Inherited from higher contexts
        """ Apply rules in one context to the same or another
        """

# A rule here is defined by logic:implies, which associates the template (premise, precondidtion,
# antecedent) to the conclusion (postcondition).
#
# This is just a database search, very SQL-like.
#
# To verify that for all x, f(s) one can either find that asserted explicitly,
# or find an example for some specific value of x.  Here, we deliberately
# chose only to do the first.
        
        if targetContext is None: targetContext = workingContext # return new data to store
        if filterContext is None: filterContext = workingContext # apply own rules

        # Execute a filter:
        
        _variables = universals[:] # Rule-wide or wider universals
        _total = 0
        for s in filterContext.occursAs[CONTEXT]:
            t = s.triple
            if t[PRED] is self.forAll and t[SUBJ] is filterContext:
                _variables.append(t[OBJ])
#        print "\n\n# APPLY RULES TO %s, (%i vars)" % (filterContext, len(_variables),), _variables
        
        for s in filterContext.occursAs[CONTEXT]:
            t = s.triple
            if t[PRED] is self.implies:
                tries = 0
                found = self.tryRule(s, workingContext, targetContext, _variables[:])
                if (chatty >40) or (chatty > 5 and tries > 1):
                    progress( "Found %i new stmts for rule %s" % (tries, quadToString(t)))
                _total = _total+found
            else:
                c = None
                if t[PRED] is self.asserts and t[SUBJ] is filterContext: c=t[OBJ]
                elif t[PRED] is self.type and t[OBJ] is self.Truth: c=t[SUBJ]
# We could shorten the rule format if forAll(x,y) asserted truth of y too, but this messes up
# { x foo y } forAll x,y; log:implies {...}. where truth is NOT asserted. This line would do it:
                elif t[PRED] is self.forAll and t[SUBJ] is self.Truth: c=t[SUBJ]  # DanC suggestion @@
                if c:
                    _vs = _variables[:]
                    for s in filterContext.occursAs[CONTEXT]: # find forAlls pointing downward
                        if s.triple[PRED] is self.forAll and s.triple[SUBJ] is c:
                            _vs.append(s.triple[OBJ])
                    _total = _total + self.applyRules(workingContext, c, targetContext, _vs)  # Nested rules


        if chatty > 4: progress("Total %i new statements from rules in %s" % ( _total, filterContext))
        return _total

    # Beware lists are corrupted
    def tryRule(self, s, workingContext, targetContext, _variables):
        t = s.triple
        template = t[SUBJ]
        conclusion = t[OBJ]

        if chatty >30: progress("\n=================== IMPLIES RULE ============")

        # When the template refers to itself, the thing we are
        # are looking for will refer to the context we are searching
        # Similarly, refernces to the working context have to be moved into the
        # target context when the conclusion is drawn.

        unmatched, _templateVariables = self.oneContext(template)
        _substitute([( template, workingContext)], unmatched)

# If we know :a :b :c, then [ :b :c ] is true.
        u2 = []  #  Strip out "forSome" at top level as we don't need to find them
        for quad in unmatched:
            if (quad[CONTEXT] is workingContext
                and quad[SUBJ] is workingContext
                and quad[PRED] is self.forSome):
                pass
                if chatty>80: progress( " Stripped forSome <%s" % `quad[OBJ]`[-10:])
            else:
                u2.append(quad)
        if chatty>80: progress( " Stripped %i  %i" % (len(unmatched), len(u2)))
        unmatched = u2
        
        if chatty >20:
            progress( "# IMPLIES Template" + setToString(unmatched, _variables))

        conclusions, _outputVariables = self.nestedContexts(conclusion)
        _substitute([( conclusion, targetContext)], conclusions)                

        if chatty > 50:
            progress( "# IMPLIES rule, %i terms in template %s (%i t,%i e) => %s (%i t, %i e)" % (
                len(template.occursAs[CONTEXT]),
                `template`[-8:], len(unmatched), len(_templateVariables),
                `conclusion`[-8:], len(conclusions), len(_outputVariables)))
        if chatty > 95:
            for v in _variables:
                progress( "    Variable: " + `v`[-8:])
    # The smartIn context was the template context but it has been mapped to the workingContext.
        return self.match(unmatched, _variables, _templateVariables, [workingContext],
                      self.conclude, ( self, conclusions, targetContext, _outputVariables))





# Return whether or nor workingContext containts a top-level template equvalent to subexp 
    def testIncludes(self, workingContext, template, _variables, smartIn=[], bindings=[]):
        global chatty

        if chatty >30: progress("\n\n=================== testIncludes ============")
#        chatty = chatty+100

        # When the template refers to itself, the thing we are
        # are looking for will refer to the context we are searching

        if not(isinstance(workingContext, Formula) and isinstance(template, Formula)): return 0


        unmatched, _templateVariables = self.oneContext(template)
        _substitute([( template, workingContext)], unmatched)
        
        if bindings != []: _substitute(bindings, unmatched)

        if chatty > 20:
            progress( "# testIncludes BUILTIN, %i terms in template %s, %i unmatched, %i template variables" % (
                len(template.occursAs[CONTEXT]),
                `template`[-8:], len(unmatched), len(_templateVariables)))
        if chatty > 80:
            for v in _variables:
                progress( "    Variable: " + `v`[-8:])

        result = self.match(unmatched, [], _variables + _templateVariables, smartIn, justOne=1)
        if chatty >30: progress("=================== end testIncludes =" + `result`)
#        chatty = chatty-100
        return result
 
    def genid(self,context, type=RESOURCE):        
        self._nextId = self._nextId + 1
        return self.intern((type, self._genPrefix+`self._nextId`))

    def subContexts(self,con, path = []):
        """
        slow...
        """
        global subcontext_cache_context
        global subcontext_cache_subcontexts
        if con is subcontext_cache_context:
            return subcontext_cache_subcontexts
#        progress("subcontext "+`con`+" path "+`len(path)`)
        set = [con]
        path2 = path + [ con ]     # Avoid loops
        for s in con.occursAs[CONTEXT]:
            for p in PRED, SUBJ, OBJ:
                if isinstance(s[p], Formula):
                    if s[p] not in path2:
                        set2 = self.subContexts(s[p], path2)
                        for c in set2:
                            if c not in set: set.append(c)
        if path == []:
            subcontext_cache_context = con
            subcontext_cache_subcontexts = set  #  @@ when set this dirty?
        return set
                        
    def nestedContexts(self, con):
        """ Return a list of statements and variables of either type
        found within the nested subcontexts
        """
        statements = []
        variables = []
        existentials = []
#        print "# NESTING in ", `self`, " using ", `subExpression`
        for arc in con.occursAs[CONTEXT]:
#            print"#    NESTED ",arc.triple
            context, pred, subj, obj = arc.triple
            statements.append(arc.triple)
#            print "%%%%%%", quadToString(arc.triple)
            if subj is context and (pred is self.forSome or pred is self.forAll): # @@@@
                variables.append(obj)   # Collect list of existentials
#                if obj is self.Truth: print "#@@@@@@@@@@@@@", quadToString(arc.triple)
            if subj is context and pred is self.forSome: # @@@@
                existentials.append(obj)   # Collect list of existentials
                
        # Find all subforumlae  - forumulae which are mentioned at least once.
        subformulae = []
        for arc in con.occursAs[CONTEXT]:
#           if pred is self.subExpression and subj is con:
            for p in [ SUBJ, PRED, OBJ]:  # @ can remove PRED if formulae and predicates distinct
                x = arc.triple[p]
                if isinstance(x, Formula) and x in existentials:  # x is a Nested context
                    if x not in subformulae: subformulae.append(x) # Only one copy of each please
                    
        for x in  subformulae:
            for a2 in con.occursAs[CONTEXT]:  # Rescan for variables
                c2, p2, s2, o2 = a2.triple
                if  s2 is x and (p2 is self.forSome or p2 is self.forAll):
                    variables.append(o2)   # Collect list of existentials
#                            if o2 is self.Truth: print "#@@@@@@@@@@@@@", quadToString(a2.triple)
            s, v = self.nestedContexts(x)
            statements = statements + s
            variables = variables + v
        return statements, variables


#  One context only:
# When we return the context, any nested ones are of course referenced in it

    def oneContext(self, con):
        """ Return a list of statements and variables of either type
        found within the top level
        """
        statements = []
        variables = []
        existentials = []
#        print "# NESTING in ", `self`, " using ", `subExpression`
        for arc in con.occursAs[CONTEXT]:
#            print"#    NESTED ",arc.triple
            context, pred, subj, obj = arc.triple
            statements.append(arc.triple)
#            print "%%%%%%", quadToString(arc.triple)
            if subj is context and (pred is self.forSome or pred is self.forAll): # @@@@
                variables.append(obj)   # Collect list of existentials
#                if obj is self.Truth: print "#@@@@@@@@@@@@@", quadToString(arc.triple)
            if subj is context and pred is self.forSome: # @@@@
                existentials.append(obj)   # Collect list of existentials
                
        return statements, variables

#   Find how many variables occur in an expression
#   Not sure whether we need thus .. but anyway, here iut is for the record.

    def variableOccurence(x, vars):
        """ Figure out, given a set of variables which if any occur in a list, formula etc."""
        if x in vars:
            return [ x ]
        if isinstance(x, Literal):
            return []
        set = []
        if isinstance(x, Formula):
            for s in x.occursAs[CONTEXT]:
                for p in PRED, SUBJ, OBJ:
                    v2 = variableOccuences(s[p], vars)
                    for v in v2:
                        if v not in set: set.append(v)
            return set 

        ld = x.definedAsListIn()
        if ld:
            first = variableOccurrences(ld[OBJ], vars) 
            rest = variableOccurrences(ld[PRED], vars)
            for v in first + rest:
                if v not in set: set.append(v)
            return set

        return []
    


#   Find whether any variables occur in an expression
#  Used in the built-ins to see whether they can run

    def anyOccurrences(x, vars):
        """ Figure out, given a set of variables which if any occur in a list, formula etc."""
        if x in vars:
            return x
        if isinstance(x, Literal):
            return None
        if isinstance(x, Formula):
            for s in x.occursAs[CONTEXT]:
                for p in PRED, SUBJ, OBJ:
                    if anyOccurences(s[p], vars):
                        return s[p]
            return None

        ld = x.definedAsListIn()
        if ld:
            if anyOccurrences(ld[OBJ], vars) or Occurrences(ld[PRED], vars):
                return x
            
        return None
    



############################################################## Query engine
#
# Template matching in a graph
#
# Optimizations we have NOT done:
#   - storing the tree of matches so that we don't have to duplicate them another time
#   - using that tree to check only whether new data would extend it (very cool - memory?)
#      (this links to dynamic data, live variables.)
#   - recognising in advance disjoint graph templates, doing cross product of separate searches
#
# Built-Ins:
#   The trick seems to be to figure out which built-ins are going to be faster to
# calculate, and so should be resolved before query terms involving a search, and
# which, like those involving recursive queries or net access, will be slower than a query term,
# and so should be left till last.
#   I feel that it should be possible to argue about built-ins just like anything else,
# so we do not exclude these things from the query system. We therefore may have both light and
# heavy built-ins which still have too many variables to calculate at this stage.
# When we do the variable substitution for new bindings, these can be reconsidered.

#
#  Lists
#     List links can be resolved either of two ways.  Firstly, they can be matched against
# links in the store, which process can only, as far as I can see, start from the nil end
# and work back up.  This gives you a list which is not a variable, and whose contents
# are defined in the store.  This may then match against other parts of the template
# and be resolved usual, or be presented to a built-in function which succeeds.
#    Secondly, the list links may not themselves be found, but the first (obj) part of
# each may be resolved. This gives us, at the head, a list which is a variable. This
# means that its contents are defined in the query queue.  This is still interesting
# as a built-in function, as in  v:x st:concat ("hot" "house") .  For that purpose,
# a queue element which defines a list which contains no variables is put into a special
# state when a search fails for it. (It would otherwise cause the query to fail.)

#   The list can be built hypothetically and acted on.  An alternative way of looking
# at this is that all list statements "are true" in that they define the resource. That
# resource is then used for nothing else. Yes, we can search to see whether list is in the
# store, as there may be a statemnt aboiut it, but built-ins can work on hypothetical lists.

# Utilities to search the store:

#    def any(self, quad):             # Returns first match for one variable
#        variables = []
#        q2 = [ quad[0], quad[1], quad[2], quad[3]]  # tuple to list
#        for p in ALL4:
#            if quad[p] == None:
#                v = self.intern((RESOURCE, "internaluseonly:#var"+`p`))
#               variables.append(v)
#                q2[p] = v
#        unmatched = [ ( q2[0], q2[1], q2[2], q2[3])]
#        listOfBindings = []
#        count = self.match(unmatched, variables, [], action=self.collectBindings, param=listOfBindings, justOne=1)
#        if listOfBindings == []: return None
##        progress("#@@@ any findss %s " % listOfBindings)
#
#        return listOfBindings[0][0][1]  # First result, first variable, value.


    def every(self, quad):             # Returns a list of lists of values
        variables = []
        q2 = [ quad[0], quad[1], quad[2], quad[3]]  # tuple to list
        for p in ALL4:
            if quad[p] == None:
                v = self.intern((RESOURCE, "internaluseonly:#var"+`p`))
                variables.append(v)
                q2[p] = v
        unmatched = [ ( q2[0], q2[1], q2[2], q2[3])]
        listOfBindings = []
        count = match(self, unmatched, variables, [], action=collectBindings, param=listOfBindings, justOne=0)
        results = []
        for bindings in listOfBindings:
            res = []
            for var, val in bindings:
                res.append(val)
            results.append(res)
        return results


    # Note that there are no unbound variables in a list L
    def _noteBoundList(self, L, queue, allVariables):
        if chatty > 49: progress("Bound list: " + x2s(L))
        for i in range(len(queue)):
            item = queue[i]
            state, short, consts, vars, boundLists, quad = item
            for p in PARTS:
                if quad[p] is L:
                    # Might not be on vars yet, as may be in state 99
                    if p in queue[i][VARS]: queue[i][VARS].remove(p)
                    queue[i][BOUNDLISTS].append(p)
                    if queue[i][STATE] == 20 or queue[i][STATE] == 50:
                        state, short, consts, vars, boundLists, quad = queue[i]
                        queue[i] = (99, short, consts, vars, boundLists, quad)
                        # Try again    @@@ reorder!!
            if quad[PRED] is L and (quad[OBJ] not in allVariables):  # Propagate
                self._noteBoundList(quad[SUBJ], queue, allVariables)

# Generic match routine, outer level:  Prepares query
        
    def  match(self,                 # Neded for getting interned constants
               unmatched,           # Tuple of interned quads we are trying to match CORRUPTED
               variables,           # List of variables to match and return CORRUPTED
               existentials,        # List of variables to match to anything
                                    # Existentials or any kind of variable in subexpression
               smartIn = [],        # List of contexts in which to use builtins - typically the top one
               action = None,       # Action routine return subtotal of actions
               param = None,        # a tuple, see the call itself and conclude()
               hypothetical =0,     # The formulae are not in the store - check for their contents
               justOne = 0):        # Flag: Stop when you find the first one

        """ Apply action(bindings, param) to succussful matches
        """
        if action == None: action=self.doNothing
        
        if chatty > 50:
            progress( "match: called with %i terms." % (len(unmatched)))
            if chatty > 90: progress( setToString(unmatched, variables))

        if not hypothetical:
            for x in existentials[:]:   # Existentials don't count when they are just formula names
                                        # Also, we don't want a partial match. 
                if isinstance(x,Formula):
                    existentials.remove(x)

        queue = []   #  Unmatched with more info, in order
        for quad in unmatched:
            item = (99, INFINITY, [], [], [], quad) 
#        self.quad = quad   # The pattern being searched for
#        self.state = 99    # See table elsewhere
#        self.short = 99999 # Shortest one to check 
#        self.consts = []   # List of positions (PRED, SUBJ, etc) where quad is bound (not var)
#        self.vars = []     #   Positions where quad has a variable (local exist'l, or rule univ'l), eEXcluding: 
#        self.boundLists = [] # Variables which are in fact just list Ids for Lists containing no unbound vars
            queue.append(item)
        return self.query(queue, variables, existentials, smartIn, action, param,
                          bindings=[], justOne=justOne)


    STATES = """State values as follows, high value=try first:
    99  State unknown - to be [re]calculated.
    60  Not a light built-in, haven't searched yet.
    50  Light built-in, not enough constants to calculate, haven't searched yet.
    20  Light built-in, not enough constants to calculate, search failed.
    10  Heavy built-in, not enough constants to calculate, search failed
     5  List defining statement, search failed.
                    """

    def  query(self,                # Neded for getting interned constants
               queue,               # Ordered queue of items we are trying to match CORRUPTED
               variables,           # List of variables to match and return
               existentials,        # List of variables to match to anything
                                    # Existentials or any kind of variable in subexpression
               smartIn = [],        # List of contexts in which to use builtins - typically the top one
               action = None,       # Action routine return subtotal of actions
               param = None,        # a tuple, see the call itself and conclude()
               bindings = [],       # Bindings discovered so far
               newBindings = [],    # Bindings JUST discovered - to be folded in
               justOne = 0):        # Flag: Stop when you find the first one

        """ Apply action(bindings, param) to succussful matches
    bindings      collected matches already found
    newBindings  matches found and not yet applied - used in recursion
        """
        if action == None: action=self.doNothing
        total = 0
        
        if chatty > 50:
            progress( "QUERY: called %i terms, %i bindings %s, (new: %s)" %
                      (len(queue),len(bindings),bindingsToString(bindings),
                       bindingsToString(newBindings)))
            if chatty > 90: progress( queueToString(queue))

        for pair in newBindings:   # Take care of business left over from recursive call
            if chatty>40: progress("New binding:  %s -> %s" % (x2s(pair[0]), x2s(pair[1])))
            if pair[0] in variables:
                variables.remove(pair[0])
                bindings.append(pair)  # Record for posterity
            else:      # Formulae aren't bed as existentials, unlike lists. hmm.
                if not isinstance(pair[0], Formula): # Hack - else rules13.n3 fails @@
                    existentials.remove(pair[0]) # Can't match anything anymore, need exact match

        # Perform the substitution, noting where lists become boundLists.
        # We do this carefully, messing up the order only of things we have already processed.
        i = len(queue) - 1
        while i >= 0:  # A valid index into q
            state, short, consts, vars, boundLists, quad = queue[i]
            changed = 0
            newBoundList = 0
            for var, val in newBindings:
                for p in ALL4:  # any variables, even list IDs, can be bound
                    if quad[p] is var:
                        if p in vars: vars.remove(p)
                        changed = 1
                        if (p == OBJ
                            and (PRED in boundLists or quad[PRED] is self.nil)): # and this is a list with no vars in daml:rest   @@@@???
                            newBoundList = 1
            if changed:   # Has fewer variables now .. this is progress
                state = 99
                quad = _lookupQuad(newBindings, quad)
                queue[i] = (state, short, consts, vars, boundLists, quad)
                if newBoundList:
                    self._noteBoundList(quad[SUBJ], queue, variables + existentials)  # The list is now bound, so propagate this up
                    # Note that noteBoundList affcets queue, so must store our changed first.

            i = i - 1


        if len(queue) == 0:
            if chatty>50: progress( "# QUERY FOUND MATCH with bindings: " + bindingsToString(bindings))
            return action(bindings, param)  # No terms left .. success!


#        queue.sort()  # Should sort by first thing ie state

        while len(queue) > 0:

            if (chatty > 90) or (chatty > 65) and queue[-1][STATE] != 99:
                progress( "   query iterating with %i terms, %i bindings: %s; %i new bindings: %s ." %
                          (len(queue),
                           len(bindings),bindingsToString(bindings),
                           len(newBindings),bindingsToString(newBindings)))
                progress (queueToString(queue))


            # Take last.  (Could search here instead of keeping queue in order)
            # state, short, consts, vars, boundLists, quad = queue.pop()

            best = len(queue) -1 # , say...
            i = best - 1
            while i >=0:
                if (queue[i][STATE] > queue[best][STATE]
                            or queue[i][STATE] == queue[best][STATE]
                               and (len(queue[i][CONSTS]) < len(queue[best][CONSTS])
                                    or len(queue[i][CONSTS]) == len(queue[best][CONSTS])
                                            and queue[i][SHORT] < queue[best][SHORT])): best=i
                i = i - 1                
            state, short, consts, vars, boundLists, quad = queue[best]
            queue = queue[:best] + queue[best+1:]


            con, pred, subj, obj = quad
            if state == 99:   # Haven't looked at it yet, or things have changed

                # First, check how many variables in this term, and how long it would take to search:
                short = INFINITY    
                consts = []         # Parts of speech to test for match
                vars = []           # Parts of speech which are variables
#                boundLists = []     # Parts of speech which are bound lists
                for p in ALL4 :
                    if p in boundLists: # If we know this from before
                        pass
                    elif quad[p] in variables + existentials:
                        vars.append(p)
                    else:
                        length = len(quad[p].occursAs[p])   # The length of search we would have to do
                        if length < short:
                            short = length
                            consts = [ p ] + consts    # consts[0] reserved for shortest search
                        else:
                            consts = consts + [ p ]
                # Seed bound lists:          
                if (PRED in boundLists or quad[PRED] is self.nil) and SUBJ in vars and OBJ not in vars:
                    self._noteBoundList(quad[SUBJ], queue, variables + existentials)
                            
                # Next, check for "light" (quick) built-in functions
#                progress ("Q BuiltIn %s isinstnace LightBuiltIn = %i" % (`pred`,isinstance(pred, LightBuiltIn)))
#                progress ("    "+`pred.__class__`)
#                progress ("    "+ `LightBuiltIn`)
                
                if con in smartIn and isinstance(pred, LightBuiltIn):
                    if len(vars) == 0:   # no variables: constant expression - we can definitely evaluate it
                        obj_py = self._toPython(obj, OBJ in boundLists, queue)
                        subj_py = self._toPython(subj, SUBJ in boundLists, queue)
                        if pred.evaluate(self, con, subj, subj_py, obj, obj_py):
                            return self.query(queue, variables, existentials, smartIn, action, param,
                                          bindings, [], justOne) # No new bindings but success in calculated logical operator
                                                        #    and so, one less query line.
                        else: return 0   # We absoluteley know this won't match with this in it
                    elif len(vars) == 1 :  # The statement has one variable - try functions
                        if vars[0] == OBJ and isinstance(pred, Function):
                            subj_py = self._toPython(subj, SUBJ in boundLists, queue)
                            result = pred.evaluateObject(self, con, subj, subj_py)
                            if result == None: state = 50 # Light, Waiting for SOME CONDITION, not searched
                            else: return self.query(queue, variables, existentials, smartIn, action, param,
                                                      bindings, [ (obj, result)], justOne)
                        elif vars[0] == SUBJ and isinstance(pred, ReverseFunction):
                            obj_py = self._toPython(obj, OBJ in boundLists, queue)
                            result = pred.evaluateSubject(self, con, obj, obj_py)
                            if result == None: state = 50 # Light, Waiting for constants, not searched
                            else: return self.query(queue, variables, existentials, smartIn, action, param,
                                                      bindings, [ (subj, result)], justOne)
                    # Now we have a light builtin needs search, otherwise waiting for enough constants to run
                    state = 50

                else:   # Not a light builtin
                    if short == 0:  # Skip search if no possibilities!
                        if PRED in boundLists: state = 5  # hypothetical
                        elif not isinstance(pred, HeavyBuiltIn): return 0  # No way
                        
                    state = 60   # Not a light built in, not searched. Try it when it comes around.


            elif state == 50 or state == 60: #  Not searched yet
                # Search the store
                if len(vars) == 4:
                    raise notimp # Can't handle something with no constants at all.
                    return 0    
                                # Not a closed world problem - and this is a cwm!
                                # Actually, it could be a valid problem -but pathalogical.
                shortest_p = consts[0]
                if chatty > 36:
                    progress( "# Searching %i with %s in slot %i for %s" %(
                        len(quad[shortest_p].occursAs[shortest_p]),
                        x2s(quad[shortest_p]),
                        shortest_p,
                        quadToString(quad, vars, boundLists)))
                    if chatty > 95:
                        progress( "#    where variables are")
                        for i in variables + existentials:
                            progress ("#   var or ext:      " + `i`[-8:-1]) 

                matches = 0
                for s in quad[shortest_p].occursAs[shortest_p]:
                    for p in consts:
                        if s.triple[p] is not quad[p]:
                            if chatty>90: progress( "   Rejecting " + quadToString(s.triple) +
                                                    "\n      for " + quadToString(quad))
                            break
                    else:  # found match
                        nb = []
                        reject = 0
                        for p in vars:
                            binding = ( quad[p], s.triple[p])
                            duplicate = 0
                            for oldbinding in nb:
                                if oldbinding[0] is quad[p]:
                                    if oldbinding[1] is binding[1]: # A binding we have already - no sweat
                                        duplicate = 1
                                    else: # A clash - reject binding the same to var to 2 different things!
                                        reject = 1
                            if not duplicate:
                                nb.append(( quad[p], s.triple[p]))
                        if not reject:
                        #  We must take copies of the lists each time, as they get corrupted and we need them again:
                            total = total + self.query(queue[:], variables[:], existentials[:], smartIn, action, param,
                                                  bindings[:], nb[:], justOne=justOne)
                            matches = matches + 1
                            if justOne and total: return total

                if state == 50: state = 20   # Note that search on light builtin tried
                else: # state was 60 (not light, may be heavy)
                    state = 0  # Not found and if not heavy (below), fail

# notIncludes has to be a recursive call, but log:includes just extends the search
                    if con in smartIn and isinstance(pred, HeavyBuiltIn):
                        state = 10   # Heavy, man
                        if pred is self.includes:
                            if (isinstance(subj, Formula)
                                and isinstance(obj, Formula)):

                                more_unmatched, more_variables = self.oneContext(quad[OBJ])
                                _substitute([( obj, subj)], more_unmatched)
                                _substitute(bindings, more_unmatched)
                                for quad in more_unmatched:
                                    item = 99, 0, [], [], [], quad
                                    queue.append(item)
                                existentials = existentials + more_variables
                                if chatty > 40: progress(" **** Includes: Adding %i new terms and %s as new existentials."%
                                                         (len(more_unmatched),seqToString(more_variables)))
                                return self.query(queue, variables, existentials, smartIn, action, param,
                                                  bindings=bindings, justOne=justOne) # bindings new to this forumula
                            else:  # Not forumla
                                if len(vars) == 0: return total  # Not going to work if not forumlae ever
                                # otherwise might work if vars 

                        elif len(vars)==0:  # Deal with others

                                if pred.evaluate2(self, subj, obj, variables[:], bindings[:]):
                                    if chatty > 80: progress("Heavy predicate succeeds")
                                    return self.query(queue, variables, existentials, smartIn, action, param,
                                                  bindings, [],justOne=justOne) # No new bindings but success in calculated logical operator
                                else:
                                    if chatty > 80: progress("Heavy predicate fails")
                                    return total   # We absoluteley know this won't match with this in it
                        elif len(vars) == 1 :  # The statement has one variable - try functions
                            if vars[0] == OBJ and isinstance(pred, Function):
                                result = pred.evaluateObject2(self, subj)
                                if result != None:
                                    return self.query(queue, variables, existentials, smartIn, action, param,
                                                          bindings, [ (obj, result)],justOne=justOne)
                            elif vars[0] == SUBJ and isinstance(pred, ReverseFunction):
                                obj_py = self._toPython(obj, OBJ in boundLists, queue)
                                result = pred.evaluateSubject2(self, obj, obj_py)
                                if result != None:  # There is some such result
                                    return self.query(queue, variables, existentials, smartIn, action, param,
                                                          bindings, [ (subj, result)],justOne=justOne)
                    # Now we have a heavy builtin  waiting for enough constants to run
                        state = 10
                    elif pred is self.nil or PRED in boundLists:  # This is a structural line: a hypothesis. Keep it
                        state = 5
                    else: # Not heavy, done search.
                        if chatty > 80: progress("Not builtin, search done, %i found." % total)
                        return total
                        
            elif state == 5: # All we are left with are list definitions, which are fine
                if chatty>50: progress( "# QUERY FOUND MATCH (dropping lists) with bindings: " + bindingsToString(bindings))
                return action(bindings, param)  # No non-list terms left .. success!

            else: # state was not 99, 60 or 50, so either 20 or 10:
                if chatty > 0:
                    progress("@@@@ Warning: query can't find term which will work.")
                    progress( "   state is %s, que length %i" % (state, len(queue)))

                    item = state, short, consts, vars, boundLists, quad
                    progress("@@ Current item: %s" % itemToString(item))
                    progress(queueToString(queue))
                return total  # Forget it
#                raise internalError # We have something in an unknown state in the queue

# Reinsert into queue, so that the easiest tasks are later on:                    
# We prefer terms with a single variable to those with two.
# (Those with none we immediately check and therafter ignore)
# Secondarily, we prefer short searches to long ones.

            if state != 0:   # state 0 means leave me off the list
                i = 0
                while (i <len(queue)
                       and (state > queue[i][0]
                            or state == queue[i][0] and (len(consts) > len(queue[i][2])
                                                                 or len(consts) == len(queue[i][2])
                                                                     and short < queue[i][1]))):
                    i = i + 1
                item = state, short, consts, vars, boundLists, quad
                queue[i:i] = [ item ]
            # And loop back to take the next item

        if queue != []:
            raise canNotResolve  # we have ended up with an impossible combination of things it seems
        return total
         
    def doNothing(self, bindings, param):
        if chatty>99: progress( "Success! found it!")
        return 1                    # Return count of calls only

    # Whether we do a smart match determines whether we will be able to conclude
    # things which in fact we knew already thanks to the builtins.
    def conclude(self, bindings, param):  # Returns number of statements added to store
        store, conclusions, targetContext, oes = param
        if chatty >60: progress( "\n#Concluding tentatively..." + bindingsToString(bindings))

        myConclusions = conclusions[:]
        _substitute(bindings, myConclusions)
        # Does this conclusion exist already in the database?
        found = self.match(myConclusions[:], [], oes[:], smartIn=[targetContext],hypothetical=1, justOne=1)  # Find first occurrence, SMART
        if found:
            if chatty>60: progress( "Concluding: Forget it, already had" + bindingsToString(bindings))
            return 0
        if chatty>60: progress( "Concluding definitively" + bindingsToString(bindings))
        
        # Regenerate a new form with its own existential variables
        # because we can't reuse the subexpression identifiers.
        bindings2 = []
        for i in oes:
            if isinstance(i, Formula):
                g = store.genid(targetContext, FORMULA)  #  Generate with same type as original
            else:
                g = store.genid(targetContext, RESOURCE)  #  Generate with same type as original
            bindings2.append((i,g))
        total = 0
        for q in myConclusions:
            q2 = _lookupQuad(bindings2, q)
            total = total + store.storeQuad(q2)
            if chatty>75: progress( "        *** Conclude: " + quadToString(q2))
        return total

# An action routine for collecting bindings:

    def collectBindings(self, bindings, param):  # Returns number of bindings found and collects them
        param = param + bindings
        return len(bindings)
    

def _substitute(bindings, list):
    for i in range(len(list)):
        q = list[i]
        list[i] = _lookupQuad(bindings, q)
                            
def _lookupQuad(bindings, q):
	context, pred, subj, obj = q
	return (
            _lookup(bindings, context),
            _lookup(bindings, pred),
            _lookup(bindings, subj),
            _lookup(bindings, obj) )

def _lookup(bindings, value):
    for left, right in bindings:
        if left == value: return right
    return value


#   DIAGNOSTIC STRING OUTPUT
#
def bindingsToString(bindings):
    str = ""
    for x, y in bindings:
        str = str + (" %s->%s" % ( x2s(x), x2s(y)))
    return str

def setToString(set, vars=[], boundLists = []):
    str = ""
    for q in set:
        str = str+ "        " + quadToString(q, vars, boundLists) + "\n"
    return str

def seqToString(set):
    str = ""
    for x in set[:-1]:
        str = str+ " " + x2s(x) + ","
    for x in set[-1:]:
        str = str+ " " + x2s(x)
    return str

def queueToString(queue):
    str = ""
    for item in queue:
        str = str + "    "+ itemToString(item) + "\n"
    return str


def quadToString(q, vars=[], boundLists = []):
    qm=[" "," "," "," "]
    for p in ALL4:
        if p in vars: qm[p]= "?"
        if p in boundLists: qm[p]= "~"
    return "%s%s ::  %8s%s %8s%s %8s%s ." %(x2s(q[CONTEXT]), qm[CONTEXT],
                                            x2s(q[SUBJ]),qm[SUBJ],
                                            x2s(q[PRED]),qm[PRED],
                                            x2s(q[OBJ]),qm[OBJ])
def itemToString(item):
    return "%3i)  %s  short=%i" % (item[STATE],
                                   quadToString(item[QUAD], item[VARS], item[BOUNDLISTS]),
                                   item[SHORT] )

def x2s(x):
    if isinstance(x, Literal):
        return '"' + x.string[0:8] + '"'
    s = `x`[1:-1]
    p = string.find(s,'#')
    if p >= 0: return s[p+1:]
    p = string.find(s,'/')
    if p >= 0: return s[p+1:]
    return s



######################################################### Tests
  
def test():
    import sys
    testString = []
    
    t0 = """bind x: <http://example.org/x-ns/> .
	    bind dc: <http://purl.org/dc/elements/1.1/> ."""

    t1="""[ >- x:firstname -> "Ora" ] >- dc:wrote ->
    [ >- dc:title -> "Moby Dick" ] .
     bind default <http://example.org/default>.
     <uriPath> :localProp defaultedName .
     
"""
    t2="""
[ >- x:type -> x:Receipt;
  >- x:number -> "5382183";
  >- x:for -> [ >- x:USD -> "2690" ];
  >- x:instrument -> [ >- x:type -> x:visa ] ]

>- x:inReplyTo ->

[ >- x:type -> x:jobOrder;
  >- x:number -> "025709";
 >- x:from ->

 [
  >- x:homePage -> <http://www.topnotchheatingandair.com/>;
  >- x:est -> "1974";
  >- x:address -> [ >- x:street -> "23754 W. 82nd Terr.";
      >- x:city -> "Lenexa";
      >- x:state -> "KS";
      >- x:zip -> "66227"];
  >- x:phoneMain -> <tel:+1-913-441-8900>;
  >- x:fax -> <tel:+1-913-441-8118>;
  >- x:mailbox -> <mailto:info@topnotchheatingandair.com> ]
].    

<http://www.davelennox.com/residential/furnaces/re_furnaces_content_body_elite90gas.asp>
 >- x:describes -> [ >- x:type -> x:furnace;
 >- x:brand -> "Lennox";
 >- x:model -> "G26Q3-75"
 ].
"""
    t3="""
bind pp: <http://example.org/payPalStuff?>.
bind default <http://example.org/payPalStuff?>.

<> a pp:Check; pp:payee :tim; pp:amount "$10.00";
  dc:author :dan; dc:date "2000/10/7" ;
  is pp:part of [ a pp:Transaction; = :t1 ] .
"""

# Janet's chart:
    t4="""
bind q: <http://example.org/>.
bind m: <>.
bind n: <http://example.org/base/>.
bind : <http://void-prefix.example.org/>.
bind w3c: <http://www.w3.org/2000/10/org>.

<#QA> :includes 
 [  = w3c:internal ; :includes <#TAB> , <#interoperability> ,
     <#validation> , w3c:wai , <#i18n> , <#translation> ,
     <#readability_elegance>, w3c:feedback_accountability ],
 [ = <#conformance>;
     :includes <#products>, <#content>, <#services> ],
 [ = <#support>; :includes
     <#tools>, <#tutorials>, <#workshops>, <#books_materails>,
     <#certification> ] .

<#internal> q:supports <#conformance> .  
<#support> q:supports <#conformance> .

"""

    t5 = """

bind u: <http://www.example.org/utilities>
bind default <>

:assumption = { :fred u:knows :john .
                :john u:knows :mary .} .

:conclusion = { :fred u:knows :mary . } .

"""
    thisURI = "file:notation3.py"

    testString.append(  t0 + t1 + t2 + t3 + t4 )
#    testString.append(  t5 )

#    p=notation3.SinkParser(RDFSink(),'http://example.org/base/', 'file:notation3.py',
#		     'data:#')

    r=notation3.SinkParser(notation3.ToN3(sys.stdout.write, base='file:output'),
                  thisURI,'http://example.org/base/',)
    r.startDoc()
    
    progress( "=== test stringing: ===== STARTS\n " + t0 + "\n========= ENDS\n")
    r.feed(t0)

    progress( "=== test stringing: ===== STARTS\n " + t1 + "\n========= ENDS\n")
    r.feed(t1)

    progress( "=== test stringing: ===== STARTS\n " + t2 + "\n========= ENDS\n")
    r.feed(t2)

    progress( "=== test stringing: ===== STARTS\n " + t3 + "\n========= ENDS\n")
    r.feed(t3)

    r.endDoc()

    progress( "----------------------- Test store:")

    store = RDFStore()

    thisDoc = store.internURI(thisURI)    # Store used interned forms of URIs
    thisContext = store.intern((FORMULA, thisURI+ "#_formula"))    # @@@ Store used interned forms of URIs

    # (sink,  thisDoc,  baseURI, bindings)
    p = notation3.SinkParser(store,  thisURI, 'http://example.org/base/')
    p.startDoc()
    p.feed(testString[0])
    p.endDoc()

    progress( "\n\n------------------ dumping chronologically:")

    store.dumpChronological(thisContext, notation3.ToN3(sys.stdout.write, base=thisURI))

    progress( "\n\n---------------- dumping in subject order:")

    store.dumpBySubject(thisContext, notation3.ToN3(sys.stdout.write, base=thisURI))

    progress( "\n\n---------------- dumping nested:")

    store.dumpNested(thisContext, notation3.ToN3(sys.stdout.write, base=thisURI))

    progress( "Regression test **********************************************")

    
    testString.append(reformat(testString[-1], thisURI))

    if testString[-1] == testString[-2]:
        progress( "\nRegression Test succeeded FIRST TIME- WEIRD!!!!??!!!!!\n")
        return
    
    testString.append(reformat(testString[-1], thisURI))

    if testString[-1] == testString[-2]:
        progress( "\nRegression Test succeeded SECOND time!!!!!!!!!\n")
    else:
        progress( "Regression Test Failure: ===================== LEVEL 1:")
        progress( testString[1])
        progress( "Regression Test Failure: ===================== LEVEL 2:")
        progress( testString[2])
        progress( "\n============================================= END")

    testString.append(reformat(testString[-1], thisURI))
    if testString[-1] == testString[-2]:
        progress( "\nRegression Test succeeded THIRD TIME. This is not exciting.\n")

    
                
def reformat(str, thisURI):
    if 0:
        progress( "Regression Test: ===================== INPUT:")
        progress( str)
        progress( "================= ENDs")
    buffer=StringIO.StringIO()
    r=notation3.SinkParser(notation3.ToN3(buffer.write, base=thisURI), thisURI)
    r.startDoc()
    r.feed(str)
    r.endDoc()

    return buffer.getvalue()    # Do we need to explicitly close it or will it be GCd?
    


              
            
        
############################################################## Web service
# Author: DanC
#
import random
import time
import cgi
import sys
import StringIO

def serveRequest(env):
    import random #for message identifiers. Hmm... should seed from request

    #sys.stderr = open("/tmp/connolly-notation3-log", "w")

    form = cgi.FieldStorage()

    if form.has_key('data'):
	try:
	    convert(form, env)
	except BadSyntax, e:
	    print "Status: 500 syntax error in input data"
	    print "Content-type: text/plain"
	    print
	    print e
	    

	except:
	    import traceback

	    print "Status: 500 error in python script. traceback follows"
	    print "Content-type: text/plain"
	    print
	    traceback.print_exc(sys.stdout)
	    
    else:
	showForm()

def convert(form, env):
    """ raises KeyError if the form data is missing required fields."""

    serviceDomain = 'w3.org' #@@ should compute this from env['SCRIPT_NAME']
         # or whatever; cf. CGI spec
    thisMessage = 'mid:t%s-r%f@%s' % (time.time(), random.random(), serviceDomain)

    data = form['data'].value

    if form.has_key('genspace'):
	genspace = form['genspace'].value
    else: genspace = thisMessage + '#_'

    if form.has_key('baseURI'):	baseURI = form['baseURI'].value
    elif env.has_key('HTTP_REFERER'): baseURI = env['HTTP_REFERER']
    else: baseURI = None

    # output is buffered so that we only send
    # 200 OK if all went well
    buf = StringIO.StringIO()

    xlate = notation3.ToRDFParser(buf, baseURI, thisMessage, genspace)
    xlate.startDoc()
    xlate.feed(data)
    xlate.endDoc()

    print "Content-Type: text/xml"
    #hmm... other headers? last-modified?
    # handle if-modified-since? i.e. handle input by reference?
    print # end of HTTP response headers
    print buf.getvalue()

def showForm():
    print """Content-Type: text/html

<html>
<title>Notation3 to RDF Service</title>
<body>

<form method="GET">
<textarea name="data" rows="4" cols="40">
bind dc: &lt;http://purl.org/dc/elements/1.1/&gt;
</textarea>
<input type="submit"/>
</form>

<div>
<h2>References</h2>
<ul>
<li><a href="http://www.w3.org/DesignIssues/Notation3">Notation 3</a></li>
<li><a href="http://www.python.org/doc/">python documentation</a></li>
<li><a href="http://www.w3.org/2000/01/sw/">Semantic Web Development</a></li>
</ul>
</div>

<address>
<a href="http://www.w3.org/People/Connolly/">Dan Connolly</a>
</address>

</body>
</html>
"""
#################################################  Command line
    
def doCommand():
        """Command line RDF/N3 tool
        
 <command> <options> <inputURIs>
 
--pipe      Don't store, just pipe out *

--rdf       Input & Output ** in RDF M&S 1.0 insead of n3 from now on
--n3        Input & Output in N3 from now on
--rdf=flags Input & Output ** in RDF and set given RDF flags
--n3=flags  Input & Output in N3 and set N3 flags
--ntriples  Input & Output in NTriples (equiv --n3=spart -bySubject -quiet)
--ugly      Store input and regurgitate *
--bySubject Store input and regurgitate in subject order *
--no        No output *
            (default is to store and pretty print with anonymous nodes) *
--apply=foo Read rules from foo, apply to store, adding conclusions to store
--filter=foo Read rules from foo, apply to store, REPLACING store with conclusions
--rules     Apply rules in store to store, adding conclusions to store
--think     as -rules but continue until no more rule matches (or forever!)
--reify     Replace the statements in the store with statements describing them.
--flat      Reify only nested subexpressions (not top level) so that no {} remain.
--help      print this message
--chatty=50 Verbose output of questionable use, range 0-99
 

            * mutually exclusive
            ** doesn't work for complex cases :-/
Examples:
  cwm --rdf foo.rdf --n3 --pipe     Convert from rdf/xml to rdf/n3
  cwm foo.n3 bar.n3 --think         Combine data and find all deductions
  cwm foo.n3 --flat --n3=spart

"""
        
        import urllib
        import time
        global chatty
        global sax2rdf
#        import sax2rdf

        option_need_rdf_sometime = 0  # If we don't need it, don't import it
                               # (to save errors where parsers don't exist)
        
        option_pipe = 0     # Don't store, just pipe though
        option_inputs = []
        option_test = 0     # Do simple self-test
        option_reify = 0    # Flag: reify on output  (process?)
        option_flat = 0    # Flag: reify on output  (process?)
        option_outURI = None
        option_outputStyle = "-best"
        _gotInput = 0     #  Do we not need to take input from stdin?
        option_meta = 0
        option_rdf_flags = ""  # Random flags affecting parsing/output
        option_n3_flags = ""  # Random flags affecting parsing/output
        option_quiet = 0

        _step = 0           # Step number used for metadata

        hostname = "localhost" # @@@@@@@@@@@ Get real one
        
        # The base URI for this process - the Web equiv of cwd
#	_baseURI = "file://" + hostname + os.getcwd() + "/"
	_baseURI = "file:" + fixslash(os.getcwd()) + "/"
	
        option_format = "n3"      # Use RDF rather than XML
        option_first_format = None
        
        _outURI = _baseURI
        option_baseURI = _baseURI     # To start with - then tracks running base
        for arg in sys.argv[1:]:  # Command line options after script name
            if arg.startswith("--"): arg = arg[1:]   # Chop posix-style double dash to one
            _equals = string.find(arg, "=")
            _lhs = ""
            _rhs = ""
            if _equals >=0:
                _lhs = arg[:_equals]
                _rhs = arg[_equals+1:]
                _uri = urlparse.urljoin(option_baseURI, _rhs) # Make abs from relative
            if arg == "-test":
                option_test = 1
                _gotInput = 1
            elif arg == "-ugly": option_outputStyle = arg
            elif _lhs == "-base": option_baseURI = _uri
            elif arg == "-rdf":
                option_format = "rdf"
                option_need_rdf_sometime = 1
            elif _lhs == "-rdf":
                option_format = "rdf"
                option_rdf_flags = _rhs
                option_need_rdf_sometime = 1
            elif arg == "-n3": option_format = "n3"
            elif _lhs == "-n3":
                option_format = "n3"
                option_n3_flags = _rhs
            elif arg == "-quiet": option_quiet = 1
            elif arg == "-pipe": option_pipe = 1
            elif arg == "-bySubject": option_outputStyle = arg
            elif arg == "-triples" or arg == "-ntriples":
                option_format = "n3"
                option_n3_flags = "spart"
                option_outputStyle = "-bySubject"
                option_quiet = 1
            elif _lhs == "-outURI": option_outURI = _uri
            elif _lhs == "-chatty": chatty = int(_rhs)
            elif arg[:7] == "-apply=": pass
            elif arg == "-reify": option_reify = 1
            elif arg == "-flat": option_flat = 1
            elif arg == "-help":
                print doCommand.__doc__
                print notation3.ToN3.flagDocumentation
                return
            elif arg[0] == "-": pass  # Other option
            else :
                option_inputs.append(urlparse.urljoin(option_baseURI,arg))
                _gotInput = _gotInput + 1  # input filename
            

        # This is conditional as it is not available on all platforms,
        # needs C and Python to compile xpat.
        if option_need_rdf_sometime:
            import sax2rdf      # RDF1.0 syntax parser to N3 RDF stream

# Between passes, prepare for processing
        chatty =  0
#  Base defauts

        if option_baseURI == _baseURI:  # Base not specified explicitly - special case
            if _outURI == _baseURI:      # Output name not specified either
                if _gotInput == 1 and not option_test:  # But input file *is*, 
                    _outURI = option_inputs[0]        # Just output to same URI
                    option_baseURI = _outURI          # using that as base.

#  Fix the output sink
        
	if option_format == "rdf":
            _outSink = notation3.ToRDF(sys.stdout, _outURI, base=option_baseURI, flags=option_rdf_flags)
        else:
            _outSink = notation3.ToN3(sys.stdout.write, base=option_baseURI,
                                      quiet=option_quiet, flags=option_n3_flags)
        version = "$Id$"
	if not option_quiet:
            _outSink.makeComment("Processed by " + version[1:-1]) # Strip $ to disarm
            _outSink.makeComment("    using base " + option_baseURI)
        if option_reify: _outSink = notation3.Reifier(_outSink, _outURI+ "#_formula")
        if option_flat: _outSink = notation3.Reifier(_outSink, _outURI+ "#_formula", flat=1)


        if option_pipe:
            _store = _outSink
        else:
            _metaURI = urlparse.urljoin(option_baseURI, "RUN/") + `time.time()`  # Reserrved URI @@
            _store = RDFStore( _outURI+"#_gs", metaURI=_metaURI)
            workingContext = _store.intern((FORMULA, _outURI+ "#_formula"))   #@@@ Hack - use metadata
#  Metadata context - storing information about what we are doing

#            _store.reset(_metaURI)
            history = None
	

        if not _gotInput: #@@@@@@@@@@ default input
            _inputURI = _baseURI # Make abs from relative
            p = notation3.SinkParser(_store,  _inputURI)
            p.load("")
            del(p)
            if not option_pipe:
                inputContext = _store.intern((FORMULA, _inputURI+ "#_formula"))
                history = inputContext
                if inputContext is not workingContext:
                    _store.moveContext(inputContext,workingContext)  # Move input data to output context


#  Take commands from command line: Second Pass on command line:

        option_format = "n3"      # Use RDF rather than XML
        option_rdf_flags = ""
        option_n3_flags = ""
        option_quiet = 0
        _outURI = _baseURI
        option_baseURI = _baseURI     # To start with
        for arg in sys.argv[1:]:  # Command line options after script name
            if arg.startswith("--"): arg = arg[1:]   # Chop posix-style double dash to one
            _equals = string.find(arg, "=")
            _lhs = ""
            _rhs = ""
            if _equals >=0:
                _lhs = arg[:_equals]
                _rhs = arg[_equals+1:]
                _uri = urlparse.urljoin(option_baseURI, _rhs) # Make abs from relative
                
            if arg[0] != "-":
                _inputURI = urlparse.urljoin(option_baseURI, arg) # Make abs from relative
                if option_format == "rdf" : p = sax2rdf.RDFXMLParser(_store,  _inputURI)
                else: p = notation3.SinkParser(_store,  _inputURI)
                p.load(_inputURI)
                del(p)
                if not option_pipe:
                    inputContext = _store.intern((FORMULA, _inputURI+ "#_formula"))
                    _store.moveContext(inputContext,workingContext)  # Move input data to output context
                    _step  = _step + 1
                    s = _metaURI + `_step`  #@@ leading 0s to make them sort?
                    if doMeta and history:
                        _store.storeQuad((_store._experience, META_mergedWith, s, history))
                        _store.storeQuad((_store._experience, META_source, s, inputContext))
                        _store.storeQuad((_store._experience, META_run, s, run))
                        history = s
                    else:
                        history = inputContext
                _gotInput = 1

            elif arg == "-help":
                print doCommand.__doc__

            elif arg == "-test": test()
            elif _lhs == "-base":
                option_baseURI = _uri
                progress("Base now "+option_baseURI)

            elif arg == "-ugly":
                option_outputStyle = arg            

            elif arg == "-pipe": pass
            elif _lhs == "-outURI": option_outURI = _uri

            elif arg == "-rdf": option_format = "rdf"
            elif _lhs == "-rdf":
                option_format = "rdf"
                option_rdf_flags = _rhs
            elif arg == "-n3": option_format = "n3"
            elif _lhs == "-n3":
                option_format = "n3"
                option_n3_flags = _rhs
            elif arg == "-quiet" : option_quiet = 1            
            elif _lhs == "-chatty": chatty = int(_rhs)

            elif arg == "-reify":
                pass

            elif arg == "-flat":  # reify only nested expressions, not top level
                pass

            elif option_pipe: ############## End of pipable options
                print "# Command line error: %s illegal option with -pipe", arg
                break

            elif arg == "-triples" or arg == "-ntriples":
                option_format = "n3"
                option_n3_flags = "spart"
                option_outputStyle = "-bySubject"
                option_quiet = 1

            elif arg == "-bySubject":
                option_outputStyle = arg            

            elif arg[:7] == "-apply=":
                filterContext = (_store.intern((FORMULA, _uri+ "#_formula")))
                if chatty > 4: print "# Input rules to apply from ", _uri
                _store.loadURI(_uri)
                _store.applyRules(workingContext, filterContext);

            elif _lhs == "-filter":
                filterContext = _store.intern((FORMULA, _uri+ "#_formula"))
                _playURI = urlparse.urljoin(_baseURI, "PLAY")  # Intermediate
                _playContext = _store.intern((FORMULA, _playURI+ "#_formula"))
                _store.moveContext(workingContext, _playContext)
#                print "# Input filter ", _uri
                _store.loadURI(_uri)
                _store.applyRules(_playContext, filterContext, workingContext)

                if doMeta:
                    _step  = _step + 1
                    s = _metaURI + `_step`  #@@ leading 0s to make them sort?
                    _store.storeQuad(_store._experience, META_basis, s, history)
                    _store.storeQuad(_store._experience, META_filter, s, inputContext)
                    _store.storeQuad(_store._experience, META_run, s, run)
                    history = s

            elif arg == "-purge":
                _store.purge(workingContext)

            elif arg == "-rules":
                _store.applyRules(workingContext, workingContext)

            elif arg == "-think":
                grandtotal = 0
                iterations = 0
                while 1:
                    iterations = iterations + 1
                    step = _store.applyRules(workingContext, workingContext)
                    if step == 0: break
                    grandtotal= grandtotal + step
                if chatty > 5: progress("Grand total of %i new statements in %i iterations." %
                         (grandtotal, iterations))

            elif arg == "-size":
                progress("Size of store: %i statements." %(_store.size,))

            elif arg == "-no":  # suppress output
                option_outputStyle = arg
                
            elif arg[:8] == "-outURI=": pass
            else: print "Unknown option", arg



# Squirt it out if not piped

        if not option_pipe:
            if chatty>5: progress("Begining output.")
            if option_outputStyle == "-ugly":
                _store.dumpChronological(workingContext, _outSink)
            elif option_outputStyle == "-bySubject":
                _store.dumpBySubject(workingContext, _outSink)
            elif option_outputStyle == "-no":
                pass
            else:  # "-best"
                _store.dumpNested(workingContext, _outSink)

    
def fixslash(str):
    """ Fix windowslike filename to unixlike
    """
    s = str
    for i in range(len(s)):
        if s[i] == "\\": s = s[:i] + "/" + s[i+1:]
    if s[0] != "/" and s[1] == ":": s = s[2:]  # @@@ Hack when drive letter
    return s
        
############################################################ Main program
    
if __name__ == '__main__':
    import os
    import urlparse
    if os.environ.has_key('SCRIPT_NAME'):
        serveRequest(os.environ)
    else:
        doCommand()

