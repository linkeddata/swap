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

Interfaces
==========

This store stores many formulae, where one formula is what in
straight RDF implementations is known as a "triple store".
So look at the Formula class for a triple store interface.

See also for comparison, a python RDF API for the Redland library (in C):
   http://www.redland.opensource.ac.uk/docs/api/index.html 
and the redfoot/rdflib interface, a python RDF API:
   http://rdflib.net/latest/doc/triple_store.html

Agenda:
=======

 - get rid of other globals (DWC 30Aug2001)
 - Add dynamic load of web python via rdf-schema: imp.load_source("foo", "llyn.py", open("llyn.py", "r"))
 - implement a back-chaining reasoner (ala Euler/Algernon) on this store? (DWC)
 - run http daemon/client sending changes to database
 - act as client/server for distributed system
  - postgress, mySQl underlying database?
 -    daml:import
 -    standard mappping of SQL database into the web in N3/RDF
 -    
 - logic API as requested DC 2000/12/10
 - Jena-like API x=model.createResource(); addProperty(DC.creator, "Brian", "en")
 -   syntax for "all she wrote" - schema is complete and definitive
 - metaindexes - "to know more about x please see r" - described by
 - general python URI access with catalog!
 - equivalence handling inc. equivalence of equivalence?
 Shakedown:
 - Find all synonyms of synonym
 - Find closure for all synonyms
 - Find superclass closure?
- represent URIs bound to same equivalence closure object?
 - proof generation

- dynamic bultins - ontology for adding python.

BULTINS WE NEED
    - {x log:entails y } <=>  { x!log:conclusion log:includes y}.    [is log:conclusion of x] log:includes y
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
 - sucking in the schema (http library?) --schemas ;
 - to know about r1 see r2;
 - split Query engine out as subclass of RDFStore? (DWC)
    SQL-equivalent client
 - split out separate modules: CGI interface, command-line stuff,
   built-ins (DWC 30Aug2001)
- (test/retest.sh is another/better list of completed functionality --DWC)
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
 ULTINS WE HAVE DONE
    - includes(expr1, expr2)      (cf >= ,  dixitInterAlia )
    - indirectlyImplies(expr1, expr2)   
    - startsWith(x,y)
    - uri(x, str)
    - usesNamespace(x,y)   # find transitive closure for validation  - awful function in reality

NOTES

This is slow - Parka [guiFrontend PIQ] for example is faster but is propritary (patent pending). Jim Hendler owsns the
research version. Written in C. Of te order of 30k lines
"""

# emacsbug="""emacs got confused by long string above@@"""

from __future__ import generators
# see http://www.amk.ca/python/2.2/index.html#SECTION000500000000000000000

import types
import string
import re
import StringIO
import sys
import time
import uripath

import urllib # for log:content
import md5, binascii  # for building md5 URIs

import notation3    # N3 parsers and generators, and RDF generator
# import sax2rdf      # RDF1.0 syntax parser to N3 RDF stream

import diag  # problems importing the tracking flag, must be explicit it seems diag.tracking
from diag import progress, progressIndent, verbosity, tracking
from thing import Namespace, BuiltIn, LightBuiltIn, \
    HeavyBuiltIn, Function, ReverseFunction, \
    Literal, Symbol, Fragment, FragmentNil, Anonymous, Term, List, EmptyList

#import RDFSink
from RDFSink import Logic_NS, RDFSink, forSomeSym, forAllSym
from RDFSink import CONTEXT, PRED, SUBJ, OBJ, PARTS, ALL4
from RDFSink import N3_nil, N3_first, N3_rest, DAML_NS, N3_Empty, N3_List
from RDFSink import RDF_NS_URI

from RDFSink import FORMULA, LITERAL, ANONYMOUS, SYMBOL
# = RDFSink.SYMBOL # @@misnomer

LITERAL_URI_prefix = "data:application/n3;"

cvsRevision = "$Revision$"

# Magic resources we know about

from RDFSink import RDF_type_URI, DAML_equivalentTo_URI

from why import Because, BecauseBuiltIn, BecauseOfRule, \
    BecauseOfExperience, becauseSubexpression, BecauseMerge ,report

STRING_NS_URI = "http://www.w3.org/2000/10/swap/string#"
META_NS_URI = "http://www.w3.org/2000/10/swap/meta#"
INTEGER_DATATYPE = "http://www.w3.org/2001/XMLSchema#integer"
FLOAT_DATATYPE = "http://www.w3.org/2001/XMLSchema#double"

reason=Namespace("http://www.w3.org/2000/10/swap/reason#")

META_mergedWith = META_NS_URI + "mergedWith"
META_source = META_NS_URI + "source"
META_run = META_NS_URI + "run"

doMeta = 0  # wait until we have written the code! :-)

INFINITY = 1000000000           # @@ larger than any number occurences


# State values as follows, high value=try first:
S_UNKNOWN = 	99  # State unknown - to be [re]calculated by setup.
S_FAIL =   	80  # Have exhausted all possible ways to saitsfy this item. stop now.
S_LIGHT_UNS_GO= 70  # Light, not searched yet, but can run
S_LIGHT_GO =  	65  # Light, can run  Do this!
S_NOT_LIGHT =   60  # Not a light built-in, haven't searched yet.
S_LIGHT_EARLY=	50  # Light built-in, not enough constants to calculate, haven't searched yet.
S_HEAVY_READY=	40  # Heavy built-in, search failed, but formula now has no vars left. Ready to run.
S_LIGHT_WAIT=	30  # Light built-in, not enough constants to calculate, search done.
S_HEAVY_WAIT=	20  # Heavy built-in, too many variables in args to calculate, search failed.
S_HEAVY_WAIT_F=	19  # Heavy built-in, too many vars within formula args to calculate, search failed.
S_REMOTE =	10  # Waiting for local query to be resolved as much as possible
S_LIST_UNBOUND = 7  # List defining statement, search failed, unbound variables in list.?? no
S_LIST_BOUND =	 5  # List defining statement, search failed, list is all bound.
S_DONE =	 0  # Item has been staisfied, and is no longer a constraint



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
	    if self.datatype == other.datatype:
		diff = cmp(self.string, other.string)
		if diff != 0 : return diff
		return cmp(self.lang, other.lang)
	    else:
		if self.datatype == None: return -1
		if other.datatype == None: return 1
		return compareURI(self.datatype, other.datatype)
        else:
            return -1
    if isinstance(other, Literal):
        return 1

    if isinstance(self, Formula):
        if isinstance(other, Formula):
	    for f in self, other:
		if f.cannonical is not f:
		    progress("@@@@@ Comparing formula NOT CANNONICAL", `f`)
            s = self.statements
            o = other.statements
            ls = len(s)
            lo = len(o)
            if ls > lo: return 1
            if ls < lo: return -1

            for se, oe, in  ((self.universals(), other.universals()),
			     (self.existentials(), other.existentials())
			    ):
		lse = len(se)
		loe = len(oe)
		if lse > loe: return 1
		if lse < loe: return -1
		se.sort(compareURI)
		oe.sort(compareURI)
		for i in range(lse):
		    diff = compareURI(se[i], oe[i])
		    if diff != 0: return diff

#		No need - cannonical formulae are always sorted
            s.sort(StoredStatement.compareSubjPredObj) # forumulae are all the same
            o.sort(StoredStatement.compareSubjPredObj)
            for i in range(ls):
                diff = s[i].compareSubjPredObj(o[i])
                if diff != 0: return diff
            raise RuntimeError("Identical formulae not interned! Length %i: %s\n\t%s\n vs\t%s" % (
			ls, `s`, self.debugString(), other.debugString()))
        else:
            return 1
    if isinstance(other, Formula):
        return -1

        # Both regular URIs
#        progress("comparing", self.representation(), other.representation())
    _type = RDF_type_URI
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
    also provides an ordering which allows is to render a graph in a cannonical way.
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
       
    NOT WRITTEN
    """
    pass



class DataObject:
    """The info about a term in the context of a specific formula
    It is created by being passed the formula and the term, and is
    then accessed like a python dictionary of sequences of values. Example:
    
    F = myWorkingFormula
    x = F.theObject(pred=rdfType obj=fooCar)
    for y in x[color][label]
    """
    def __init__(context, term):
	self.context = context
	self.term = term
	
    def __getItem__(pred):   #   Use . or [] ?
	values = context.objects(pred=pred, subj=self.term)
	for v in value:
	    yield DataObject(self.context, v)


def dereference(x, mode="", workingContext=None):
    """dereference an object, finding the semantics of its schema if any
    
    Returns None if it cannot be retreived.
    Could be speeded up by hanging the cached value as a python attribute on x
    """
    if isinstance(x, Fragment): x = x.resource
    if hasattr(x, "_semantics"): return x._semantics

    inputURI = x.uriref()
    if verbosity() > 20: progress("Web: Looking up %s" % x)
    if "E" not in mode: F = x.store.load(inputURI)
    else:
	try:
	    F = x.store.load(inputURI)
	except:
	#except (IOError, SyntaxError, DocumentAccessError, xml.sax._exceptions.SAXParseException):
	    F = None
    if F != None and "m" in mode:
	workingContext.reopen()
	if verbosity() > 45: progress("Web: dereferenced %s  added to %s" %(
		    x, workingContext))
	workingContext.store.copyFormula(F, workingContext)
    setattr(x, "_semantics", F)
    if verbosity() > 25: progress("Web: Dereferencing %s gave %s" %(x, F))
    return F
		

###################################### Forumula
#
# A Formula is a set of triples.

class Formula(Fragment):
    """A formula of a set of RDF statements, triples.
    
    (The triples are actually instances of StoredStatement.)
    Other systems such as jena and redland use the term "Model" for Formula.
    For rdflib, this is known as a TripleStore.
    Cwm and N3 extend RDF to allow a literal formula as an item in a triple.
    
    A formula is either open or closed.  Initially, it is open. In this
    state is may be modified - for example, triples may be added to it.
    When it is closed, note that a different interned version of itself
    may be returned. From then on it is a constant.
    
    Only closed formulae may be mentioned in statements in other formuale.
    
    There is a reopen() method but it is not recommended, and if desperate should
    only be used immediately after a close().
    """
    def __init__(self, resource, fragid):
        Fragment.__init__(self, resource, fragid)
        self.descendents = None   # Placeholder for list of closure under subcontext
        self.cannonical = None # Set to self if this has been checked for duplicates
	self.collector = None # Object collecting evidence, if any 
	self._listValue = {}
	self.statements = []
	self._index = {}
	self._index[(None,None,None)] = self.statements

	self._closureMode = ""
	self._closureAgenda = []
	self._closureAlready = []
	self._existentialVariables = []
	self._universalVariables = []


    def existentials(self):
        """Return a list of existential variables with this formula as scope.
	
	Implementation:
	we may move to an internal storage rather than these pseudo-statements"""
        return self._existentialVariables
#        return self.each(subj=self, pred=self.store.forSome)

    def universals(self):
        """Return a list of variables universally quantified with this formula as scope.

	Implementation:
	We may move to an internal storage rather than these statements."""
	return self._universalVariables
