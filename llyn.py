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
from term import BuiltIn, LightBuiltIn, \
    HeavyBuiltIn, Function, ReverseFunction, \
    Literal, Symbol, Fragment, FragmentNil, Anonymous, Term, CompoundTerm, List, EmptyList, NonEmptyList
from term import merge
from formula import Formula, StoredStatement, compareTerm

from RDFSink import Logic_NS, RDFSink, forSomeSym, forAllSym
from RDFSink import CONTEXT, PRED, SUBJ, OBJ, PARTS, ALL4
from RDFSink import N3_nil, N3_first, N3_rest, OWL_NS, N3_Empty, N3_List, List_NS
from RDFSink import RDF_NS_URI

from RDFSink import FORMULA, LITERAL, ANONYMOUS, SYMBOL

from pretty import Serializer

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

#reason=Namespace("http://www.w3.org/2000/10/swap/reason#")

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
S_NEED_DEEP=	45  # Can't search because of unbound compound term, could do recursive unification
S_HEAVY_READY=	40  # Heavy built-in, search done, but formula now has no vars left. Ready to run.
S_LIGHT_WAIT=	30  # Light built-in, not enough constants to calculate, search done.
S_HEAVY_WAIT=	20  # Heavy built-in, too many variables in args to calculate, search failed.
S_HEAVY_WAIT_F=	19  # Heavy built-in, too many vars within formula args to calculate, search failed.
S_REMOTE =	10  # Waiting for local query to be resolved as much as possible
S_LIST_UNBOUND = 7  # List defining statement, search failed, unbound variables in list.?? no
S_LIST_BOUND =	 5  # List defining statement, search failed, list is all bound.
S_DONE =	 0  # Item has been staisfied, and is no longer a constraint

    

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
    if F != None:
	if "m" in mode:
	    workingContext.reopen()
	    if verbosity() > 45: progress("Web: dereferenced %s  added to %s" %(
			x, workingContext))
	    workingContext.store.copyFormula(F, workingContext)
	if "x" in mode:   # capture experience
	    workingContext.add(r, x.store.semantics, F)
    setattr(x, "_semantics", F)
    if verbosity() > 25: progress("Web: Dereferencing %s gave %s" %(x, F))
    return F
		

###################################### Forumula
#
class IndexedFormula(Formula):
    """A formula which has indexes to facilitate queries.
    
    A formula is either open or closed.  Initially, it is open. In this
    state is may be modified - for example, triples may be added to it.
    When it is closed, note that a different interned version of itself
    may be returned. From then on it is a constant.
    
    Only closed formulae may be mentioned in statements in other formuale.
    
    There is a reopen() method but it is not recommended, and if desperate should
    only be used immediately after a close().
    """
    def __init__(self, resource, fragid):
        Formula.__init__(self, resource, fragid)
        self.descendents = None   # Placeholder for list of closure under subcontext
	self.collector = None # Object collecting evidence, if any 
	self._redirection = {}
	self._index = {}
	self._index[(None,None,None)] = self.statements

	self._closureMode = ""
	self._closureAgenda = []
	self._closureAlready = []
	self.lists = []  # Made later when we compactLists


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


    def compactLists(self):
	"""For any lists expressed longhand, convert to objects.
	
	Works in place. Strips out the reifications fo the lists,
	and converts any statements which refer to the list to refer to the object."""
	assert self.canonical == None
	if verbosity() > 90:
	    progress("Comapcting lists:"+`self`)
	
	if self._redirection == {}: return

	for s in self.statements[:]:
	    context, pred, subj, obj = s.quad
	    try:
		subj = self._redirection[subj]
		if pred is self.store.first or pred is self.store.rest:
		    self.removeStatement(s)
		    if verbosity()>80: progress(" \tList compact: removing", s)
		    assert false
		    if pred is self.store.first: # nested list
			try:
			    nested = self._redirection[obj]
			    rest = subj.rest
			    del(rest._prec[obj])
			    rest._prec[nested] = subj
			    subj.first = nested  # Patch list! (yuk! = but avoids recusrive subst.)
			except:
			    pass
		    continue   # Just strip the first and rest out
		else:
		    self.lists.append(subj)
		    try:
			obj = self._redirection[obj]
			self.lists.append(obj)
		    except:
			pass
	    except KeyError:
		try:
		    obj = self._redirection[obj]
		    self.lists.append(obj)
		except:
		    continue
	    
	    if verbosity()>80: progress(" \tList compact: replacing", s)
	    assert false
	    self.removeStatement(s)
	    self.add(subj=subj, pred=pred, obj=obj)

