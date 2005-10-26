#! /usr/bin/python
"""
$Id$

A class for storing the reason why something is known.
The dontAsk constant reason is used as a reason for the explanations themselves-
 we could make it more complicated here for the recursively minded but i don't
 see the need at the moment.

Assumes wwe are using the process-global store -- uses Namespace() @@@
"""

giveForumlaArguments = 0 # How detailed do you want your proof?

import string
#import re
#import StringIO
import sys

from set_importer import Set

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
	if self.me.get(ko, None) != None:
	    raise ooops
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
	self.formula = formula
	if formula != None:
	    proofOf[formula] = self
	self.reasonForStatement = {}
	return


    def	newStatement(self, s, why):
	if verbosity() > 80: progress("Believing %s because of %s"%(s, why))
	assert why is not self
	self.reasonForStatement[s]=why

    def explanation(self, ko=None):
	"""Produce a justification for this formula into the output formula
	
	Creates an output formula if necessary.
	returns it.
	(This is different from reason.explain(ko) which returns the reason)"""

	if ko == None: ko = self.formula.store.newFormula()
	ko.bind("n3", "http://www.w3.org/2004/06/rei#")
	ko.bind("log", "http://www.w3.org/2000/10/swap/log#")
	ko.bind("pr", "http://www.w3.org/2000/10/swap/reason#")
	ko.bind("run", runNamespace())
	me=self.explain(ko)
	ko.add(me, rdf.type, reason.Proof, why=dontAsk)
	return ko
	
    def explain(self, ko):
	me = self.me.get(ko, None)
	if me != None: return me  #  Only do this once
    	me = self.meIn(ko)

	qed = ko.newBlankNode(why= dontAsk)
	ko.add(subj=me, pred=rdf.type, obj=reason.Conjunction, why=dontAsk) 
        ko.add(subj=me, pred=reason.gives, obj=self.formula, why=dontAsk)
    
	for s, rea in self.reasonForStatement.items():
            if rea is self:
                raise ValueError("Loop in reasons!", self, id(self), s)
            pred = s.predicate()
	    if diag.chatty_flag > 29: progress(
		"Explaining reason %s for %s" % (rea, s))
	    # Why is the following conditional needed to weed out log:forAll's?
            if pred is not pred.store.forAll and pred is not pred.store.forSome:
		si = describeStatement(s, ko)
		ko.add(si, rdf.type, reason.Extraction, why=dontAsk)
		ko.add(si, reason.because, rea.explain(ko), why=dontAsk)
		ko.add(me, reason.component, si, why=dontAsk)
	return me

class BecauseMerge(FormulaReason):
    """Because this formula is a merging of others"""
    def __init__(self, f, set):
	FormulaReason.__init__(self, f)
	self.fodder = Set()

    def	newStatement(self, s, why):  # Why isn't a reason here, it is the source
	if verbosity() > 80:progress("Merge: Believing %s because of merge"%(s))
	self.fodder.add(why)
	
    def explain(self, ko):
	me = self.me.get(ko, None)
	if me != None: return me  #  Only do this once
    	me = self.meIn(ko)
	qed = ko.newBlankNode(why= dontAsk)
	ko.add(subj=me, pred=rdf.type, obj=reason.Conjunction, why=dontAsk) 
        if giveForumlaArguments:
	    ko.add(subj=me, pred=reason.gives, obj=self.formula, why=dontAsk)
#	ko.add(obj=qed, pred=reason.because, subj=self.formula, why=dontAsk)
	for x in self.fodder:
	    ko.add(subj=me, pred=reason.mergeOf, obj=proofOf[x]) 
    	return me

class BecauseSubexpression(Reason):

    def explain(self, ko):
	"""Describe this reason to an RDF store
	Returns the value of this reason as interned in the store.
	"""
	me = self.me.get(ko, None)
	if me != None: return me  #  Only do this once
	me = self.meIn(ko)
	ko.add(subj=me, pred=rdf.type, obj=reason.TextExplanation, why=dontAsk)
	ko.add(subj=me, pred=reason.text, obj=ko.newLiteral("(Subexpression)"),
		    why=dontAsk)
	return me

becauseSubexpression = BecauseSubexpression()



