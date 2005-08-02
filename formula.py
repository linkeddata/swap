#! /usr/bin/python
"""

$Id$

Formula
See:  http://www.w3.org/DesignIssues/Notation3

Interfaces
==========

The store stores many formulae, where one formula is what in
straight RDF implementations is known as a "triple store".
So look at the Formula class for a triple store interface.

See also for comparison, a python RDF API for the Redland library (in C):
   http://www.redland.opensource.ac.uk/docs/api/index.html 
and the redfoot/rdflib interface, a python RDF API:
   http://rdflib.net/latest/doc/triple_store.html

"""

reifyNS = 'http://www.w3.org/2004/06/rei#'
owlOneOf = 'http://www.w3.org/2002/07/owl#oneOf'

from __future__ import generators

import types
import string
import re
import StringIO
import sys
import time
import uripath

from OrderedSequence import merge

from set_importer import Set, ImmutableSet

import urllib # for log:content
import md5, binascii  # for building md5 URIs

import notation3    # N3 parsers and generators, and RDF generator
# import sax2rdf      # RDF1.0 syntax parser to N3 RDF stream

import diag  # problems importing the tracking flag, must be explicit it seems diag.tracking
from diag import progress, verbosity, tracking
from term import BuiltIn, LightBuiltIn, \
    HeavyBuiltIn, Function, ReverseFunction, \
    Literal, AnonymousNode , AnonymousExistential, AnonymousUniversal, \
    Symbol, Fragment, FragmentNil,  Term, CompoundTerm, List, EmptyList, NonEmptyList

from RDFSink import Logic_NS, RDFSink, forSomeSym, forAllSym
from RDFSink import CONTEXT, PRED, SUBJ, OBJ, PARTS, ALL4
from RDFSink import N3_nil, N3_first, N3_rest, OWL_NS, N3_Empty, N3_List, List_NS
from RDFSink import RDF_NS_URI
from RDFSink import RDF_type_URI
from RDFSink import FORMULA, LITERAL, ANONYMOUS, SYMBOL



cvsRevision = "$Revision$"

# Magic resources we know about


from why import Because, BecauseBuiltIn, BecauseOfRule, \
    BecauseOfExperience, becauseSubexpression, BecauseMerge ,report



		

###################################### Forumula
#
# A Formula is a set of triples.

class Formula(AnonymousNode, CompoundTerm):
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
    def __init__(self, store, uri=None):
        AnonymousNode.__init__(self, store, uri)
        self.canonical = None # Set to self if this has been canonicalized
	self.statements = []
	self._existentialVariables = Set()
	self._universalVariables = Set()
	self.stayOpen = 0   # If set, works as a knowledegbase, never canonicalized.

    def __repr__(self):
	if self.statements == []:
	    return "{}"
	if len(self.statements) == 1:
	    st = self.statements[0]
	    return "{"+`st[SUBJ]`+" "+`st[PRED]`+" "+`st[OBJ]`+"}"

	s = Term.__repr__(self)
	return "{%i}" % len(self.statements)
	
    def classOrder(self):
	return	11  # Put at the end of a listing because it makes it easier to read

    def compareTerm(self, other):
	"Assume is also a Formula - see function compareTerm below"
	for f in self, other:
	    if f.canonical is not f:
		progress("@@@@@ Comparing formula NOT canonical", `f`)
	s = self.statements
	o = other.statements
	ls = len(s)
	lo = len(o)
	if ls > lo: return 1
	if ls < lo: return -1

	for se, oe, in  ((list(self.universals()), list(other.universals())),
			    (list(self.existentials()), list(other.existentials()))
			):
	    lse = len(se)
	    loe = len(oe)
	    if lse > loe: return 1
	    if lse < loe: return -1
	    se.sort(Term.compareAnyTerm)
	    oe.sort(Term.compareAnyTerm)
	    for i in range(lse):
		diff = se[i].compareAnyTerm(oe[i])
		if diff != 0: return diff