#	for v in self._redirection.keys():
#	    if verbosity()>80: progress(" \tList compact: removing existential", v)
#	    self._existentialVariables.remove(v)
	self._redirection = {}
		    

    def add(self, subj, pred, obj, why=None):
	"""Add a triple to the formula.
	
	The formula must be open.
	subj, pred and obj must be objects as for example generated by Formula.newSymbol() and newLiteral(), or else literal values which can be interned.
	why 	may be a reason for use when a proof will be required.
	"""
        if self.canonical != None:
            raise RuntimeError("Attempt to add statement to canonical formula "+`self`)

	store = self.store
	triple = [ pred, subj, obj ]
	for i in 0, 1, 2:
	    if not isinstance(triple[i], Term): triple[i] = store.intern(triple[i])
	    try:
		x = self._redirection[triple[i]]  # redirect to list value
		if verbosity()>90: progress("\tRedirecting %s to %s" %( triple[i], x))
		triple[i] = x
		if not ((pred is self.store.first) or (pred is self.store.rest)) or i!=1:
		    self.lists.append(triple[i])
	    except KeyError:
		pass
	
	pred = triple[0]
	subj = triple[1]
	obj = triple[2]
        if verbosity() > 50:
            progress("add quad (size before %i) %s: %s " % (self.store.size, self,  `triple`) )
        if self.statementsMatching(pred, subj, obj):
            if verbosity() > 97:  progress("storeQuad duplicate suppressed"+`triple`)
            return 0  # Return no change in size of store
	assert not isinstance(pred, Formula) or pred.canonical is pred, "pred Should be closed"+`pred`
	assert (not isinstance(subj, Formula)
		or subj is self
		or subj.canonical is subj), "subj Should be closed or this"+`subj`
	assert not isinstance(obj, Formula) or obj.canonical is obj, "obj Should be closed"+`obj`

        store.size = store.size+1

# We collapse lists from the declared daml first,rest structure into List objects.
# To do this, we need a bnode with (a) a first; (b) a rest, and (c) the rest being a list.
# We trigger List collapse on any of these three becoming true.
# @@@ we don't reverse this on remove statement.  Remove statement is really not a user call.

	if subj in self._existentialVariables:
	    if pred is store.rest and isinstance(obj, List):
		ss = self.statementsMatching(pred=store.first, subj=subj)
		if ss:
		    s = ss[0]
		    self.removeStatement(s)
		    first = s[OBJ]
		    list = obj.prepend(first)
		    self._checkList(subj, list)
		    return 1  # Added a statement but ... it is hidden in lists
    
	    elif pred is store.first:
		ss = self.statementsMatching(pred=store.rest, subj=subj)
		if ss:
		    s = ss[0]
		    rest = s[OBJ]
		    list = rest.prepend(obj)
		    self.removeStatement(s)
		    self._checkList(subj, list)
		    return 1

        s = StoredStatement((self, pred, subj, obj))
	
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
    
    def canonicalize(F):
        """If this formula already exists, return the master version.
        If not, record this one and return it.
        Call this when the formula is in its final form, with all its statements.
        Make sure no one else has a copy of the pointer to the smushed one.
	In canonical form,
	 - the statments are ordered
	 - the lists are all internalized as lists
	 
	Store dependency: Uses store._formulaeOfLength
        """
	store = F.store
	if F.canonical != None:
            if verbosity() > 70:
                progress("End formula -- @@ already canonical:"+`F`)
            return F.canonical

	F.compactLists()
	
        fl = F.statements
        l = len(fl), len(F.universals()), len(F.existentials())   # The number of statements
        possibles = store._formulaeOfLength.get(l, None)  # Formulae of same length

        if possibles == None:
            store._formulaeOfLength[l] = [F]
            if verbosity() > 70:
                progress("End formula - first of length", l, F)
            F.canonical = F
            return F

        fl.sort(StoredStatement.compareSubjPredObj)
	fe = F.existentials()
	fe.sort(compareTerm)
	fu = F.universals ()
	fu.sort(compareTerm)

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
		oe.sort(compareTerm)
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
        F.canonical = F
        if verbosity() > 70:
            progress("End formula, a fresh one:"+`F`)
        return F


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
	      pred is self.store.imports)):   # check subject? @@@  semantics?
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

    def includes(f, g, _variables=[], smartIn=[], bindings={}):
	"""Does this formula include the information in the other?
	
	smartIn gives a list of formulae for which builtin functions should operate
	   in the consideration of what "includes" means.
	bindings is for use within a query.
	"""
	return  f.store.testIncludes(f, g, _variables=_variables, smartIn=smartIn, bindings=bindings)


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

    def _checkList(self,  L, rest):
        """Check whether this new list (given as bnode) causes other things to become lists.
	Set up redirection so the list is used from now on instead of the bnode.	
	Internal function."""
	self._redirection[L] = rest
	self._existentialVariables.remove(L)
        if verbosity() > 80: progress("\tChecking new list was %s, now %s = %s"%(`L`, `rest`, `rest.value()`))
        possibles = self.statementsMatching(pred=self.store.rest, obj=L)  # What has this as rest?
        for s in possibles[:]:
            L2 = s[SUBJ]
            ff = self.statementsMatching(pred=self.store.first, subj=L2)
            if ff != []:
                first = ff[0][OBJ]
		self.removeStatement(s) 
		self.removeStatement(ff[0])
		list = rest.prepend(first)
		self._checkList(L2, list)

	ss = self.statementsMatching(obj=L)
	for s in ss:
	    c1, p1, s1, o1 = s.quad
	    self.removeStatement(s)
	    self.add(pred=p1, subj=s1, obj=rest)

	ss = self.statementsMatching(subj=L)
	for s in ss:
	    c1, p1, s1, o1 = s.quad
	    self.removeStatement(s)
	    self.add(pred=p1, subj=rest, obj=o1)


	
