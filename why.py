#! /usr/bin/python
"""
$Id$

A class for storing the reason why something is known.
The dontAsk constant reason is used as a reason for the explanations themselves- we could make
it more complicated here for the recursively minded but i don't see the need at the moment.
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
from thing   import Namespace

from diag import verbosity, progress

from RDFSink import CONTEXT, PRED, SUBJ, OBJ, PARTS, ALL4
from RDFSink import FORMULA, LITERAL, ANONYMOUS, SYMBOL
from RDFSink import Logic_NS


rdf=Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
log=Namespace("http://www.w3.org/2000/10/swap/log#")
reason=Namespace("http://www.w3.org/2000/10/swap/reason#")


global dontAsk

class Reason:
    """The Reason class holds a reason for having some information.
    Well, its subclasses actually do hold data.  This class should not be used itself
    to make instances.  Reasons may be given to any functions which put data into stores,
    is tracking or proof/explanation generation may be required"""
    def __init__(self):
	self.me = {}
	return


    def meIn(self, ko):
	"The representation of this object in the formula ko"
	me = self.me.get(ko, None)
	if me == None:
	    me = ko.newBlankNode(why= dontAsk)	   # @@@ ko - specific, not reentrant
	    self.me[ko] = me
	return me

    def explain(self, ko):
	"""Describe this reason to an RDF store
	Returns the value of this object as interned in the store.
	"""
	raise RuntimeErrot("What, no explain method for this class?")

class Because(Reason):
    """For the reason given on the string.
    This is a kinda end of the road reason. Try to make a more useful one up! ;-)
    
    A nested reason can also be given.
    """
    def __init__(self, str, because=None):
	Reason.__init__(self)
	self._string = str
	self._reason = because
	return

    def explain(self, ko):
	"""Describe this reason to an RDF store
	Returns the value of this reason as interned in the store.
	"""
	me = self.meIn(ko)
	ko.add(subj=me, pred=rdf.type, obj=reason.Parsing, why=dontAsk)
	ko.add(subj=me, pred=reason.comment, obj=ko.store._fromPython(ko, self._string), why=dontAsk)
	return me

dontAsk = Because("Generating explanation")

class BecauseOfRule(Reason):
    def __init__(self, rule, bindings, evidence, because=None):
	Reason.__init__(self)
	self._bindings = bindings
	self._rule = rule
	self._evidence = evidence # Set of statements etc to justify LHS
	self._reason = because
	return

    def explain(self, ko):
	"""Describe this reason to an RDF store
	Returns the value of this reason as interned in the store.
	"""
	me = self.meIn(ko)
	ko.add(subj=me, pred=rdf.type, obj=reason.Inference, why=dontAsk) 
	for var, val in self._bindings:
	    b = ko.newBlankNode(why= dontAsk)
	    ko.add(subj=me, pred=reason.binding, obj=b, why= dontAsk)
	    ko.add(subj=b, pred=reason.variable, obj=var,why= dontAsk)
	    ko.add(subj=b, pred=reason.boundTo, obj=val, why= dontAsk)
	if self._rule.why != None:
	    si = explainStatement(self._rule, ko)
	    ko.add(subj=me, pred=reason.rule, obj=si, why= dontAsk)
	else:
	    progress("No reason for rule "+`self._rule`)
	for s in self._evidence:
	    if s.why != None:
		si = explainStatement(s, ko)
		ko.add(subj=me, pred=reason.given, obj=si, why= dontAsk)
	return me

	
class BecauseOfData(Because):
    """Directly from data in the resource whose URI is the string.
    
    A nested reason can also be given, for why this resource was parsed.
    """
    pass

    def __init__(self, source, because=None):
	Reason.__init__(self)
	self._source = source
	self._reason = because
	return

    def explain(self, ko):
	"""Describe this reason to an RDF store
	Returns the value of this reason as interned in the store.
	"""
	me = self.meIn(ko)
	ko.add(subj=me, pred=rdf.type, obj=reason.Parsing, why=dontAsk)
	ko.add(subj=me, pred=reason.source, obj=self._source, why=dontAsk)
	return me


class BecauseOfCommandLine(Because):
    """Becase the command line given in the string"""
    pass
    
class BecauseBuiltIn(Reason):
    """Because the built-in function given concluded so.
    A nested reason for running the function can also be given"""
    def __init__(self, subj, pred, obj, because=None):
	Reason.__init__(self)
	self._subject = subj
	self._predicate = pred
	self._object = obj
	self._reason = because
	
###################################### Explanations of things
#
# Routine extending class Formula (how to extend a class in Python?)
# 
#
def explanation(self, ko=None):
    """Produce a justification for this formula into the output formula
    
    Creates an output formula if necessary.
    returns it.
    (NB: This is different from reason.explain(ko) which returns the reason)"""
    if ko == None: ko = self.store.newFormula()
    qed = ko.newBlankNode(why= dontAsk)
#    ko.add(subj=ko, pred=reason.proves, obj=self, why=dontAsk) 
#   ko.add(obj=ko, pred=reason.proof, subj=self, why=dontAsk) 
    ko.add(subj=self, pred=reason.because, obj=qed, why=dontAsk) 
    ko.add(subj=qed, pred=rdf.type, obj=reason.Conjunction, why=dontAsk) 
#    ko.add(subj=qed, pred=reason.gives, obj=self, why=dontAsk)
    ko.add(obj=qed, pred=reason.because, subj=self, why=dontAsk)


    for s in self.statements:
	if s[PRED] is not self.store.forAll and s[PRED] is not self.store.forSome:
	    si = explainStatement(s,  ko)
	    if si == None:
		progress("ooops .. no explain for statement", s)
		continue
	    ko.add(subj=qed, pred=reason.given, obj=si, why=dontAsk)
    return ko


def explainStatement(s, ko):
    """Explain a statement.
    
    Returns the statement as a formula, having explained that statement."""
    r = s.why
    if r != None:
	statementAsFormula = asFormula(s, ko.store)
	ri = r.explain(ko)
#	ko.add(subj=ri, pred=reason.gives, obj=statementAsFormula, why=dontAsk)
	ko.add( subj=statementAsFormula, pred=reason.because,  obj=ri, why=dontAsk)
	return statementAsFormula
    else:
	progress("Statement has no reason recorded "+`s`)
	return None

def asFormula(self, store):
    """The formula which contains only a statement like this.
    
    This extends the StoredStatement class with functionality we only need with who module."""
    statementAsFormula = store.newFormula()   # @@@CAN WE DO THIS BY CLEVER SUBCLASSING? statement subclass of f?
    statementAsFormula.add(subj=self[SUBJ], pred=self[PRED], obj=self[OBJ], why=dontAsk)
    kb = self[CONTEXT]
    uu = store.occurringIn(statementAsFormula, kb.universals())
    ee = store.occurringIn(statementAsFormula, kb.existentials())
    for v in uu:
	statementAsFormula.add(subj= statementAsFormula, pred=log.forAll, obj=v, why=dontAsk)
    for v in ee:
	statementAsFormula.add(subj= statementAsFormula, pred=log.forSome, obj=v, why=dontAsk)
    return statementAsFormula.close()  # probably slow - much slower than statement subclass of formula



# ends