#        return self.each(subj=self, pred=self.store.forAll)
    
    def variables(self):
        """Return a list of all variables quantified within this scope."""
        return self.existentials() + self.universals()
	
    def listValue(self, x):
	"""as stored in this formula, does this have a value as a list?"""
	if x is self.store.nil: return x._asList  # bootstrap nil list
	return self._listValue.get(x, None)

    def size(self):
        """Return the number statements.
	Obsolete: use len(F)."""
        return len(self.statements)

    def __len__(self):
        """ How many statements? """
        return len(self.statements)

    def __iter__(self):
	"""The internal method which allows one to iterate over the statements
	as though a formula were a sequence.
	"""
	for s in self.statements:
	    yield s

    def newSymbol(self, uri):
	"""Create or reuse the internal representation of the RDF node whose uri is given
	
	The symbol is created in the same store as the formula."""
	return self.store.newSymbol(uri)

    def newLiteral(self, str, dt=None, lang=None):
	"""Create or reuse the internal representation of the RDF literal whose string is given
	
	The literal is created in the same store as the formula."""
	return self.store.newLiteral(str, dt, lang)
	
    def newBlankNode(self, uri=None, why=None):
	"""Create a new unnamed node with this formula as context.
	
	The URI is typically omitted, and the system will make up an internal idnetifier.
        If given is used as the (arbitrary) internal identifier of the node."""
	return self.store.newBlankNode(self, uri,  why=why)
    
    def declareUniversal(self, v):
	if v not in self._universalVariables:
	    self._universalVariables.append(v)
	
    def declareExistential(self, v):
	if v not in self._existentialVariables:
	    self._existentialVariables.append(v)
	
    def newExistential(self, uri=None, why=None):
	"""Create a named variable existentially qualified within this formula
	
	If the URI is not given, an arbitrary identifier is generated.
	See also: existentials()."""
	return self.store.newExistential(self, uri, why=why)
    
    def newUniversal(self, uri=None, why=None):
	"""Create a named variable universally qualified within this formula
	
	If the URI is not given, an arbitrary identifier is generated.
	See also: universals()"""
	return self.store.newUniversal(self, uri, why=why)

    def newFormula(self, uri=None):
	"""Create a new open, empty, formula in the same store as this one.
	
	The URI is typically omitted, and the system will make up an internal idnetifier.
        If given is used as the (arbitrary) internal identifier of the formula."""
	return self.store.newFormula(uri)

    def statementsMatching(self, pred=None, subj=None, obj=None):
        """Return a READ-ONLY list of StoredStatement objects matching the parts given
	
	For example:
	for s in f.statementsMatching(pred=pantoneColor):
	    print "We've got one which is ", `s[OBJ]`
	    
	If none, returns []
	"""
        return self._index.get((pred, subj, obj), [])

    def contains(self, pred=None, subj=None, obj=None):
        """Return boolean true iff formula contains statement(s) matching the parts given
	
	For example:
	if f.contains(pred=pantoneColor):
	    print "We've got one statement about something being some color"
	"""
        x =  self._index.get((pred, subj, obj), [])
	if x : return 1
	return 0


    def any(self, subj=None, pred=None, obj=None):
        """Return None or the value filing the blank in the called parameters.
	
	Specifiy exactly two of the arguments.
	color = f.any(pred=pantoneColor, subj=myCar)
	somethingRed = f.any(pred=pantoneColor, obj=red)
	
	Note difference from the old store.any!!
	Note SPO order not PSO.
	To aboid confusion, use named parameters.
	"""
	hits = self._index.get((pred, subj, obj), [])
	if not hits: return None
	s = hits[0]
	if pred == None: return s[PRED]
	if subj == None: return s[SUBJ]
	if obj == None: return s[OBJ]
	raise ParameterError("You must give one wildcard")


    def the(self, subj=None, pred=None, obj=None):
        """Return None or the value filing the blank in the called parameters
	
	This is just like any() except it checks that there is only
	one answer in the store. It wise to use this when you expect only one.
	
	color = f.the(pred=pantoneColor, subj=myCar)
	redCar = f.the(pred=pantoneColor, obj=red)
	"""
	hits = self._index.get((pred, subj, obj), [])
	if not hits: return None
	assert len(hits) == 1, """There should only be one match for (%s %s %s).
	    Found: %s""" %(subj, pred, obj, self.each(subj, pred, obj))
	s = hits[0]
	if pred == None: return s[PRED]
	if subj == None: return s[SUBJ]
	if obj == None: return s[OBJ]
	raise parameterError("You must give one wildcard using the()")

    def each(self, subj=None, pred=None, obj=None):
        """Return a list of values value filing the blank in the called parameters
	
	Examples:
	colors = f.each(pred=pantoneColor, subj=myCar)
	
	for redthing in f.each(pred=pantoneColor, obj=red): ...
	
	"""
	hits = self._index.get((pred, subj, obj), [])
	if hits == []: return []
	if pred == None: wc = PRED
	elif subj == None: wc = SUBJ
	elif obj == None: wc = OBJ
	else: raise ParameterError("You must give one wildcard None for each()")
	res = []
	for s in hits:
	    res.append(s[wc])   # should use yeild @@ when we are ready
	return res

    def searchable(self, subj=None, pred=None, obj=None):
	"""A pair of the difficulty of searching and a statement iterator of found statements
	
	The difficulty is a store-portable measure of how long the store
	thinks (in arbitrary units) it will take to search.
	This will only be used for choisng which part of the query to search first.
	If it is 0 there is no solution to the query, we know now.
	
	In this implementation, we use the length of the sequence to be searched."""
        res = self._index.get((pred, subj, obj), [])
	return len(res), res

    def bind(self, prefix, uri):
	"""Give a prefix and associated URI as a hint for output
	
	The store does not use prefixes internally, but keeping track
	of those usedd in the input data makes for more human-readable output.
	"""
	return self.store.bind(prefix, uri)

    def add(self, subj, pred, obj, why=None):
	"""Add a triple to the formula.
	
	The formula must be open.
	subj, pred and obj must be objects as for example generated by Formula.newSymbol() and newLiteral(), or else literal values which can be interned.
	why 	may be a reason for use when a proof will be required.
	"""
	store = self.store
	if not isinstance(pred, Term): pred = store.intern(pred)
	if not isinstance(subj, Term): subj = store.intern(subj)
	if not isinstance(obj, Term): obj = store.intern(obj)


	q = self, pred, subj, obj
        if verbosity() > 50:
            progress("add quad (size before %i) " % self.store.size +`q`)
        if self.statementsMatching(pred, subj, obj):
            if verbosity() > 97:  progress("storeQuad duplicate suppressed"+`q`)
            return 0  # Return no change in size of store
        if self.cannonical != None:
            raise RuntimeError("Attempt to add statement to cannonical formula "+`self`)
	assert not isinstance(pred, Formula) or pred.cannonical is pred, "pred Should be closed"+`pred`
	assert (not isinstance(subj, Formula)
		or subj is self
		or subj.cannonical is subj), "subj Should be closed or this"+`subj`
	assert not isinstance(obj, Formula) or obj.cannonical is obj, "obj Should be closed"+`obj`

        store.size = store.size+1

# We collapse lists from the declared daml first,rest structure into List objects.
# To do this, we need (a) a first; (b) a rest, and (c) the rest being a list.
# We trigger List collapse on any of these three becoming true.
# @@@ we don't reverse this on remove statement.

        if pred is store.rest and self.listValue(obj) != None:
            first = self.the(pred=store.first, subj=subj)
            if first != None and self.listValue(subj) == None:
                self._listValue[subj] = self.listValue(obj).precededBy(first)
                self._checkList(subj)

        elif pred is store.first:
            rest = self.the(pred=store.rest, subj=subj)
            if rest !=None:
                if content.listValue(rest) != None and self.listValue(subj) == None:
                    self._listValue[subj] = self.listValue(rest).precededBy(obj)
                    self._checkList(subj)

        s = StoredStatement(q)
	
	if diag.tracking:
	    if (why == None): raise RuntimeError(
		"Tracking reasons but no reason given for"+`s`)
	    report(s, why)

        # Build 8 indexes.
#       This now takes a lot of the time in a typical  cwm run! :-( 

	if subj is self:  # Catch variable declarations
	    if pred is self.store.forAll:
		if obj not in self._universalVariables:
		    if verbosity() > 50: progress("\tUniversal ", obj)
		    self._universalVariables.append(obj)
		return 1
	    if pred is self.store.forSome:
		if obj not in self._existentialVariables:
		    if verbosity() > 50: progress("\tExistential ", obj)
		    self._existentialVariables.append(obj)
		return 1

        self.statements.append(s)
       
        list = self._index.get((None, None, obj), None)
        if list == None: self._index[(None, None, obj)]=[s]
        else: list.append(s)

        list = self._index.get((None, subj, None), None)
        if list == None: self._index[(None, subj, None)]=[s]
        else: list.append(s)

        list = self._index.get((None, subj, obj), None)
        if list == None: self._index[(None, subj, obj)]=[s]
        else: list.append(s)

        list = self._index.get((pred, None, None), None)
        if list == None: self._index[(pred, None, None)]=[s]
        else: list.append(s)

        list = self._index.get((pred, None, obj), None)
        if list == None: self._index[(pred, None, obj)]=[s]
        else: list.append(s)

        list = self._index.get((pred, subj, None), None)
        if list == None: self._index[(pred, subj, None)]=[s]
        else: list.append(s)

        list = self._index.get((pred, subj, obj), None)
        if list == None: self._index[(pred, subj, obj)]=[s]
        else: list.append(s)

	if self._closureMode != "":
	    self.checkClosure(subj, pred, obj)

        return 1  # One statement has been added  @@ ignore closure extras from closure
		    # Obsolete this return value? @@@ 
    
    def removeStatement(self, s):
	"""Removes a statement The formula must be open.
	
	This implementation is alas slow, as removal of items from tha hash is slow.
	"""
        self.store.size = self.store.size-1
	if verbosity() > 97:  progress("removing %s" % (s))
	context, pred, subj, obj = s.quad
        self.statements.remove(s)
        self._index[(None, None, obj)].remove(s)
        self._index[(None, subj, None)].remove(s)
        self._index[(None, subj, obj)].remove(s)
        self._index[(pred, None, None)].remove(s)
        self._index[(pred, None, obj)].remove(s)
        self._index[(pred, subj, None)].remove(s)
        self._index[(pred, subj, obj)].remove(s)
	return
    
    def close(self):
        """No more to add. Please return interned value.
	NOTE You must now use the interned one, not the original!"""
        return self.store.endFormula(self)

    def reopen(self):
	"""Make a formula which was once closed oopen for input again.
	
	NOT Recommended.  Dangers: this formula will be, because of interning,
	the same objet as a formula used elsewhere which happens to have the same content.
	You mess with this one, you mess with that one.
	Much better to keep teh formula open until you don't needed it open any more.
	The trouble is, the parsers close it at the moment automatically. To be fixed."""
        return self.store.reopen(self)

    def setClosureMode(self, x):
	self._closureMode = x

    def checkClosure(self, subj, pred, obj):
	"""Check the closure of the formula given new contents
	
	The s p o flags cause llyn to follow those parts of the new statement.
	i asks it to follow owl:imports
	r ask it to follow doc:rules
	"""
	firstCall = (self._closureAgenda == [])
	if "s" in self._closureMode: self.checkClosureOfSymbol(subj)
	if "p" in self._closureMode: self.checkClosureOfSymbol(pred)
	if ("o" in self._closureMode or
	    "t" in self._closureMode and pred is self.store.type):
	    self.checkClosureOfSymbol(obj)
	if (("r" in self._closureMode and
	      pred is self.store.docRules) or
	    ("i" in self._closureMode and
	      pred is self.store.imports)) and subj in self._closureAlready:
	    self.checkClosureDocument(obj)
	if firstCall:
	    while self._closureAgenda != []:
		x = self._closureAgenda.pop()
		self._closureAlready.append(x)
		dereference(x, "m" + self._closureMode, self)
    
    def checkClosureOfSymbol(self, y):
	if not isinstance(y, Fragment): return
	return self.checkClosureDocument(y.resource)

    def checkClosureDocument(self, x):
	if x != None and x not in self._closureAlready and x not in self._closureAgenda:
	    self._closureAgenda.append(x)


    def n3String(self, flags=""):
        "Dump the formula to an absolute string in N3"
        buffer=StringIO.StringIO()
#      _outSink = ToRDF(buffer, _outURI, flags=flags)
        _outSink = notation3.ToN3(buffer.write,
                                      quiet=1, flags=flags)
        self.store.dumpNested(self, _outSink)
        return buffer.getvalue()   # Do we need to explicitly close it or will it be GCd?

    def debugString(self, already=[]):
	"""A simple dump of a formula in debug form.
	
	This formula is dumped, using ids for nested formula.
	Then, each nested formula mentioned is dumped."""
	str = `self`+" is {"
	for vv, ss in ((self.universals(), "@forAll"),(self.existentials(), "@forSome")):
	    if vv != []:
		str = str + " " + ss + " " + `vv[0]`
		for v in vv[1:]:
		    str = str + ", " + `v`
		str = str + "."
	todo = []
	for s in self.statements:
	    con, pred, subj, obj = s.quad
	    str = str + "\n%28s  %20s %20s ." % (`subj`, `pred`, `obj`)
	    for p in PRED, SUBJ, OBJ:
		if (isinstance(s[p], Formula)
		    and s[p] not in already and s[p] not in todo and s[p] is not self):
		    todo.append(s[p])
	str = str+ "}.\n"
	already = already + todo + [ self ]
	for f in todo:
	    str = str + "        " + f.debugString(already)
	return str

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

    def includes(f, g, _variables=[], smartIn=[], bindings=[]):
	"""Does this formula include the information in the other?
	
	smartIn gives a list of formulae for which builtin functions should operate
	   in the consideration of what "includes" means.
	bindings is for use within a query.
	"""
	return  f.store.testIncludes(f, g, _variables=_variables, smartIn=smartIn, bindings=bindings)


    def subFormulae(self, path = []):
        """Returns a sequence of the all the formulae nested within this one.
        
	slow...typically only used in pretty print functions.
        """

        if self.descendents != None:
            return self.descendents
        
#        progress("subcontext "+`con`+" path "+`len(path)`)
        set = [self]
        path2 = path + [ self ]     # Avoid loops
        for s in self.statements:
            for p in PRED, SUBJ, OBJ:
                if isinstance(s[p], Formula):
                    if s[p] not in path2:
                        set2 = s[p].subFormulae(path2)
                        for c in set2:
                            if c not in set: set.append(c)
        self.descendents = set
        return set

    def generated(self):
	"""Yes, any identifier you see for this is arbitrary."""
        return 1

    def asPair(self):
	"""Return an old representation. Obsolete"""
        return (FORMULA, self.uriref())

    def subjects(self, pred=None, obj=None):
        """Obsolete - use each(pred=..., obj=...)"""
	for s in self.statementsMatching(pred=pred, obj=obj)[:]:
	    yield s[SUBJ]

    def predicates(self, subj=None, obj=None):
        """Obsolete - use each(subj=..., obj=...)"""
	for s in self.statementsMatching(subj=subj, obj=obj)[:]:
	    yield s[PRED]

    def objects(self, pred=None, subj=None):
        """Obsolete - use each(subj=..., pred=...)"""
	for s in self.statementsMatching(pred=pred, subj=subj)[:]:
	    yield s[OBJ]

    def _checkList(self,  L):
        """Check whether this new list causes other things to become lists.
	
	Internal function."""
        if verbosity() > 80: progress("Checking new list ",`L`)
        rest = self.listValue(L)
        possibles = self.statementsMatching(pred=self.store.rest, obj=L)  # What has this as rest?
        for s in possibles:
            L2 = s[SUBJ]
            ff = self.statementsMatching(pred=self.store.first, subj=L2)
            if ff != []:
                first = ff[0][OBJ]
                if self.listValue(L2) == None:
                    self._listValue[L2] = rest.precededBy(first)
                    self._checkList(L2)
                return