#		@@@@ No need - canonical formulae are always sorted
	s.sort(StoredStatement.compareSubjPredObj) # forumulae are all the same
	o.sort(StoredStatement.compareSubjPredObj)
	for i in range(ls):
	    diff = s[i].compareSubjPredObj(o[i])
	    if diff != 0: return diff
	raise RuntimeError("Identical formulae not interned! Length %i: %s\n\t%s\n vs\t%s" % (
		    ls, `s`, self.debugString(), other.debugString()))


    def existentials(self):
        """Return a list of existential variables with this formula as scope.
	
	Implementation:
	we may move to an internal storage rather than these pseudo-statements"""
        return self._existentialVariables


    def universals(self):
        """Return a list of variables universally quantified with this formula as scope.

	Implementation:
	We may move to an internal storage rather than these statements."""
	return self._universalVariables
    
    def variables(self):
        """Return a list of all variables quantified within this scope."""
        return self.existentials() | self.universals()
	
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

    def newList(self, list):
	return self.store.nil.newList(list)

    def newLiteral(self, str, dt=None, lang=None):
	"""Create or reuse the internal representation of the RDF literal whose string is given
	
	The literal is created in the same store as the formula."""
	return self.store.newLiteral(str, dt, lang)

    def intern(self, value):
	return self.store.intern(value)
	
    def newBlankNode(self, uri=None, why=None):
	"""Create a new unnamed node with this formula as context.
	
	The URI is typically omitted, and the system will make up an internal idnetifier.
        If given is used as the (arbitrary) internal identifier of the node."""
	x = AnonymousExistential(self, uri)
	self._existentialVariables.add(x)
	return x

    
    def declareUniversal(self, v):
	if verbosity() > 90: progress("Declare universal:", v)
	if v not in self._universalVariables:
	    self._universalVariables.add(v)
	
    def declareExistential(self, v):
	if verbosity() > 90: progress("Declare existential:", v)
	if v not in self._existentialVariables:  # Takes time
	    self._existentialVariables.add(v)
