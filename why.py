#! /usr/bin/python
"""
$Id$

A class for storing the reason why something is known.
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
reason=Namespace("http://www.w3.org/2000/10/swap/reason#")

class Reason:
    """The Reason class holds a reason for beieving or doing something.
    Well, its subclasses actually do hold data.  This class should not be used itself
    to make instances.  Reasons may be given to any functions which put data into stores,
    is tracking or proof/explanation generation may be required"""
    def __init__(self):
	self.me = None
	return

    def explain(self, ko):
	"""Describe this reason to an RDF store
	Returns the value of this object as interned in the store.
	"""
	if self.me == None:
	    self.me = ko.bNode()
	return self.me

class Because(Reason):
    """For the reason given on the string.
    
    A nested reason can also be given.
    """
    def __init__(self, str, because=None):
	Reason.__init__(self)
	self._string = str
	self._reason = because
	return

    def explain(self, ko):
	"""Describe this reason to an RDF store
	Returns the value of this object as interned in the store.
	"""
	if self.me == None:
	    self.me = ko.newBlankNode()
	ko.add(subj=self.me, pred=rdf.type, obj=reason.Parsing)
	ko.add(subj=self.me, pred=reason.comment, obj=ko.store._fromPython(ko, self._string))
	return self.me

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
	if self.me == None:
	    self.me = ko.newBlankNode()	
	    ko.add(subj=self.me, pred=rdf.type, obj=reason.Inference) 
	for var, val in self._bindings:
	    b = ko.newBlankNode()
	    ko.add(subj=self.me, pred=reason.binding, obj=b)
	    ko.add(subj=b, pred=reason.variable, obj=var)
	    ko.add(subj=b, pred=reason.boundTo, obj=val)
	if self._rule.why != None:
	    si = explainStatement(self._rule, ko)
	    ko.add(subj=self.me, pred=reason.rule, obj=si)
	else:
	    progress("No reason for rule "+`self._rule`)
	for s in self._evidence:
	    if s.why != None:
		si = explainStatement(s, ko)
		ko.add(subj=self.me, pred=reason.evidence, obj=si)
	return self.me

	
class BecauseOfData(Because):
    """Directly from data in the resource whose URI is the string.
    
    A nested reason can also be given.
    """
    pass

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
# Routine extending class Formula (how do in Python?)
#
def explanation(self, ko=None):
    """Produce a justification for this formula into the output formula
    
    Creates an output formula if necessary.
    returns it.
    (This is different from the reason.explain(ko) which returns the reason)"""
    if ko == None: ko = self.store.newFormula()
    qed = ko.newBlankNode()
    ko.add(subj=ko, pred=reason.proves, obj=self) 
    ko.add(subj=ko, pred=reason.because, obj=qed) 
    ko.add(subj=qed, pred=rdf.type, obj=reason.Conjunction) 
    ko.add(subj=qed, pred=reason.gives, obj=self) 
    for s in self.statements:
	si = explainStatement(s,  ko)
	if si == None:
	    progress("ooops .. no explain for statement", s)
	    continue
	ko.add(subj=qed, pred=reason.given, obj=si)
    return ko


def explainStatement(s, ko):
    """Explain a statement.
    
    Returns the statement as a formula, having explained that statement."""
    r = s.why
    if r != None:
	statementAsFormula = s.asFormula(ko.store)
	ri = r.explain(ko)
	ko.add(subj=ri, pred=reason.gives, obj=statementAsFormula)
	return statementAsFormula
    else:
	progress("Statement has no reason recorded "+`s`)
	return None


# ends
