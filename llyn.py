#! /usr/bin/python
"""

$Id$

RDF Store and Query engine

Logic Lookup: Yet another Name

(also, in Wales, a lake - a storage area at the centre of the valley?)

This is an engine which knows a certian amount of stuff and can manipulate it.
It is a (forward chaining) query engine, not an (backward chaining) inference engine:
that is, it will apply all rules it can
but won't figure out which ones to apply to prove something.  It is not
optimized particularly.

Used by cwm - the closed world machine.

See:  http://www.w3.org/DesignIssues/Notation3
 

Agenda:
=======

 - get rid of other globals (DWC 30Aug2001)
 - split out separate modules: CGI interface, command-line stuff,
   built-ins (DWC 30Aug2001)
 - split Query engine out as subclass of RDFStore? (DWC)
    SQL-equivalent client
 - implement a back-chaining reasoner (ala Euler/Algernon) on this store? (DWC)
 - run http daemon/client sending changes to database
 - act as client/server for distributed system
  - postgress, mySQl underlying database?
 -    
 -    standard mappping of SQL database into the web in N3/RDF
 -    
 - logic API as requested DC 2000/12/10
 - Jena-like API x=model.createResource(); addProperty(DC.creator, "Brian", "en")
 - sucking in the schema (http library?) --schemas ;
 - to know about r1 see r2; daml:import
 -   syntax for "all she wrote" - schema is complete and definitive
 - metaindexes - "to know more about x please see r" - described by
 - general python URI access with catalog!
 - equivalence handling inc. equivalence of equivalence?
 Shakedown:
 - Find all synonyms of synonym
 - Find closure for all synonyms
 - Find superclass closure?
- represent URIs bound to same equivalence closure object?

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
     statements not enough. See foo2.n3 - change existential representation :-( to make context a real conjunction again?
    (the forSome triple is special in that you can't remove it and reduce info)
 - filter out duplicate conclusions - BUG! - DONE
 - Validation:  validate domain and range constraints against closuer of classes and
   mutually disjoint classes.
 - Use unambiguous property to infer synomnyms
   (see sameDan.n3 test case in test/retest.sh)
 - schema validation - done partly but no "no schema for xx predicate".
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

"""emacs got confused by long string above@@"""

import string
import urlparse
import re
import StringIO
import sys

import urllib # for log:content
import md5, binascii  # for building md5 URIs
urlparse.uses_fragment.append("md5") #@@kludge/patch
urlparse.uses_relative.append("md5") #@@kludge/patch

import notation3    # N3 parsers and generators, and RDF generator
# import sax2rdf      # RDF1.0 syntax parser to N3 RDF stream

import thing
from thing import  progress, progressIndent, BuiltIn, LightBuiltIn, \
    HeavyBuiltIn, Function, ReverseFunction, \
    Literal, Resource, Fragment, FragmentNil, Thing, List, EmptyList

import RDFSink
from RDFSink import Logic_NS
from RDFSink import CONTEXT, PRED, SUBJ, OBJ, PARTS, ALL4

from RDFSink import FORMULA, LITERAL, ANONYMOUS, VARIABLE, SYMBOL
# = RDFSink.SYMBOL # @@misnomer

LITERAL_URI_prefix = "data:application/n3;"

cvsRevision = "$Revision$"

# Should the internal representation of lists be with DAML:first and :rest?
DAML_LISTS = notation3.DAML_LISTS    # If not, do the funny compact ones

# Magic resources we know about

RDF_type_URI = notation3.RDF_type_URI # "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
DAML_equivalentTo_URI = notation3.DAML_equivalentTo_URI


STRING_NS_URI = "http://www.w3.org/2000/10/swap/string#"
META_NS_URI = "http://www.w3.org/2000/10/swap/meta#"

META_mergedWith = META_NS_URI + "mergedWith"
META_source = META_NS_URI + "source"
META_run = META_NS_URI + "run"

doMeta = 0  # wait until we have written the code! :-)

INFINITY = 1000000000           # @@ larger than any number occurences


#  Keep a cache of subcontext closure:
subcontext_cache_context = None
subcontext_cache_subcontexts = None


######################################################## Storage
# The store uses an index in the interned resource objects.
    # Use the URI to allow sorted listings - for cannonnicalization if nothing else
    #  Put a type declaration before anything else except for strings
    
def compareURI(self, other):
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
    if isinstance(self, Literal):
        if isinstance(other, Literal):
            return cmp(self.string, other.string)
        else:
            return -1
    if isinstance(other, Literal):
        return 1

    if isinstance(self, Formula):
        if isinstance(other, Formula):
            s = self.statements
            o = other.statements
            ls = len(s)
            lo = len(o)
            if ls > lo: return 1
            if ls < lo: return -1

            s.sort(StoredStatement.compareSubjPredObj) # forumulae are all the same
            o.sort(StoredStatement.compareSubjPredObj)
            for i in range(ls):
                diff = s[i].compareSubjPredObj(o[i])
                if diff != 0: return diff
            raise RuntimeError("Identical formulae not interned!")
        else:
            return 1
    if isinstance(other, Formula):
        return -1

        # Both regular URIs
#        progress("comparing", self.representation(), other.representation())
    _type = notation3.RDF_type_URI
    s = self.uriref()
    if s == _type:
            return -1
    o = other.uriref()
    if o == _type:
            return 1
    if s < o :
            return -1
    if s > o :
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
    pass

###################################### Forumula
#

class Formula(Fragment):
    """A formula of a set of RDF statements, triples. these are actually
    instances of StoredStatement.  Other systems such as jena use the term "Model"
    for this.  Cwm and N3 extend RDF to allow a literal formula as an item in a triple.
    """
    def __init__(self, resource, fragid):
        Fragment.__init__(self, resource, fragid)
#        self.statements = []
        self.descendents = None   # Placeholder for list of closure under subcontext
        self.cannonical = None # Set to self if this has been checked for duplicates

    def generated(self):
        return 1

    def asPair(self):
        return (FORMULA, self.uriref())

    def existentials(self):
        "we may move to an internal storage rather than these statements"
        exs = []
        ss = self._index.get((self.store.forSome, self, None),[])
        for s in ss:
            exs.append(s[OBJ])
        if thing.verbosity() > 90: progress("Existentials in %s: %s" % (self, exs))
        return exs

    def universals(self):
        "we may move to an internal storage rather than these statements"
        exs = []
        ss = self._index.get((self.store.forAll, self, None),[])
        for s in ss:
            exs.append(s[OBJ])
        if thing.verbosity() > 90: progress("Universals in %s: %s" % (self, exs))
        return exs
    
    def variables(self):
        return self.existentials() + self.universals()

#   TRAP:  If we define __len__, then the "if F" will fail if len(F)==0 !!!
#   Rats .. so much for making it more like a list!
    def size(self):
        """ How many statements? """
        return len(self.statements)

    def statementsMatching(self, pred=None, subj=None, obj=None):
        return self._index.get((pred, subj, obj), [])
    
    def add(self, triple):
        return self.store.storeQuad((self, triple[0], triple[1], triple[2]))

    def outputStrings(self, channel=None, relation=None):
        """Fetch output strings from store, sort and output

        To output a string, associate (using the given relation) with a key
        such that the order of the keys is the order in which you want the corresponding
        strings output.
        """
        if channel == None:
            channel = sys.stdout
        if relation == None:
            relation = self.store.intern((SYMBOL, Logic_NS + "outputString"))
        list = self.statementsMatching(pred=relation)  # List of things of (subj, obj) pairs
        pairs = []
        for s in list:
            pairs.append((s[SUBJ], s[OBJ]))
        pairs.sort(comparePair)
        for key, str in pairs:
            channel.write(str.string.encode('utf-8'))

def comparePair(self, other):
    for i in 0,1:
        x = compareURI(self[i], other[i])
        if x != 0:
            return x




class StoredStatement:

    def __init__(self, q):
        self.quad = q

    def __getitem__(self, i):   # So that we can index the stored thing directly
        return self.quad[i]

    def __repr__(self):
        return "{"+`self[CONTEXT]`+":: "+`self[SUBJ]`+" "+`self[PRED]`+" "+`self[OBJ]`+"}"

#   The order of statements is only for cannonical output
#   We cannot override __cmp__ or the object becomes unhashable, and can't be put into a dictionary.

# Unused:
#    def compareContextSubjPredObj(self, other):
#        if self is other: return 0
#        for p in [CONTEXT, SUBJ, PRED, OBJ]: # Note NOT internal order
#            if self.quad[p] is not other.quad[p]:
#                return compareURI(self.quad[p],other.quad[p])
#        progress("Problem with duplicates - CSPO: '%s' and '%s'" % (self,other))
#        raise RuntimeError, "should never have two identical distinct [@@]"

    def compareSubjPredObj(self, other):
        """Just compare SUBJ, Pred and OBJ, others the same
        Avoid loops by spotting reference to containing formula"""
        if self is other: return 0
        sc = self.quad[CONTEXT]
        oc = other.quad[CONTEXT]
        for p in [SUBJ, PRED, OBJ]: # Note NOT internal order
            s = self.quad[p]
            o = other.quad[p]
            if s is sc:
                if o is oc: continue
                else: return -1  # @this is smaller than other formulae
            else:           
                if o is oc: return 1
            if s is not o:
                return compareURI(s,o)
        return 0

    def comparePredObj(self, other):
        """Just compare P and OBJ, others the same"""
        if self is other: return 0
        sc = self.quad[CONTEXT]
        oc = other.quad[CONTEXT]
        for p in [PRED, OBJ]: # Note NOT internal order
            s = self.quad[p]
            o = other.quad[p]
            if s is sc:
                if o is oc: continue
                else: return -1  # @this is smaller than other formulae
            else:           
                if o is oc: return 1
            if s is not o:
                return compareURI(s,o)
        return 0

    def compareObj(self, other):
        """Just compare OBJ, others the same"""
        if self is other: return 0
        s = self.quad[OBJ]
        o = other.quad[OBJ]
        if s is self.quad[CONTEXT]:
            if o is other.quad[CONTEXT]: return 0
            else: return -1  # @this is smaller than other formulae
        else:           
            if o is other.quad[CONTEXT]: return 1
        return compareURI(s,o)


    
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
        #@@hm... check string for URI syntax?
        # or at least for non-uri chars, such as space?

        if type(obj_py) is type(""):
            return store.intern((SYMBOL, obj_py))
        elif type(obj_py) is type(u""):
            uri = obj_py.encode('utf-8')
            return store.intern((SYMBOL, uri))

class BI_rawType(LightBuiltIn, Function):
    """
    The raw type is a type from the point of view of the langauge: is
    it a formula, list, and so on. Needed for test for formula in finding subformulae
    eg see test/includes/check.n3 
    """

    def evaluateObject(self, store, context, subj, subj_py):
        if isinstance(subj, Literal): y = store.Literal
        elif isinstance(subj, Formula): y = store.Formula
        elif subj.asList(): y = store.List
        else: y = store.Other  #  None?  store.Other?
        if thing.verbosity() > 91:
            progress("%s  rawType %s." %(`subj`, y))
        return y
        

class BI_racine(LightBuiltIn, Function):    # The resource whose URI is the same up to the "#" 

    def evaluateObject(self, store, context, subj, subj_py):
        if isinstance(subj, Fragment):
            return subj.resource
        else:
            return subj

# Heavy Built-ins

#
#class BI_directlyIncludes(HeavyBuiltIn):
#    def evaluate2(self, subj, obj,  bindings):
#        return store.testIncludes(subj, obj, variables, bindings=bindings)
#    
#class BI_notDirectlyIncludes(HeavyBuiltIn):
#    def evaluate2(self, subj, obj,  bindings):
#        return not store.testIncludes(subj, obj, variables, bindings=bindings)
    

class BI_includes(HeavyBuiltIn):
    pass    # Implemented specially inline in the code below by query queue expansion.
            
    
class BI_notIncludes(HeavyBuiltIn):
    """Check that one formula does not include the other.

    notIncludes is a heavy function not only because it may take more time than
    a simple search, but also because it must be performed after other work so that
    the variables within the object formula have all been subsituted.  It makes no sense
    to ask a notIncludes question with variables, "Are there any ?x for which
    F does not include foo bar ?x" because of course there will always be an
    infinite number for any finite F.  So notIncludes can only be used to check, when a
    specific case has been found, that it does not exist in the formula.
    This means we have to know that the variables do not occur in obj.

    As for the subject, it does make sense for the opposite reason.  If F(x)
    includes G for all x, then G would have to be infinite.  
    """
    def evaluate2(self, subj, obj, bindings):
        store = subj.store
        if isinstance(subj, Formula) and isinstance(obj, Formula):
            return not store.testIncludes(subj, obj, [], bindings=bindings) # No (relevant) variables
        return 0   # Can't say it *doesn't* include it if it ain't a formula

class BI_semantics(HeavyBuiltIn, Function):
    """ The semantics of a resource are its machine-readable meaning, as an
    N3 forumula.  The URI is used to find a represnetation of the resource in bits
    which is then parsed according to its content type."""
    def evaluateObject2(self, subj):
        store = subj.store
        if isinstance(subj, Fragment): doc = subj.resource
        else: doc = subj
        F = store.any((store._experience, store.semantics, doc, None))
        if F:
            if thing.verbosity() > 10: progress("Already read and parsed "+`doc`+" to "+ `F`)
            return F
        
        if thing.verbosity() > 10: progress("Reading and parsing " + `doc`)
        inputURI = doc.uriref()
        loadToStore(store, inputURI)
        if thing.verbosity()>10: progress("    semantics: %s" % (inputURI+ "#_formula"))
        F = store.intern((FORMULA, inputURI+ "#_formula"))
        return F
    
class BI_semanticsOrError(BI_semantics):
    """ Either get and parse to semantics or return an error message on any error """
    def evaluateObject2(self, subj):
        store = subj.store
        x = store.any((store._experience, store.semanticsOrError, subj, None))
        if x:
            if thing.verbosity() > 10: progress(`store._experience`+`store.semanticsOrError`+": Already found error for "+`subj`+" was: "+ `x`)
            return x
        try:
            return BI_semantics.evaluateObject2(self, subj)
        except (IOError, SyntaxError):
            message = sys.exc_info()[1].__str__()
            result = store.intern((LITERAL, message))
            if thing.verbosity() > 0: progress(`store.semanticsOrError`+": Error trying to resolve <" + `subj` + ">: "+ message) 
            store.storeQuad((store._experience,
                             store.semanticsOrError,
                             subj,
                             result))
            return result
    

HTTP_Content_Type = 'content-type' #@@ belongs elsewhere?

def loadToStore(store, addr):
    """raises IOError, SyntaxError
    """
    try:
        netStream = urllib.urlopen(addr)
        ct=netStream.headers.get(HTTP_Content_Type, None)
    #    if thing.verbosity() > 19: progress("HTTP Headers:" +`netStream.headers`)
    #    @@How to get at all headers??
    #    @@ Get sensible net errors and produce dignostics

        guess = ct
        if thing.verbosity() > 29: progress("Content-type: " + ct)
        if ct.find('text/plain') >=0 :   # Rats - nothing to go on
            buffer = netStream.read(500)
            netStream.close()
            netStream = urllib.urlopen(addr)
            if buffer.find('xmlns="') >=0 or buffer.find('xmlns:') >=0:
                guess = 'application/xml'
            elif buffer[0] == "#" or buffer[0:7] == "@prefix":
                guess = 'application/n3'
            if thing.verbosity() > 29: progress("    guess " + guess)
    except (IOError):
        raise DocumentAccessError(addr, sys.exc_info() )
        
    # Hmmm ... what about application/rdf; n3 or vice versa?
    if guess.find('xml') >= 0 or guess.find('rdf') >= 0:
        if thing.verbosity() > 49: progress("Parsing as RDF")
        import sax2rdf, xml.sax._exceptions
        p = sax2rdf.RDFXMLParser(store, addr)
        p.loadStream(netStream)
    else:
        if thing.verbosity() > 49: progress("Parsing as N3")
        p = notation3.SinkParser(store, addr)
        p.startDoc()
        p.feed(netStream.read())
        p.endDoc()
    store.storeQuad((store._experience,
                     store.semantics,
                     store.intern((SYMBOL, addr)),
                     store.intern((FORMULA, addr + "#_formula" ))))

def _indent(str):
    """ Return a string indented by 4 spaces"""
    s = "    "
    for ch in str:
        s = s + ch
        if ch == "\n": s = s + "    "
    if s.endswith("    "):
        s = s[:-4]
    return s

class BuiltInFailed(Exception):
    def __init__(self, info, item):
        progress("@@@@@@@@@ BUILTIN FAILED")
        self._item = item
        self._info = info
        
    def __str__(self):
        reason = _indent(self._info[1].__str__())
#        return "reason=" + reason
        return ("Error during built-in operation\n%s\nbecause:\n%s" % (
            `self._item`,
#            `self._info`))
            `reason`))
    
class DocumentAccessError(IOError):
    def __init__(self, uri, info):
        self._uri = uri
        self._info = info
        
    def __str__(self):
        # See C:\Python16\Doc\ref\try.html or URI to that effect
#        reason = `self._info[0]` + " with args: " + `self._info[1]`
        reason = _indent(self._info[1].__str__())
        return ("Unable to access document <%s>, because:\n%s" % ( self._uri, reason))
    
class BI_content(HeavyBuiltIn, Function): #@@DWC: Function?
    def evaluateObject2(self, subj):
        store = subj.store
        if isinstance(subj, Fragment): doc = subj.resource
        else: doc = subj
        C = store.any((store._experience, store.content, doc, None))
        if C:
            if thing.verbosity() > 10: progress("already read " + `doc`)
            return C
        if thing.verbosity() > 10: progress("Reading " + `doc`)
        inputURI = doc.uriref()
        try:
            netStream = urllib.urlopen(inputURI)
        except IOError:
            return None
        
        str = netStream.read() # May be big - buffered in memory!
        C = store.intern((LITERAL, str))
        store.storeQuad((store._experience,
                         store.content,
                         doc,
                         C))
        return C


class BI_n3ExprFor(HeavyBuiltIn, Function):
    def evaluateObject2(self, subj):
        store = subj.store
        if isinstance(subj, Literal):
            F = store.any((store._experience, store.n3ExprFor, subj, None))
            if F: return F
            if thing.verbosity() > 10: progress("parsing " + subj.string[:30] + "...")
            inputURI = subj.asHashURI() # iffy/bogus... rather asDataURI? yes! but make more efficient
            p = notation3.SinkParser(store, inputURI)
            p.startDoc()
            p.feed(subj.string.encode('utf-8')) #@@ catch parse errors
            p.endDoc()
            del(p)
            F = store.intern((FORMULA, inputURI+ "#_formula"))
            return F
    
class BI_cufi(HeavyBuiltIn, Function):
    """ Deductive Closure

    Closure under Forward Inference, equivalent to cwm's --think function
    conclusion  might be a better word than cufi."""
    def evaluateObject2(self, subj):
        store = subj.store
        if isinstance(subj, Formula):
            F = store.any((store._experience, store.cufi, subj, None))  # Cached value?
            if F: return F

            if thing.verbosity() > 10: progress("Bultin: " + `subj`+ " log:conclusion " + `F`)
            F = store.genid(FORMULA)
#            store.storeQuad((context, store.forSome, context, F ))
            store.copyContext(subj, F)
            store.think(F)
            store.storeQuad((store._experience, store.cufi, subj, F))  # Cache for later
            return F
    
class BI_conjunction(LightBuiltIn, Function):      # Light? well, I suppose so.
    """ The conjunction of a set of formulae is the set of statements which is
    just the union of the sets of statements
    modulo non-duplication of course"""
    def evaluateObject(self, store, context, subj, subj_py):
        if thing.verbosity() > 50:
            progress("Conjunction input:"+`subj_py`)
            for x in subj_py:
                progress("    conjunction input formula %s has %i statements" % (x, x.size()))
#        F = conjunctionCache.get(subj_py, None)
#        if F != None: return F
        F = store.genid(FORMULA)
#        store.storeQuad((context, store.forSome, context, F ))
        for x in subj_py:
            if not isinstance(x, Formula): return None # Can't
            store.copyContext(x, F)
            if thing.verbosity() > 74:
                progress("    Formula %s now has %i" % (x2s(F),len(F.statements)))
        return store.endFormula(F)

    
###################################################################################        
class RDFStore(RDFSink.RDFSink) :
    """ Absorbs RDF stream and saves in triple store
    """

    def __init__(self, genPrefix=None, metaURI=None, argv=None):
        RDFSink.RDFSink.__init__(self)

        self.resources = {}    # Hash table of URIs for interning things
        self.formulae = []     # List of all formulae        
        self._experience = None   #  A formula of all the things program run knows from direct experience
        self._formulaeOfLength = {} # A dictionary of all the constant formuale in the store, lookup by length.

        self.size = 0
        self._nextId = 0
        self.argv = argv     # List of command line arguments for N3 scripts
        if genPrefix: self._genPrefix = genPrefix
        else: self._genPrefix = "#_gs"

#        self._index = {}   

        # Constants, as interned:
        
        self.forSome = self.internURI(RDFSink.forSomeSym)
        self.forAll  = self.internURI(RDFSink.forAllSym)
        self.implies = self.internURI(Logic_NS + "implies")
        self.asserts = self.internURI(Logic_NS + "asserts")
        
# Register Light Builtins:

        log = self.internURI(Logic_NS[:-1])   # The resource without the hash
        daml = self.internURI(notation3.DAML_NS[:-1])   # The resource without the hash

# Functions:        

        log.internFrag("racine", BI_racine)  # Strip fragment identifier from string

        self.rawType =          log.internFrag("rawType", BI_rawType) # syntactic type, oneOf:
        self.Literal =          log.internFrag("Literal", Fragment) # syntactic type possible value - a class
        self.List =             log.internFrag("List", Fragment) # syntactic type possible value - a class
        self.Formula =          log.internFrag("Formula", Fragment) # syntactic type possible value - a class
        self.Other =            log.internFrag("Other", Fragment) # syntactic type possible value - a class (Use?)

        log.internFrag("conjunction", BI_conjunction)
        
# Bidirectional things:
        log.internFrag("uri", BI_uri)
        log.internFrag("equalTo", BI_EqualTo)
        log.internFrag("notEqualTo", BI_notEqualTo)

# Heavy relational operators:

        self.includes =         log.internFrag( "includes", BI_includes)
#        log.internFrag("directlyIncludes", BI_directlyIncludes)
        log.internFrag("notIncludes", BI_notIncludes)
#        log.internFrag("notDirectlyIncludes", BI_notDirectlyIncludes)

#Heavy functions:

        log.internFrag("resolvesTo", BI_semantics) # obsolete
        self.semantics = log.internFrag("semantics", BI_semantics)
        self.cufi = log.internFrag("conclusion", BI_cufi)
        self.semanticsOrError = log.internFrag("semanticsOrError", BI_semanticsOrError)
        self.content = log.internFrag("content", BI_content)
        self.n3ExprFor = log.internFrag("n3ExprFor",  BI_n3ExprFor)
        
# Constants:

        self.Truth = self.internURI(Logic_NS + "Truth")
        self.type = self.internURI(notation3.RDF_type_URI)
        self.Chaff = self.internURI(Logic_NS + "Chaff")


# List stuff - beware of namespace changes! :-(

        self.first = self.intern(notation3.N3_first)
        self.rest = self.intern(notation3.N3_rest)
        self.nil = self.intern(notation3.N3_nil)
        self.nil._asList = EmptyList(self, None, None)
#        self.nil = EmptyList(self, None, None)
#        self.only = self.intern(notation3.N3_only)
        self.Empty = self.intern(notation3.N3_Empty)
        self.List = self.intern(notation3.N3_List)

        import cwm_string  # String builtins
        import cwm_os      # OS builtins
        import cwm_math    # Mathematics
        import cwm_crypto  # Cryptography
        cwm_string.register(self)
        cwm_math.register(self)
        cwm_os.register(self)
        cwm_crypto.register(self)
        
        if metaURI != None:
            self.reset(metaURI)

# Internment of URIs and strings (was in Engine).

# We ought to intern formulae too but it ain't as simple as that.
# - comparing foumale is graph isomorphism complete.
# - formulae grow with addStatement() and would have to be re-interned

    def reset(self, metaURI): # Set the metaURI
        self._experience = self.intern((FORMULA, metaURI + "_formula"))

    def internURI(self, str):
        assert type(str) is type("") # caller %xx-ifies unicode
        return self.intern((SYMBOL,str))
    
    def intern(self, pair):
        """find-or-create a Fragment or a Resource or Literal as appropriate

        returns URISyntaxError if, for example, the URIref has
        two #'s.
        
        This is the way they are actually made.
        """

        typ, urirefString = pair

        if typ == LITERAL:
            uriref2 = LITERAL_URI_prefix + urirefString # @@@ encoding at least hashes!!
            result = self.resources.get(uriref2, None)
            if result != None: return result
            result = Literal(self, urirefString)
            self.resources[uriref2] = result
        else:
            assert type(urirefString) is type("") # caller %xx-ifies unicode

            hash = string.rfind(urirefString, "#")
            if hash < 0 :     # This is a resource with no fragment
                result = self.resources.get(urirefString, None)
                if result != None: return result
                result = Resource(self, urirefString)
                self.resources[urirefString] = result
            
            else :      # This has a fragment and a resource
                resid = urirefString[:hash]
                if string.find(resid, "#") >= 0:
                    raise URISyntaxError # Hash in document ID - can be from parsing XML as N3!
                r = self.internURI(resid)
                if typ == SYMBOL:
                    if urirefString == notation3.N3_nil[1]:  # Hack - easier if we have a different classs
                        result = r.internFrag(urirefString[hash+1:], FragmentNil)
                    else:
                        result = r.internFrag(urirefString[hash+1:], Fragment)
                elif typ == FORMULA: result = r.internFrag(urirefString[hash+1:], Formula)
                else: raise RuntimeError, "did not expect other type"
        return result

    def initThing(self, x):
        """ The store initialized the pointers in a new Thing
        """

#        x.occursAs = [], [], [], []    # These are special cases of indexes

        if isinstance(x, Formula):
             x.statements = []
             x._index = {}
             x._index[(None,None,None)] = x.statements
             self.formulae.append(x)
        return x
     
    def internList(self, value):
        x = nil
        l = len(value)
        while l > 0:
            l = l - 1
            x = x.precededBy(value[l])
        return x

    def deleteFormula(self,F):
        if thing.verbosity() > 30: progress("Deleting formula %s %ic" %
                                            ( `F`, len(F.statements)))
        for s in F.statements[:]:   # Take copy
            self.removeStatement(s)
#        for p in ALL4:
#            if F.occursAs[p] != []:
#                raise RuntimeError("Attempt to delete Formula in use "+`F`, F.occursAs)
        self.formulae.remove(F)

    def endFormula(self, F):
        """If this formula already exists, return the master version.
        If not, record this one and return it.
        Call this when the formula is in its final form, with all its statements.
        Make sure no one else has a copy of the pointer to the smushed one.
        """
        if F.cannonical:
            return F.cannonical
        fl = F.statements
        fl.sort(StoredStatement.compareSubjPredObj)
        l = len(fl)   # The number of statements
        possibles = self._formulaeOfLength.get(l, None)  # Formulae of same length

    
        if possibles == None:
            self._formulaeOfLength[l] = [F]
            return F

        for G in possibles:
            gl = G.statements
            if len(gl) != l: raise RuntimeError("@@Length is %i instead of %i" %(len(gl), l))
            for i in range(l):
                for p in CONTEXT, PRED, SUBJ, OBJ:
                    if (fl[i][p] is not gl[i][p]
                        and (fl[i][p] is not F or gl[i][p] is not G)):
                        break # mismatch
                else: #match one statement
                    continue
                break
            else: #match
                if thing.verbosity() > 20: progress("** Smushed new formula %s giving old %s" % (F, G))
#                self.replaceWith(F,G)
                return G
        possibles.append(F)
#        raise oops
        F.cannonical = F
        return F

    def reopen(self, F):
        if not F.cannonical: return F # was open
        self._formulaeOfLength[len(F.statements)].remove(F)  # Formulae of same length
        F.cannonical = None
        return F

    def replaceWith(self,old, new):
        if thing.verbosity() > 30:
            progress("Smush: Replacing %s (%i statements) with %s" %
                        ( `old`,
                          len(old.statements),
                          `new`))
        bindings = [ (old, new) ]
        for F in self.formulae[:]:
            for s in F.statements[:]:
                if thing.verbosity() > 95: progress(".......removed", s.quad)
                q2 = _lookupQuad(bindings, s.quad)
                self.removeStatement(s)
                self.storeQuad(q2)
                if thing.verbosity() > 95: progress(".......restored", q2)
        return new

    def endFormulaNested(self, F, bindings = [], level=0):
        """Cannonicalize this after cannonicalizing any subformulae recusrively
        Note the subs must be done first. Also note that we can't assume statements
        or formulae are valid after a call to this, unless we track the
        changes which are kept in a shared list, bindings. """
        if thing.verbosity() > 80:
            progress("  "*level, "endFormulaNested:"+`F`+ `bindings`)

        if F.cannonical:
            return F.cannonical
        subs = []   # Immediate subformulae
        for s in F.statements:
            for p in PRED, SUBJ, OBJ:
                x = s[p]
                if isinstance(x, Formula) and x is not F:
                    if x not in subs: subs.append(x)
        for x in subs:
            self.endFormulaNested( _lookup(bindings, x), bindings, level=level+1)
        if bindings != []:
            for s in F.statements[:]:  # Take a copy as the lists change
                q2 = _lookupQuad(bindings, s.quad)
                if q2 != s.quad:
                    if thing.verbosity() > 95: progress(".......removed", s.quad)
                    self.removeStatement(s)
                    self.storeQuad(q2)   #  Could be faster? Patch the existing one?
                    if thing.verbosity() > 95: progress(".......restored", q2)

        new = self.endFormula(F)
        if new is not F:
            bindings.append((F, new))
        return new

# Input methods:

    def loadURI(self, uri):
        p = notation3.SinkParser(self,  uri)
        p.load(uri)
        del(p)


    def bind(self, prefix, nsPair):
        if prefix:   #  Ignore binding to empty prefix
            return RDFSink.RDFSink.bind(self, prefix, nsPair) # Otherwise, do as usual.
    
    def makeStatement(self, tuple):
        q = ( self.intern(tuple[CONTEXT]),
              self.intern(tuple[PRED]),
              self.intern(tuple[SUBJ]),
              self.intern(tuple[OBJ]) )
        if q[PRED] is self.forSome and isinstance(q[OBJ], Formula):
            if thing.verbosity() > 97:  progress("Makestatement suppressed")
            return  # This is implicit, and the same formula can be used un >1 place
        self.storeQuad(q)
                    
    def makeComment(self, str):
        pass        # Can't store comments


    def any(self, q):
        """  Quad contains one None as wildcard. Returns first value
        matching in that position.
	"""
        list = q[CONTEXT].statementsMatching(q[PRED], q[SUBJ], q[OBJ])
        if not list: return None
        for p in ALL4:
            if q[p] == None:
                return list[0].quad[p]


    def storeQuad(self, q):
        """ intern quads, in that dupliates are eliminated.

        Builds the indxes and does stuff for lists.         
        """
        #  Check whether this quad already exists
#        print "Before, Formula now has %i statements" % len(self._index[(q[CONTEXT],None,None,None)])
        if thing.verbosity() > 97:
            progress("storeQuad (size before %i) "%self.size +`q`)
        
        context, pred, subj, obj = q
        if context.statementsMatching(pred, subj, obj):
            if thing.verbosity() > 97:  progress("storeQuad duplicate suppressed"+`q`)
            return 0  # Return no change in size of store
        if context.cannonical:
            raise RuntimeError("Attempt to add statement to cannonical formula "+`context`)

# We collapse lists from there declared daml first,rest structure into List objects.
# To do this, we need (a) a first; (b) a rest, and (c) the rest being a list.
# We trigger List collapse on any of these three becoming true.

        self.size = self.size+1
        if pred is self.rest and obj.asList() != None:
            ifirst = context.statementsMatching(pred=self.first, subj=subj)
            if ifirst and subj._asList == None:
                subj._asList = obj._asList.precededBy(ifirst[0][OBJ])
#                self.removeStatement(ifirst[0])  # Neither first nor rest is needed now
                self.checkList(context, subj)
#                return 1  # @@ what are we counting, exactly? We did learn something!

        elif pred is self.first:
            irest = context.statementsMatching(self.rest, subj, None)
            if irest:
                rest = irest[0][OBJ]
                if rest.asList() != None and subj._asList == None:
#                    self.removeStatement(irest[0])  # Neither first nor rest is needed now
                    subj._asList = rest._asList.precededBy(obj)
                    self.checkList(context, subj)
#                    return 1

        s = StoredStatement(q)


        # Build 8 indexes.
#       This now takes a lot of the time in a typical  cwm run! :-( 

        context.statements.append(s)
        
        list = context._index.get((None, None, obj), None)
        if list == None: context._index[(None, None, obj)]=[s]
        else: list.append(s)

        list = context._index.get((None, subj, None), None)
        if list == None: context._index[(None, subj, None)]=[s]
        else: list.append(s)

        list = context._index.get((None, subj, obj), None)
        if list == None: context._index[(None, subj, obj)]=[s]
        else: list.append(s)

        list = context._index.get((pred, None, None), None)
        if list == None: context._index[(pred, None, None)]=[s]
        else: list.append(s)

        list = context._index.get((pred, None, obj), None)
        if list == None: context._index[(pred, None, obj)]=[s]
        else: list.append(s)

        list = context._index.get((pred, subj, None), None)
        if list == None: context._index[(pred, subj, None)]=[s]
        else: list.append(s)

        list = context._index.get((pred, subj, obj), None)
        if list == None: context._index[(pred, subj, obj)]=[s]
        else: list.append(s)


        return 1  # One statement has been added


    def startDoc(self):
        pass

    def endDoc(self, rootFormulaPair):
        self.endFormulaNested(self.intern(rootFormulaPair))
        return

##########################################################################
#
# Output methods:
#
    def selectDefaultPrefix(self, context):

        """ Resource whose fragments have the most occurrences.
        we suppress the RDF namespace itself because the XML syntax has problems with it
        being default as it is used for attributes."""

        counts = {}   # Dictionary of how many times each
        closure = self.subContexts(context)    # This context and all subcontexts
        for con in closure:
            for s in con.statements:
                for p in PRED, SUBJ, OBJ:
                    x = s[p]
                    if (x is self.first or x is self.rest) and p == PRED:
                        continue  # ignore these - they tend to be in lists
                    if isinstance(x, Fragment):
                        _anon, _incoming = self._topology(x, con)
                        if not _anon and not isinstance(x, Formula):
                            r = x.resource
                            total = counts.get(r, 0) + 1
                            counts[r] = total
        best = 0
        mp = None
        for r, count in counts.items():
            if thing.verbosity() > 25: progress("    Count is %3i for %s" %(count, r.uriref()))
            if (r.uri != notation3.RDF_NS_URI[:-1]
                and (count > best or
                     (count == best and `mp` > `r`))) :  # Must be repeatable for retests
                best = count
                mp = r

        if thing.verbosity() > 20:
            progress("# Most popular Namesapce in %s is %s with %i" % (`context`, `mp`, best))

        if mp is None: return
        self.defaultNamespace = (SYMBOL, mp.uriref()+"#")
        return

        
        mpPair = (SYMBOL, mp.uriref()+"#")
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
        if self.defaultNamespace:
            sink.setDefaultNamespace(self.defaultNamespace)
        prefixes = self.namespaces.keys()   #  bind in same way as input did FYI
        prefixes.sort()
        for pfx in prefixes:
            sink.bind(pfx, self.namespaces[pfx])

    def dumpChronological(self, context, sink):
        sink.startDoc()
        self.dumpPrefixes(sink)
#        print "# There are %i statements in %s" % (len(context.statements), `context` )
        for s in context.statements:
            self._outputStatement(sink, s.quad)
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

        statements = context.statementsMatching(self.forSome, context, None)
        if sorting: statements.sort(StoredStatement.compareObj)
        for s in statements:
            self._outputStatement(sink, s.quad)

        rs = self.resources.values()
        if sorting: rs.sort()
        for r in rs :  # First the bare resource
            statements = context.statementsMatching(subj=r)
            if sorting: statements.sort(StoredStatement.comparePredObj)
            for s in statements :
                if not(context is s.quad[SUBJ]and s.quad[PRED] is self.forSome):
                    self._outputStatement(sink, s.quad)
            if not isinstance(r, Literal):
                fs = r.fragments.values()
                if sorting: fs.sort
                for f in fs :  # then anything in its namespace
                    statements = context.statementsMatching(subj=f)
                    if sorting: statements.sort(StoredStatement.comparePredObj)
                    for s in statements:
                        self._outputStatement(sink, s.quad)
        sink.endDoc()
#
#  Pretty printing
#
#   x is an existential if there is in the context C we are printing
# is a statement  (C log:forSome x). If so, the anonymous syntaxes follow.
#
# An intersting alternative is to use the reverse syntax to the max, which
# makes the DLG an undirected labelled graph. s and o above merge. The only think which
# then prevents us from dumping the graph without genids is the presence of cycles.

# Formulae
#
# These are in some way like literal strings, in that they are defined completely
# by their contents. They are sets of statements. (To say a statement occurs
# twice has no menaing).  Can they be given an id?  You can assert that any
# object is equivalent to (=) a given formula.
# If one could label it in one place then one would want to
# be able to label it in more than one.  I'm not sure whether this is wise.
# Let's try it with no IDs on formulae as in the N3 syntax.  There would be
# the question of in which context the assertion wa made that the URI was
# a label for the expression. You couldn't just treat it as part of the
# machinery as we do for URI of a regular thing.


    def _topology(self, x, context): 
        """ Can be output as an anonymous node in N3. Also counts incoming links.
        Output tuple parts:

        1. True iff can be represented as anonymous node in N3, [] or {}
        2. Number of incoming links: >0 means occurs as object or pred, 0 means as only as subject.
            1 means just occurs once
            >1 means occurs too many times to be anon
        
        Returns  number of incoming links (1 or 2) including forSome link
        or zero if self can NOT be represented as an anonymous node.
        Paired with this is whether this is a subexpression.
        """

        _asPred = len(context._index.get((x, None, None),[]))
        _elsewhere = 0
        _isExistential = len(context._index.get((self.forSome, context, x),[]))
        _asObj = len(context._index.get((None, None, x),[])) - _isExistential
        _loop = len(context._index.get((None, x, x),[]))  # does'es count as incomming
        
        if isinstance(x, Literal):
            anon = 0     #  Never anonymous, always just use the string
        if x.asList() != None or isinstance(x, Formula):
            _anon = 2    # Always represent it just as itself
        else:
            contextClosure = self.subContexts(context)[:]
            contextClosure.remove(context)
            for sc in contextClosure:
                if (sc._index.get((None, None, x),None)
                    or sc._index.get((None, x, None),None)
                        or sc._index.get((x, None, None),None)):
                    _elsewhere = 1  # Occurs in a subformula - can't be anonymous!
                    break
            _anon = (_asObj < 2) and ( _asPred == 0) and (_loop ==0) and _isExistential and not _elsewhere

        if thing.verbosity() > 98:
            progress( "Topology %s in %s is: anon=%i ob=%i, loop=%i pr=%i ex=%i elsewhere=%i"%(
            `x`[-8:], `context`[-8:], _anon, _asObj, _loop, _asPred,  _isExistential, _elsewhere))

        return ( _anon, _asObj+_asPred )  


    

    def _toPython(self, x, queue=None):
        """#  Convert a data item in query with no unbound variables into a python equivalent 
       Given the entries in a queue template, find the value of a list.
       @@ slow
       These methods are at the disposal of built-ins.