def comparePair(self, other):
    for i in 0,1:
        x = compareTerm(self[i], other[i])
        if x != 0:
            return x





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
        elif isinstance(subj, List): y = store.List
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
        return F.canonicalize()
    
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
            F = F.close()
	    store._experience.add(subj=subj, pred=store.parsedAsN3, obj=F)
	    return F

class BI_conclusion(HeavyBuiltIn, Function):
    """ Deductive Closure

    Closure under Forward Inference, equivalent to cwm's --think function.
    This is a function, so the object is calculated from the subject.
    """
    def evalObj(self, subj, queue, bindings, proof, query):
        store = subj.store
        if isinstance(subj, Formula):
	    assert subj.canonical != None
            F = self.store.any((store._experience, store.cufi, subj, None))  # Cached value?
            if F != None:
		if verbosity() > 10: progress("Bultin: " + `subj`+ " cached log:conclusion " + `F`)
		return F

            F = self.store.newInterned(FORMULA)
	    if diag.tracking:
		reason = BecauseMerge(F, subj)
		F.collector = reason
		proof.append(reason)
	    else: reason = None
            if verbosity() > 10: progress("Bultin: " + `subj`+ " log:conclusion " + `F`)
            self.store.copyFormula(subj, F, why=reason) # leave open
            self.store.think(F)
	    F = F.close()
	    assert subj.canonical != None
	    
            self.store.storeQuad((store._experience, store.cufi, subj, F),
		    why=BecauseOfExperience("conclusion"))  # Cache for later
            return F
    
class BI_conjunction(LightBuiltIn, Function):      # Light? well, I suppose so.
    """ The conjunction of a set of formulae is the set of statements which is
    just the union of the sets of statements
    modulo non-duplication of course"""
    def evalObj(self, subj, queue, bindings, proof, query):
	subj_py = subj.value()
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
                progress("    Formula %s now has %i" % (`F`,len(F.statements)))
        return F.canonicalize()

class BI_n3String(LightBuiltIn, Function):      # Light? well, I suppose so.
    """ The n3 string for a formula is what you get when you
    express it in the N3 language without using any URIs.
    Note that there is no guarantee that two implementations will
    generate the same thing, but whatever they generate should
    parse back using parsedAsN3 to exaclty the same original formula.
    If we *did* have a canonical form it would be great for signature
    A canonical form is possisble but not simple."""
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
        
        self.forSome = self.symbol(forSomeSym)
	self.integer = self.symbol(INTEGER_DATATYPE)
	self.float  = self.symbol(FLOAT_DATATYPE)
        self.forAll  = self.symbol(forAllSym)
        self.implies = self.symbol(Logic_NS + "implies")
        self.means = self.symbol(Logic_NS + "means")
        self.asserts = self.symbol(Logic_NS + "asserts")
        
# Register Light Builtins:

        log = self.symbol(Logic_NS[:-1])   # The resource without the hash

# Functions:        

        log.internFrag("racine", BI_racine)  # Strip fragment identifier from string

        self.rawType =  log.internFrag("rawType", BI_rawType) # syntactic type, oneOf:
        log.internFrag("rawUri", BI_rawUri)
        self.Literal =  log.internFrag("Literal", Fragment) # syntactic type possible value - a class
        self.List =     log.internFrag("List", Fragment) # syntactic type possible value - a class
        self.Formula =  log.internFrag("Formula", Fragment) # syntactic type possible value - a class
        self.Other =    log.internFrag("Other", Fragment) # syntactic type possible value - a class

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

        self.Truth = self.symbol(Logic_NS + "Truth")
        self.Falsehood = self.symbol(Logic_NS + "Falsehood")
        self.type = self.symbol(RDF_type_URI)
        self.Chaff = self.symbol(Logic_NS + "Chaff")
	self.docRules = self.symbol("http://www.w3.org/2000/10/swap/pim/doc#rules")
	self.imports = self.symbol("http://www.w3.org/2002/07/owl#imports")

# List stuff - beware of namespace changes! :-(

	from cwm_list import BI_first, BI_rest
        rdf = self.symbol(List_NS[:-1])
	self.first = rdf.internFrag("first", BI_first)
        self.rest = rdf.internFrag("rest", BI_rest)
        self.nil = self.intern(N3_nil, FragmentNil)