###################################### Forumula
#
# A Formula is a set of triples.

class FormulaSimple(Formula):
    """A formula of a set of RDF statements, triples.
    
    (The triples are actually instances of StoredStatement.)
    Other systems such as jena and redland use the term "Model" for Formula.
    For rdflib, this is known as a TripleStore.
    Cwm and N3 extend RDF to allow a literal formula as an item in a triple.
    
    A formula is either open or closed.  Initially, it is open. In this
    state is may be modified - for example, triples may be added to it.
    When it is closed, note that a different interned version of itself
    may be returned. From then on it is a constant.
    
    Only closed formulae may be mentioned in statements in other formuale.
    
    There is a reopen() method but it is not recommended, and if desperate should
    only be used immediately after a close().
    
    This version is simplified by having no indexing at all.
    """
    def __init__(self, resource, fragid):
        Fragment.__init__(self, resource, fragid)
        self.descendents = None   # Placeholder for list of closure under subcontext
        self.cannonical = None # Set to self if this has been checked for duplicates
	self.collector = None # Object collecting evidence, if any 
	self._listValue = {}
	self.statements = []
	self._index[(None,None,None)] = self.statements
	self._closureMode = ""
	self._closureAlready = []

	
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

    def context(self):
	"""Return the context of the statement"""
	return self.quad[CONTEXT]
    
    def predicate(self):
	"""Return the predicate of the statement"""
	return self.quad[PRED]
    
    def subject(self):
	"""Return the subject of the statement"""
	return self.quad[SUBJ]
    
    def object(self):
	"""Return the object of the statement"""
	return self.quad[OBJ]

    def __len__(self):
	return 1

    def statements(self):
	return [self]


    def asFormula(self, why=None):
	"""The formula which contains only a statement like this.
	
	When we split the statement up, we lose information in any existentials which are
	shared with other statements. So we introduce a skolem constant to tie the
	statements together.  We don't have access to any enclosing formula 
	so we can't express its quantification.  This @@ not ideal.
	
	This extends the StoredStatement class with functionality we only need with "why" module."""
	
	store = self.quad[CONTEXT].store
	c, p, s, o = self.quad
	f = store.newFormula()   # @@@CAN WE DO THIS BY CLEVER SUBCLASSING? statement subclass of f?
	f.add(s, p, o, why=why)
	uu = store.occurringIn(f, c.universals())
	ee = store.occurringIn(f, c.existentials())
	bindings = []
	for v in uu:
	    x = f.newUniversal(v.uriref(), why=why)
	for v in ee:
	    x  = f.newExistential(v.uriref(), why=why)
	return f.close()  # probably slow - much slower than statement subclass of formula


###############################################################################################
#
#                       C W M - S P E C I A L   B U I L T - I N s
#
###########################################################################
    
# Equivalence relations

class BI_EqualTo(LightBuiltIn,Function, ReverseFunction):
    def eval(self,  subj, obj, queue, bindings, proof, query):
        return (subj is obj)   # Assumes interning

    def evalObj(self, subj, queue, bindings, proof, query):
        return subj

    def evalSubj(self, obj, queue, bindings, proof, query):
        return obj

class BI_notEqualTo(LightBuiltIn):
    def eval(self, subj, obj, queue, bindings, proof, query):
        return (subj is not obj)   # Assumes interning


# Functions 
    
class BI_uri(LightBuiltIn, Function, ReverseFunction):

#    def evaluateObject(self, subject):
#	return subject.uriref()
    def evalObj(self, subj, queue, bindings, proof, query):
	type, value = subj.asPair()
	if type == SYMBOL:     #    or type == ANONYMOUS: 
         # @@@@@@ Should not allow anonymous, but test/forgetDups.n3 uses it
	    return self.store.intern((LITERAL, value))

    def evaluateSubject(self, object):
	"""Return the object which has this string as its URI
	
        #@@hm... check string for URI syntax?
        # or at least for non-uri chars, such as space?
	Note that relative URIs can be OK as the whole process
	has a base, which may be irrelevant. Eg see roadmap-test in retest.sh
	"""
	store = self.store
	if ':' not in object:
	    progress("Warning: taking log:uri of non-abs: %s" % object)
        if type(object) is type(""):
	    return store.intern((SYMBOL, object))
        elif type(object) is type(u""):
	    uri = object.encode('utf-8') #@@ %xx-lify
	    return store.intern((SYMBOL, uri))


class BI_rawUri(BI_uri):
    """This is like  uri except that it allows you to get the internal
    identifiers for anonymous nodes and formuale etc."""
     
    def evalObj(self, subj, queue, bindings, proof, query):
	type, value = subj.asPair()
	return self.store.intern((LITERAL, value))


class BI_rawType(LightBuiltIn, Function):
    """
    The raw type is a type from the point of view of the langauge: is
    it a formula, list, and so on. Needed for test for formula in finding subformulae
    eg see test/includes/check.n3 
    """

    def evalObj(self, subj,  queue, bindings, proof, query):
	store = self.store
        if isinstance(subj, Literal): y = store.Literal
        elif isinstance(subj, Formula): y = store.Formula
        #@@elif context.listValue.get(subj, None): y = store.List
        else: y = store.Other  #  None?  store.Other?
        if verbosity() > 91:
            progress("%s  rawType %s." %(`subj`, y))
        return y
        

class BI_racine(LightBuiltIn, Function):    # The resource whose URI is the same up to the "#" 

    def evalObj(self, subj,  queue, bindings, proof, query):
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
    """Check that one formula does include the other.
    This limits the ability to bind a variable by searching inside another
    context. This is quite a limitation in some ways. @@ fix
    """
    def eval(self, subj, obj, queue, bindings, proof, query):
        store = subj.store
        if isinstance(subj, Formula) and isinstance(obj, Formula):
            return store.testIncludes(subj, obj, [], bindings=bindings) # No (relevant) variables
        return 0
            
    
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
    def eval(self, subj, obj, queue, bindings, proof, query):
        store = subj.store
        if isinstance(subj, Formula) and isinstance(obj, Formula):
            return not store.testIncludes(subj, obj, [], bindings=bindings) # No (relevant) variables
        return 0   # Can't say it *doesn't* include it if it ain't a formula

class BI_semantics(HeavyBuiltIn, Function):
    """ The semantics of a resource are its machine-readable meaning, as an
    N3 forumula.  The URI is used to find a represnetation of the resource in bits
    which is then parsed according to its content type."""
    def evalObj(self, subj, queue, bindings, proof, query):
        store = subj.store
        if isinstance(subj, Fragment): doc = subj.resource
        else: doc = subj
        F = store.any((store._experience, store.semantics, doc, None))
        if F != None:
            if verbosity() > 10: progress("Already read and parsed "+`doc`+" to "+ `F`)
            return F

        if verbosity() > 10: progress("Reading and parsing " + doc.uriref())
        inputURI = doc.uriref()
        F = self.store.load(inputURI)
        if verbosity()>10: progress("    semantics: %s" % (F))
	if diag.tracking:
	    proof.append(F.collector)
        return F
    
class BI_semanticsOrError(BI_semantics):
    """ Either get and parse to semantics or return an error message on any error """
    def evalObj(self, subj, queue, bindings, proof, query):
        import xml.sax._exceptions # hmm...
        store = subj.store
        x = store.any((store._experience, store.semanticsOrError, subj, None))
        if x != None:
            if verbosity() > 10: progress(`store._experience`+`store.semanticsOrError`+": Already found error for "+`subj`+" was: "+ `x`)
            return x
        try:
            return BI_semantics.evalObj(self, subj, queue, bindings, proof, query)
        except (IOError, SyntaxError, DocumentAccessError, xml.sax._exceptions.SAXParseException):
            message = sys.exc_info()[1].__str__()
            result = store.intern((LITERAL, message))
            if verbosity() > 0: progress(`store.semanticsOrError`+": Error trying to resolve <" + `subj` + ">: "+ message) 
            store.storeQuad((store._experience,
                             store.semanticsOrError,
                             subj,
                             result))
            return result
    

HTTP_Content_Type = 'content-type' #@@ belongs elsewhere?


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
    
class BI_content(HeavyBuiltIn, Function):
    def evalObj(self, subj, queue, bindings, proof, query):
        store = subj.store
        if isinstance(subj, Fragment): doc = subj.resource
        else: doc = subj
        C = store.any((store._experience, store.content, doc, None))
        if C != None:
            if verbosity() > 10: progress("already read " + `doc`)
            return C
        if verbosity() > 10: progress("Reading " + `doc`)
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


class BI_parsedAsN3(HeavyBuiltIn, Function):
    def evalObj(self, subj, queue, bindings, proof, query):
        store = subj.store
        if isinstance(subj, Literal):
            F = store.any((store._experience, store.parsedAsN3, subj, None))
            if F != None: return F
            if verbosity() > 10: progress("parsing " + subj.string[:30] + "...")
            inputURI = subj.asHashURI() # iffy/bogus... rather asDataURI? yes! but make more efficient
            p = notation3.SinkParser(store, inputURI)
            p.startDoc()
            p.feed(subj.string.encode('utf-8')) #@@ catch parse errors
            p.endDoc()
            del(p)
            F = store.intern((FORMULA, inputURI+ "#_formula"))
            return F.close()
    
class BI_conclusion(HeavyBuiltIn, Function):
    """ Deductive Closure

    Closure under Forward Inference, equivalent to cwm's --think function.
    """
    def evalObj(self, subj, queue, bindings, proof, query):
        store = subj.store
        if isinstance(subj, Formula):
            F = self.store.any((store._experience, store.cufi, subj, None))  # Cached value?
            if F != None: return F

            F = self.store.newInterned(FORMULA)
	    if diag.tracking:
		reason = BecauseMerge(F, subj)
		F.collector = reason
		proof.append(reason)
	    else: reason = None
            if verbosity() > 10: progress("Bultin: " + `subj`+ " log:conclusion " + `F`)
            self.store.copyFormula(subj, F, why=reason)
            self.store.think(F)
	    F = F.close()
            self.store.storeQuad((store._experience, store.cufi, subj, F),
		    why=BecauseOfExperience("conclusion"))  # Cache for later
            return F
    
class BI_conjunction(LightBuiltIn, Function):      # Light? well, I suppose so.
    """ The conjunction of a set of formulae is the set of statements which is
    just the union of the sets of statements
    modulo non-duplication of course"""
    def evalObj(self, subj, queue, bindings, proof, query):
	subj_py = self.store._toPython(subj, queue, query)
        if verbosity() > 50:
            progress("Conjunction input:"+`subj_py`)
            for x in subj_py:
                progress("    conjunction input formula %s has %i statements" % (x, x.size()))
#        F = conjunctionCache.get(subj_py, None)
#        if F != None: return F
        F = self.store.newInterned(FORMULA)
	if diag.tracking:
	    reason = BecauseMerge(F, subj_py)
	    F.collector = reason
	    proof.append(reason)
	else: reason = None
        for x in subj_py:
            if not isinstance(x, Formula): return None # Can't
            self.store.copyFormula(x, F, why=reason)
            if verbosity() > 74:
                progress("    Formula %s now has %i" % (x2s(F),len(F.statements)))
        return self.store.endFormula(F)

class BI_n3String(LightBuiltIn, Function):      # Light? well, I suppose so.
    """ The n3 string for a formula is what you get when you
    express it in the N3 language without using any URIs.
    Note that there is no guarantee that two implementations will
    generate the same thing, but whatever they generate should
    parse back using parsedAsN3 to exaclty the same original formula.
    If we *did* have a cannonical form it would be great for signature
    A cannonical form is possisble but not simple."""
    def evalObj(self, store, context, subj, queue, bindings, proof, query):
        if verbosity() > 50:
            progress("Generating N3 string for:"+`subj`)
        if isinstance(subj, Formula):
            return store.intern((LITERAL, subj.n3String()))

    
################################################################################################

class RDFStore(RDFSink) :
    """ Absorbs RDF stream and saves in triple store
    """

    def clear(self):
        "Remove all formulas from the store     @@@ DOESN'T ACTUALLY DO IT/BROKEN"
        self.resources = {}    # Hash table of URIs for interning things
