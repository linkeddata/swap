#! /usr/bin/python
"""A forumla which is defined as the union (conjunction) of a set of formulae

$Id$

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

class FormulaUnion(Formula):
    """A formula of a set of RDF statements, triples.

    Variables are NOT rewritten ,must be guaranteed distinct by caller.
    """
    def __init__(self, store, uri=None):
        AnonymousNode.__init__(self, store, uri)
        self.canonical = None # Set to self if this has been canonicalized
	self.components = components
	self.statements = []
	self.universals = []
	self.existentials = []
	for f in components:
	    if f.canonical == None:
		raise RuntimeError("cannot form union of open formula %s" % f)
	    self.statements += f.statements
	    self._universalVariables += f.universals()
	    self._existentialVariables += f.existentials()

	for list in self.existentials, self.universals:
	    list.sort()
	    i = 1
	    while i  <  len(list)-1:
		if list[i] is list[i-1]: del list[i:i+1]
		else: i+=1





	
    def newBlankNode(self, uri=None, why=None):
	"""Create a new unnamed node with this formula as context.
	
	The URI is typically omitted, and the system will make up an internal idnetifier.
        If given is used as the (arbitrary) internal identifier of the node."""
	raise ValueError("Cannot make new blank node in union formula %s" % self)

    def cantDoThat(self):
	raise ValueError("Cannot do this in union formula %s" % self)
    
    def declareUniversal(self, v):
	return self.cantDoThat()
	
    def declareExistential(self, v):
	return self.cantDoThat()

    def newExistential(self, uri=None, why=None):
	return self.cantDoThat()

    def newUniversal(self, uri=None, why=None):
	return self.cantDoThat()


    def any(self, subj=None, pred=None, obj=None):
        """Return None or the value filing the blank in the called parameters.
	
	Specifiy exactly two of the arguments.
	color = f.any(pred=pantoneColor, subj=myCar)
	somethingRed = f.any(pred=pantoneColor, obj=red)
	
	Note difference from the old store.any!!
	Note SPO order not PSO.
	To aboid confusion, use named parameters.
	"""
        for x in self.components:
	    y = x.any(subj, pred, obj)
	    if x != None: return x
	return None


    def the(self, subj=None, pred=None, obj=None):
        """Return None or the value filing the blank in the called parameters
	
	This is just like any() except it checks that there is only
	one answer in the store. It wise to use this when you expect only one.
	
	color = f.the(pred=pantoneColor, subj=myCar)
	redCar = f.the(pred=pantoneColor, obj=red)
	"""
        z = []
	for x in self.components:
	    z += x.each(subj, pred, obj)
	if len(z) > 1: raise RuntimeError(
	    "More than one value of %s %s %s." %(subj, pred, obj))
	if len(z) == 0: return None
	return z[0]


    def each(self, subj=None, pred=None, obj=None):
        """Return a list of values value filing the blank in the called parameters
	
	Examples:
	colors = f.each(pred=pantoneColor, subj=myCar)
	
	for redthing in f.each(pred=pantoneColor, obj=red): ...
	
	"""
        z = []
	for x in self.components:
	    z += x.each(subj, pred, obj)
	return z


    def searchable(self, subj=None, pred=None, obj=None):
	"""A pair of the difficulty of searching and a statement iterator of found statements
	
	The difficulty is a store-portable measure of how long the store
	thinks (in arbitrary units) it will take to search.
	This will only be used for choisng which part of the query to search first.
	If it is 0 there is no solution to the query, we know now.
	
	In this implementation, we use the length of the sequence to be searched."""
	
	difficulty = 0
	for x in self.compoents:
	    difficulty += x.searchable(subj, pred, obj)
	return difficulty


    def loadFormulaWithSubsitution(self, old, bindings={}, why=None):
	return self.cantDoThat()

                
    def unify(self, other, vars, existentials, bindings):
	"""See Term.unify()
	"""

#	@@@@@
	if not isinstance(other, Formula): return 0
	if self is other: return [({}, None)]
	if (len(self) != len(other)
	    or self. _existentialVariables != other._existentialVariables
	    or self. _universalVariables != other._existentialVariables
	    ): return 0
	raise RuntimeError("Not implemented unification method on formulae")
	return 0    # @@@@@@@   FINISH THIS
	
		    


    def add(self, subj, pred, obj, why=None):
	return self.cantDoThat()

    def removeStatement(self, s):
	return self.cantDoThat()
    
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
	return self.cantDoThat()


    def reopen(self):
	"""Make a formula which was once closed oopen for input again.
	
	NOT Recommended.  Dangers: this formula will be, because of interning,
	the same objet as a formula used elsewhere which happens to have the same content.
	You mess with this one, you mess with that one.
	Much better to keep teh formula open until you don't needed it open any more.
	The trouble is, the parsers close it at the moment automatically. To be fixed."""
	return self.cantDoThat()


#################################################################################



#ends

