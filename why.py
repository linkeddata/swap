#! /usr/bin/python
"""
$Id$

A class for storing the reason why something is known.
The dontAsk constant reason is used as a reason for the explanations themselves- we could make
it more complicated here for the recursively minded but i don't see the need at the moment.

Assumes wwe are using the process-glbal store -- uses Namespace() @@@
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
from myStore  import Namespace

from diag import verbosity, progress

#from RDFSink import CONTEXT, PRED, SUBJ, OBJ, PARTS, ALL4
#from RDFSink import FORMULA, LITERAL, ANONYMOUS, SYMBOL
from RDFSink import runNamespace


rdf=Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
log=Namespace("http://www.w3.org/2000/10/swap/log#")
reason=Namespace("http://www.w3.org/2000/10/swap/reason#")


global 	dontAsk
global	proofOf
proofOf = {} # Track reasons for formulae

# origin = {}   # track (statement, formula) to reason

def report(s, why):
    """Report a new statement to the reason tracking software
    
    See the FormulaReason class"""
    context, pred, subj, obj = s.quad
    if (context.collector != None):
	context.collector.newStatement(s, why)


#    global origin
#    x = origin.get(s, [])
#    x.append(why)

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
	

	
class FormulaReason(Reason):
    """A Formula reason reproduces the information in a formula
    but includes reason information.  There is a link each way (formula,
    collector) with the actual formula. Beware that when a new formula is
    interned, the collector must be informed that its identity has changed.
    The collector is also informed of each statement added."""
    def __init__(self, formula=None):
	Reason.__init__(self)
	self._string = str
#	self._reason = because
	self.statementReasons = []
	self.formula = formula
	if formula != None:
	    formula.collector = self
	    self.setFormula(formula)
	self.reasonForStatement = {}
	return

    def setFormula(self, formula):
	"""Change the address fo the formula when the formula is moved on close()"""
	global proofOf
	self.store = formula.store
	proofOf[formula] = self
	progress("@@@@@@@ Proof of %s is %s"%(formula, self))
	return

    def	newStatement(self, s, why):
	if verbosity() > 80: progress("Believing %s because of %s"%(s, why))
	self.statementReasons.append((s, why)) # @@@ redundant
	self.reasonForStatement[s]=why

    def explanation(self, ko=None):
	"""Produce a justification for this formula into the output formula
	
	Creates an output formula if necessary.
	returns it.
	(NB: This is different from reason.explain(ko) which returns the reason)"""
	if ko == None: ko = self.formula.store.newFormula()
	ko.bind("n3", "http://www.w3.org/2000/10/swap/reify#")
	ko.bind("log", "http://www.w3.org/2000/10/swap/log#")
	ko.bind("reason", "http://www.w3.org/2000/10/swap/reason#")
	ko.bind("run", runNamespace())
	me=self.explain(ko)
	ko.add(me, rdf.type, reason.Proof, why=dontAsk)
	return ko
	
    def explain(self, ko):
    	me = self.meIn(ko)

	qed = ko.newBlankNode(why= dontAsk)
#        ko.add(subj=ko, pred=reason.prooves, obj=self.formula, why=dontAsk) 
    #   ko.add(obj=ko, pred=reason.proof, subj=self.formula, why=dontAsk) 
#	ko.add(subj=self.formula, pred=rdf.type, obj=reason.QED, why=dontAsk) 
#	ko.add(subj=self.formula, pred=reason.because, obj=qed, why=dontAsk) 
	ko.add(subj=me, pred=rdf.type, obj=reason.Conjunction, why=dontAsk) 
        ko.add(subj=me, pred=reason.gives, obj=self.formula, why=dontAsk)
#	ko.add(obj=qed, pred=reason.because, subj=self.formula, why=dontAsk)
    

	# Needed? u and e
	for u in self.formula.universals():
	    ko.add(me, reason.universal, u.uriref() , why=dontAsk) # ko.newLiteral(u.uriref())

	for e in self.formula.existentials():
	    ko.add(me, reason.existential, e.uriref(), why=dontAsk)

	for s, rea in self.statementReasons:
	    pred = s.predicate()
	    if pred is not self.store.forAll and pred is not self.store.forSome:
		si = describeStatement(s, ko)
		ko.add(si, rdf.type, reason.Extraction, why=dontAsk)
		ko.add(si, reason.because, rea.explain(ko), why=dontAsk)
		ko.add(me, reason.component, si, why=dontAsk)
	return me

class BecauseMerge(FormulaReason):
    """Because this formula is a merging of others"""
    def __init__(self, f, set):
	FormulaReason.__init__(self, f)
	self.fodder = set

class BecauseSubexpression(Reason):
    pass

becauseSubexpression = BecauseSubexpression()



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
	ko.add(subj=me, pred=reason.comment, obj=ko.newLiteral(self._string), why=dontAsk)
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
	    ko.add(subj=b, pred=reason.variable, obj=var.reification(ko, why= dontAsk),why= dontAsk)
	    ko.add(subj=b, pred=reason.boundTo, obj=val.reification(ko, why= dontAsk), why= dontAsk)
	ru = explainStatement(self._rule,ko)
	ko.add(subj=me, pred=reason.rule, obj=ru, why=dontAsk)
	    
	for s in self._evidence:
	    if isinstance(s, BecauseBuiltIn):
		e = s.explain(ko)
		ko.add(subj=me, pred=reason.evidence, obj=e, why= dontAsk)
	    else:
		e = explainStatement(s, ko)
		ko.add(me, reason.evidence, e, why= dontAsk)

	return me



def explainStatement(s, ko):
    si = describeStatement(s, ko)

    f = s.context()
    statementFormulaReason = proofOf.get(f, None)

#    if statementFormulaReason == None:
#	statementFormulaReason = f.collector  # try  that - works for subformulae? @@@ no
    if statementFormulaReason == None:
	raise RuntimeError(
	"Ooops, only have proofs for %s.\n No proof for formula %s needed for statement %s\n%s\n" 
				% (proofOf,f,s, f.debugString()))

	pass
    else:
	statementReason = statementFormulaReason.reasonForStatement.get(s, None)
	if statementReason == None:
	    progress("Ooops, formula has no reason for statement,", s)
	    raise RuntimeError("see above")
	    return None
	ri = statementReason.explain(ko)
	ko.add(subj=si, pred=reason.because, obj=ri, why=dontAsk)
    return si

def describeStatement(s, ko):
	"Describe the statement into the output formula ko"
	si = ko.newBlankNode(why=dontAsk)
	ko.add(si, rdf.type, reason.Extraction, why=dontAsk)
	ko.add(si, reason.gives, s.asFormula(why=dontAsk), why=dontAsk)

#	con, pred, subj, obj = s.quad
#	ko.add(subj=si, pred=reason.subj, obj=subj.uriref(), why=dontAsk)
#	ko.add(subj=si, pred=reason.pred, obj=pred.uriref(), why=dontAsk)
#	ko.add(subj=si, pred=reason.obj, obj=obj.uriref(), why=dontAsk)
	return si

	

	
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
    
class BecauseOfExperience(Because):
    """Becase the command line given in the string"""
    pass
    
class BecauseBuiltIn(Reason):
    """Because the built-in function given concluded so.
    A nested reason for running the function can also be given"""
    def __init__(self, subj, pred, obj, proof):
	Reason.__init__(self)
	self._subject = subj
	self._predicate = pred
	self._object = obj
	self._proof = None
	if len(proof)>0:
	    self._proof = proof[0]
	
    def explain(self, ko):
	"This is just a plain fact - or was at the time."
	me = self.meIn(ko)
	fact = ko.newFormula()
	fact.add(subj=self._subject, pred=self._predicate, obj=self._object, why=dontAsk)
	fact = fact.close()
	ko.add(me, rdf.type, reason.Fact, why=dontAsk)
	ko.add(me, reason.gives, fact, why=dontAsk)
	if self._proof != None:
	    ko.add(me, reason.proof, self._proof.explain(ko), why=dontAsk)
	return me

###################################### Explanations of things
#
# Routine extending class Formula (how to extend a class in Python?)
# 
#



# ends