"""
        if thing.verbosity() > 85: progress("#### Converting to python "+ x2s(x))
        """ Returns an N3 list as a Python sequence"""
        if x.asList() != None:
            if x is self.nil: return []
#            if @@@ this is not in the queue, must be in the store @@@@
            if queue != None:
                f = None
                r = None
                for item in queue:
                    con, pred, subj, obj = item.quad
                    if subj is x and pred is self.first: f = obj
                    if subj is x and pred is self.rest: r = obj
                if f != None and r != None:
                    if r.asList() ==None:  #cut
                        raise RuntimeError("@@@@@@@ List rest not a list:" + `r`)
                    return [ self._toPython(f, queue) ] + self._toPython(r, queue)
#                progress("@@@", `x`, x.asList())
                y = []
                for i in x.asList().value():
                    y.append(self._toPython(i))
                return y                
        if isinstance(x, Literal):
            return x.string
        return x    # If not a list, return unchanged

    def _fromPython(self, context, x):
        if isString(x):
            return self.intern((LITERAL, x))
        elif type(x) == type(2):
            return self.intern((LITERAL, `x`))    # @@ Add literal numeric type to N3?
        elif type(x) == type([]):
            g = store.nil
            y = x
            y.reverse()
            for e in y:
                g1 = store.genid()
                self.storeQuad((context, self.forSome, context, g1))
                self.storeQuad((context, self.first, g1, self._fromPython(context, e)))
                self.storeQuad((context, self.rest, g1, g))
                g = g1
            return g
        return x

    def dumpNested(self, context, sink):
        """ Iterates over all URIs ever seen looking for statements
        """
        self.selectDefaultPrefix(context)        
        sink.startDoc()
        self.dumpPrefixes(sink)
        self.dumpFormulaContents(context, sink, sorting=1)
        sink.endDoc()

    def dumpFormulaContents(self, context, sink, sorting):
        """ Iterates over statements in formula, bunching them up into a set
        for each subject.
        @@@ Dump "this" first before everything else
        """
        if sorting: context.statements.sort(StoredStatement.compareSubjPredObj)

        statements = context.statementsMatching(subj=context)  # context is subject
        if statements:
            self._dumpSubject(context, context, sink, sorting, statements)

        currentSubject = None
        statements = []
        for s in context.statements:
            con, pred, subj, obj =  s.quad
            if subj is con: continue # Done them above
            if not currentSubject: currentSubject = subj
            if subj != currentSubject:
                self._dumpSubject(currentSubject, context, sink, sorting, statements)
                statements = []
                currentSubject = subj
            statements.append(s)
        if currentSubject:
            self._dumpSubject(currentSubject, context, sink, sorting, statements)


##########
#    def _dumpList(self, subj, context, sink, sorting, list):
#        self.dumpStatement(sink, (context, subject, self.first, list.first), sorting)
#        self.dumpStatement(sink, (context, subject, self.rest, list.rest), sorting)
#        # which handles the recursion
#        return
            
    def _dumpSubject(self, subj, context, sink, sorting, statements=[]):
        """ Dump the infomation about one top level subject
        
        This outputs arcs leading away from a node, and where appropriate
     recursively descends the tree, by dumping the object nodes
     (and in the case of a compact list, the predicate (rest) node).
     It does NOTHING for anonymous nodes which don't occur explicitly as subjects.

     The list of statements must be sorted if sorting is true.     
        """
        _anon, _incoming = self._topology(subj, context)    # Is anonymous?
        if _anon and  _incoming == 1 and not isinstance(subj, Formula): return           # Forget it - will be dealt with in recursion

        if isinstance(subj, Formula) and subj is not context:
            sink.startBagSubject(subj.asPair())
            self.dumpFormulaContents(subj, sink, sorting)  # dump contents of anonymous bag
            sink.endBagSubject(subj.asPair())       # Subject is now set up
            # continue to do arcs
            
        elif _anon and _incoming == 0:    # Will be root anonymous node - {} or [] or ()

            if subj is context:
                pass
            else:     #  Could have alternative syntax here

                for s in statements:  # Find at least one we will print
                    context, pre, sub, obj = s.quad
                    if sub is obj: break  # Ok, we will do it
                    _anon, _incoming = self._topology(obj, context)
                    if not((pre is self.forSome) and sub is context and _anon):
                        break # We will print it
                else: return # Nothing to print - so avoid printing [].

                if sorting: statements.sort(StoredStatement.comparePredObj)    # Order only for output

                li = subj.asList()
                if li and not isinstance(li, EmptyList):   # The subject is a list
                    sink.startAnonymousNode(subj.asPair(), li)
#                    self.dumpStatement(sink, (context, self.first, subj, li.first))
#                    self.dumpStatement(sink, (context, self.rest, subj, li.rest)) # includes rest of list
                    for s in statements:
                        p = s.quad[PRED]
                        if p is self.first or p is self.rest:
                            self.dumpStatement(sink, s.quad, sorting) # Dump the rest outside the ()
                    sink.endAnonymousNode(subj.asPair())
                    for s in statements:
                        p = s.quad[PRED]
                        if p is not self.first and p is not self.rest:
                            self.dumpStatement(sink, s.quad, sorting) # Dump the rest outside the ()
                    return
                else:
                    sink.startAnonymousNode(subj.asPair())
                    for s in statements:  #   [] color blue.  might be nicer. @@@$$$$  Try it!
                        self.dumpStatement(sink, s.quad, sorting)
                    sink.endAnonymousNode()
                    return  # arcs as subject done


        if sorting: statements.sort(StoredStatement.comparePredObj)
        for s in statements:
            self.dumpStatement(sink, s.quad, sorting)

                
    def dumpStatement(self, sink, triple, sorting):
        # triple = s.quad
        context, pre, sub, obj = triple
        if (sub is obj and not isinstance(sub, Formula))  \
           or (isinstance(obj.asList(), EmptyList)) \
           or isinstance(obj, Literal):
            self._outputStatement(sink, triple) # Do 1-loops simply
            return

        _anon, _incoming = self._topology(obj, context)
        _se = isinstance(obj, Formula) and obj is not context
        
        if ((pre is self.forSome) and sub is context and _anon):
            return # implicit forSome
        li = (obj.asList() != None)
        if _anon and (_incoming == 1 or li or _se):  # Embedded anonymous node in N3
            _isSubject = len(context._index.get((obj, None, None), [])) # Has properties in this context?

#            if _isContext > 0 and _isSubject > 0: raise CantDoThat # Syntax problem!@@@
            
            if _isSubject > 0 or not _se :   #   Do [ ] if nothing else as placeholder.

                sink.startAnonymous(self.extern(triple), li)
                if not li or not isinstance(obj.asList(), EmptyList):   # nil gets no contents
                    if li:
                        if thing.verbosity()>49:
                            progress("List found as object of dumpStatement " + x2s(obj))
#                        self.dumpStatement(sink, (context, self.first, obj, obj.asList().first))
#                        self.dumpStatement(sink, (context, self.rest, obj, obj.asList().rest)) # includes rest of list
                    ss = context.statementsMatching(subj=obj)
                    if sorting: ss.sort(StoredStatement.comparePredObj)
                    for t in ss:
                        self.dumpStatement(sink, t.quad, sorting)
      
                    if _se > 0:
                        sink.startBagNamed(context.asPair(),obj.asPair()) # @@@@@@@@@  missing "="
                        self.dumpFormulaContents(obj, sink, sorting)  # dump contents of anonymous bag
                        sink.endBagObject(pre.asPair(), sub.asPair())
                        
                sink.endAnonymous(sub.asPair(), pre.asPair()) # Restore parse state

            else:  # _isSubject == 0 and _se
                sink.startBagObject(self.extern(triple))
                self.dumpFormulaContents(obj, sink, sorting)  # dump contents of anonymous bag
                sink.endBagObject(pre.asPair(), sub.asPair())
            return # Arc is done

        if _se:
            sink.startBagObject(self.extern(triple))
            self.dumpFormulaContents(obj, sink, sorting)  # dump contents of anonymous bag
            sink.endBagObject(pre.asPair(), sub.asPair())
            return

        self._outputStatement(sink, triple)
                


########1#########################  Manipulation methods:
#
#  Note when we move things, then the store may shrink as they may
# move on top of existing entries and we don't allow duplicates.
#
#    def moveContext(self, old, new, bindings=None):
#        if thing.verbosity() > 0: progress("Move context - SLOW")
#        self.reopen(new)    # If cannonical, uncannonicalize #@@ error prone if any references
#        if bindings == None:
#            bindings = [(old, new)]
#        for s in old.statements[:] :   # Copy list!
#            q = s.quad
#            self.removeStatement(s)  # SLOW!
#            del(s)
#            self.storeQuad(_lookupQuad(bindings, q))

    def copyContextRecursive(self, old, new, bindings):
        total = 0
        for s in old.statements[:] :   # Copy list!
#            q = s.quad
#            self.removeStatement(s)
            q2 = _lookupQuadRecursive(bindings, s.quad)
            if thing.verbosity() > 30: progress("    Conclude: "+`q2`) 
            total = total -1 + self.storeQuad(q2)
        return total
                
    def copyContext(self, old, new):
        for s in old.statements[:] :   # Copy list!
            q = s.quad
            for p in CONTEXT, PRED, SUBJ, OBJ:
                x = q[p]
                if x is old:
                    q = q[:p] + (new,) + q[p+1:]
            self.storeQuad(q)
                
#  Clean up intermediate results:
#
# Statements in the given context that a term is a Chaff cause
# any mentions of that term to be removed from the context.

    def purge(self, context, boringClass=None):
        if not boringClass:
            boringClass = self.Chaff
        for s in context.statementsMatching(self.type, None, boringClass)[:]:
            con, pred, subj, obj = s.quad  # subj is a member of boringClass
            total = 0
            for t in context.statementsMatching(subj=subj)[:]:
                        self.removeStatement(t)    # SLOW
                        total = total + 1
            for t in context.statementsMatching(pred=subj)[:]:
                        self.removeStatement(t)    # SLOW
                        total = total + 1
            for t in context.statementsMatching(obj=subj)[:]:
                        self.removeStatement(t)    # SLOW
                        total = total + 1
                        
            if thing.verbosity() > 30:
                progress("Purged %i statements with %s" % (total,`subj`))


    def removeStatement(self, s):
        "Slow, alas. The remove()s take a lot of time."
        context, pred, subj, obj = s.quad
        if thing.verbosity() > 97:  progress("removeStatement "+`s.quad`)
        context.statements.remove(s)
        context._index[(None, None, obj)].remove(s)
        context._index[(None, subj, None)].remove(s)
        context._index[(None, subj, obj)].remove(s)
        context._index[(pred, None, None)].remove(s)
        context._index[(pred, None, obj)].remove(s)
        context._index[(pred, subj, None)].remove(s)
        context._index[(pred, subj, obj)].remove(s)
        self.size = self.size-1
#        del s

#   Iteratively apply rules to a formula

    def think(self, F, G=None):
        grandtotal = 0
        iterations = 0
        if G == None: G = F
        self.reopen(F)
        bindingsFound = {}  # rule: list bindings already found
        while 1:
            iterations = iterations + 1
            step = self.applyRules(F, G, alreadyDictionary=bindingsFound)
            if step == 0: break
            grandtotal= grandtotal + step
        if thing.verbosity() > 5: progress("Grand total of %i new statements in %i iterations." %
                 (grandtotal, iterations))
        return grandtotal


#  Apply rules from one context to another
                
    def applyRules(self, workingContext,    # Data we assume 
                   filterContext = None,    # Where to find the rules
                   targetContext = None,    # Where to put the conclusions
                   universals = [],             # Inherited from higher contexts
                   alreadyDictionary = None):  # rule: list of bindings already found
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
        
        _total = 0
        
        for s in filterContext.statements:
            con, pred, subj, obj  = s.quad
            if (pred is self.implies
                and isinstance(subj, Formula)
                and isinstance(obj, Formula)):
                if alreadyDictionary == None:
                    already = None
                else:
                    already = alreadyDictionary.get(s, None)
                    if already == None:
                        alreadyDictionary[s] = []
                        already = alreadyDictionary[s]
                v2 = universals + filterContext.universals() # Note new variables can be generated
                found = self.tryRule(s, workingContext, targetContext, v2,
                                     already=already)
                if (thing.verbosity() >40):
                    progress( "Found %i new stmts on for rule %s" % (found, s))
                _total = _total+found
            else:
                c = None
#                if pred is self.asserts and subj is filterContext: c=obj
                if pred is self.type and obj is self.Truth: c=subj
                if c:
                    _total = _total + self.applyRules(workingContext,
                                                      c, targetContext,
                                                      universals=universals
                                                      + filterContext.universals())


        if thing.verbosity() > 4:
                progress("Total %i new statements from rules in %s"
                         % ( _total, filterContext))
        return _total

    # Beware lists are corrupted. Already list is updated if present.
    def tryRule(self, s, workingContext, targetContext, _variables, already=None):
        t = s.quad
        template = t[SUBJ]
        conclusion = t[OBJ]


        # When the template refers to itself, the thing we are
        # are looking for will refer to the context we are searching
        # Similarly, refernces to the working context have to be moved into the
        # target context when the conclusion is drawn.

        unmatched, templateExistentials = self.oneContext(template)
        _substitute([( template, workingContext)], unmatched)

        variablesMentioned = self.occurringIn(template, _variables)
        variablesUsed = self.occurringIn(conclusion, variablesMentioned)
        for x in variablesMentioned:
            if x not in variablesUsed:
                templateExistentials.append(x)
        if thing.verbosity() >20:
            progress("\n=================== tryRule ============ looking for:")
            progress( setToString(unmatched))
            progress("Variables declared       " + seqToString(_variables))
            progress(" mentioned in template   " + seqToString(variablesMentioned))
            progress(" also used in conclusion " + seqToString(variablesUsed))
            progress("Existentials        " + seqToString(templateExistentials))

#        conclusions, _outputVariables = self.nestedContexts(conclusion)
#        _substitute([( conclusion, targetContext)], conclusions)                

    # The smartIn context was the template context but it has been mapped to the workingContext.
        return self.match(unmatched, variablesUsed, templateExistentials, [workingContext],
                          self.conclude,
                          ( self, conclusion, targetContext,  # _outputVariables,
                            already))





# Return whether or nor workingContext containts a top-level template equvalent to subexp 
    def testIncludes(self, workingContext, template, _variables=[], smartIn=[], bindings=[]):

        if thing.verbosity() >30: progress("\n\n=================== testIncludes ============")

        # When the template refers to itself, the thing we are
        # are looking for will refer to the context we are searching

        if not(isinstance(workingContext, Formula) and isinstance(template, Formula)): return 0


        unmatched, templateExistentials = self.oneContext(template)
        _substitute([( template, workingContext)], unmatched)
        
        if bindings != []: _substitute(bindings, unmatched)

        if thing.verbosity() > 20:
            progress( "# testIncludes BUILTIN, %i terms in template %s, %i unmatched, %i template variables" % (
                len(template.statements),
                `template`[-8:], len(unmatched), len(templateExistentials)))
        if thing.verbosity() > 80:
            for v in _variables:
                progress( "    Variable: " + `v`[-8:])

        result = self.match(unmatched, [], _variables + templateExistentials, smartIn, justOne=1)
        if thing.verbosity() >30: progress("=================== end testIncludes =" + `result`)
#        thing.verbosity() = thing.verbosity()-100
        return result
 
    def genid(self, type):        
        self._nextId = self._nextId + 1
        return self.intern((type, self._genPrefix+`self._nextId`))

    def subContexts(self,con, path = []):
        """
        slow...
        """

        if con.descendents != None:
            return con.descendents
        
#        progress("subcontext "+`con`+" path "+`len(path)`)
        set = [con]
        path2 = path + [ con ]     # Avoid loops
        for s in con.statements:
            for p in PRED, SUBJ, OBJ:
                if isinstance(s[p], Formula):
                    if s[p] not in path2:
                        set2 = self.subContexts(s[p], path2)
                        for c in set2:
                            if c not in set: set.append(c)
        con.descendents = set
        return set
                        
    def nestedContexts(self, con):
        """ Return a list of statements and variables of either type
        found within the nested subcontexts
        """
        statements = []
        variables = []
        existentials = []
        for arc in con.statements:
            context, pred, subj, obj = arc.quad
            statements.append(arc.quad)
            if subj is context and (pred is self.forSome or pred is self.forAll): # @@@@
                variables.append(obj)   # Collect list of existentials
            if subj is context and pred is self.forSome: # @@@@
                existentials.append(obj)   # Collect list of existentials
                
        # Find all subformulae  - forumulae which are mentioned at least once.
        subformulae = []
        for arc in con.statements:
            for p in [ SUBJ, PRED, OBJ]:  # @ can remove PRED if formulae and predicates distinct
                x = arc.quad[p]
                if isinstance(x, Formula) and x in existentials:  # x is a Nested context
                    if x not in subformulae: subformulae.append(x) # Only one copy of each please
                    
        for x in  subformulae:
            for a2 in con.statements:  # Rescan for variables
                c2, p2, s2, o2 = a2.quad
                if  s2 is x and (p2 is self.forSome or p2 is self.forAll):
                    variables.append(o2)   # Collect list of existentials
            s, v = self.nestedContexts(x)
            statements = statements + s
            variables = variables + v
        return statements, variables


#  One context only:
# When we return the context, any nested ones are of course referenced in it

    def oneContext(self, con):
        """Find statements and variables in formula as template of a query.

        Return a list of statements and variables of either type
        found within the top level. Strip out forSome statments as
        when we are searching an existentially qualified can match against a constant (or a universal).
        """
        statements = []
        variables = []
#        existentials = []
        for arc in con.statements:
            context, pred, subj, obj = arc.quad
            if not(subj is context and pred is self.forSome):
                statements.append(arc.quad)
            else:
                if thing.verbosity()>79: progress( " Stripped forSome %s" % x2s(obj))

            if subj is context and (pred is self.forSome or pred is self.forAll): # @@@@
                if not isinstance(obj, Formula):
                    variables.append(obj)   # Collect list of existentials
#                if pred is self.forSome: # @@@@
#                    existentials.append(obj)   # Collect list of existentials
                
        return statements, variables

#   Find which variables occur in an expression

    def occurringIn(self, x, vars, level=0):
        """ Figure out, given a set of variables which if any occur in a formula, list, etc
         The result is returned as an ordered set so that merges can be done faster.
        """
        if isinstance(x, Formula):
            set = []
#            if thing.verbosity() > 98: progress("    occuringIn: "+"  "*level+`x`)
            for s in x.statements:
                if s[PRED] is not self.forSome:
                    for p in PRED, SUBJ, OBJ:
                        y = s[p]
                        if y is x:
                            pass
                        else:
                            set = merge(set, self.occurringIn(y, vars, level+1))
            return set
        elif x.asList() != None:
            set = []
            for y in x.asList().value():
                set = merge(set, self.occurringIn(y, vars, level+1))
            return set
        else:
            if x in vars:
                return [x]
            return []


#  Find whether any variables occur in an expression
#  NOT Used.

#    def anyOccurrences(self, vars, x):
#        """ Figure out, given a set of variables whether any occur in a list, formula etc."""
#        if x in vars: return x
#        if isinstance(x, Formula):
#            for s in x.statements:   # Should be valid list
#                for p in PRED, SUBJ, OBJ:
#                    y = s[p]
#                    z = self.anyOccurrences(vars, y)
#                    if z != None: return z
#        elif x.asList() != None:
#            for y in x.asList().value():
#                z = self.anyOccurrences(vars, y)
#                if z != None: return z
#            return None
#        return None            
        


############################################################## Query engine
#
# Template matching in a graph
#
# Optimizations we have NOT done:
#   - storing the tree of bindings so that we don't have to duplicate them another time
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


#    def every(self, quad):             # Returns a list of lists of values.  Used?
#        variables = []
#        q2 = list(quad)
#        for p in ALL4:
#            if quad[p] == None:
#                v = self.intern((SYMBOL, "internaluseonly:#var"+`p`))
#                variables.append(v)
#                q2[p] = v
#        unmatched = [ tuple(q2) ]
#        listOfBindings = []
#        count = self.match(unmatched, variables, [],
#                      action=collectBindings, param=listOfBindings, justOne=0)
#        results = []
#        for bindings in listOfBindings:
#            res = []
#            for var, val in bindings:
#                res.append(val)
#            results.append(res)
#        return results

    def checkList(self, context, L):
        """Check whether this new list causes ohter things to become lists"""
        if thing.verbosity() > 80: progress("Checking new list ",`L`)
        rest = L.asList()
        possibles = context.statementsMatching(pred=self.rest, obj=L)  # What has this as rest?
        for s in possibles:
            L2 = s[SUBJ]
            ff = context.statementsMatching(pred=self.first, subj=L2)
            if ff:
                first = ff[0][OBJ]
                if L2.asList() == None:
                    L2._asList = rest.precededBy(first)
                    self.checkList(context, L2)
                return

# Generic match routine, outer level:  Prepares query
        
    def match(self,                 # Neded for getting interned constants
               unmatched,           # Tuple of interned quads we are trying to match CORRUPTED
               variables,           # List of variables to match and return CORRUPTED
               existentials,        # List of variables to match to anything
                                    # Existentials or any kind of variable in subexpression
               smartIn = [],        # List of contexts in which to use builtins - typically the top onebb
               action = None,       # Action routine return subtotal of actions
               param = None,        # a tuple, see the call itself and conclude()
               hypothetical =0,     # The formulae are not in the store - check for their contents
               justOne = 0,         # Flag: Stop when you find the first one
               level = 0):          # nesting level
        """ Apply action(bindings, param) to succussful matches
        """
        if action == None: action=self.doNothing
        
        if thing.verbosity() > 50:
            progress( "match: called with %i terms." % (len(unmatched)))
            if thing.verbosity() > 80: progress( setToString(unmatched))

        if not hypothetical:
            for x in existentials[:]:   # Existentials don't count when they are just formula names
                                        # Also, we don't want a partial match. 
                if isinstance(x,Formula):
                    existentials.remove(x)

        queue = []   #  Unmatched with more info
        for quad in unmatched:
            item = QueryItem(self, quad)
            if item.setup(allvars=variables+existentials, smartIn=smartIn) == 0:
                if thing.verbosity() > 80: progress("match: abandoned, no way for "+`item`)
                return 0
            queue.append(item)
        return self.query2(queue, variables, existentials, smartIn, action, param,
                          bindings=[], justOne=justOne)

         
    def doNothing(self, bindings, param, level=0):
        if thing.verbosity()>99: progress( " "*level, "doNothing: Success! found it!")
        return 1                    # Return count of calls only

    # Whether we do a smart match determines whether we will be able to conclude
    # things which in fact we knew already thanks to the builtins.
    def conclude(self, bindings, param, level=0):  # Returns number of statements added to store
        store, conclusion, targetContext,  already = param
        if thing.verbosity() >60: progress( "\n#Concluding tentatively..." + bindingsToString(bindings))

        if already != None:
            if bindings in already:
                if thing.verbosity() > 30: progress("@@Duplicate result: ", bindingsToString(bindings))
                # raise foo
                return 0
            if thing.verbosity() > 30: progress("Not duplicate: ", bindingsToString(bindings))
            already.append(bindings)   # A list of lists

        b2 = bindings + [(conclusion, targetContext)]
        ok = targetContext.universals()  # It is actually ok to share universal variables with other stuff
        poss = conclusion.universals()
        for x in poss[:]:
            if x in ok: poss.remove(x)
        vars = conclusion.existentials() + poss  # Things with arbitrary identifiers
#        clashes = self.occurringIn(targetContext, vars)    Too slow to do every time
#        for v in clashes:
        for v in vars:
            b2.append((v, store.genid(SYMBOL))) # Regenerate names to avoid clash
        if thing.verbosity()>20:
            progress( "Concluding definitively" + bindingsToString(b2) )
        before = self.size
        self.copyContextRecursive(conclusion, targetContext, b2)
        if thing.verbosity()>20:
            progress( "  Size of store changed from %i to %i"%(before, self.size))
        return self.size - before

#        myConclusions = conclusions[:]
#        _substitute(bindings, myConclusions)
#        # Does this conclusion exist already in the database?
#        found = self.match(myConclusions[:],
#                           [], oes[:], smartIn=[targetContext],
#                           hypothetical=1,
#                           justOne=1,
#                           level = level + 8)  # Find first occurrence, SMART
#        if found:
#            if thing.verbosity()>00:
#                progress( "Concluding: Forget it, already had info" + bindingsToString(bindings))
#                progress("Already list: ", already) 
#                
#            if already != None: raise RunTimeError, "Already in store but bindings new?" 
#            return 0
        if thing.verbosity()>20:
            progress( "Concluding definitively" + bindingsToString(bindings))
        

        total = 0
        for q in myConclusions:
            q2 = _lookupQuad(bindings2, q)
            total = total + store.storeQuad(q2)
            if thing.verbosity()>10: progress( "        *** Conclude: " + quadToString(q2))
        return total

##################################################################################

    STATES2 = """State values as follows, high value=try first:
    99  State unknown - to be [re]calculated by setup, which should change it to stg else.
    80  Have exhausted all possible ways to saitsfy this item. stop now.
    65  Light, can run  Do this!
    60  Not a light built-in, haven't searched yet.
    50  Light built-in, not enough constants to calculate, haven't searched yet.
    20  Light built-in, not enough constants to calculate, search done.
    35  Heavy built-in, search failed, but formula now has no vars left. Ready to run.
    10  Heavy built-in, too many variables in args to calculate, search failed.
     9  Heavy built-in, too many variables within formula args to calculate, search failed.
     7  List defining statement, search failed, unbound variables in list.?? no
     5  List defining statement, search failed, list is all bound.
                    """

    def  query2(self,                # Neded for getting interned constants
               queue,               # Ordered queue of items we are trying to match CORRUPTED
               variables,           # List of variables to match and return CORRUPTED
               existentials,        # List of variables to match to anything
                                    # Existentials or any kind of variable in subexpression
               smartIn = [],        # List of contexts in which to use builtins - typically the top one
               action = None,       # Action routine return subtotal of actions
               param = None,        # a tuple, see the call itself and conclude()
               bindings = [],       # Bindings discovered so far
               newBindings = [],    # New bindings not yet incorporated
               justOne = 0,         # Flag: Stop when you find the first one
               level = 0):          # Nesting level for diagnostic indentation only
        """ Apply action(bindings, param) to succussful matches
    bindings      collected matches already found
    newBindings  matches found and not yet applied - used in recursion
        """
        if action == None: action=self.doNothing
        total = 0
        
        if thing.verbosity() > 50:
            progress( " "*level+"QUERY2: called %i terms, %i bindings %s, (new: %s)" %
                      (len(queue),len(bindings),bindingsToString(bindings),
                       bindingsToString(newBindings)))
            if thing.verbosity() > 90: progress( queueToString(queue, level))

        for pair in newBindings:   # Take care of business left over from recursive call
            if thing.verbosity()>95: progress(" "*level+"    new binding:  %s -> %s" % (x2s(pair[0]), x2s(pair[1])))
            if pair[0] in variables:
                variables.remove(pair[0])
                bindings.append(pair)  # Record for posterity
            else:      # Formulae aren't needed as existentials, unlike lists. hmm.
                if not isinstance(pair[0], Formula): # Hack - else rules13.n3 fails @@
                    existentials.remove(pair[0]) # Can't match anything anymore, need exact match

        # Perform the substitution, noting where lists become boundLists.
        # We do this carefully, messing up the order only of things we have already processed.
        if newBindings != []:
            for item in queue:
                if item.bindNew(newBindings) == 0: return 0


        while len(queue) > 0:

            if (thing.verbosity() > 90):
                progress(  " "*level+"query iterating with %i terms, %i bindings: %s; %i new bindings: %s ." %
                          (len(queue),
                           len(bindings),bindingsToString(bindings),
                           len(newBindings),bindingsToString(newBindings)))
                progress ( " "*level, queueToString(queue, level))


            # Take best.  (Design choice: search here or keep queue in order)
            # item = queue.pop()
            best = len(queue) -1 # , say...
            i = best - 1
            while i >=0:
                if (queue[i].state > queue[best].state
                    or (queue[i].state == queue[best].state
                        and queue[i].short < queue[best].short)): best=i
                i = i - 1                
            item = queue[best]
            queue.remove(item)
            if thing.verbosity()>49:
                progress( " "*level+"Looking at " + `item`
                         + "\nwith vars("+seqToString(variables)+")"
                         + " ExQuVars:("+seqToString(existentials)+")")
            con, pred, subj, obj = item.quad
            state = item.state
            if state == 80:
                return total # Forget it -- must be impossible
            if state == 70 or state == 65:
                nbs = item.tryLight(queue)
            elif state == 50 or state == 60: #  Not searched yet
                nbs = item.trySearch()
            elif state == 35:  # not light, may be heavy; or heavy ready to run
                if pred is self.includes:
                    if (isinstance(subj, Formula)
                        and isinstance(obj, Formula)):

                        more_unmatched, more_variables = self.oneContext(obj)
                        _substitute([( obj, subj)], more_unmatched)
                        _substitute(bindings, more_unmatched)
                        existentials = existentials + more_variables
                        allvars = variables + existentials
                        for quad in more_unmatched:
                            newItem = QueryItem(self, quad)
                            queue.append(newItem)
                            newItem.setup(allvars, smartIn + [subj])
                        if thing.verbosity() > 40:
                                progress( " "*level+
                                          "**** Includes: Adding %i new terms and %s as new existentials."%
                                          (len(more_unmatched),
                                           seqToString(more_variables)))
                        item.state = 0
                    else:
                        raise RuntimeError("Include can only work on formulae "+`item`)
                    nbs = []
                else:
                    nbs = item.tryHeavy(queue, bindings)
            elif state == 7: # Lists with unbound vars
                if thing.verbosity()>50:
                        progress( " "*level+ "List left unbound, returing")
                return 0   # forget it  (this right?!@@)
            elif state == 5: # bound list
                if thing.verbosity()>50: progress( " "*level+ "QUERY FOUND MATCH (dropping lists) with bindings: " + bindingsToString(bindings))
                return action(bindings, param)  # No non-list terms left .. success!
            elif state ==10 or state == 20: # Can't
                if thing.verbosity() > 49 :
                    progress("@@@@ Warning: query can't find term which will work.")
                    progress( "   state is %s, queue length %i" % (state, len(queue)+1))
                    progress("@@ Current item: %s" % `item`)
                    progress(queueToString(queue))
#                    raise RuntimeError, "Insufficient clues"
                return 0  # Forget it
            else:
                raise RuntimeError, "Unknown state " + `state`
            if thing.verbosity() > 90: progress(" "*level +"nbs=" + `nbs`)
            if nbs == 0: return 0
            else:
                total = 0
                for nb in nbs:
                    q2 = []
                    for i in queue:
                        newItem = i.clone()
                        q2.append(newItem)  #@@@@@@@@@@  If exactly 1 binding, loop (tail recurse)
                    total = total + self.query2(q2, variables[:], existentials[:], smartIn, action, param,
                                          bindings[:], nb, justOne=justOne, level=level+2)
                    if justOne and total:
                        return total

            if item.state == 80: return total
            if item.state != 0:   # state 0 means leave me off the list
                queue.append(item)
            # And loop back to take the next item

        if thing.verbosity()>50: progress( " "*level+"QUERY MATCH COMPLETE with bindings: " + bindingsToString(bindings))
        return action(bindings, param, level)  # No terms left .. success!


class QueryItem:
    def __init__(self, store, quad):
        self.quad = quad
        self.searchPattern = None # Will be list of variables
        self.store = store
        self.state = 99  # Invalid
        self.short = INFINITY
        self.neededToRun = None   # see setup()
        self.myIndex = None     # will be list of satistfying statements
        return

    def clone(self):
        """Take a copy when for iterating on a query"""
        x = QueryItem(self.store, self.quad)
        x.state = self.state
        x.short = self.short
        x.neededToRun = []
        x.searchPattern = self.searchPattern[:]
        for p in ALL4:   # Deep copy!  Prevent crosstalk
            x.neededToRun.append(self.neededToRun[p][:])
        x.myIndex = self.myIndex
        return x



    def setup(self, allvars, smartIn):        
        """Check how many variables in this term,
        and how long it would take to search

        Returns, [] normally or 0 if there is no way this query will work.
        Only called on virgin query item."""
        con, pred, subj, obj = self.quad
        self.neededToRun = [ [], [], [], [] ]  # for each part of speech
        self.searchPattern = [con, pred, subj, obj]  # What do we search for?
        hasUnboundFormula = 0
        for p in PRED, SUBJ, OBJ :
            x = self.quad[p]
            if x in allvars:   # Variable
                self.neededToRun[p] = [x]
                self.searchPattern[p] = None   # can bind this
            if x.asList() != None and x is not self.store.nil:
                self.searchPattern[p] = None   # can bind this
                ur = self.store.occurringIn(x, allvars)
                self.neededToRun[p] = ur
            elif isinstance(x, Formula): # expr
                ur = self.store.occurringIn(x, allvars)
                self.neededToRun[p] = ur
                if ur != []:
                    hasUnboundFormula = 1     # Can't search
                
        if hasUnboundFormula:
            self.short = INFINITY   # can't search
        else:
            self.myIndex = con._index.get((self.searchPattern[1],
                                           self.searchPattern[2],
                                           self.searchPattern[3]), [])
            self.short = len(self.myIndex)

        if con in smartIn and isinstance(pred, LightBuiltIn):
            if self.canRun(): self.state = 70  # Can't do it here
            else: self.state = 50 # Light built-in, can't run yet, not searched
        elif self.short == 0:  # Skip search if no possibilities!
            self.searchDone()
        else:
            self.state = 60   # Not a light built in, not searched.
        if thing.verbosity() > 80: progress("setup:" + `self`)
        if self.state == 80: return 0
        return []



    def tryLight(self, queue):                    
        """check for "light" (quick) built-in functions.
        Return codes:  0 - give up;  1 - continue,
                [...] list of binding lists"""
        con, pred, subj, obj = self.quad

        self.state = 50   # Assume can't run
        if (self.neededToRun[SUBJ] == []):
            if (self.neededToRun[OBJ] == []):   # bound expression - we can evaluate it
                obj_py = self.store._toPython(obj, queue)
                subj_py = self.store._toPython(subj, queue)
                if pred.evaluate(self.store, con, subj, subj_py, obj, obj_py):
                    self.state = 0 # satisfied
                    return []   # No new bindings but success in logical operator
                else: return 0   # We absoluteley know this won't match with this in it
            else: 
                if isinstance(pred, Function):
                    subj_py = self.store._toPython(subj, queue)
                    result = pred.evaluateObject(self.store, con, subj, subj_py)
                    if result != None:
                        self.state = 80
                        return [[ (obj, result)]]
        else:
            if (self.neededToRun[OBJ] == []):
                if isinstance(pred, ReverseFunction):
                    obj_py = self.store._toPython(obj, queue)
                    result = pred.evaluateSubject(self.store, con, obj, obj_py)
                    if result != None:
                        self.state = 80
                        return [[ (subj, result)]]
        if thing.verbosity() > 30:
            progress("Builtin could not give result"+`self`)

        # Now we have a light builtin needs search,
        # otherwise waiting for enough constants to run
        return []   # Keep going
        
    def trySearch(self):
        """Search the store"""
        nbs = []
        if self.short == INFINITY:
            if thing.verbosity() > 36:
                progress( "  Can't search for %s" % `self`)
        else:
            if thing.verbosity() > 36:
                progress( "  Searching %i for %s" %(self.short, `self`))
            for s in self.myIndex :  # search the index
                nb = []
                reject = 0
                for p in ALL4:
                    if self.searchPattern[p] == None:
                        x = self.quad[p]
                        binding = ( x, s.quad[p])
                        duplicate = 0
                        for oldbinding in nb:
                            if oldbinding[0] is self.quad[p]:
                                if oldbinding[1] is binding[1]:
                                    duplicate = 1  
                                else: # don't bind same to var to 2 things!
                                    reject = 1
                        if not duplicate:
                            nb.append(( self.quad[p], s.quad[p]))
                if not reject:
                    nbs.append(nb)  # Add the new bindings into the set

        self.searchDone()  # State transitions
        return nbs

    def searchDone(self):
        """Search has been done: figure out next state."""
        con, pred, subj, obj = self.quad
        if self.state == 50:   # Light, can't run yet.
            self.state = 20    # Search done, can't run
        elif (subj.asList() != None
              and ( pred is self.store.first or pred is self.store.rest)):
            if self.neededToRun[SUBJ] == [] and self.neededToRun[OBJ] == []:
                self.state = 5   # , it is true as an axiom.
            else:
                self.state = 7   # Still need to resolve this
        elif not isinstance(pred, HeavyBuiltIn):
            self.state = 80  # Done with this one: Do new bindings & stop
        elif self.canRun():
            self.state = 35
        else:
            self.state = 10
        if thing.verbosity() > 90:
            progress("...searchDone, now ",self)
        return
    
    def canRun(self):
        "Is this built-in ready to run?"

        if (self.neededToRun[SUBJ] == []):
            if (self.neededToRun[OBJ] == []): return 1
            else:
                pred = self.quad[PRED]
                return (isinstance(pred, Function)
                          or pred is self.store.includes)  # Can use variables
        else:
            if (self.neededToRun[OBJ] == []):
                return isinstance(self.quad[PRED], ReverseFunction)
        
    def  tryHeavy(self, queue, bindings):
        """Deal with heavy built-in functions."""
        con, pred, subj, obj = self.quad
        try:
            self.state = 10  # Assume can't resolve
            if self.neededToRun[SUBJ] == []:
                if self.neededToRun[OBJ] == []: # Binary operators?
                    result = pred.evaluate2(subj, obj, bindings[:])
                    if result:
                        if thing.verbosity() > 80:
                                progress("Heavy predicate succeeds")
                        self.state = 0  # done
                        return []
                    else:
                        if thing.verbosity() > 80:
                                progress("Heavy predicate fails")
                        return 0   # It won't match with this in it
                else:   # The statement has one variable - try functions
                    if isinstance(pred, Function):
                        result = pred.evaluateObject2(subj)
                        if result == None: return 0
                        else:
                            self.state = 80
                            return [[ (obj, result)]]
            else:
                if (self.neededToRun[OBJ] == []
                    and isinstance(pred, ReverseFunction)):
                        obj_py = self.store._toPython(obj, queue)
                        result = pred.evaluateSubject2(self.store, obj, obj_py)
                        if result != None:  # There is some such result
                            self.state = 80  # Do this then stop - that is all
                            return [[ (subj, result)]]
                        else: return 0
            if thing.verbosity() > 30:
                progress("Builtin could not give result"+`self`)
        except (IOError, SyntaxError):
            raise BuiltInFailed(sys.exc_info(), self ),None


    def bindNew(self, newBindings):
        """Take into account new bindings from query processing to date

        The search may get easier, and builtins may become ready to run.
        Lists may either be matched against store by searching,
        and/or may turn out to be bound and therefore ready to run."""
        con, pred, subj, obj = self.quad
        if thing.verbosity() > 90:
            progress("....Binding ", `self` + " with "+ `newBindings`)
        q=[con, pred, subj, obj]
        changedPattern = 0
        for p in ALL4:
            changed = 0
            for var, val in newBindings:
                if var in self.neededToRun[p]:
                    self.neededToRun[p].remove(var)
                    changed = 1
                if q[p] is var and self.searchPattern[p]==None:
                    self.searchPattern[p] = val # const now
                    changedPattern = 1
                    changed = 1
                    self.neededToRun[p] = [] # Now it is definitely all bound
            if changed:
                q[p] = _lookupRecursive(newBindings, q[p])   # possibly expensive
                
        self.quad = q[0], q[1], q[2], q[3]  # yuk

        if self.state in [60, 50, 75]: # Not searched yet
            for p in PRED, SUBJ, OBJ:
                x = self.quad[p]
                if isinstance(x, Formula):
                    if self.neededToRun[p]!= []:
                        self.short = INFINITY  # Forget it
                        break
            else:
                self.myIndex = con._index.get(( self.searchPattern[1],
                                                self.searchPattern[2],
                                                self.searchPattern[3]), [])
                self.short = len(self.myIndex)
#                progress("@@@ Ooops, short is ", self.short, self.searchPattern)
            if self.short == 0:
                self.searchDone()


        if isinstance(self.quad[PRED], BuiltIn):
            if self.canRun():
                if self.state == 50: self.state = 70
                elif self.state == 20: self.state = 65
                elif self.state == 10: self.state = 35
        elif (self.state == 7
              and self.neededToRun[SUBJ] == []
              and self.neededToRun[OBJ] == []):
            self.state = 5
        if thing.verbosity() > 90:
            progress("...bound becomes ", `self`)
        if self.state == 80: return 0
        return [] # continue

    def __repr__(self):
        """Diagnostic string only"""
        return "%3i) short=%i, %s" % (
                self.state, self.short,
                quadToString(self.quad, self.neededToRun, self.searchPattern))


# An action routine for collecting bindings:

def collectBindings(bindings, param, level=0):
    """Return number of bindings found and collects them"""
    param.append(bindings)
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

def _lookupQuadRecursive(bindings, q):
	context, pred, subj, obj = q
	return (
            _lookupRecursive(bindings, context),
            _lookupRecursive(bindings, pred),
            _lookupRecursive(bindings, subj),
            _lookupRecursive(bindings, obj) )

def _lookup(bindings, value):
    for left, right in bindings:
        if left == value: return right
    return value

def _lookupRecursive(bindings, x, old=None, new=None):
    """ Subsitute into formula. Problem: intermiediate formulae won't get garbage collected."""
    vars = []
    if x is old: return new
    for left, right in bindings:
        if left == x: return right
        vars.append(left)
    if not isinstance(x, Formula):
        return x
    store = x.store
    oc = store.occurringIn(x, vars)
    if oc == []: return x # phew!
    y = store.genid(FORMULA)
    if thing.verbosity() > 90: progress("lookupRecursive "+`x`+" becomes new "+`y`)
    for s in x.statements:
        store.storeQuad((y,
                         _lookupRecursive(bindings, s[PRED], x, y),
                         _lookupRecursive(bindings, s[SUBJ], x, y),
                         _lookupRecursive(bindings, s[OBJ], x, y)))
    return store.endFormula(y) # intern


