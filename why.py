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

from RDFSink import CONTEXT, PRED, SUBJ, OBJ, PARTS, ALL4
from RDFSink import FORMULA, LITERAL, ANONYMOUS, SYMBOL
from RDFSink import Logic_NS


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
    def __init(self, str, because=None):
	Reason.__init__(self)
	self._string = str
	self._reason = because
	return

    def explain(self, ko):
	"""Describe this reason to an RDF store
	Returns the value of this object as interned in the store.
	"""
	if self.me == None:
	    self.me = ko.bNode()
	ko.add(subj=self.me, pred=reason.comment, obj=ko.fromPython(self._string))
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
	Returns the value of this object as interned in the store.
	"""
	if self.me == None:
	    self.me = ko.bNode()
	for var, val in self._bindings:
	    b = ko.bNode()
	    ko.add(subj=self.me, pred=reason.binding, obj=b)
	    ko.add(subj=b, pred=reason.variable, obj=var)
	    ko.add(subj=b, pred=reason.boundTo, obj=val)
	ko.add(subj=self.me, pred=reason.rule, obj=self._rule)
	if rule.why != None:
	    rule.why.explain(ko)
	for s in evidence:
	    ko.add(subj=self.me, pred=reason.rule, obj=self._rule)
	    if s.why != None:
		s.why.explain(ko)
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


# ends
