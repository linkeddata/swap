""" Update for cwm architecture

The update module provides for the deletion as well as the addition of information to
a formula.  This module assumed the llyn.py store.  It conects intimiately with the
query module.

2004-03-17 written as an extension of query.py
"""



import diag
from diag import chatty_flag, tracking, progress
from formula import Formula
from query import Query, Rule, seqToString, _substitute

    
def patch(workingContext, patchFormula):
    """A task of running a set of updates on a knowledge base
    
    This is simpler than an Inference task, in that a patch is only done
    once, patches cannot lead to new patches, etc.
    """
    if diag.chatty_flag >20:
	progress("New Update task, patches from %s" % patchFormula)
    store = workingContext.store

    true = store.newFormula().close()  #   {}
    universals = []
    lhs_done = []
    insertions = patchFormula.statementsMatching(pred=store.insertion)[:]
    deletions = patchFormula.statementsMatching(pred=store.deletion)[:]

    for st in insertions + deletions:
	lhs = st.subject()
	pred = st.predicate()
	if isinstance(lhs, Formula):
	    if pred == store.insertion:
		lhs_done.append(lhs)
		deletions = patchFormula.each(subj = lhs, pred=store.deletion)
		conclusion = st.object()
	    else:
		if lhs in lhs_done: continue
		deletions = [ st.object() ]
		conclusion = true

	    if lhs.universals() != []:
		raise RuntimeError("""Cannot query for universally quantified things.
		As of 2003/07/28 forAll x ...x cannot be on left hand side of rule.
		This/these were: %s\n""" % lhs.universals())
	
	    unmatched = lhs.statements[:]
	    templateExistentials = lhs.existentials()[:]
	    _substitute({lhs: workingContext}, unmatched)
	
	    variablesMentioned = lhs.occurringIn(patchFormula.universals())
	    variablesUsed = conclusion.occurringIn(variablesMentioned)
	    for x in variablesMentioned:
		if x not in variablesUsed:
		    templateExistentials.append(x)
	    if diag.chatty_flag >20:
		progress("New Patch  =========== applied to %s" %(workingContext) )
		for s in lhs.statements: progress("    ", `s`)
		progress("+=>")
		for s in conclusion.statements: progress("    ", `s`)
		progress("-=>")
		for deletion in deletions:
		    for s in deletion.statements: progress("    ", `s`)
		progress("Universals declared in outer " + seqToString(patchFormula.universals()))
		progress(" mentioned in template       " + seqToString(variablesMentioned))
		progress(" also used in conclusion     " + seqToString(variablesUsed))
		progress("Existentials in template     " + seqToString(templateExistentials))

	    q = UpdateQuery(store, 
		    unmatched = unmatched,
		    template = lhs,
		    variables = patchFormula.universals(),
		    existentials =templateExistentials,
		    workingContext = workingContext,
		    conclusion = conclusion,
		    retractions = deletions,
		    rule = st)
	    q.resolve()

	
class UpdateQuery(Query):
    "Subclass of query for doing patches onto the KB: adding and removing bits.  Aka KB Update"
    def __init__(self,
	       store,
               unmatched,           # List of statements we are trying to match CORRUPTED
	       template,		# formula
               variables,           # List of variables to match and return CORRUPTED
               existentials,        # List of variables to match to anything
                                    # Existentials or any kind of variable in subexpression
	       workingContext,
	       conclusion,	# Things to be added
	       retractions,		# Things to be deleted
	       rule):		    # The rule statement

	Query.__init__(self, store, unmatched, template, variables, existentials,
		workingContext, conclusion, targetContext = workingContext, rule=rule)
	self.retractions = retractions

    def conclude(self, bindings, evidence = []):
	"""When a match found in a query, add conclusions to target formula,
	and also remove retractions.

	Returns the number of statements added."""
	result = Query.conclude(self, bindings, evidence)
#	if result == 0: return result
	
	# delete statements
	if diag.chatty_flag > 25: progress(
	    "Insertions made, deletions will now be made. Bindings %s" % bindings)
	for retraction in self.retractions:
	    for st in retraction:
		s, p, o = st.spo()
		ss = self.workingContext.statementsMatching(
			subj = self.doSubst(s, bindings),
			pred = self.doSubst(p, bindings),
			obj = self.doSubst(o, bindings))
		if len(ss) != 1:
		    raise RuntimeError(
			"Error: %i matches removing statement {%s %s %s} from %s:\n%s" %
			 (len(ss),s,p,o,self.workingContext, ss))
		if diag.chatty_flag > 25: progress("Deleting %s" % ss[0])
		self.workingContext.removeStatement(ss[0])
	self.justOne = 1  # drop out of here when done
	return 1     # Success -- no behave as a test and drop out

    def doSubst(self, x, bindings):
	if x.generated() and x not in bindings:
	    raise ValueError("""Retractions cannot have bnodes in them.
	    Use explict variables which also occur on the LHS.
	    Found bnode: %s, bindings are: %s""" % (x, bindings))
	return bindings.get(x, x)


	     
# ends
