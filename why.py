#! /usr/bin/python
"""
$Id$

A class for storing the reason why something is known.
The dontAsk constant reason is used as a reason for the explanations themselves-
 we could make it more complicated here for the recursively minded but i don't
 see the need at the moment.

Assumes wwe are using the process-global store -- uses Namespace() @@@
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
from term import Literal, CompoundTerm, AnonymousNode
# from formula import Formula

import diag
from diag import verbosity, progress

REIFY_NS = 'http://www.w3.org/2004/06/rei#'

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

def smushedFormula(F, G):
    """The formula F has been replaced by G"""
    progress("why: Formula %s has been replaced by %s" %(F,G))
    pF = proofOf[F]
    pG = proofOf[G]
    if F is not becauseSubexpression:
	if G is becauseSubexpression:
	    proofOf[G] = pF    # becauseSubexpression is boring
	else:
	    raise RuntimeError("Two interesting reasons for formulae %s and %s"
			%(F, G))
    del proofOf[F]


def report(s, why):
    """Report a new statement to the reason tracking software
    
    See the FormulaReason class"""
    context, pred, subj, obj = s.quad
    reason = proofOf.get(context, None)
    if reason == None: return
    return reason.newStatement(s, why)

def giveTerm(x, ko):
    if isinstance(x, (Literal, CompoundTerm)):
#	b = ko.newBlankNode(why=why)
#	ko.add(subj=b, pred=ko.newSymbol(REIFY_NS+"value"), obj=x, why=dontAsk)
	return x
    elif isinstance(x, AnonymousNode):
	b = ko.newBlankNode(why=dontAsk)
	ko.add(subj=b, pred=ko.newSymbol(REIFY_NS+"nodeId"), obj=x.uriref(),
			why=dontAsk)
	return b
    else:
	return x.reification(ko, why=dontAsk)

class Reason:
    """The Reason class holds a reason for having some information.
    Well, its subclasses actually do hold data.  This class should not be used
    itself to make instances.  Reasons may be given to any functions which put
    data into stores, is tracking or proof/explanation generation may be
    required"""
    def __init__(self):
	self.me = {}
	return


    def meIn(self, ko):
	"The representation of this object in the formula ko"
	me = self.me.get(ko, None)
	if me == None:
	    me = ko.newBlankNode(why= dontAsk)	# @@ ko, specific, not reentrant
	    self.me[ko] = me
	return me

    def explain(self, ko):
	"""Describe this reason to an RDF store
	Returns the value of this object as interned in the store.
	"""
	raise RuntimeError("What, no explain method for this class?")
	

	
class FormulaReason(Reason):
    """A Formula reason reproduces the information in a formula
    but includes reason information.  Beware that when a new formula is
    interned, the proofOf dict must be informed that its identity has changed.
    The ForumulaReason is informed of each statement added."""
    def __init__(self, formula=None):
	Reason.__init__(self)
	self._string = str
#	self._reason = because
	self.statementReasons = []
	self.formula = formula
	if formula != None:
	    self.setFormula(formula)
	self.reasonForStatement = {}
	return

    def setFormula(self, formula):
	"""Change the address fo the formula when the formula is moved on close()"""
	global proofOf
	self.store = formula.store
	proofOf[formula] = self
#	progress("@@@@@@@ Proof of %s is %s"%(formula, self))
	return

    def	newStatement(self, s, why):
	if verbosity() > 80: progress("Believing %s because of %s"%(s, why))
	assert why is not self
	self.statementReasons.append((s, why)) # @@@ redundant
	self.reasonForStatement[s]=why

    def explanation(self, ko=None):
	"""Produce a justification for this formula into the output formula
	
	Creates an output formula if necessary.
	returns it.
	(NB: This is different from reason.explain(ko) which returns the reason)"""
	if ko == None: ko = self.formula.store.newFormula()
	ko.bind("n3", "http://www.w3.org/2004/06/rei#")
	ko.bind("log", "http://www.w3.org/2000/10/swap/log#")
	ko.bind("pr", "http://www.w3.org/2000/10/swap/reason#")
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
#	for u in self.formula.universals():
#	    ko.add(me, reason.universal, u.uriref() , why=dontAsk) # ko.newLiteral(u.uriref())
#
#	for e in self.formula.existentials():
#	    ko.add(me, reason.existential, e.uriref(), why=dontAsk)
	    
        for s, rea in self.statementReasons:
            if rea is self:
                raise ValueError("Loop in reasons!", self, id(self), s)
            pred = s.predicate()
	    if diag.chatty_flag > 29: progress(
		"Explaining reason %s for %s" % (rea, s))
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

    def	newStatement(self, s, why):  # Why isn't a reason here, it is the source
	if verbosity() > 80: progress("Merge: Believing %s because of merge"%(s))
#	assert why is  self # Every statement just because this is a merge
#	self.statementReasons.append((s, why)) # @@@ redundant
#	self.reasonForStatement[s]=why

    def explain(self, ko):
    	me = self.meIn(ko)

	qed = ko.newBlankNode(why= dontAsk)
	ko.add(subj=me, pred=rdf.type, obj=reason.Conjunction, why=dontAsk) 
        ko.add(subj=me, pred=reason.gives, obj=self.formula, why=dontAsk)
	ko.add(obj=qed, pred=reason.because, subj=self.formula, why=dontAsk)
    

#	# Needed? u and e
#	for u in self.formula.universals():
#	    ko.add(me, reason.universal, u.uriref() , why=dontAsk) # ko.newLiteral(u.uriref())
#
#	for e in self.formula.existentials():
#	    ko.add(me, reason.existential, e.uriref(), why=dontAsk)
#	    
#        for s, rea in self.statementReasons:
#            if rea is self:
#                raise ValueError("Loop in reasons!", self, id(self), s)
#            pred = s.predicate()
#	    si = describeStatement(s, ko)
#	    ko.add(si, rdf.type, reason.Extraction, why=dontAsk)
#	    ko.add(si, reason.because, rea.explain(ko), why=dontAsk)
#	    ko.add(me, reason.component, si, why=dontAsk)

	return me

class BecauseSubexpression(Reason):

    def explain(self, ko):
	"""Describe this reason to an RDF store
	Returns the value of this reason as interned in the store.
	"""
	me = self.meIn(ko)
	ko.add(subj=me, pred=rdf.type, obj=reason.TextExplanation, why=dontAsk)
	ko.add(subj=me, pred=reason.text, obj=ko.newLiteral("(Subexpression)"), why=dontAsk)
	return me

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
	ko.add(subj=me, pred=rdf.type, obj=reason.TextExplanation, why=dontAsk)
	ko.add(subj=me, pred=reason.text, obj=ko.newLiteral(self._string), why=dontAsk)
	return me

dontAsk = Because("Generating explanation")


class BecauseOfRule(Reason):
    def __init__(self, rule, bindings, evidence, because=None):
        #print rule
        #raise Error
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
	for var, val in self._bindings.items():
	    b = ko.newBlankNode(why= dontAsk)
	    ko.add(subj=me, pred=reason.binding, obj=b, why= dontAsk)
	    ko.add(subj=b, pred=reason.variable,
			obj=giveTerm(var,ko),why= dontAsk)
	    ko.add(subj=b, pred=reason.boundTo,
			obj=giveTerm(val, ko), why= dontAsk)
	ru = explainStatement(self._rule,ko)
	ko.add(subj=me, pred=reason.rule, obj=ru, why=dontAsk)
	    
	ev = []  # For PML compatability we will store it as a collection
	for s in self._evidence:
	    if isinstance(s, BecauseBuiltIn):
		e = s.explain(ko)
	    else:
		e = explainStatement(s, ko)
	    ev.append(e)
	ko.add(subj=me, pred=reason.evidence, obj=ev, why= dontAsk)

	return me



def explainStatement(s, ko):
    si = describeStatement(s, ko)

    f = s.context()
    statementFormulaReason = proofOf.get(f, None)

    if statementFormulaReason == None:
	raise RuntimeError(
	"Ooops, only have proofs for %s.\n No proof for formula %s needed for statement %s\n%s\n" 
				% (proofOf,f,s, f.debugString()))

	pass
    else:
	statementReason = statementFormulaReason.reasonForStatement.get(s, None)
	if statementReason == None:
	    progress("Ooops, formula has no reason for statement,", s)
	    progress("formula is: %s" % `f.statements`)
	    progress("hash table is: %s" % `statementFormulaReason.reasonForStatement`)
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
	if because == None:
	    raise RuntimeError("Why are we doing this?")
	return

    def explain(self, ko):
	"""Describe this reason to an RDF store
	Returns the value of this reason as interned in the store.
	"""
	me = self.meIn(ko)
	ko.add(subj=me, pred=rdf.type, obj=reason.Parsing, why=dontAsk)
	ko.add(subj=me, pred=reason.source, obj=self._source, why=dontAsk)
	ko.add(subj=me, pred=reason.because, obj=self._reason.explain(ko), why=dontAsk)
#	ko.add(subj=me, pred=reason.gives, obj=giveTerm(@@@outout formula @@)
	return me


class BecauseOfCommandLine(Because):
    """Because of the command line given in the string"""


    def explain(self, ko):
	"""Describe this reason to an RDF store
	Returns the value of this reason as interned in the store.
	"""
	me = self.meIn(ko)
	ko.add(subj=me, pred=rdf.type, obj=reason.CommandLine, why=dontAsk)
	ko.add(subj=me, pred=reason.args, obj=self._string, why=dontAsk)
	return me
    
class BecauseOfExperience(Because):
    """Becase the command line given in the string"""
    pass
    
class BecauseBuiltIn(Reason):
    """Because the built-in function given concluded so.
    A nested reason for running the function must be given"""
    def __init__(self, subj, pred, obj, proof):
	Reason.__init__(self)
	self._subject = subj
	self._predicate = pred
	self._object = obj
	self._proof = proof   # Proof should be hubg on here?
	
    def explain(self, ko):
	"This is just a plain fact - or was at the time."
	me = self.meIn(ko)
	fact = ko.newFormula()
	fact.add(subj=self._subject, pred=self._predicate, obj=self._object, why=dontAsk)
	fact = fact.close()
	ko.add(me, rdf.type, reason.Fact, why=dontAsk)
	ko.add(me, reason.gives, fact, why=dontAsk)
	for x in self._subject, self._object:
	    proof = proofOf.get(x, None)
	    if proof != None:
		ko.add(me, reason.proof, proof.explain(ko), why=dontAsk)

#	if self._proof != None:
#	    ko.add(me, reason.proof, self._proof.explain(ko), why=dontAsk)
	return me



# ends