#        self.formulae = []     # List of all formulae        
        self._experience = None   #  A formula of all the things program run knows from direct experience
        self._formulaeOfLength = {} # A dictionary of all the constant formuale in the store, lookup by length key.
        self.size = 0
        
    def __init__(self, genPrefix=None, metaURI=None, argv=None, crypto=0):
        RDFSink.__init__(self, genPrefix=genPrefix)
        self.clear()
        self.argv = argv     # List of command line arguments for N3 scripts

	run = uripath.join(uripath.base(), ".RUN/") + `time.time()`  # Reserrved URI @@

        if metaURI != None: meta = metaURI
	else: meta = run + "meta#formula"
	self.reset(meta)




        # Constants, as interned:
        
        self.forSome = self.internURI(forSomeSym)
	self.integer = self.internURI(INTEGER_DATATYPE)
	self.float  = self.internURI(FLOAT_DATATYPE)
        self.forAll  = self.internURI(forAllSym)
        self.implies = self.internURI(Logic_NS + "implies")
        self.means = self.internURI(Logic_NS + "means")
        self.asserts = self.internURI(Logic_NS + "asserts")
        
# Register Light Builtins:

        log = self.internURI(Logic_NS[:-1])   # The resource without the hash
        daml = self.internURI(DAML_NS[:-1])   # The resource without the hash

# Functions:        

        log.internFrag("racine", BI_racine)  # Strip fragment identifier from string

        self.rawType =  log.internFrag("rawType", BI_rawType) # syntactic type, oneOf:
        log.internFrag("rawUri", BI_rawUri)
        self.Literal =  log.internFrag("Literal", Fragment) # syntactic type possible value - a class
        self.List =     log.internFrag("List", Fragment) # syntactic type possible value - a class
        self.Formula =  log.internFrag("Formula", Fragment) # syntactic type possible value - a class
        self.Other =    log.internFrag("Other", Fragment) # syntactic type possible value - a class (Use?)

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

#        log.internFrag("resolvesTo", BI_semantics) # obsolete
        self.semantics = log.internFrag("semantics", BI_semantics)
        self.cufi = log.internFrag("conclusion", BI_conclusion)
        self.semanticsOrError = log.internFrag("semanticsOrError", BI_semanticsOrError)
        self.content = log.internFrag("content", BI_content)
        self.parsedAsN3 = log.internFrag("parsedAsN3",  BI_parsedAsN3)
        self.n3ExprFor = log.internFrag("n3ExprFor",  BI_parsedAsN3) ## Obsolete
        log.internFrag("n3String",  BI_n3String)

# Remote service flag in metadata:

	self.definitiveService = log.internFrag("definitiveService", Fragment)
	self.definitiveDocument = log.internFrag("definitiveDocument", Fragment)
	self.pointsAt = log.internFrag("pointsAt", Fragment)  # This was EricP's

# Constants:

        self.Truth = self.internURI(Logic_NS + "Truth")
        self.Falsehood = self.internURI(Logic_NS + "Falsehood")
        self.type = self.internURI(RDF_type_URI)
        self.Chaff = self.internURI(Logic_NS + "Chaff")
	self.docRules = self.internURI("http://www.w3.org/2000/10/swap/pim/doc#rules")
	self.imports = self.internURI("http://www.w3.org/2002/07/owl#imports")

# List stuff - beware of namespace changes! :-(

        self.first = self.intern(N3_first)
        self.rest = self.intern(N3_rest)
        self.nil = self.intern(N3_nil)
        self.nil._asList = EmptyList(self, None, None)
#        self.nil = EmptyList(self, None, None)
#        self.only = self.intern(N3_only)
        self.Empty = self.intern(N3_Empty)
        self.List = self.intern(N3_List)

        import cwm_string  # String builtins
        import cwm_os      # OS builtins
        import cwm_time    # time and date builtins
        import cwm_math    # Mathematics
        import cwm_times    # time and date builtins
        import cwm_maths   # Mathematics, perl/string style
        cwm_string.register(self)
        cwm_math.register(self)
        cwm_maths.register(self)
        cwm_os.register(self)
        cwm_time.register(self)
        cwm_times.register(self)
        if crypto:
	    import cwm_crypto  # Cryptography
	    cwm_crypto.register(self)  # would like to anyway to catch bug if used but not available

    def newLiteral(self, str, dt=None, lang=None):
	"Interned version: generat new literal object as stored in this store"
	uriref2 = LITERAL_URI_prefix + `dt` + " " + `lang` + " " + str # @@@ encoding at least hashes!!
	result = self.resources.get(uriref2, None)
	if result != None: return result
	result = Literal(self, str, dt, lang)
	self.resources[uriref2] = result
	return result
	
    def newFormula(self, uri=None):
	return self.intern(RDFSink.newFormula(self, uri))

    def newSymbol(self, uri):
	return self.intern(RDFSink.newSymbol(self, uri))

    def newBlankNode(self, context, uri=None, why=None):
	"""Create or reuse, in the default store, a new unnamed node within the given
	formula as context, and return it for future use"""
	return self.intern(RDFSink.newBlankNode(self, context, uri, why=why))
    
    def newExistential(self, context, uri=None, why=None):
	"""Create or reuse, in the default store, a new named variable
	existentially qualified within the given
	formula as context, and return it for future use"""
	return self.intern(RDFSink.newExistential(self, context, uri, why=why))
    
    def newUniversal(self, context, uri=None, why=None):
	"""Create or reuse, in the default store, a named variable
	universally qualified within the given
	formula as context, and return it for future use"""
	return self.intern(RDFSink.newUniversal(self, context, uri, why=why))



###################

    def reset(self, metaURI): # Set the metaURI
        self._experience = self.intern((FORMULA, metaURI + "_formula"))
	assert isinstance(self._experience, Formula)

    def load(store, uri=None, contentType=None, formulaURI=None, remember=1, why=None):
	"""Get and parse document.  Guesses format if necessary.

	uri:      if None, load from standard input.
	remember: if 1, store as metadata the relationship between this URI and this formula.
	
	Returns:  top-level formula of the parsed document.
	Raises:   IOError, SyntaxError, DocumentError
	
	This was and could be an independent function, as it is fairly independent
	of the store. However, it is natural to call it as a method on the store.
	And a proliferation of APIs confuses.
	"""
	try:
	    baseURI = uripath.base()
	    if contentType == None: contentType = ""
	    ct = contentType
	    if uri != None:
		addr = uripath.join(baseURI, uri) # Make abs from relative
		source = store.newSymbol(addr)
		if remember:
		    F = store._experience.the(source, store.semantics)
		    if F != None:
			if verbosity() > 40: progress("Using cached semantics for",addr)
			return F 
		    
		if verbosity() > 40: progress("Taking input from " + addr)
		netStream = urllib.urlopen(addr)
		if contentType == None: ct=netStream.headers.get(HTTP_Content_Type, None)
	    else:
		if verbosity() > 40: progress("Taking input from standard input")
		addr = uripath.join(baseURI, "STDIN") # Make abs from relative
		netStream = sys.stdin
    
	#    if verbosity() > 19: progress("HTTP Headers:" +`netStream.headers`)
	#    @@How to get at all headers??
	#    @@ Get sensible net errors and produce dignostics
    
	    guess = ct
	    buffer = netStream.read()
	    if verbosity() > 9: progress("Content-type: " + `ct` + " for "+addr)
	    if ct == None or (ct.find('xml') < 0 and ct.find('rdf') < 0) :   # Rats - nothing to go on
#		buffer = netStream.read(500)
#		netStream.close()
#		netStream = urllib.urlopen(addr)
                # can't be XML if it starts with these...
		if buffer[0:1] == "#" or buffer[0:7] == "@prefix":
		    guess = 'application/n3'
                elif buffer.find('xmlns="') >=0 or buffer.find('xmlns:') >=0:
		    guess = 'application/xml'
		if verbosity() > 29: progress("    guess " + guess)
	except (IOError, OSError):  
	    raise DocumentAccessError(addr, sys.exc_info() )
	    
	# Hmmm ... what about application/rdf; n3 or vice versa?
	if guess.find('xml') >= 0 or guess.find('rdf') >= 0:
	    if verbosity() > 49: progress("Parsing as RDF")
	    import sax2rdf, xml.sax._exceptions
	    p = sax2rdf.RDFXMLParser(store, addr)
#	    Fpair = p.loadStream(netStream)
	    p.feed(buffer)
	    Fpair = p.close()
	else:
	    if verbosity() > 49: progress("Parsing as N3")
	    p = notation3.SinkParser(store, addr, formulaURI=formulaURI, why=why)
	    p.startDoc()
	    p.feed(buffer)
	    Fpair = p.endDoc()
	F = store.intern(Fpair)
	F = F.close()
	if remember: store._experience.add(
		    store.intern((SYMBOL, addr)), store.semantics, F,
		    why=BecauseOfExperience("load document"))
	return F 
    



    def loadMany(self, uris):
	"""Get, parse and merge serveral documents, given a list of URIs. 
	
	Guesses format if necessary.
	Returns top-level formula which is the parse result.
	Raises IOError, SyntaxError
	"""
	assert type(uris) is type([])
	F = self.load(uris[0], remember=0)
	f = F.uriref()
	for u in uris[1:]:
	    F.reopen()
	    self.load(u, formulaURI=f, remember=0)
	return F

    def genId(self):
	"""Generate a new identifier
	
	This uses the inherited class, but also checks that we haven't for some pathalogical reason
	ended up generating the same one as for example in another run of the same system. 
	"""
	while 1:
	    uriRefString = RDFSink.genId(self)
            hash = string.rfind(uriRefString, "#")
            if hash < 0 :     # This is a resource with no fragment
		return uriRefString # ?!
	    resid = uriRefString[:hash]
	    r = self.resources.get(resid, None)
	    if r == None: return uriRefString
	    fragid = uriRefString[hash+1:]
	    f = r.fragments.get(fragid, None)
	    if f == None: return uriRefString
	    if verbosity() > 70:
		progress("llyn.genid Rejecting Id already used: "+uriRefString)
		
    def checkNewId(self, urirefString):
	"""Raise an exception if the id is not in fact new.
	
	This is useful because it is usfeul
	to generate IDs with useful diagnostic ways but this lays them
	open to possibly clashing in pathalogical cases."""
	hash = string.rfind(urirefString, "#")
	if hash < 0 :     # This is a resource with no fragment
	    result = self.resources.get(urirefString, None)
	    if result == None: return
	else:
	    r = self.resources.get(urirefString[:hash], None)
	    if r == None: return
            f = r.fragments.get(urirefString[hash+1:], None)
            if f == None: return
	raise RuntimeError("Ooops! Attempt to create new identifier hits on one already used: %s"%(urirefString))
	return


    def internURI(self, str, why=None):
        assert type(str) is type("") # caller %xx-ifies unicode
        return self.intern((SYMBOL,str), why=None)
    
    def intern(self, what, dt=None, lang=None, why=None, ):
        """find-or-create a Fragment or a Symbol or Literal as appropriate

        returns URISyntaxError if, for example, the URIref has
        two #'s.
        
        This is the way they are actually made.
        """

	if isinstance(what, Term): return what # Already interned.  @@Could mask bugs
	if type(what) is not types.TupleType:
#	    progress("llyn1450 @@@ interning ", `what`)
	    if isinstance(what, tuple(types.StringTypes)):
		return self.newLiteral(what, dt, lang)
	    progress("llyn1450 @@@ interning non-string", `what`)
	    if type(what) is types.IntType:
		return self.newLiteral(`what`, INTEGER_DATATYPE)
	    if type(what) is types.FloatType:
		return self.newLiteral(`what`, FLOAT_DATATYPE)
		
	    raise RuntimeError("Eh?  can't intern "+`what`)
        typ, urirefString = what

        if typ == LITERAL:
	    return self.newLiteral(urirefString, dt, lang)
        else:
	    assert isinstance(urirefString, tuple(types.StringTypes))
	    if isinstance(urirefString, types.UnicodeType):
		urirefString = notation3.hexify(urirefString.encode('utf-8'))
#            assert type(urirefString) is type("") # caller %xx-ifies unicode
            assert ':' in urirefString, "must be absolute: %s" % urirefString

            hash = string.rfind(urirefString, "#")
            if hash < 0 :     # This is a resource with no fragment
		assert typ == SYMBOL, "If URI <%s>has no hash, must be symbol" % urirefString
                result = self.resources.get(urirefString, None)
                if result != None: return result
                result = Symbol(urirefString, self)
                self.resources[urirefString] = result
            
            else :      # This has a fragment and a resource
                resid = urirefString[:hash]
                if string.find(resid, "#") >= 0:
                    raise URISyntaxError("Hash in document ID - can be from parsing XML as N3! -"+resid)
                r = self.internURI(resid)
                if typ == SYMBOL:
                    if urirefString == N3_nil[1]:  # Hack - easier if we have a different classs
                        result = r.internFrag(urirefString[hash+1:], FragmentNil)
                    else:
                        result = r.internFrag(urirefString[hash+1:], Fragment)
                elif typ == ANONYMOUS:
		    result = r.internFrag(urirefString[hash+1:], Anonymous)
                elif typ == FORMULA: result = r.internFrag(urirefString[hash+1:], Formula)
                else: raise RuntimeError, "did not expect other type:"+`typ`
        return result

     
    def internList(self, value):
        x = nil
        l = len(value)
        while l > 0:
            l = l - 1
            x = x.precededBy(value[l])
        return x

    def deleteFormula(self,F):
        if verbosity() > 30: progress("Deleting formula %s %ic" %
                                            ( `F`, len(F.statements)))
        for s in F.statements[:]:   # Take copy
            self.removeStatement(s)