#	else:
#	    raise RuntimeError("Redeclared %s in %s -- trying to erase that" %(v, self)) 
	
    def newExistential(self, uri=None, why=None):
	"""Create a named variable existentially qualified within this formula
	
	If the URI is not given, an arbitrary identifier is generated.
	See also: existentials()."""
	if uri == None:
	    raise RuntimeError("Please use newBlankNode with no URI")
	    return self.newBlankNode()  # Please ask for a bnode next time
	return self.store.newExistential(self, uri, why=why)
    
    def newUniversal(self, uri=None, why=None):
	"""Create a named variable universally qualified within this formula
	
	If the URI is not given, an arbitrary identifier is generated.
	See also: universals()"""
	x = AnonymousUniversal(self, uri)
	self._universalVariables.add(x)
	return x

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
        for s in self.statements:
	    if ((pred == None or pred is s.predciate()) and
		    (subj == None or subj is s.subject()) and
		    (obj == None or obj is s.object())):
		yield s

    def contains(self, pred=None, subj=None, obj=None):
        """Return boolean true iff formula contains statement(s) matching the parts given
	
	For example:
	if f.contains(pred=pantoneColor):
	    print "We've got one statement about something being some color"
	"""
        for s in self.statements:
	    if ((pred == None or pred is s.predciate()) and
		    (subj == None or subj is s.subject()) and
		    (obj == None or obj is s.object())):
		return 1
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
        for s in self.statements:
	    if ((pred == None or pred is s.predicate()) and
		    (subj == None or subj is s.subject()) and
		    (obj == None or obj is s.object())):
		break
	else: return None
	if obj == None: return s.object()
	if subj == None: return s.subject()
	if pred == None: return s.predicate()
	raise ValueError("You must give one wildcard in (%s, %s, %s)" %(subj, pred, obj))


    def the(self, subj=None, pred=None, obj=None):
        """Return None or the value filing the blank in the called parameters
	
	This is just like any() except it checks that there is only
	one answer in the store. It wise to use this when you expect only one.
	
	color = f.the(pred=pantoneColor, subj=myCar)
	redCar = f.the(pred=pantoneColor, obj=red)
	"""
	return self.any(subj, pred, obj) # @@check >1

    def each(self, subj=None, pred=None, obj=None):
        """Return a list of values value filing the blank in the called parameters
	
	Examples:
	colors = f.each(pred=pantoneColor, subj=myCar)
	
	for redthing in f.each(pred=pantoneColor, obj=red): ...
	
	"""
        for s in self.statements:
	    if ((pred == None or pred is s.predicate()) and
		    (subj == None or subj is s.subject()) and
		    (obj == None or obj is s.object())):
		if pred == None: yield s.predicate()
		elif subj == None: yield s.subject()
		elif obj == None: yield s.object()
		else: raise ValueError(
		  "You must give one wildcard in (%s, %s, %s)" %(subj, pred, obj))

    def searchable(self, subj=None, pred=None, obj=None):
	"""A pair of the difficulty of searching and a statement iterator of found statements
	
	The difficulty is a store-portable measure of how long the store
	thinks (in arbitrary units) it will take to search.
	This will only be used for choisng which part of the query to search first.
	If it is 0 there is no solution to the query, we know now.
	
	In this implementation, we use the length of the sequence to be searched."""
	difficulty = 1
	for p in subj, pred, obj:
	    if p == None:
		difficulty += 1
	return difficulty, self.statementsMatching(subj, pred, obj) # use lazy eval here


    def substitution(self, bindings, why=None):
	"Return this or a version of me with subsitution made"
	assert type(bindings) is type({})
	store = self.store
	oc = self.occurringIn(bindings.keys())
	if oc == Set(): return self # phew!

	y = store.newFormula()
	if verbosity() > 90: progress("substitution: formula"+`self`+" becomes new "+`y`,
				    " because of ", oc)
	y.loadFormulaWithSubstitution(self, bindings, why=why)
	return y.canonicalize()

    def loadFormulaWithSubstitution(self, old, bindings={}, why=None):
	"""Load information from another formula, subsituting as we go
	returns number of statements added (roughly)"""
        total = 0
        subWhy=Because('I said so')
	for v in old.universals():
	    self.declareUniversal(bindings.get(v, v))
	for v in old.existentials():
	    self.declareExistential(bindings.get(v, v))
	bindings2 = bindings.copy()
	bindings2[old] = self
        for s in old.statements[:] :   # Copy list!
	    total += self.add(subj=s[SUBJ].substitution(bindings2, why=subWhy),
		    pred=s[PRED].substitution(bindings2, why=subWhy),
		    obj=s[OBJ].substitution(bindings2, why=subWhy),
		    why=why)
        return total
                
    def substituteEquals(self, bindings, newBindings):
	"""Return this or a version of me with subsitution made
	
	Subsitution of = for = does NOT happen inside a formula,
	as the formula is a form of quotation."""
	return self

    def occurringIn(self, vars):
	"Which variables in the list occur in this?"
	set = Set()
	if verbosity() > 98: progress("----occuringIn: ", `self`)
	for s in self.statements:
	    for p in PRED, SUBJ, OBJ:
		y = s[p]
		if y is self:
		    pass
		else:
		    set = set | y.occurringIn(vars)
	return set

    def unify(self, other, vars, existentials, bindings):
	"""See Term.unify()
	"""

	if not isinstance(other, Formula): return 0
	if self is other: return [({}, None)]
	if (len(self) != len(other)
	    or self. _existentialVariables != other._existentialVariables
	    or self. _universalVariables != other._existentialVariables
	    ): return 0