#        self.nil._asList = EmptyList(self, None, None)
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
	import cwm_list	   # List handling operations
        cwm_string.register(self)
        cwm_math.register(self)
        cwm_maths.register(self)
        cwm_os.register(self)
        cwm_time.register(self)
        cwm_times.register(self)
	cwm_list.register(self)
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
		if verbosity() > 60:
		    progress("   Headers for %s: %s\n" %(addr, netStream.headers.items()))
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
	raise ValueError("Ooops! Attempt to create new identifier hits on one already used: %s"%(urirefString))
	return


    def internURI(self, str, why=None):
	"old -use symbol()"
        assert type(str) is type("") # caller %xx-ifies unicode
        return self.intern((SYMBOL,str), why=None)

    def symbol(self, str):
	"""Intern a URI for a symvol, returning a symbol object"""
        assert type(str) is type("") # caller %xx-ifies unicode
        return self.intern((SYMBOL,str), why=None)
    
    def _fromPython(self, x, queue=None):
	"""Takem a python string, seq etc and represent as a llyn object"""
        if isinstance(x, tuple(types.StringTypes)):
            return self.newLiteral(x)
        elif type(x) is types.IntType:
            return self.newLiteral(`x`, self.integer)
        elif type(x) is types.FloatType:
            return self.newLiteral(`x`, self.float)
        elif type(x) == type([]):
	    return self.store.nil.newList(x)
        return x

    def intern(self, what, dt=None, lang=None, why=None, ):
        """find-or-create a Fragment or a Symbol or Literal or list as appropriate

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
	    if type(what) is types.SequenceType:
		return self.newList(what)
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
                r = self.symbol(resid)
                if typ == SYMBOL:
                    if urirefString == N3_nil[1]:  # Hack - easier if we have a different classs
                        result = r.internFrag(urirefString[hash+1:], FragmentNil)
                    else:
                        result = r.internFrag(urirefString[hash+1:], Fragment)
                elif typ == ANONYMOUS:
		    result = r.internFrag(urirefString[hash+1:], Anonymous)
                elif typ == FORMULA:
		    result = r.internFrag(urirefString[hash+1:], IndexedFormula)
                else: raise RuntimeError, "did not expect other type:"+`typ`
        return result

     
    def newList(self, value):
	return nil.newList(value)

    def deleteFormula(self,F):
        if verbosity() > 30: progress("Deleting formula %s %ic" %
                                            ( `F`, len(F.statements)))
        for s in F.statements[:]:   # Take copy
            self.removeStatement(s)


    def reopen(self, F):
        if F.canonical == None:
            if verbosity() > 50:
                progress("reopen formula -- @@ already open: "+`F`)
            return F # was open
        if verbosity() > 70:
            progress("reopen formula:"+`F`)
	key = len(F.statements), len(F.universals()), len(F.existentials())  
        self._formulaeOfLength[key].remove(F)  # Formulae of same length
        F.canonical = None
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
	

    def startDoc(self):
        pass

    def endDoc(self, rootFormulaPair):
        return




##########################################################################
#
# Output methods:
#
    def dumpChronological(self, context, sink):
	"Fast as possible. Only dumps data. No formulae or universals."
	pp = Serializer(context, sink)
	pp. dumpChronological()
	del(pp)
	
    def dumpBySubject(self, context, sink, sorting=1):
        """ Dump by order of subject except forSome's first for n3=a mode"""
	pp = Serializer(context, sink, sorting=sorting)
	pp. dumpBySubject()
	del(pp)
	

    def dumpNested(self, context, sink):
        """ Iterates over all URIs ever seen looking for statements
        """
	pp = Serializer(context, sink)
	pp. dumpNested()
	del(pp)



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
	bindings2 = bindings.copy()
	bindings2[old] = new
        for s in old.statements[:] :   # Copy list!
	    self.storeQuad((new,
                         s[PRED].substitution(bindings2),
                         s[SUBJ].substitution(bindings2),
			s[OBJ].substitution(bindings2))
			 , why)
        return total
                
    def copyFormula(self, old, new, why=None):
	bindings = {old: new}
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
	"""Forward inference
	
	This is tricky in the case in which rules are added back into the
	store. The store is used for read (normally canonical) and write
	(normally open) at the samne time.
	"""
        grandtotal = 0
        iterations = 0
        if G == None:
	    G = F
	assert not G.canonical # Must be open to add stuff
	if F._redirection != {}: F.compactLists()
        if verbosity() > 45: progress("think: rules from %s added to %s" %(F, G))
        bindingsFound = {}  # rule: list bindings already found
        while 1:
            iterations = iterations + 1
            step = self.applyRules(F, G, alreadyDictionary=bindingsFound, mode=mode)
            if step == 0: break
            grandtotal= grandtotal + step
        if verbosity() > 5: progress("Grand total of %i new statements in %i iterations." %
                 (grandtotal, iterations))
	G = G.canonicalize()
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