#        self.formulae.remove(F)

    def endFormula(self, F):
        """If this formula already exists, return the master version.
        If not, record this one and return it.
        Call this when the formula is in its final form, with all its statements.
        Make sure no one else has a copy of the pointer to the smushed one.
        """
        if F.cannonical != None:
            if verbosity() > 70:
                progress("End formula -- @@ already cannonical:"+`F`)
            return F.cannonical
	collector = F.collector

        fl = F.statements
        l = len(fl), len(F.universals()), len(F.existentials())   # The number of statements
        possibles = self._formulaeOfLength.get(l, None)  # Formulae of same length

    
        if possibles == None:
            self._formulaeOfLength[l] = [F]
            if verbosity() > 70:
                progress("End formula - first of length", l, F)
            F.cannonical = F
            return F

        fl.sort(StoredStatement.compareSubjPredObj)
	fe = F.existentials()
	fe.sort(compareURI)
	fu = F.universals ()
	fu.sort(compareURI)

        for G in possibles:
            gl = G.statements
	    gkey = len(gl), len(G.universals()), len(G.existentials())
            if gkey != l: raise RuntimeError("@@Key of %s is %s instead of %s" %(G, `gkey`, `l`))

	    gl.sort(StoredStatement.compareSubjPredObj)
            for se, oe, in  ((fe, G.existentials()),
			     (fu, G.universals())):
		lse = len(se)
		loe = len(oe)
		if lse > loe: return 1
		if lse < loe: return -1
		oe.sort(compareURI)
		for i in range(lse):
		    if se[i] is not oe[i]:
			break # mismatch
		else:
		    continue # match
		break

            for i in range(l[0]):
                for p in PRED, SUBJ, OBJ:
                    if (fl[i][p] is not gl[i][p]
                        and (fl[i][p] is not F or gl[i][p] is not G)): # Allow self-reference @@
                        break # mismatch
                else: #match one statement
                    continue
                break
            else: #match
                if verbosity() > 20: progress(
		    "** End Formula: Smushed new formula %s giving old %s" % (F, G))
		del(F)  # Make sure it ain't used again
                return G
        possibles.append(F)
#        raise oops
        F.cannonical = F
        if verbosity() > 70:
            progress("End formula, a fresh one:"+`F`)
        return F

    def reopen(self, F):
        if F.cannonical == None:
            if verbosity() > 50:
                progress("reopen formula -- @@ already open: "+`F`)
            return F # was open
        if verbosity() > 70:
            progress("reopen formula:"+`F`)
	key = len(F.statements), len(F.universals()), len(F.existentials())  
        self._formulaeOfLength[key].remove(F)  # Formulae of same length
        F.cannonical = None
        return F


    def bind(self, prefix, uri):
	assert type(uri) is type("")
        if prefix != "":   #  Ignore binding to empty prefix
            return RDFSink.bind(self, prefix, uri) # Otherwise, do as usual.
    
    def makeStatement(self, tuple, why=None):
	"""Add a quad to the store, each part of the quad being in pair form."""
        q = ( self.intern(tuple[CONTEXT]),
              self.intern(tuple[PRED]),
              self.intern(tuple[SUBJ]),
              self.intern(tuple[OBJ]) )
        if q[PRED] is self.forSome and isinstance(q[OBJ], Formula):
            if verbosity() > 97:  progress("Makestatement suppressed")
            return  # This is implicit, and the same formula can be used un >1 place
        self.storeQuad(q, why)
                    
    def makeComment(self, str):
        pass        # Can't store comments


    def any(self, q):
        """Query the store for the first match.
	
	Quad contains one None as wildcard. Returns first value
        matching in that position.
	"""
        list = q[CONTEXT].statementsMatching(q[PRED], q[SUBJ], q[OBJ])
        if list == []: return None
        for p in ALL4:
            if q[p] == None:
                return list[0].quad[p]


    def storeQuad(self, q, why=None):
        """ intern quads, in that dupliates are eliminated.

	subject, predicate and object are terms - or atomic values to be interned.
        Builds the indexes and does stuff for lists.
	Deprocated: use Formula.add()         
        """
        
        context, pred, subj, obj = q
	assert isinstance(context, Formula), "Should be a Formula: "+`context`
	return context.add(subj=subj, pred=pred, obj=obj, why=why)
	

    def crawl(s):
	"Crawl the web to find the definitions of terms used"
	for p in PRED, SUBJ, OBJ:
	    if mask(p):
		if isinstance(p, Fragment):
		    p = p.resource

    def startDoc(self):
        pass

    def endDoc(self, rootFormulaPair):
	self.endFormula(self.intern(rootFormulaPair)) # notThis=1
        return
        #        F =self.intern(rootFormulaPair)
        #        return F.close()


    def listElements(store, x, statements):
	"""Find the elments of a list stored in DAML form in a given container.
    
	Returns None if there is no fully formed list there.
	The statements can statements in a formula, or a queue, or an array of quads
	etc"""
	ur = []
	tail = x
	while tail is not store.nil:
	    f, r = None, None
	    for s in statements:
		if s[SUBJ] is tail:
		    if s[PRED] is store.first:
			f = s[OBJ]
			if r != None: break
		    if s[PRED] is store.rest:
			r = s[OBJ]
			if f != None: break
	    else:
		return None  # Not a fully formed list
	    ur.append(f)
	    tail = r
	return ur
			    


##########################################################################
#
# Output methods:
#
    def selectDefaultPrefix(self, context):

        """ Symbol whose fragments have the most occurrences.
        we suppress the RDF namespace itself because the XML syntax has problems with it
        being default as it is used for attributes."""

        counts = {}   # Dictionary of how many times each
        closure = context.subFormulae()    # This context and all subFormulae
	counts[self.implies.resource] = 0
        for con in closure:
	    for x in con.existentials() + con.universals():
		_anon, _incoming = self._topology(x, con)
		if not _anon:
		    r = x.resource
		    total = counts.get(r, 0) + 1
		    counts[r] = total
		counts[self.forAll.resource] = counts[self.forAll.resource] + 1
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
            if verbosity() > 25: progress("    Count is %3i for %s" %(count, r.uriref()))
            if (r.uri != RDF_NS_URI[:-1]
                and count > 0
		and (count > best or
                     (count == best and mp.uriref() > r.uriref()))) :  # Must be repeatable for retests
                best = count
                mp = r

        if verbosity() > 20:
            progress("# Most popular Namespace in %s is %s with %i" % (`context`, `mp`, best))

        if mp is None: return counts
        self.defaultNamespace = mp.uriref()+"#"
        return counts

        


    def dumpPrefixes(self, sink, counts=None):
#        if self.defaultNamespace != None:
	if self.defaultNamespace != None:
	    sink.setDefaultNamespace(self.defaultNamespace)
        prefixes = self.namespaces.keys()   #  bind in same way as input did FYI
        prefixes.sort()
#	if counts:
#	    for pfx in prefixes:
#		uri = self.namespaces[pfx]
#		r = self.intern((SYMBOL, uri[:-1]))  # Remove trailing slash
#		n = counts.get(r, -1)
#		if verbosity()>20: progress("   Prefix %s has %i" % (pfx, n))
#		if n > 0:
#		    sink.bind(pfx, uri)	    
#	else:
	for pfx in prefixes:
	    uri = self.namespaces[pfx]
	    sink.bind(pfx, uri)

    def dumpChronological(self, context, sink):
	"Fast as possible. Only dumps data. No formulae or universals."
        sink.startDoc()
        self.dumpPrefixes(sink, None)
	self.dumpVariables(context, sink, sorting=0, dataOnly=1)
	uu = context.universals()
        for s in context.statements:
	    for p in SUBJ, PRED, OBJ:
		x = s[p]
		if isinstance(x, Formula) or x in uu:
		    break
	    else:
		self._outputStatement(sink, s.quad)
        sink.endDoc()

    def _outputStatement(self, sink, quad):
        sink.makeStatement(self.extern(quad))

    def extern(self, t):
        return(t[CONTEXT].asPair(),
                            t[PRED].asPair(),
                            t[SUBJ].asPair(),
                            t[OBJ].asPair(),
                            )

    def dumpVariables(self, context, sink, sorting=1, pretty=0, dataOnly=0):
	"""Dump the forAlls and the forSomes at the top of a formula"""
	if sorting:
	    uv = context.universals()[:]
	    uv.sort(compareURI)
	    ev = context.existentials()[:]
	    ev.sort(compareURI)
	else:
	    uv = context.universals()
	    ev = context.existentials()
	if not dataOnly:
	    for v in uv:
		self._outputStatement(sink, (context, self.forAll, context, v))
	for v in ev:
	    if pretty:
		_anon, _incoming = self._topology(v, context)
	    else:
		_anon = 0
	    if not _anon:
		self._outputStatement(sink, (context, self.forSome, context, v))

    def dumpBySubject(self, context, sink, sorting=1):
        """ Dump by order of subject except forSome's first for n3=a mode"""
        
        counts = self.selectDefaultPrefix(context)        
        sink.startDoc()
        self.dumpPrefixes(sink, counts)

	self.dumpVariables(context, sink, sorting)

        rs = self.resources.values()
        if sorting: rs.sort(compareURI)
        for r in rs :  # First the bare resource
            statements = context.statementsMatching(subj=r)
            if sorting: statements.sort(StoredStatement.comparePredObj)
            for s in statements :
#                if not(context is s.quad[SUBJ]and s.quad[PRED] is self.forSome):
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
# then prevents us from dumping the graph without new bnode ids is the presence of cycles.

# Formulae
#
# These are in some way like literal strings, in that they are defined completely
# by their contents. They are sets of statements. (To say a statement occurs
# twice has no meaning).  Can they be given an id? No, not directly. You can assert that any
# object is equivalent to (=) a given formula.
# If one could label it in one place then one would want to
# be able to label it in more than one.

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

        _asPred = len(context.each(pred=x))
        _elsewhere = 0
        _isExistential = x in context.existentials()
        _asObj = len(context.each(obj=x))
        _loop = context.any(subj=x, obj=x)  # does'nt count as incomming
        
        if isinstance(x, Literal):
            _anon = 0     #  Never anonymous, always just use the string
	elif isinstance(x, Formula):
	    _anon = 2	# always anonymous, represented as itself
	elif not x.generated():
	    _anon = 0	# Got a name, not anonymous
        elif context.listValue(x) != None:
            _anon = 2    # Always represent it just as itself
        else:
            contextClosure = context.subFormulae()[:]
            contextClosure.remove(context)
            for sc in contextClosure:
                if (sc.any(obj=x)
                    or sc.any(subj=x)
		    or sc.any(pred=x)):
                    _elsewhere = 1  # Occurs in a subformula - can't be anonymous!
                    break
            _anon = (_asObj < 2) and ( _asPred == 0) and (not _loop) and _isExistential and not _elsewhere

        if verbosity() > 98:
            progress( "Topology %s in %s is: anon=%i ob=%i, loop=%s pr=%i ex=%i elsewhere=%i"%(
            `x`, `context`, _anon, _asObj, _loop, _asPred,  _isExistential, _elsewhere))

        return ( _anon, _asObj+_asPred )  


    

    def _toPython(self, x, queue, query):
        """#  Convert a data item in query with no unbound variables into a python equivalent 
       Given the entries in a queue template, find the value of a list.
       @@ slow
       These methods are at the disposal of built-ins.
"""
        """ Returns an N3 list as a Python sequence"""
        if verbosity() > 85: progress("#### Converting to python "+ x2s(x))
        if isinstance(x, Literal):
	    if x.datatype == None: return x.string
	    if x.datatype is self.integer: return int(x.string)
	    if x.datatype is self.float: return float(x.string)
	    raise ValueError("Attempt to run built-in on unknown datatype %s of value %s." 
			    % (`x.datatype`, x.string))
	if x is self.nil: return []
#       if this is not in the queue, must be in the store 
#	What if it is defined partly in one and partly in the other - in both?  @@

#        lv = query.workingContext.listValue(x)
#	if lv != None:        # @@@@@@@  try it in each case :-(
#	    raise RuntimeError("@@@ Hmm. it is classes as a list" + `x`) # @@ could use that -- faster?
	elements = self.listElements(x, queue)
	if elements == None:
	    elements = self.listElements(x, query.workingContext)
	if elements != None:
	    list = []
	    for e in elements:
		list.append(self._toPython(e, queue, query))
	    return list

	
        return x    # If not a list, return unchanged

    def _fromPython(self, x, queue):
	"""Takem a python string, seq etc and represent as a llyn object"""
        if isinstance(x, tuple(types.StringTypes)):
            return self.intern((LITERAL, x))
        elif type(x) is types.IntType:
            return self.newLiteral(`x`, self.integer)
        elif type(x) is types.FloatType:
#	    s = `x`
#	    if s[-2:] == '.0': s=s[:-2]   # Tidy things which are ints back into floats
            return self.newLiteral(`x`, self.float)
        elif type(x) == type([]):