class URISyntaxError(ValueError):
    """A parameter is passed to a routine that requires a URI reference"""
    pass

#################################
#
# Utilty routines

def merge(a,b):
    """Merge sorted sequences

    The fact that the sequences are sorted makes this faster"""
    i = 0
    j = 0
    m = len(a)
    n = len(b)
    result = []
    while 1:
        if i==m:   # No more of a, return rest of b
            return result + b[j:]
        if j==n:
            return result + a[i:]
        if a[i] < b[j]:
            result.append(a[i])
            i = i + 1
        elif a[i] > b[j]:
            result.append(b[j])
            j = j + 1
        else:  # a[i]=b[j]
            result.append(a[i])
            i = i + 1
            j = j + 1
        

#   DIAGNOSTIC STRING OUTPUT
#
def bindingsToString(bindings):
    str = ""
    for x, y in bindings:
        str = str + (" %s->%s" % ( x2s(x), x2s(y)))
    return str

def setToString(set):
    str = ""
    for q in set:
        str = str+ "        " + quadToString(q) + "\n"
    return str

def seqToString(set):
    str = ""
    for x in set[:-1]:
        str = str + x2s(x) + ","
    for x in set[-1:]:
        str = str+  x2s(x)
    return str

def queueToString(queue, level=0):
    str = ""
    for item in queue:
        str = str + " "*level +  `item` + "\n"
    return str


def quadToString(q, neededToRun=[[],[],[],[]], pattern=[1,1,1,1]):
    qm=[" "," "," "," "]
    for p in ALL4:
        n = neededToRun[p]
        if n == []: qm[p]=""
#        elif n == [q[p]]: qm[p] = "?"
        else: qm[p] = "(" + `n`[1:-1] + ")"
        if pattern[p]==None: qm[p]=qm[p]+"?"
    return "%s%s ::  %8s%s %8s%s %8s%s." %(x2s(q[CONTEXT]), qm[CONTEXT],
                                            x2s(q[SUBJ]),qm[SUBJ],
                                            x2s(q[PRED]),qm[PRED],
                                            x2s(q[OBJ]),qm[OBJ])


def x2s(x):
    return `x`


def isString(x):
    # in 2.2, evidently we can test for isinstance(types.StringTypes)
    return type(x) is type('') or type(x) is type(u'')