class Because(Reason):
    """For the reason given on the string.
    This is a kinda end of the road reason.
    
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
	me = self.me.get(ko, None)
	if me != None: return me  #  Only do this once
	me = self.meIn(ko)
	ko.add(subj=me, pred=rdf.type, obj=reason.TextExplanation, why=dontAsk)
	ko.add(subj=me, pred=reason.text, obj=ko.newLiteral(self._string),
				why=dontAsk)
	return me

dontAsk = Because("Generating explanation")


class BecauseOfRule(Reason):
    def __init__(self, rule, bindings, evidence, kb, because=None):
        #print rule
        #raise Error
	Reason.__init__(self)
	self._bindings = bindings
	self._rule = rule
	self._evidence = evidence # Set of statements etc to justify LHS
	self._kb = kb # The formula the rule was trusting at base
	self._reason = because
	return


    def explain(self, ko):
	"""Describe this reason to an RDF store
	Returns the value of this reason as interned in the store.
	"""
	me = self.me.get(ko, None)
	if me != None: return me  #  Only do this once
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
		f = s.context()
		if f is self._kb: # Normal case
		    e = explainStatement(s, ko)
		    if s.predicate() is f.store.includes:
			for t in self.evidence:
			    if t.context() is s.subject():
				progress("Included statement used:" + `t`)
				ko.add(e, reason.includeEvidence,
				    explainStatement(t, ko)) 
#		else:
#		    progress("Included statement found:" + `s`)
	    ev.append(e)
	ko.add(subj=me, pred=reason.evidence, obj=ev, why= dontAsk)

	return me



def explainStatement(s, ko):
    si = describeStatement(s, ko)

    f = s.context()
    statementFormulaReason = proofOf.get(f, None)

    if statementFormulaReason == None:
	raise RuntimeError(
	"""Ooops, only have proofs for %s.
	No proof for formula %s needed for statement %s
	%s
	""" % (proofOf,f,s, f.debugString()))	
    else:
	statementReason = statementFormulaReason.reasonForStatement.get(s, None)
	if statementReason == None:
	    progress("Ooops, formula has no reason for statement,", s)
	    progress("formula is: %s" % `f.statements`)
	    progress("hash table is: %s" % 
				`statementFormulaReason.reasonForStatement`)
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
	me = self.me.get(ko, None)
	if me != None: return me  #  Only do this once
	me = self.meIn(ko)
	ko.add(subj=me, pred=rdf.type, obj=reason.Parsing, why=dontAsk)
	ko.add(subj=me, pred=reason.source, obj=self._source, why=dontAsk)
	ko.add(subj=me, pred=reason.because, obj=self._reason.explain(ko),
							why=dontAsk)
#	ko.add(subj=me, pred=reason.gives, obj=giveTerm(@@@outout formula @@)
	return me


class BecauseOfCommandLine(Because):
    """Because of the command line given in the string"""


    def explain(self, ko):
	"""Describe this reason to an RDF store
	Returns the value of this reason as interned in the store.
	"""
	me = self.me.get(ko, None)
	if me != None: return me  #  Only do this once
	me = self.meIn(ko)
	ko.add(subj=me, pred=rdf.type, obj=reason.CommandLine, why=dontAsk)
	ko.add(subj=me, pred=reason.args, obj=self._string, why=dontAsk)
	return me
    
class BecauseOfExperience(Because):
    """Becase of the experience of this agent, as described in the string"""
    pass
    
class BecauseBuiltIn(Reason):
    """Because the built-in function given concluded so.
    A nested reason for running the function must be given"""
    def __init__(self, subj, pred, obj):
	Reason.__init__(self)
	self._subject = subj
	self._predicate = pred
	self._object = obj
	
    def explain(self, ko):
	"This is just a plain fact - or was at the time."
	me = self.me.get(ko, None)
	if me != None: return me  #  Only do this once
	me = self.meIn(ko)
	fact = ko.newFormula()
	fact.add(subj=self._subject, pred=self._predicate, obj=self._object,
							why=dontAsk)
	fact = fact.close()
	ko.add(me, rdf.type, reason.Fact, why=dontAsk)
	ko.add(me, reason.gives, fact, why=dontAsk)
	if giveForumlaArguments:
	    for x in self._subject, self._object:
		proof = proofOf.get(x, None)
		if proof != None:
		    ko.add(me, reason.proof, proof.explain(ko), why=dontAsk)

#	if self._proof != None:
#	    ko.add(me, reason.proof, self._proof.explain(ko), why=dontAsk)
	return me

class BecauseIncludes(BecauseBuiltIn):
    """Because of the speific built-in log:includes"""
    pass


# ends