#	x = template.occurringIn(template.universals()[:])
	if template.universals() != []:
	    raise RuntimeError("""Cannot query for universally quantified things.
	    As of 2003/07/28 forAll x ...x cannot be on left hand side of rule.
	    This/these were: %s\n""" % x)

        unmatched = template.statements[:]
	templateExistentials = template.existentials()[:]
        _substitute({template: workingContext}, unmatched)

        variablesMentioned = template.occurringIn(_variables)
        variablesUsed = conclusion.occurringIn(variablesMentioned)
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



    def testIncludes(self, f, g, _variables=[], smartIn=[], bindings={}):
	"""Return whether or nor f contains a top-level formula equvalent to g.
	Just a test: no bindings returned."""
        if verbosity() >30: progress("\n\n=================== testIncludes ============")

        # When the template refers to itself, the thing we are
        # are looking for will refer to the context we are searching

        if not(isinstance(f, Formula) and isinstance(g, Formula)): return 0

	assert f.canonical is f
	assert g.canonical is g

        unmatched = g.statements[:]
	templateExistentials = g.existentials()
        _substitute({g: f}, unmatched)
        
	if g.universals() != []:
	    raise RuntimeError("""Cannot query for universally quantified things.
	    As of 2003/07/28 forAll x ...x cannot be on left hand side of rule.
	    This/these were: %s\n""" % x)

        if bindings != {}: _substitute(bindings, unmatched)

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



    def conclude(self, bindings, evidence = []):
	"""When a match found in a query, add conclusions to target formula.

	Returns the number of statements added."""
	if self.justOne: return 1   # If only a test needed
	assert type(bindings) is type({})
#        store, workingContext, conclusion, targetContext,  already, rule = param

        if verbosity() >60: progress( "\nConcluding tentatively..." + bindingsToString(bindings))

        if self.already != None:
            if bindings in self.already:
                if verbosity() > 30: progress("@@Duplicate result: ", bindingsToString(bindings))
                # raise foo
                return 0
            if verbosity() > 30: progress("Not duplicate: ", bindingsToString(bindings))
            self.already.append(bindings)   # A list of dicts

	if diag.tracking:
	    reason = BecauseOfRule(self.rule, bindings=bindings, evidence=evidence)
	else:
	    reason = None

	es, exout = self.workingContext.existentials(), []
	for var, val in bindings.items():
	    if val in es:
		exout.append(val)
		if verbosity() > 25:
		    progress("Matches we found which is just existential: %s -> %s" % (var, val))
		self.targetContext.add(subj=self.targetContext, pred=self.store.forSome, obj=val, why=reason)

        b2 = bindings.copy()
	b2[self.conclusion] = self.targetContext
	assert type(b2) is type({})
        ok = self.targetContext.universals()  # It is actually ok to share universal variables with other stuff
        poss = self.conclusion.universals()[:]
        for x in poss[:]:
            if x in ok: poss.remove(x)
        vars = self.conclusion.existentials() + poss  # Terms with arbitrary identifiers
#        clashes = self.occurringIn(targetContext, vars)    Too slow to do every time; play safe
	if verbosity() > 25:
	    s = "Universals in conclusion but not in target regenerated:" + `vars`
        for v in vars:
	    if v not in exout:
		v2 = self.store.newInterned(ANONYMOUS)
		b2[v] =v2   # Regenerate names to avoid clash
		if verbosity() > 25: s = s + ", %s -> %s" %(v, v2)
	    else:
		if verbosity() > 25: s = s + (", (%s is existential in kb)"%v)
	if len(vars) >0 and verbosity() > 25:
	    progress(s)
	

        if verbosity()>10:
            progress("Concluding definitively" + bindingsToString(b2) )
        before = self.store.size
        self.store.copyFormulaRecursive(
		    self.conclusion, self.targetContext, b2, why=reason)
        if verbosity()>30:
            progress("   size of store changed from %i to %i."%(before, self.store.size))
        return self.store.size - before