#	raise RuntimeError("Not implemented unification method on formulae")
	return 0    # @@@@@@@   FINISH THIS
	
		    

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
        if self.canonical != None:
            raise RuntimeError("Attempt to add statement to canonical formula "+`self`)

        self.store.size += 1

        s = StoredStatement((self, pred, subj, obj))
	
        self.statements.append(s)
       
        return 1  # One statement has been added  @@ ignore closure extras from closure
		    # Obsolete this return value? @@@ 
    
    def removeStatement(self, s):
	"""Removes a statement The formula must be open.
	
	This implementation is alas slow, as removal of items from tha hash is slow.
	"""
        assert self.canonical == None, "Cannot remove statement from canonical "+`self`
	self.store.size = self.store.size-1
        self.statements.remove(s)
	return
    
    def close(self):
        """No more to add. Please return interned value.
	NOTE You must now use the interned one, not the original!"""
        return self.canonicalize()

    def canonicalize(F):
        """If this formula already exists, return the master version.
        If not, record this one and return it.
        Call this when the formula is in its final form, with all its statements.
        Make sure no one else has a copy of the pointer to the smushed one.
	 
	LIMITATION: The basic Formula class does NOT canonicalize. So
	it won't spot idenical formulae. The IndexedFormula will.
        """
	store = F.store
	if F.canonical != None:
            if verbosity() > 70:
                progress("Canonicalize -- @@ already canonical:"+`F`)
            return F.canonical
	# @@@@@@@@ no canonicalization @@ warning
	F.canonical = F
	return F


    def n3String(self, base=None, flags=""):
        "Dump the formula to an absolute string in N3"
        buffer=StringIO.StringIO()
        _outSink = notation3.ToN3(buffer.write,
                                      quiet=1, base=base, flags=flags)
        self.store.dumpNested(self, _outSink)
        return buffer.getvalue().decode('utf_8')

    def rdfString(self, base=None, flags=""):
        "Dump the formula to an absolute string in RDF/XML"
        buffer=StringIO.StringIO()
        import toXML
        _outURI = 'http://example.com/'
        _outSink = toXML.ToRDF(buffer, _outURI, base=base, flags=flags)
        self.store.dumpNested(self, _outSink)
        return buffer.getvalue()

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

    def reopen(self):
	"""Make a formula which was once closed oopen for input again.
	
	NOT Recommended.  Dangers: this formula will be, because of interning,
	the same objet as a formula used elsewhere which happens to have the same content.
	You mess with this one, you mess with that one.
	Much better to keep teh formula open until you don't needed it open any more.
	The trouble is, the parsers close it at the moment automatically. To be fixed."""
        return self.store.reopen(self)


    def includes(f, g, _variables=[],  bindings=[]):
	"""Does this formula include the information in the other?
	
	bindings is for use within a query.
	"""
	return  f.store.testIncludes(f, g, _variables=_variables,  bindings=bindings)

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



    def doesNodeAppear(self, symbol):
        """Does that particular node appear anywhere in this formula

        This function is necessarily recursive, and is useful for the pretty printer
        It will also be useful for the flattener, when we write it.
        """
        for quad in self.statements:
            for s in PRED, SUBJ, OBJ:
                val = 0
                if isinstance(quad[s], CompoundTerm):
                    val = val or quad[s].doesNodeAppear(symbol)
                elif quad[s] == symbol:
                    val = 1
                else:
                    pass
                if val == 1:
                    return 1
        return 0


#################################################################################


class StoredStatement:
    """A statememnt as an element of a formula
    """
    def __init__(self, q):
        self.quad = q

    def __getitem__(self, i):   # So that we can index the stored thing directly
        return self.quad[i]

    def __repr__(self):
        return "{"+`self[CONTEXT]`+":: "+`self[SUBJ]`+" "+`self[PRED]`+" "+`self[OBJ]`+"}"

#   The order of statements is only for canonical output
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
                return s.compareAnyTerm(o)
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
                return s.compareAnyTerm(o)
        return 0


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

    def spo(self):
	return (self.quad[SUBJ], self.quad[PRED], self.quad[OBJ])

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
#	uu = store.occurringIn(f, c.universals())
#	ee = store.occurringIn(f, c.existentials())
	uu = f.occurringIn(c.universals())
	ee = f.occurringIn(c.existentials())
	bindings = []
	for v in uu:
	    x = f.newUniversal(v.uriref(), why=why)
	for v in ee:
	    x  = f.newExistential(v.uriref(), why=why)
	return f.close()  # probably slow - much slower than statement subclass of formula






#ends