#	    progress("x is >>>%s<<<" % x)
	    raise RuntimeError("Internals generating lists not supported yet")
            g = self.nil
            y = x[:]
            y.reverse()
            for e in y:
                g1 = self.newBnode()
                queue.append(QueryItem((context, self.first, g1, self._fromPython(e, queue))))
                queue.append(QueryItem((context, self.rest, g1, g)))
                g = g1
            return g
        return x

    def dumpNested(self, context, sink):
        """ Iterates over all URIs ever seen looking for statements
        """
        counts = self.selectDefaultPrefix(context)        
        sink.startDoc()
        self.dumpPrefixes(sink, counts)
        self.dumpFormulaContents(context, sink, sorting=1)
        sink.endDoc()

    def dumpFormulaContents(self, context, sink, sorting):
        """ Iterates over statements in formula, bunching them up into a set
        for each subject.
        We dump "this" first before everything else
        """
        if sorting: context.statements.sort(StoredStatement.compareSubjPredObj)

	self.dumpVariables(context, sink, sorting, pretty=1)

	statements = context.statementsMatching(subj=context)  # context is subject
        if statements:
	    progress("@@ Statement with context as subj?!", statements,)
            self._dumpSubject(context, context, sink, sorting, statements)

        currentSubject = None
        statements = []
        for s in context.statements:
            con, pred, subj, obj =  s.quad
            if subj is con: continue # Done them above
            if currentSubject == None: currentSubject = subj
            if subj != currentSubject:
                self._dumpSubject(currentSubject, context, sink, sorting, statements)
                statements = []
                currentSubject = subj
            statements.append(s)
        if currentSubject != None:
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

	li = context.listValue(subj)
        if isinstance(subj, Formula) and subj is not context:
            sink.startBagSubject(subj.asPair())
            self.dumpFormulaContents(subj, sink, sorting)  # dump contents of anonymous bag
            sink.endBagSubject(subj.asPair())       # Subject is now set up
            # continue to do arcs
            
        elif _anon and (_incoming == 0 or 
	    (li != None and not isinstance(li, EmptyList) and subj.generated())):    # Will be root anonymous node - {} or [] or ()
		
            if subj is context:
                pass
            else:     #  Could have alternative syntax here

#                for s in statements:  # Find at least one we will print
#                    context, pre, sub, obj = s.quad
#                    if sub is obj: break  # Ok, we will do it
#                    _anon, _incoming = self._topology(obj, context)
#                    if not((pre is self.forSome) and sub is context and _anon):
#                        break # We will print it
#                else: return # Nothing to print - so avoid printing [].

                if sorting: statements.sort(StoredStatement.comparePredObj)    # Order only for output

                if li != None and not isinstance(li, EmptyList) and subj.generated():   # The subject is a list
                    for s in statements:
                        p = s.quad[PRED]
                        if p is not self.first and p is not self.rest:
			    if verbosity() > 90: progress("@ Is list, has values for", `p`)
                            break # Something to print (later)
                    else:
			if subj.generated(): return # Nothing.
                    sink.startAnonymousNode(subj.asPair(), li)
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
		    if verbosity() > 90: progress("%s Not list, has values for" % `subj`)
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
           or (isinstance(context.listValue(obj), EmptyList)) \
           or isinstance(obj, Literal):
            self._outputStatement(sink, triple) # Do 1-loops simply
            return

        _anon, _incoming = self._topology(obj, context)
        _se = isinstance(obj, Formula) and obj is not context
        li = 0
#        if ((pre is self.forSome) and sub is context and _anon):
#            return # implicit forSome
        if (context.listValue(obj) != None) and obj is not self.nil and obj.generated():
	    for s in context.statementsMatching(subj=obj):
		p = s.quad[PRED]
		if p is not self.first and p is not self.rest:
		    if verbosity() > 90: progress("@ Is list, has values for", `p`)
		    break # Can't print as object, just print it elsewhere.
	    else:
		    li = 1

        if _anon and (_incoming == 1 or li or _se):  # Embedded anonymous node in N3

            _isSubject = context.any(pred=obj) # Has any properties in this context? 
	    # was: _isSubject = len(context.each(pred=obj)_index.get((obj, None, None), []))
	    # Has properties in this context?
	    #@@@@@ comments don't match code
            
            if _isSubject > 0 or not _se :   #   Do [ ] if nothing else as placeholder.

                sink.startAnonymous(self.extern(triple), li)
                if not li or not isinstance(context.listValue(obj), EmptyList):   # nil gets no contents
                    if li:
                        if verbosity()>90:
                            progress("List found as object of dumpStatement " + x2s(obj))
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
	

##################################  Manipulation methods:
#
#  Note when we move things, then the store may shrink as they may
# move on top of existing entries and we don't allow duplicates.
#
#   @@@@ Should automatically here rewrite any variable name clashes
#  for variable names which occur in the other but not as the saem sort of variable
# Must be done by caller.

    def copyFormulaRecursive(self, old, new, bindings, why=None):
        total = 0
	for v in old.universals():
	    new.declareUniversal(_lookup(bindings, v))
	for v in old.existentials():
	    new.declareExistential(_lookup(bindings, v))
	bindings2 = bindings + [(old, new)]
        for s in old.statements[:] :   # Copy list!
	    self.storeQuad((new,
                         _lookupRecursive(bindings2, s[PRED], why=why),
                         _lookupRecursive(bindings2, s[SUBJ], why=why),
                         _lookupRecursive(bindings2, s[OBJ],  why=why))
			 , why)
        return total
                
    def copyFormula(self, old, new, why=None):
	bindings = [ (old, new) ]
	for v in old.universals():
	    new.declareUniversal(_lookup(bindings, v))
	for v in old.existentials():
	    new.declareExistential(_lookup(bindings, v))
        for s in old.statements[:] :   # Copy list!
            q = s.quad
            for p in CONTEXT, PRED, SUBJ, OBJ:
                x = q[p]
                if x is old:
                    q = q[:p] + (new,) + q[p+1:]
            self.storeQuad(q, why)
                

    def purge(self, context, boringClass=None):
        """Clean up intermediate results

    Statements in the given context that a term is a Chaff cause
    any mentions of that term to be removed from the context.
    """
        if boringClass == None:
            boringClass = self.Chaff
        for subj in context.subjects(pred=self.type, obj=boringClass):
	    self.purgeSymbol(context, subj)

    def purgeSymbol(self, context, subj):
	"""Purge all triples in which a symbol occurs.
	"""
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
	if verbosity() > 30:
	    progress("Purged %i statements with %s" % (total,`subj`))
	return total


    def removeStatement(self, s):
        "Remove statement from store"
 	return s[CONTEXT].removeStatement(s)

    def purgeExceptData(self, context):
	"""Remove anything which can't be expressed in plain RDF"""
	uu = context.universals()
	for s in context.statements[:]:
	    for p in PRED, SUBJ, OBJ:
		x = s[p]
		if x in uu or isinstance(x, Formula):
		    context.removeStatement(s)
		    break
	context._universalVariables =[]  # Cheat! @ use API
		    
#   Iteratively apply rules to a formula

    def think(self, F, G=None, mode=""):
        grandtotal = 0
        iterations = 0
        if G == None: G = F
        self.reopen(F)
        bindingsFound = {}  # rule: list bindings already found
        while 1:
            iterations = iterations + 1
            step = self.applyRules(F, G, alreadyDictionary=bindingsFound, mode=mode)
            if step == 0: break
            grandtotal= grandtotal + step
        if verbosity() > 5: progress("Grand total of %i new statements in %i iterations." %
                 (grandtotal, iterations))
        return grandtotal


    def applyRules(self, workingContext,    # Data we assume 
                   filterContext = None,    # Where to find the rules
                   targetContext = None,    # Where to put the conclusions
                   universals = [],             # Inherited from higher contexts
                   alreadyDictionary = None,  # rule: list of bindings already found
		   mode="",			# modus operandi
		   why=None):			# Trace reason for all this
        """ Apply rules in one context to the same or another

	A rule here is defined by log:implies, which associates the template (premise, precondidtion,
	antecedent) to the conclusion (postcondition).
    
	    This is just a database search, very SQL-like.
    
	To verify that for all x, f(s) one can either find that asserted explicitly,
	or find an example for some specific value of x.  Here, we deliberately
	chose only to do the first.
        """
        
        if targetContext is None: targetContext = workingContext # return new data to store
        if filterContext is None: filterContext = workingContext # apply own rules

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
                                     already=already, mode=mode)
                if (verbosity() >40):
                    progress( "Found %i new stmts on for rule %s" % (found, s))
                _total = _total+found
            else:
                c = None
#                if pred is self.asserts and subj is filterContext: c=obj
                if pred is self.type and obj is self.Truth: c=subj
                if c != None:
                    _total = _total + self.applyRules(workingContext,
                                                      c, targetContext,
                                                      universals=universals
                                                      + filterContext.universals(),
						      mode=mode)


        if verbosity() > 4:
                progress("Total %i new statements from rules in %s"
                         % ( _total, filterContext))
        return _total


    def tryRule(self, rule, workingContext, targetContext, _variables, already=None, mode=""):
	"""Try a rule
	
	Beware lists are corrupted. Already list is updated if present.
	"""
        template = rule[SUBJ]
        conclusion = rule[OBJ]

        # When the template refers to itself, the thing we are
        # are looking for will refer to the context we are searching
        # Similarly, refernces to the working context have to be moved into the
        # target context when the conclusion is drawn.


	x = self.occurringIn(template, template.universals()[:])
	if template.universals() != []:
	    raise RuntimeError("""Cannot query for universally quantified things.
	    As of 2003/07/28 forAll x ...x cannot be on left hand side of rule.
	    This/these were: %s\n""" % x)

        unmatched = template.statements[:]
	templateExistentials = template.existentials()[:]
        _substitute([( template, workingContext)], unmatched)

        variablesMentioned = self.occurringIn(template, _variables)
        variablesUsed = self.occurringIn(conclusion, variablesMentioned)
        for x in variablesMentioned:
            if x not in variablesUsed:
                templateExistentials.append(x)
        if verbosity() >20:
            progress("\n=================== tryRule ============ (mode=%s) looking for:" %mode)
            progress( setToString(unmatched))
            progress("Universals declared in outer " + seqToString(_variables))
            progress(" mentioned in template       " + seqToString(variablesMentioned))
            progress(" also used in conclusion     " + seqToString(variablesUsed))
            progress("Existentials in template     " + seqToString(templateExistentials))

    # The smartIn context was the template context but it has been mapped to the workingContext.
        query = Query(self, unmatched=unmatched,
			template = template,
			variables=variablesUsed,
			existentials=templateExistentials,
			workingContext = workingContext,
			conclusion = conclusion,
			targetContext = targetContext,
			already = already,
			rule = rule,
			smartIn = [workingContext],    # (...)
			meta=workingContext,
			mode=mode)

	total = query.resolve()
	if verbosity() > 20:
	    progress("tryRule generated %i new statements" % total)
	return total



    def testIncludes(self, f, g, _variables=[], smartIn=[], bindings=[]):
	"""Return whether or nor f contains a top-level formula equvalent to g.
	Just a test: no bindings returned."""
        if verbosity() >30: progress("\n\n=================== testIncludes ============")

        # When the template refers to itself, the thing we are
        # are looking for will refer to the context we are searching

        if not(isinstance(f, Formula) and isinstance(g, Formula)): return 0

	assert f.cannonical is f
	assert g.cannonical is g

        unmatched = g.statements[:]
	templateExistentials = g.existentials()
        _substitute([( g, f)], unmatched)
        
	if g.universals() != []:
	    raise RuntimeError("""Cannot query for universally quantified things.
	    As of 2003/07/28 forAll x ...x cannot be on left hand side of rule.
	    This/these were: %s\n""" % x)

        if bindings != []: _substitute(bindings, unmatched)

        if verbosity() > 20:
            progress( "# testIncludes BUILTIN, %i terms in template %s, %i unmatched, %i template variables" % (
                len(g.statements),
                `g`[-8:], len(unmatched), len(templateExistentials)))
        if verbosity() > 80:
            for v in _variables:
                progress( "    Variable: " + `v`[-8:])

        result = Query(self, unmatched=unmatched,
		    template = g,
		    variables=[],
		    existentials=_variables + templateExistentials,
		    smartIn=smartIn, justOne=1, mode="").resolve()

        if verbosity() >30: progress("=================== end testIncludes =" + `result`)
#        verbosity() = verbosity()-100
        return result
 
    def newInterned(self, type):        
        return self.intern((type, self.genId()))

 
    def occurringIn(self, x, vars, level=0, context=None):
        """ Figure out, given a set of variables which if any occur in a formula, list, etc
         The result is returned as an ordered set so that merges can be done faster.
        """
#	progress("  "*level+"@@@@ occurringIn x=%s, vars=%s:"%(x, vars))
        if isinstance(x, Formula):
            set = []
            if verbosity() > 98: progress("  "*level+"----occuringIn: "+"  "*level+`x`)
            for s in x.statements:
#                if s[PRED] is not self.forSome:
                    for p in PRED, SUBJ, OBJ:
                        y = s[p]
                        if y is x:
                            pass
                        else:
                            set = merge(set, self.occurringIn(y, vars, level+1, context=x))
            return set

	assert context != None, "needs context param for this"
        if context.listValue(x) != None and x.generated():
            set = []
            for y in context.listValue(x).value():
                set = merge(set, self.occurringIn(y, vars, level+1, context=context))
            return set
        else:
            if x in vars:
                return [x]
            return []


        


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