##################################################################################


    def unify(query,
               queue,               # Set of items we are trying to match CORRUPTED
               variables,           # List of variables to match and return CORRUPTED
               existentials,        # List of variables to match to anything
                                    # Existentials or any kind of variable in subexpression
               bindings = {},       # Bindings discovered so far
               newBindings = {},    # New bindings not yet incorporated
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
	assert type(bindings) is type({})
	assert type(newBindings) is type({})
        if verbosity() > 59:
            progress( "QUERY2: called %i terms, %i bindings %s, (new: %s)" %
                      (len(queue),len(bindings),bindingsToString(bindings),
                       bindingsToString(newBindings)))
            if verbosity() > 90: progress( queueToString(queue))

        for pair in newBindings.items():   # Take care of business left over from recursive call
            if verbosity()>95: progress("    new binding:  %s -> %s" % (`pair[0]`, `pair[1]`))
            if pair[0] in variables:
                variables.remove(pair[0])
                bindings.update({pair[0]: pair[1]})  # Record for posterity
            else:      # Formulae aren't needed as existentials, unlike lists. hmm.
		if diag.tracking: bindings.update({pair[0]: pair[1]})  # Record for proof only
		if pair[0] not in existentials:
		    progress("@@@  Not in existentials or variables but now bound:", `pair[0]`)
                if not isinstance(pair[0], Formula): # Hack - else rules13.n3 fails @@
                    existentials.remove(pair[0]) # Can't match anything anymore, need exact match

        # Perform the substitution, noting where lists become boundLists.
        # We do this carefully, messing up the order only of things we have already processed.
        if newBindings != {}:
            for item in queue:
                if item.bindNew(newBindings) == 0: return 0


        while len(queue) > 0:

            if (verbosity() > 90):
                progress( "query iterating with %i terms, %i bindings: %s; %i new bindings: %s ." %
                          (len(queue),
                           len(bindings),bindingsToString(bindings),
                           len(newBindings),bindingsToString(newBindings)))
                progress ( queueToString(queue))


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
                progress( "Looking at " + `item`
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
            elif state == S_LIGHT_EARLY or state == S_NOT_LIGHT or state == S_NEED_DEEP: #  Not searched yet
                nbs = item.tryDeepSearch()
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


                        _substitute({obj: subj}, more_unmatched)
                        _substitute(bindings, more_unmatched)
                        existentials = existentials + more_variables
                        allvars = variables + existentials
                        for quad in more_unmatched:
                            newItem = QueryItem(query, quad)
                            queue.append(newItem)
                            newItem.setup(allvars, smartIn = query.smartIn + [subj],
				    unmatched=more_unmatched, mode=query.mode)
                        if verbosity() > 40:
                                progress(
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
                        progress("List left unbound, returing")
                return total   # forget it  (this right?!@@)
            elif state == S_LIST_BOUND: # bound list
                if verbosity()>60: progress(
		    "QUERY FOUND MATCH (dropping lists) with bindings: "
		    + bindingsToString(bindings))
                return total + query.conclude(bindings, evidence=evidence)  # No non-list terms left .. success!
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
            if verbosity() > 90: progress("    nbs=" + `nbs`)
            if nbs == 0: return total
            elif nbs != []:
                total = 0
#		if nbs != 0 and nbs != []: pass
		# progress("llyn.py 2738:   nbs = %s" % nbs)
                for nb, reason in nbs:
		    assert type(nb) is types.DictType, nb
                    q2 = []
                    for i in queue:
                        newItem = i.clone()
                        q2.append(newItem)  #@@@@@@@@@@  If exactly 1 binding, loop (tail recurse)
		    
                    total = total + query.unify(q2, variables[:], existentials[:],
                                          bindings.copy(), nb, evidence = evidence + [reason])
                    if query.justOne and total:
                        return total
		return total # The called recursive calls above will have generated the output
            if item.state == S_FAIL: return total
            if item.state != S_DONE:   # state 0 means leave me off the list
                queue.append(item)
            # And loop back to take the next item

        if verbosity()>50: progress("QUERY MATCH COMPLETE with bindings: " + bindingsToString(bindings))
        return query.conclude(bindings,  evidence=evidence)  # No terms left .. success!



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
        a = SqlDBAlgae(query.store.symbol(items[0].service.uri), cachedSchema, user, password, host, database, query.meta, query.store.pointsAt, query.store)
        # Execute the query.
        messages = []
        nextResults, nextStatements = a._processRow([], [], qp, rs, messages, {})
        # rs.results = nextResults # Store results as initial state for next use of rs.
        if verbosity() > 90: progress(string.join(messages, "\n"))
        if verbosity() > 90: progress("query matrix \"\"\""+rs.toString({'dataFilter' : None})+"\"\"\" .\n")

	nbs = []
	reason = Because("Remote query") # could be messages[0] which is the query
        # Transform nextResults to format cwm expects.
        for resultsRow in nextResults:
            boundRow = {}
            for i in range(len(query.variables)):
                v = query.variables[i]
                index = rs.getVarIndex(v)
                interned = resultsRow[index]
                boundRow[v] = interned  # bindings
            nbs.append((boundRow, reason))

        if verbosity() > 10: progress("====> bindings from remote query:"+`nbs`)
	return nbs   # No bindings for testing



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
        hasUnboundCoumpundTerm = 0
        for p in PRED, SUBJ, OBJ :
            x = self.quad[p]
#	    if x is con:  # "this" is special case.
#		self.neededToRun[p] = []
#		continue
            if x in allvars:   # Variable
                self.neededToRun[p] = [x]
                self.searchPattern[p] = None   # can bind this
#            if self.query.template.listValue(x) != None and x is not self.store.nil:
#                self.searchPattern[p] = None   # can bind this
#                ur = self.store.occurringIn(x, allvars)
#		ur = []
#		ee = self.store.listElements(x, unmatched)
#		for e in ee: 
#		    if e in allvars and e not in ur: ur.append(e)
#                self.neededToRun[p] = ur
            elif isinstance(x, Formula) or isinstance(x, List): # expr
                ur = x.occurringIn(allvars)
                self.neededToRun[p] = ur
                if ur != []:
                    hasUnboundCoumpundTerm = 1     # Can't search directly
		    self.searchPattern[p] = None   # can bind this if we recurse
		    
	    if verbosity() > 98: progress("        %s needs to run: %s"%(`x`, `self.neededToRun[p]`))
                
#        if hasUnboundCoumpundTerm:
#            self.short = INFINITY   # can't search
#        else:
	self.short, self.myIndex = con.searchable(self.searchPattern[SUBJ],
                                           self.searchPattern[PRED],
                                           self.searchPattern[OBJ])
        if con in smartIn and isinstance(pred, LightBuiltIn):
            if self.canRun(): self.state = S_LIGHT_UNS_GO  # Can't do it here
            else: self.state = S_LIGHT_EARLY # Light built-in, can't run yet, not searched
        elif self.short == 0:  # Skip search if no possibilities!
            self.searchDone()
	elif hasUnboundCoumpundTerm:
	    self.state = S_NEED_DEEP   # Put off till later than non-deep ones
        else:
            self.state = S_NOT_LIGHT   # Not a light built in, not searched.
        if verbosity() > 80: progress("setup:" + `self`)
        if self.state == S_FAIL: return 0
        return []



    def tryBuiltin(self, queue, bindings, heavy, evidence):                    
        """Check for  built-in functions to see whether it will resolve.
        Return codes:  0 - give up; 
		[] - success, no new bindings, (action has been called)
                [...] list of binding lists, each a pair of bindings and reason."""
        con, pred, subj, obj = self.quad
	proof = []  # place for built-in to hang a justification
	rea = None  # Reason for believing this item is true

	try:
	    if self.neededToRun[SUBJ] == []:
		if self.neededToRun[OBJ] == []:   # bound expression - we can evaluate it
		    if pred.eval(subj, obj,  queue, bindings.copy(), proof, self.query):
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
			if verbosity() > 97: progress("Builtin function call %s(%s)"%(pred, subj))
			result = pred.evalObj(subj, queue, bindings.copy(), proof, self.query)
			if result != None:
			    self.state = S_FAIL
			    rea=None
			    if diag.tracking: rea = BecauseBuiltIn(subj, pred, result, proof)
			    return [({obj: result}, rea)]
                        else:
			    if heavy: return 0
	    else:
		if (self.neededToRun[OBJ] == []):
		    if isinstance(pred, ReverseFunction):
			result = pred.evalSubj(obj, queue, bindings.copy(), proof, self.query)
			if result != None:
			    self.state = S_FAIL
			    rea=None
			    if diag.tracking:
				rea = BecauseBuiltIn(result, pred, obj, proof)
			    return [({subj: result}, rea)]
                        else:
			    if heavy: return 0
		else:
		    if isinstance(pred, FiniteProperty):
			result = pred.ennumerate()
			if result != 0:
			    self.state = S_FAIL
			    rea=None
			    if diag.tracking:
				rea = BecauseBuiltIn(result, pred, obj, proof)
			    return [({subj: result}, rea)]
                        else:
			    if heavy: return 0
	    if verbosity() > 30:
		progress("Builtin could not give result"+`self`)
    
	    # Now we have a light builtin needs search,
	    # otherwise waiting for enough constants to run
	    return []   # Keep going
        except (IOError, SyntaxError):
            raise BuiltInFailed(sys.exc_info(), self ),None
        
    def tryDeepSearch(self):
        """Search the store, matching nested compound structures
	
	Returns lists of list of bindings, attempting if necessary to unify
	any nested compound terms. Added 20030810, not sure whether it is worth the
	execution time in practice. It could be left to a special magic built-in like "matches"
	or something if it is only occasionnaly used.
	
	Used in state S_NEED_DEEP
	"""
        nbs = []
        if self.short == INFINITY:
            if verbosity() > 36:
                progress( "  Can't deep search for %s" % `self`)
        else:
            if verbosity() > 36:
                progress( "  Searching (S=%i) %i for %s" %(self.state, self.short, `self`))
            for s in self.myIndex :  # for everything matching what we know,
                nb = {}
                reject = 0
                for p in PRED, SUBJ, OBJ:
                    if self.searchPattern[p] == None: # Need to check
			x = self.quad[p]
			if self.neededToRun[p] == [x]:   # Normal case
			    nb1 = {x: s.quad[p]}
			else:  # Deep case
			    nbs1 = x.unify(s.quad[p], self.query.variables,
				self.query.existentials, {})  # Bindings have all been bound
			    if verbosity() > 70:
				progress( "  Searching deep %s result binding %s" %(self, nbs1))
			    if nbs1 == 0: return 0 # No way
			    if len(nbs1) > 1:
				raise RuntimeError("Not implemented this hook yet - call timbl")
			    nb1, rea = nbs1[0]
			    # @@@@ substitute into other parts of triple @@@@@@@
			for binding in nb1.items():
			    for oldbinding in nb.items():
				if oldbinding[0] is binding[0]:
				    if oldbinding[1] is binding[1]:
					del nb1[binding[0]] # duplicate  
				    else: # don't bind same to var to 2 things!
					reject = 1
					break
			else:
			    nb.update(nb1)
			    continue
			break # reject
                else:
                    nbs.append((nb, s))  # Add the new bindings into the set

        self.searchDone()  # State transitions
        return nbs

    def searchDone(self):
        """Search has been done: figure out next state."""
        con, pred, subj, obj = self.quad
        if self.state == S_LIGHT_EARLY:   # Light, can't run yet.
            self.state = S_LIGHT_WAIT    # Search done, can't run
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
        and/or may turn out to be bound and therefore ready to run.
	
	Return:
	    0		No way can this item ever complete.
	    None	Binding done, see item.state 
	"""
        con, pred, subj, obj = self.quad
        if verbosity() > 90:
            progress(" binding ", `self` + " with "+ `newBindings`)
        q=[con, pred, subj, obj]
        for p in ALL4:
            changed = 0
            for var, val in newBindings.items():
                if var in self.neededToRun[p]:
                    self.neededToRun[p].remove(var)
                    changed = 1
                if q[p] is var and self.searchPattern[p]==None:
                    self.searchPattern[p] = val # const now
                    changed = 1
                    self.neededToRun[p] = [] # Now it is definitely all bound
            if changed:
                q[p] = q[p].substitution(newBindings, why=becauseSubexpression)   # possibly expensive
		if self.searchPattern[p] != None: self.searchPattern[p] = q[p]
                
        self.quad = q[0], q[1], q[2], q[3]  # yuk

        if self.state in [S_NOT_LIGHT, S_LIGHT_EARLY, S_NEED_DEEP]: # Not searched yet
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
	if self.state == S_LIST_BOUND and self.searchPattern[SUBJ] != None:  # @@@@@@ 20030807
	    if verbosity() > 50:
		progress("Rejecting list already searched and now bound", self)
	    self.state = S_FAIL    # see test/list-bug1.n3
	    return []  #@@@@ guess 20030807
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
	return (bindings.get(context, context),
		bindings.get(pred, pred),
		bindings.get(subj, subj),
		bindings.get(obj, obj))

def _lookup(bindings, value):
    return bindings.get(value, value)

def lookupQuadRecursive(bindings, q, why=None):
	context, pred, subj, obj = q
	if verbosity() > 99: progress("\tlookupQuadRecursive:", q)
	return (
            context.substitution(bindings),
            pred.substitution(bindings),
            subj.substitution(bindings),
            obj.substitution(bindings) )


class URISyntaxError(ValueError):
    """A parameter is passed to a routine that requires a URI reference"""
    pass


#   DIAGNOSTIC STRING OUTPUT
#
def bindingsToString(bindings):
    str = ""
    for x, y in bindings.items():
        str = str + (" %s->%s " % ( x, y))
    return str

def setToString(set):
    str = ""
    for q in set:
        str = str+ "        " + quadToString(q) + "\n"
    return str

def seqToString(set):
    str = ""
    for x in set[:-1]:
        str = str + `x` + ","
    for x in set[-1:]:
        str = str+ `x`
    return str

def queueToString(queue):
    str = ""
    for item in queue:
        str = str  +  `item` + "\n"
    return str


def quadToString(q, neededToRun=[[],[],[],[]], pattern=[1,1,1,1]):
    qm=[" "," "," "," "]
    for p in ALL4:
        n = neededToRun[p]
        if n == []: qm[p]=""
        else: qm[p] = "(" + `n`[1:-1] + ")"
        if pattern[p]==None: qm[p]=qm[p]+"?"
    return "%s%s ::  %8s%s %8s%s %8s%s." %(`q[CONTEXT]`, qm[CONTEXT],
                                            `q[SUBJ]`,qm[SUBJ],
                                            `q[PRED]`,qm[PRED],
                                            `q[OBJ]`,qm[OBJ])



def isString(x):
    # in 2.2, evidently we can test for isinstance(types.StringTypes)
    #    --- but on some releases, we need to say tuple(types.StringTypes)
    return type(x) is type('') or type(x) is type(u'')

#####################  Register this module

from myStore import setStoreClass
setStoreClass(RDFStore)

#ends