class Query:
    """A query holds a hypothesis/antecedent/template which is being matched aginst (unified with)
    the knowledge base."""
    def __init__(self,
	       store,		    # Neded for getting interned constants etc etc
               unmatched=[],           # Tuple of interned quads we are trying to match CORRUPTED
	       template = None,		# Actually, must have one
               variables=[],           # List of variables to match and return CORRUPTED
               existentials=[],        # List of variables to match to anything
                                    # Existentials or any kind of variable in subexpression
	       workingContext = None,
	       conclusion = None,
	       targetContext = None,
	       already = None,	    # Dictionary of matches already found
	       rule = None,		    # The rule statement
               smartIn = [],        # List of contexts in which to use builtins - typically the top onebb
               justOne = 0,         # Flag: Stop when you find the first one
	       mode = "rs",	    # Character flags modifying modus operandi
	    meta = None):	    # Context to check for useful info eg remote stuff

        
        if verbosity() > 50:
            progress( "Query: created with %i terms. (justone=%i)" % (len(unmatched), justOne))
            if verbosity() > 80: progress( setToString(unmatched))
	    if verbosity > 90: progress(
		"    Smart in: ", smartIn)

#        if not hypothetical:
#            for x in existentials[:]:   # Existentials don't count when they are just formula names
#                                        # Also, we don't want a partial match. 
#                if isinstance(x,Formula):
#                    existentials.remove(x)

        self.queue = []   #  Unmatched with more info
	self.store = store
	self.variables = variables
	self.existentials = existentials
	self.workingContext = workingContext
	self.conclusion = conclusion
	self.targetContext = targetContext
	self.smartIn = smartIn
	self.justOne = justOne
	self.already = already
	self.rule = rule
	self.template = template  # For looking for lists
	self.meta = meta
	self.mode = mode
        for quad in unmatched:
            item = QueryItem(self, quad)
            if item.setup(allvars=variables+existentials, unmatched=unmatched, smartIn=smartIn, mode=mode) == 0:
                if verbosity() > 80: progress("match: abandoned, no way for "+`item`)
                self.noWay = 1
		return  # save time
            self.queue.append(item)
	return
	
    def resolve(self):
	if hasattr(self, "noWay"): return 0
        return self.unify(self.queue, self.variables, self.existentials)



    def conclude(self, bindings, level=0, evidence = []):
	"""When a match found in a query, add conclusions to target formula.

	Returns the number of statements added."""
	if self.justOne: return 1   # If only a test needed

#        store, workingContext, conclusion, targetContext,  already, rule = param
	if verbosity > 0: indent = " "*level
        if verbosity() >60: progress( indent, "\nConcluding tentatively..." + bindingsToString(bindings))

        if self.already != None:
            if bindings in self.already:
                if verbosity() > 30: progress(indent, "@@Duplicate result: ", bindingsToString(bindings))
                # raise foo
                return 0
            if verbosity() > 30: progress(indent, "Not duplicate: ", bindingsToString(bindings))
            self.already.append(bindings)   # A list of lists

	if diag.tracking:
	    reason = BecauseOfRule(self.rule, bindings=bindings, evidence=evidence)
	else:
	    reason = None

	es, exout = self.workingContext.existentials(), []
	for var, val in bindings:
	    if val in es:
		exout.append(val)
		if verbosity() > 25:
		    progress(indent, "Matches we found which is just existential: %s -> %s" % (var, val))
		self.targetContext.add(subj=self.targetContext, pred=self.store.forSome, obj=val, why=reason)

        b2 = bindings + [(self.conclusion, self.targetContext)]
        ok = self.targetContext.universals()  # It is actually ok to share universal variables with other stuff
        poss = self.conclusion.universals()[:]
        for x in poss[:]:
            if x in ok: poss.remove(x)
        vars = self.conclusion.existentials() + poss  # Terms with arbitrary identifiers
#        clashes = self.occurringIn(targetContext, vars)    Too slow to do every time; play safe
	if verbosity() > 25:
	    s = indent +"Universals in conclusion but not in target regenerated:" + `vars`
        for v in vars:
	    if v not in exout:
		v2 = self.store.newInterned(ANONYMOUS)
		b2.append((v, v2)) # Regenerate names to avoid clash
		if verbosity() > 25: s = s + ", %s -> %s" %(v, v2)
	    else:
		if verbosity() > 25: s = s + (", (%s is existential in kb)"%v)
	if len(vars) >0 and verbosity() > 25:
	    progress(s)
	

        if verbosity()>10:
            progress( indent, "Concluding definitively" + bindingsToString(b2) )
        before = self.store.size
        self.store.copyFormulaRecursive(
		    self.conclusion, self.targetContext, b2, why=reason)
        if verbosity()>30:
            progress( indent, "   size of store changed from %i to %i."%(before, self.store.size))
        return self.store.size - before


##################################################################################


    def unify(query,
               queue,               # Set of items we are trying to match CORRUPTED
               variables,           # List of variables to match and return CORRUPTED
               existentials,        # List of variables to match to anything
                                    # Existentials or any kind of variable in subexpression
               bindings = [],       # Bindings discovered so far
               newBindings = [],    # New bindings not yet incorporated
               level = 0,           # Nesting level for diagnostic indentation only
	       evidence = []):	    # List of statements supporting the bindings so far
        """ Iterate on the remaining query items
    bindings      collected matches already found
    newBindings  matches found and not yet applied - used in recursion
    
    You probably really need the state diagram to understand this
    http://www.w3.org/2000/10/swap/doc/states.svg
    even if it is a bit out of date.
        """
        total = 0
	
        if verbosity() > 59:
            progress( " "*level+"QUERY2: called %i terms, %i bindings %s, (new: %s)" %
                      (len(queue),len(bindings),bindingsToString(bindings),
                       bindingsToString(newBindings)))
            if verbosity() > 90: progress( queueToString(queue, level))

        for pair in newBindings:   # Take care of business left over from recursive call
            if verbosity()>95: progress(" "*level+"    new binding:  %s -> %s" % (x2s(pair[0]), x2s(pair[1])))
            if pair[0] in variables:
                variables.remove(pair[0])
                bindings.append(pair)  # Record for posterity
            else:      # Formulae aren't needed as existentials, unlike lists. hmm.
		if diag.tracking: bindings.append(pair)  # Record for proof only
                if not isinstance(pair[0], Formula): # Hack - else rules13.n3 fails @@
                    existentials.remove(pair[0]) # Can't match anything anymore, need exact match

        # Perform the substitution, noting where lists become boundLists.
        # We do this carefully, messing up the order only of things we have already processed.
        if newBindings != []:
            for item in queue:
                if item.bindNew(newBindings) == 0: return 0


        while len(queue) > 0:

            if (verbosity() > 90):
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
            if verbosity()>49:
                progress( " "*level+"Looking at " + `item`
                         + "\nwith vars("+seqToString(variables)+")"
                         + " ExQuVars:("+seqToString(existentials)+")")
            con, pred, subj, obj = item.quad
            state = item.state
            if state == S_FAIL:
                return total # Forget it -- must be impossible
            if state == S_LIGHT_UNS_GO or state == S_LIGHT_GO:
		item.state = S_LIGHT_EARLY   # Assume can't run
                nbs = item.tryBuiltin(queue, bindings, heavy=0, evidence=evidence)
		# progress("llyn.py 2706:   nbs = %s" % nbs)
            elif state == S_LIGHT_EARLY or state == S_NOT_LIGHT: #  Not searched yet
                nbs = item.trySearch()
            elif state == S_HEAVY_READY:  # not light, may be heavy; or heavy ready to run
                if pred is query.store.includes: # and not diag.tracking:  # don't optimize when tracking?
                    if (isinstance(subj, Formula)
                        and isinstance(obj, Formula)):

                        more_unmatched = obj.statements[:]
			more_variables = obj.variables()[:]

			if obj.universals() != []:
			    raise RuntimeError("""Cannot query for universally quantified things.
	    As of 2003/07/28 forAll x ...x cannot be on object of log:includes.
	    This/these were: %s\n""" % obj.universals())


                        _substitute([( obj, subj)], more_unmatched)
                        _substitute(bindings, more_unmatched)
                        existentials = existentials + more_variables
                        allvars = variables + existentials
                        for quad in more_unmatched:
                            newItem = QueryItem(query, quad)
                            queue.append(newItem)
                            newItem.setup(allvars, smartIn = query.smartIn + [subj],
				    unmatched=more_unmatched, mode=query.mode)
                        if verbosity() > 40:
                                progress( " "*level+
                                          "**** Includes: Adding %i new terms and %s as new existentials."%
                                          (len(more_unmatched),
                                           seqToString(more_variables)))
                        item.state = S_DONE
                    else:
                        progress("Include can only work on formulae "+`item`) #@@ was RuntimeError exception
                        item.state = S_FAIL
                    nbs = []
                else:
		    item.state = S_HEAVY_WAIT  # Assume can't resolve
                    nbs = item.tryBuiltin(queue, bindings, heavy=1, evidence=evidence)
            elif state == S_REMOTE: # Remote query -- need to find all of them for the same service
		items = [item]
		for i in queue[:]:
		    if i.state == S_REMOTE and i.service is item.service: #@@ optimize which group is done first!
			items.append(i)
			queue.remove(i)
		nbs = query.remoteQuery(items)
		item.state = S_DONE  # do not put back on list
            elif state == S_LIST_UNBOUND: # Lists with unbound vars
                if verbosity()>70:
                        progress( " "*level+ "List left unbound, returing")
                return total   # forget it  (this right?!@@)
            elif state == S_LIST_BOUND: # bound list
                if verbosity()>60: progress(
		    " "*level+ "QUERY FOUND MATCH (dropping lists) with bindings: "
		    + bindingsToString(bindings))
                return total + query.conclude(bindings, level, evidence=evidence)  # No non-list terms left .. success!
            elif state ==S_HEAVY_WAIT or state == S_LIGHT_WAIT: # Can't
                if verbosity() > 49 :
                    progress("@@@@ Warning: query can't find term which will work.")
                    progress( "   state is %s, queue length %i" % (state, len(queue)+1))
                    progress("@@ Current item: %s" % `item`)
                    progress(queueToString(queue))
#                    raise RuntimeError, "Insufficient clues"
                return 0  # Forget it
            else:
                raise RuntimeError, "Unknown state " + `state`
            if verbosity() > 90: progress(" "*level +"nbs=" + `nbs`)
            if nbs == 0: return total
            elif nbs != []:
                total = 0
#		if nbs != 0 and nbs != []: pass
		# progress("llyn.py 2738:   nbs = %s" % nbs)
                for nb, reason in nbs:
                    q2 = []
                    for i in queue:
                        newItem = i.clone()
                        q2.append(newItem)  #@@@@@@@@@@  If exactly 1 binding, loop (tail recurse)
		    
                    total = total + query.unify(q2, variables[:], existentials[:],
                                          bindings[:], nb, level=level+2, evidence = evidence + [reason])
                    if query.justOne and total:
                        return total
		return total # The called recursive calls above will have generated the output
            if item.state == S_FAIL: return total
            if item.state != S_DONE:   # state 0 means leave me off the list
                queue.append(item)
            # And loop back to take the next item

        if verbosity()>50: progress( " "*level+"QUERY MATCH COMPLETE with bindings: " + bindingsToString(bindings))
        return query.conclude(bindings, level, evidence)  # No terms left .. success!



    def remoteQuery(query, items):
	"""Perform remote query as client on remote store
	Currently  this only goes to an SQL store, but should later use RDFQL/DAMLQL etc
	in remote HTTP/SOAP call."""
	
        import dbork.SqlDB
        from dbork.SqlDB import ResultSet, SqlDBAlgae, ShowStatement

        # SqlDB stores results in a ResultSet.
        rs = ResultSet()
        # QueryPiece qp stores query tree.
        qp = rs.buildQuerySetsFromCwm(items, query.variables, query.existentials)
        # Extract access info from the first item.
	if verbosity() > 90:
	    progress("    Remote service %s" %items[0].service.uri)
        (user, password, host, database) = re.match("^mysql://(?:([^@:]+)(?::([^@]+))?)@?([^/]+)/([^/]+)/$",
                                                    items[0].service.uri).groups()
        # Look for one of a set of pre-compiled rdb schemas.
        HostDB2SchemeMapping = { "mysql://root@localhost/w3c" : "AclSqlObjects" }
        if (HostDB2SchemeMapping.has_key(items[0].service.uri)):
            cachedSchema = HostDB2SchemeMapping.get(items[0].service.uri)
        else:
            cachedSchema = None
        # The SqlDBAlgae object knows how to compile SQL query from query tree qp.
        a = SqlDBAlgae(query.store.internURI(items[0].service.uri), cachedSchema, user, password, host, database, query.meta, query.store.pointsAt, query.store)
        # Execute the query.
        messages = []
        nextResults, nextStatements = a._processRow([], [], qp, rs, messages, {})
        # rs.results = nextResults # Store results as initial state for next use of rs.
        if verbosity() > 90: progress(string.join(messages, "\n"))
        if verbosity() > 90: progress("query matrix \"\"\""+rs.toString({'dataFilter' : None})+"\"\"\" .\n")

	bindings = []
	reason = Because("Remote query") # could be messages[0] which is the query
        # Transform nextResults to format cwm expects.
        for resultsRow in nextResults:
            boundRow = []
            for i in range(len(query.variables)):
                v = query.variables[i]
                index = rs.getVarIndex(v)
                interned = resultsRow[index]
                boundRow = boundRow + [(v, interned)]
            bindings.append((boundRow, reason))

        if verbosity() > 10: progress("====> bindings from remote query:"+`bindings`)
	return bindings   # No bindings for testing



class QueryItem(StoredStatement):  # Why inherit? Could be useful, and is logical...
    """One line in a query being resolved.
    
    To a large extent, each line can keep track of its own state.
    When a remote query is done, query lines to the same server have to be coordinated again.
    """
    def __init__(self, query, quad):
        self.quad = quad
	self.query = query
        self.searchPattern = None # Will be list of variables
        self.store = query.store
        self.state = S_UNKNOWN  # Invalid
        self.short = INFINITY
        self.neededToRun = None   # see setup()
        self.myIndex = None     # will be list of satistfying statements
	self.service = None   # Remote database server for this predicate?
        return

    def clone(self):
        """Take a copy when for iterating on a query"""
        x = QueryItem(self.query, self.quad)
        x.state = self.state
        x.short = self.short
        x.neededToRun = []
        x.searchPattern = self.searchPattern[:]
        for p in ALL4:   # Deep copy!  Prevent crosstalk
            x.neededToRun.append(self.neededToRun[p][:])
        x.myIndex = self.myIndex
        return x



    def setup(self, allvars, unmatched, smartIn=[], mode=""):        
        """Check how many variables in this term,
        and how long it would take to search

        Returns, [] normally or 0 if there is no way this query will work.
        Only called on virgin query item.
	The mode is a set of character flags about how we think."""
        con, pred, subj, obj = self.quad
	self.service = None

	if "r" in mode:
	    schema = None
	    if "s" in mode:
		schema = dereference(pred, mode, self.query.workingContext)
		if schema != None:
		    if "a" in mode:
			if verbosity() > 95:
			    progress("Axiom processing for %s" % (pred))
			ns = pred.resource
			rules = schema.any(subj=ns, pred=self.store.docRules)
			rulefile = dereference(rulefile, "m", self.query.workingContext)
		    self.service = schema.any(pred=self.store.definitiveService, subj=pred)
	    if self.service == None and self.query.meta != None:
		self.service = self.query.meta.any(pred=self.store.definitiveService, subj=pred)
		if self.service == None:
		    uri = pred.uriref()
		    if uri[:4] == "mysql:":
			j = uri.rfind("/")
			if j>0: self.service = meta.newSymbol(uri[:j])
	    if verbosity() > 90 and self.service:
		progress("We have a Remote service %s for %s." %(self.service, pred))
	    if not self.service:
		authDoc = None
		if schema != None:
		    authDoc = schema.any(pred=self.store.definitiveDocument, subj=pred)
		if authDoc == None and self.query.meta != None:
		    authDoc = self.query.meta.any(pred=self.store.definitiveDocument, subj=pred)
		if authDoc != None:
		    if verbosity() > 90:
			progress("We have a definitive document %s for %s." %(authDoc, pred))
		    authFormula = dereference(authDoc, mode, self.query.workingContext)
		    if authFormula != None:
			self.quad = (authFormula, pred, subj, obj)
			con = authFormula

        self.neededToRun = [ [], [], [], [] ]  # for each part of speech
        self.searchPattern = [con, pred, subj, obj]  # What do we search for?
        hasUnboundFormula = 0
        for p in PRED, SUBJ, OBJ :
            x = self.quad[p]
	    if x is con:  # "this" is special case.
		self.neededToRun[p] = []
		continue
            if x in allvars:   # Variable
                self.neededToRun[p] = [x]
                self.searchPattern[p] = None   # can bind this
            if self.query.template.listValue(x) != None and x is not self.store.nil:
                self.searchPattern[p] = None   # can bind this
#                ur = self.store.occurringIn(x, allvars)
		ur = []
		ee = self.store.listElements(x, unmatched)
		for e in ee: 
		    if e in allvars and e not in ur: ur.append(e)
                self.neededToRun[p] = ur
            elif isinstance(x, Formula): # expr
                ur = self.store.occurringIn(x, allvars)
                self.neededToRun[p] = ur
                if ur != []:
                    hasUnboundFormula = 1     # Can't search
	    if verbosity() > 98: progress("        %s needs to run: %s"%(`x`, `self.neededToRun[p]`))
                
        if hasUnboundFormula:
            self.short = INFINITY   # can't search
        else:
            self.short, self.myIndex = con.searchable(self.searchPattern[SUBJ],
                                           self.searchPattern[PRED],
                                           self.searchPattern[OBJ])
        if con in smartIn and isinstance(pred, LightBuiltIn):
            if self.canRun(): self.state = S_LIGHT_UNS_GO  # Can't do it here
            else: self.state = S_LIGHT_EARLY # Light built-in, can't run yet, not searched
        elif self.short == 0:  # Skip search if no possibilities!
            self.searchDone()
        else:
            self.state = S_NOT_LIGHT   # Not a light built in, not searched.
        if verbosity() > 80: progress("setup:" + `self`)
        if self.state == S_FAIL: return 0
        return []



    def tryBuiltin(self, queue, bindings, heavy, evidence):                    
        """Check for  built-in functions to see whether it will resolve.
        Return codes:  0 - give up;  1 - continue,
                [...] list of binding lists"""
        con, pred, subj, obj = self.quad
	proof = []  # place for built-in to hang a justification
	rea = None  # Reason for believing this item is true

	try:
	    if self.neededToRun[SUBJ] == []:
		if self.neededToRun[OBJ] == []:   # bound expression - we can evaluate it
		    if pred.eval(subj, obj,  queue, bindings[:], proof, self.query):
			self.state = S_DONE # satisfied
                        if verbosity() > 80: progress("Builtin buinary relation operator succeeds")
			if diag.tracking:
			    rea = BecauseBuiltIn(subj, pred, obj, proof)
			    evidence = evidence + [rea]
#			    return [([], rea)]  # Involves extra recursion just to track reason
			return []   # No new bindings but success in logical operator
		    else: return 0   # We absoluteley know this won't match with this in it
		else: 
		    if isinstance(pred, Function):
			result = pred.evalObj(subj, queue, bindings[:], proof, self.query)
			if result != None:
			    self.state = S_FAIL
			    rea=None
			    if diag.tracking: rea = BecauseBuiltIn(subj, pred, result, proof)
			    return [([ (obj, result)], rea)]
                        else:
			    if heavy: return 0
	    else:
		if (self.neededToRun[OBJ] == []):
		    if isinstance(pred, ReverseFunction):
			result = pred.evalSubj(obj, queue, bindings[:], proof, self.query)
			if result != None:
			    self.state = S_FAIL
			    rea=None
			    if diag.tracking:
				rea = BecauseBuiltIn(result, pred, obj, proof)
			    return [([ (subj, result)], rea)]
                        else:
			    if heavy: return 0
	    if verbosity() > 30:
		progress("Builtin could not give result"+`self`)
    
	    # Now we have a light builtin needs search,
	    # otherwise waiting for enough constants to run
	    return []   # Keep going
        except (IOError, SyntaxError):
            raise BuiltInFailed(sys.exc_info(), self ),None
        
    def trySearch(self):
        """Search the store
	Returns lists of list of bindings"""
        nbs = []
        if self.short == INFINITY:
            if verbosity() > 36:
                progress( "  Can't search for %s" % `self`)
        else:
            if verbosity() > 36:
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
                    nbs.append((nb, s))  # Add the new bindings into the set

        self.searchDone()  # State transitions
        return nbs

    def searchDone(self):
        """Search has been done: figure out next state."""
        con, pred, subj, obj = self.quad
        if self.state == S_LIGHT_EARLY:   # Light, can't run yet.
            self.state = S_LIGHT_WAIT    # Search done, can't run
        elif (self.query.template.listValue(subj) != None
              and ( pred is self.store.first or pred is self.store.rest)):
            if self.neededToRun[SUBJ] == [] and self.neededToRun[OBJ] == []:
                self.state = S_LIST_BOUND   # @@@ ONYY If existentially qual'd @@, it is true as an axiom.
            else:
                self.state = S_LIST_UNBOUND   # Still need to resolve this
	elif self.service:
	    self.state = S_REMOTE    #  Search done, need to synchronize with other items
        elif not isinstance(pred, HeavyBuiltIn):
            self.state = S_FAIL  # Done with this one: Do new bindings & stop
        elif self.canRun():
            self.state = S_HEAVY_READY
        else:
            self.state = S_HEAVY_WAIT
        if verbosity() > 90:
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


    def bindNew(self, newBindings):
        """Take into account new bindings from query processing to date

        The search may get easier, and builtins may become ready to run.
        Lists may either be matched against store by searching,
        and/or may turn out to be bound and therefore ready to run."""
        con, pred, subj, obj = self.quad
        if verbosity() > 90:
            progress(" binding ", `self` + " with "+ `newBindings`)
        q=[con, pred, subj, obj]
        for p in ALL4:
            changed = 0
            for var, val in newBindings:
                if var in self.neededToRun[p]:
                    self.neededToRun[p].remove(var)
                    changed = 1
                if q[p] is var and self.searchPattern[p]==None:
                    self.searchPattern[p] = val # const now
                    changed = 1
                    self.neededToRun[p] = [] # Now it is definitely all bound
            if changed:
                q[p] = _lookupRecursive(newBindings, q[p], why=becauseSubexpression)   # possibly expensive
		if self.searchPattern[p] != None: self.searchPattern[p] = q[p]
                
        self.quad = q[0], q[1], q[2], q[3]  # yuk

        if self.state in [S_NOT_LIGHT, S_LIGHT_EARLY, 75]: # Not searched yet
            for p in PRED, SUBJ, OBJ:
                x = self.quad[p]
                if isinstance(x, Formula):
                    if self.neededToRun[p]!= []:
                        self.short = INFINITY  # Forget it
                        break
            else:
		self.short, self.myIndex = con.searchable(self.searchPattern[SUBJ],
                                           self.searchPattern[PRED],
                                           self.searchPattern[OBJ])
            if self.short == 0:
                self.searchDone()

        if isinstance(self.quad[PRED], BuiltIn):
            if self.canRun():
                if self.state == S_LIGHT_EARLY: self.state = S_LIGHT_UNS_GO
                elif self.state == S_LIGHT_WAIT: self.state = S_LIGHT_GO
                elif self.state == S_HEAVY_WAIT: self.state = S_HEAVY_READY
        elif (self.state == S_LIST_UNBOUND
              and self.neededToRun[SUBJ] == []
              and self.neededToRun[OBJ] == []):
            self.state = S_LIST_BOUND
	if self.state == S_LIST_BOUND and self.searchPattern[SUBJ] != None:
	    if verbosity() > 50:
		progress("Rejecting list already searched and now bound", self)
	    self.state = S_FAIL    # see test/list-bug1.n3
        if verbosity() > 90:
            progress("...bound becomes ", `self`)
        if self.state == S_FAIL: return 0
        return [] # continue

    def __repr__(self):
        """Diagnostic string only"""
        return "%3i) short=%i, %s" % (
                self.state, self.short,
                quadToString(self.quad, self.neededToRun, self.searchPattern))

#############  Substitution functions    

def _substitute(bindings, list):
    """Subsitustes IN-LINE into a list of quads"""
    for i in range(len(list)):
        q = list[i]
        list[i] = lookupQuad(bindings, q)
                            
def lookupQuad(bindings, q):
	"Return a subsituted quad"
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

def lookupQuadRecursive(bindings, q, why=None):
	context, pred, subj, obj = q
	if verbosity() > 99: progress("\tlookupQuadRecursive:", q)
	return (
            _lookupRecursive(bindings, context, why=why),
            _lookupRecursive(bindings, pred, why=why),
            _lookupRecursive(bindings, subj, why=why),
            _lookupRecursive(bindings, obj, why=why) )

def _lookupRecursive(bindings, x, why=None):
    """ Subsitute into formula."""
    vars = []
#    if x is old: return new
    for left, right in bindings:
        if left == x: return right
        vars.append(left)
    if not isinstance(x, Formula):
        return x
    store = x.store
    oc = store.occurringIn(x, vars)
    if oc == []: return x # phew!
    y = store.newInterned(FORMULA)
    if verbosity() > 90: progress("lookupRecursive: formula"+`x`+" becomes new "+`y`,
				" because of ", oc)
    store.copyFormulaRecursive(x, y, bindings, why=why)
#    for s in x.statements:
#        store.storeQuad((y,
#                         _lookupRecursive(bindings, s[PRED], x, y, why=why),
#                         _lookupRecursive(bindings, s[SUBJ], x, y, why=why),
#                         _lookupRecursive(bindings, s[OBJ], x, y, why=why))
#			 , why)
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
        str = str + (" %s->%s " % ( x2s(x), x2s(y)))
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
    #    --- but on some releases, we need to say tuple(types.StringTypes)
    return type(x) is type('') or type(x) is type(u'')

#####################  Register this module

from thing import setStoreClass
setStoreClass(RDFStore)

#ends

