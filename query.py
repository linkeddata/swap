""" Query for cwm architecture

2003-09-07 split off from llyn.py
"""

from RDFSink import Logic_NS, RDFSink, forSomeSym, forAllSym
from RDFSink import CONTEXT, PRED, SUBJ, OBJ, PARTS, ALL4
from RDFSink import N3_nil, N3_first, N3_rest, OWL_NS, N3_Empty, N3_List, List_NS
from RDFSink import RDF_NS_URI

from OrderedSequence import merge, intersection, minus, indentString

import diag
from diag import chatty_flag, tracking, progress
from term import BuiltIn, LightBuiltIn, \
    HeavyBuiltIn, Function, ReverseFunction, \
    Literal, Symbol, Fragment, FragmentNil, Anonymous, Term, \
    CompoundTerm, List, EmptyList, NonEmptyList
from formula import StoredStatement, Formula
from why import Because, BecauseBuiltIn, BecauseOfRule, \
    BecauseOfExperience, becauseSubexpression, BecauseMerge ,report


import types
import sys
# from sets import Set  # only in python 2.3 and following

INFINITY = 1000000000           # @@ larger than any number occurences


# State values as follows, high value=try first:
S_UNKNOWN = 	99  # State unknown - to be [re]calculated by setup.
S_DONE =   	80  # Have exhausted all possible ways to saitsfy this item. return now.
S_LIGHT_UNS_GO= 70  # Light, not searched yet, but can run
S_LIGHT_GO =  	65  # Light, can run  Do this!
S_NOT_LIGHT =   60  # Not a light built-in, haven't searched yet.
S_LIGHT_EARLY=	50  # Light built-in, not enough constants to calculate, haven't searched yet.
S_NEED_DEEP=	45  # Can't search because of unbound compound term, could do recursive unification
S_HEAVY_READY=	40  # Heavy built-in, search done, but formula now has no vars left. Ready to run.
S_LIGHT_WAIT=	30  # Light built-in, not enough constants to calculate, search done.
S_HEAVY_WAIT=	20  # Heavy built-in, too many variables in args to calculate, search done.
S_REMOTE =	10  # Waiting for local query to be resolved as much as possible
S_SATISFIED =	 0  # Item has been staisfied, and is no longer a constraint, continue with others


def think(knowledgeBase, ruleFormula=None, mode=""):
    """Forward-chaining inference
    
    In the case in which rules are added back into the
    store. The store is used for read (normally canonical) and write
    (normally open) at the samne time.  It in fact has to be open.
    """
    if ruleFormula == None:
	ruleFormula = knowledgeBase
    assert knowledgeBase.canonical == None , "Must be open to add stuff:"+ `knowledgeBase `

    if diag.chatty_flag > 45: progress("think: rules from %s added to %s" %(knowledgeBase, ruleFormula))
    return InferenceTask(knowledgeBase, ruleFormula, mode=mode, repeat=1).run()

def applyRules(
		workingContext,    # Data we assume 
		ruleFormula = None,    # Where to find the rules
		targetContext = None):   # Where to put the conclusions
    """Once"""
    t = InferenceTask(workingContext, ruleFormula, targetContext)
    result = t.run()
    del(t)
    return result


class InferenceTask:
    """A task of applying rules or filters to information"""
    def __init__(self,
		workingContext,    # Data we assume 
		ruleFormula = None,    # Where to find the rules
		targetContext = None,   # Where to put the conclusions
		universals = [],        # Inherited from higher contexts
		mode="",		# modus operandi
		why=None,			# Trace reason for all this
		repeat = 0):		# do it until finished
	""" Apply rules in one context to the same or another
    
	A rule here is defined by log:implies, which associates the template (premise, precondidtion,
	antecedent) to the conclusion (postcondition).
        
	To verify that for all x, f(s) one can either find that asserted explicitly,
	or find an example for some specific value of x.  Here, we deliberately
	chose only to do the first.
	"""
	
	if diag.chatty_flag >20:
	    progress("New Inference task, rules from %s" % ruleFormula)
	if targetContext is None: targetContext = workingContext # return new data to store
	if ruleFormula is None: self.ruleFormula = workingContext # apply own rules
	else: self.ruleFormula = ruleFormula
	self.ruleFor = {}
	self.hasMetaRule = 0

	self.workingContext, self.targetContext, self.mode, self.repeat = workingContext, targetContext, mode, repeat
	self.store = self.workingContext.store

    def runSmart(self):
	"""Run the rules by mapping rule interactions first"""
	rules= self.ruleFor.values()
	for r1 in rules:
	    vars1 = r1.templateExistentials + r1.variablesUsed
	    for r2 in rules:
		vars2 = r2.templateExistentials + r2.variablesUsed
		for s1 in r1.conclusion.statements:
		    for s2 in r2.template.statements:
			for p in PRED, SUBJ, OBJ:
			    if ((s1[p] not in vars1
				    and not isinstance(s1[p], CompoundTerm))
				and (s2[p] not in vars2
				    and not isinstance(s2[p], CompoundTerm))
				and (s1[p] is not s2[p])):
				    break
			else:
			    r1.affects[r2] = 1 # save transfer binding here?
			    if diag.chatty_flag > 20: progress(
				"%s can affect %s because %s can trigger %s" %
					    (`r1`, `r2`, `s1`, `s2`))
			    break # can affect

		    else:  # that statement couldn't but
			if diag.chatty_flag > 96:
			    progress("...couldn't beccause of ",s1,s2,p)
			continue # try next one
		    break # can

	# Calculate transitive closure of "affects"
	for r1 in rules:
	    r1.traceForward(r1)  # could lazy eval

	for r1 in rules:
	    r1.indirectlyAffects.sort()
	    r1.indirectlyAffectedBy.sort()
	    
	# Print the affects matrix
	if diag.chatty_flag > 30:
	    str = "%4s:" % "Aff"
	    for r2 in rules:
		str+= "%4s" % `r2`
	    progress(str)
	    for r1 in rules:
		str= "%4s:" % `r1`
		for r2 in rules:
		    if r2.affects.get(r1, 0): str+= "%4s" % "X"
		    elif r1 in r2.indirectlyAffects: str +="%4s" % "-"
		    else: str+= "%4s" % " "
		progress(str)
	    
	# Find cyclic subsystems
	# These are connected sets within which you can get from any node back to itself
	pool = rules[:]
	pool.sort()  # Sorted list, can use merge, intersection, etc
	cyclics = []
	while pool:
	    r1 = pool[0]
	    if r1 not in r1.indirectlyAffects:
		cyclic = [ r1 ]
		pool.remove(r1)
	    else:
		if diag.chatty_flag > 90:
		    progress("%s indirectly affects %s and is affected by %s" %
			(r1, r1.indirectlyAffects, r1.indirectlyAffectedBy))
		cyclic = intersection(r1.indirectlyAffects, r1.indirectlyAffectedBy)
		pool = minus(pool, cyclic)
	    cyclics.append(CyclicSetOfRules(cyclic))
	    if diag.chatty_flag > 90:
		progress("New cyclic: %s" % cyclics[-1])
	    

	# Because the cyclic subsystems contain any loops, we know
	# there are no cycles between them. Therefore, there is a partial
	# ordering.  If we order them in that way, then we can resolve each
	# one just once without violating

	pool = cyclics[:]
	seq = []
	while pool:
	    cy = pool[0] #  pick random one
	    seq = partialOrdered(cy, pool) + seq

	if diag.chatty_flag > 10:
	    progress("In order:" + `seq`)

	# TEMPORARY: test that
	n = len(seq)
	for i in range(n):
	    for j in range(i-1):
		if compareCyclics(seq[i], seq[j]) < 0:
		    raise RuntimeError("Should not be:  %s < %s" %(seq[i], seq[j]))

	# Run the rules
	total = 0
	for cy in seq:
	    total += cy.run()
	if diag.chatty_flag > 9:
	    progress("Grand total %i facts found" % total)
	return total


    def run(self):
	"""Perform task.
	Return number of  new facts"""
	self.gatherRules(self.ruleFormula)
	if self.hasMetaRule or not self.repeat:
	    return self.runLaborious()
	return self.runSmart()

    def runLaborious(self):
	"""Perform task.
	Return number of  new facts.
	Start again if new rule mayhave been generated."""
	grandtotal = 0
	iterations = 0
	self.ruleFor = {}
	needToCheckForRules = 1
	while 1:
	    if needToCheckForRules:
		self.gatherRules(self.ruleFormula)
		needToCheckForRules = 0
	    _total = 0
	    iterations = iterations + 1
	    for rule in self.ruleFor.values():
		found = rule.once()
		if (diag.chatty_flag >50):
		    progress( "Laborious: Found %i new stmts on for rule %s" % (found, rule))
		_total = _total+found
		if found and (rule.meta or self.targetContext._closureMode):
		    needToCheckForRules = 1
	    if diag.chatty_flag > 5: progress(
		"Total of %i new statements on iteration %i." %
		    (_total, iterations))
	    if _total == 0: break
	    grandtotal= grandtotal + _total
	    if not self.repeat: break
	if diag.chatty_flag > 5: progress("Grand total of %i new statements in %i iterations." %
		    (grandtotal, iterations))
	return grandtotal


    def gatherRules(self, ruleFormula):
	universals = [] # @@ self.universals??
	for s in ruleFormula.statementsMatching(pred=self.store.implies):
	    r = self.ruleFor.get(s, None)
	    if r != None: continue
	    con, pred, subj, obj  = s.quad
	    if (isinstance(subj, Formula)
		and isinstance(obj, Formula)):
		v2 = universals + ruleFormula.universals() # Note new variables can be generated
		r = Rule(self, s,  v2)
		self.ruleFor[s] = r
		if r.meta: self.hasMetaRule = 1
		if (diag.chatty_flag >30):
		    progress( "Found rule %r for statement %s " % (r, s))

	for F in ruleFormula.each(pred=self.store.implies, obj=self.store.Truth): #@@ take out when --closure=T ??
	    self.gatherRules(F)  #See test/rules13.n3, test/schema-rules.n3 etc


def partialOrdered(cy1, pool):
    """Return sequence conforming to the partially order in a set of cyclic subsystems
    
    Basially, we find the dependencies of a node and remove them from the pool.
    Then, any node in the pool can be done earlier, because has no depndency from those done.
    """
    seq = []
    for r1 in cy1:   # @@ did just chose first rule cy[0], but didn't get all
	for r2 in  r1.affects:
	    if r2 not in cy1:  # An external dependency
		cy2 = r2.cycle
		if cy2 in pool:
		    seq = partialOrdered(cy2, pool) + seq
    pool.remove(cy1)
    if diag.chatty_flag > 90: progress("partial topo: %s" % `[cy1] + seq`)
    return [cy1] + seq

class CyclicSetOfRules:
    """A set of rules which are connected
    """
    def __init__(self, rules):
	self.rules = rules
	for r1 in rules:
	    r1.cycle = self

    def __getitem__(self, i):
	return self.rules[i]

    def __repr__(self):
	return `self.rules`

    def run(self):
	"Run a cyclic subset of the rules"
	if diag.chatty_flag > 20:
	    progress()
	    progress("Running cyclic system %s" % (self))
	if len(self.rules) == 1:
	    rule = self.rules[0]
	    if not rule.affects.get(rule, 0):
#		rule.already = None # Suppress recording of previous answers
		# - no, needed to remove dup bnodes as in test/includes/quant-implies.n3 --think
		# When Rule.once is smarter about not iterating over things not mentioned elsewhere,
		# can remove this.
		return rule.once()
		
	agenda = self.rules[:]
	total = 0
	for r1 in self.rules:
	    af = r1.affects.keys()
	    af.sort()
	    r1.affectsInCyclic = intersection(self.rules, af)
	while agenda:
	    rule = agenda[0]
	    agenda = agenda[1:]
	    found = rule.once()
	    if diag.chatty_flag > 20: progress("Rule %s gave %i. Affects:%s." %(
			rule, found, rule.affectsInCyclic))
	    if found:
		total = total + found
		for r2 in rule.affectsInCyclic:
		    if r2 not in agenda:
			if diag.chatty_flag > 30: progress("...rescheduling", r2)
			agenda.append(r2)
	if diag.chatty_flag > 20: progress("Cyclic subsystem exhausted")
	return total
	
    
nextRule = 0
class Rule:

    def __init__(self, task, statement, _variables,):
	"""Try a rule
	
	Beware lists are corrupted. Already list is updated if present.
	"""
	global nextRule
	self.task = task
	self.template = statement[SUBJ]
	self.conclusion = statement[OBJ]
	self.store = self.template.store
	self.statement = statement
	self.number = nextRule = nextRule+1
	self.meta = self.conclusion.contains(pred=self.conclusion.store.implies) #generate rules?
	if task.repeat: self.already = []
	else: self.already = None
	self.affects = {}
	self.indirectlyAffects = []
	self.indirectlyAffectedBy = []
	self.affectsInCyclic = []
	self.cycle = None
	
	# When the template refers to itself, the thing we are
	# are looking for will refer to the context we are searching
	# Similarly, references to the working context have to be moved into the
	# target context when the conclusion is drawn.
    
    
	if self.template.universals() != []:
	    raise RuntimeError("""Cannot query for universally quantified things.
	    As of 2003/07/28 forAll x ...x cannot be on left hand side of rule.
	    This/these were: %s\n""" % self.template.universals())
    
	self.unmatched = self.template.statements[:]
	self.templateExistentials = self.template.existentials()[:]
	_substitute({self.template: task.workingContext}, self.unmatched)
    
	variablesMentioned = self.template.occurringIn(_variables)
	self.variablesUsed = self.conclusion.occurringIn(variablesMentioned)
	for x in variablesMentioned:
	    if x not in self.variablesUsed:
		self.templateExistentials.append(x)
	if diag.chatty_flag >20:
	    progress("New Rule %s ============ looking for:" % `self` )
	    for s in self.template.statements: progress("    ", `s`)
	    progress("=>")
	    for s in self.conclusion.statements: progress("    ", `s`)
	    progress("Universals declared in outer " + seqToString(_variables))
	    progress(" mentioned in template       " + seqToString(variablesMentioned))
	    progress(" also used in conclusion     " + seqToString(self.variablesUsed))
	    progress("Existentials in template     " + seqToString(self.templateExistentials))
	return

    def once(self):
    # The smartIn context was the template context but it has been mapped to the workingContext.
	if diag.chatty_flag >20:
	    progress("Trying rule %s ===================" % self )
	    progress( setToString(self.unmatched))
	task = self.task
	query = Query(self.store,
			unmatched = self.unmatched[:],
			template = self.template,
			variables = self.variablesUsed[:],
			existentials = self.templateExistentials[:],
			workingContext = task.workingContext,
			conclusion = self.conclusion,
			targetContext = task.targetContext,
			already = self.already,
			rule = self.statement,
			smartIn = [task.workingContext],    # (...)
			meta = task.workingContext,
			mode = task.mode)
    
	total = query.resolve()
	if diag.chatty_flag > 20:
	    progress("Rule try generated %i new statements" % total)
	return total
    
    def __repr__(self):
	if self in self.affects: return "R"+`self.number`+ "*"
	return "R"+`self.number`

    def compareByAffects(other):
	if other in self.indirectlyAffects: return -1  # Do me earlier
	if other in self.indirectlyAffectedBy: return 1
	return 0
	

    def traceForward(self, r1):
	for r2 in r1.affects:
	    if r2 not in self.indirectlyAffects:
		self.indirectlyAffects.append(r2)
		r2.indirectlyAffectedBy.append(self)
		self.traceForward(r2)
#	    else:
#		self.__setattr__("leadsToCycle", 1)
    
def testIncludes(f, g, _variables=[],  bindings={}):
    """Return whether or nor f contains a top-level formula equvalent to g.
    Just a test: no bindings returned."""
    if diag.chatty_flag >30: progress("testIncludes ============")
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

    if diag.chatty_flag > 20:
	progress( "# testIncludes BUILTIN, %i terms in template %s, %i unmatched, %i template variables" % (
	    len(g.statements),
	    `g`[-8:], len(unmatched), len(templateExistentials)))
	if diag.chatty_flag > 80:
	    for v in _variables:
		progress( "    Variable: " + `v`[-8:])

    result = Query(f.store,
		unmatched=unmatched,
		template = g,
		variables=[],
		existentials=_variables + templateExistentials,
		justOne=1, mode="").resolve()

    if diag.chatty_flag >30: progress("=================== end testIncludes =" + `result`)
    return result


    


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



class Query:
    """A query holds a hypothesis/antecedent/template which is being matched aginst (unified with)
    the knowledge base."""
    def __init__(self,
	       store,
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
               smartIn = [],        # List of contexts in which to use builtins
               justOne = 0,         # Flag: Stop when you find the first one
	       mode = "rs",	    # Character flags modifying modus operandi
	    meta = None):	    # Context to check for useful info eg remote stuff

        
        if diag.chatty_flag > 50:
            progress( "Query: created with %i terms. (justone=%i)" % (len(unmatched), justOne))
            if diag.chatty_flag > 80: progress( setToString(unmatched))
	    if diag.chatty_flag > 90: progress(
		"    Smart in: ", smartIn)

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
	self.lastCheckedNumberOfRedirections = 0
        for quad in unmatched:
            item = QueryItem(self, quad)
            if item.setup(allvars=variables+existentials, unmatched=unmatched, smartIn=smartIn, mode=mode) == 0:
                if diag.chatty_flag > 80: progress("match: abandoned, no way for "+`item`)
                self.noWay = 1
		return  # save time
            self.queue.append(item)
	return
	
    def resolve(self):
	if hasattr(self, "noWay"): return 0
        return self.unify(self.queue, self.variables, self.existentials)

    def checkRedirectsInAlready(self):
	"""Kludge"""
	n = len(self.targetContext._redirections)
	if n  > self.lastCheckedNumberOfRedirections:
	    self.lastCheckedNumberOfRedirections = n
	    self.redirect(self.targetContext._redirections)
	    
    def redirect(self, redirections):
	for bindings in self.already:
	    for var, value in bindings.items():
		try:
		    x = redirections[value]
		except:
		    pass
		else:
		    if diag.chatty_flag>29: progress("Redirecting binding %r to %r" % (value, x))
		    bindings[var] = x

    def conclude(self, bindings, evidence = []):
	"""When a match found in a query, add conclusions to target formula.

	Returns the number of statements added."""
	if self.justOne: return 1   # If only a test needed

        if diag.chatty_flag >60: progress( "Concluding tentatively...%r" % bindings)
        if self.already != None:
	    self.checkRedirectsInAlready() # @@@ KLUDGE - use delegation and notification systme instead
            if bindings in self.already:
                if diag.chatty_flag > 30: progress("@@ Duplicate result: %r" %  bindings)
                return 0
            if diag.chatty_flag > 30: progress("Not duplicate: %r" % bindings)
            self.already.append(bindings)

	if tracking:
	    reason = BecauseOfRule(self.rule, bindings=bindings, evidence=evidence)
	else:
	    reason = None

	es, exout = self.workingContext.existentials(), []
	for var, val in bindings.items():
	    if val in es:   #  Take time for large number of bnodes?
		exout.append(val)
		if diag.chatty_flag > 25:
		    progress("Match found to that which is only an existential: %s -> %s" % (var, val))
		if self.workingContext is not self.targetContext:
		    self.targetContext.declareExistential(val)

        b2 = bindings.copy()
	b2[self.conclusion] = self.targetContext
        ok = self.targetContext.universals()  # It is actually ok to share universal variables with other stuff
        poss = self.conclusion.universals()[:]
        for x in poss[:]:
            if x in ok: poss.remove(x)

#        vars = self.conclusion.existentials() + poss  # Terms with arbitrary identifiers
#        clashes = self.occurringIn(targetContext, vars)    Too slow to do every time; play safe
	if diag.chatty_flag > 25:
	    s=""
	for v in poss:
	    v2 = self.targetContext.newUniversal()
	    b2[v] =v2   # Regenerate names to avoid clash
	    if diag.chatty_flag > 25: s = s + ",uni %s -> %s" %(v, v2)
	for v in self.conclusion.existentials():
	    if v not in exout:
		v2 = self.targetContext.newBlankNode()
		b2[v] =v2   # Regenerate names to avoid clash
		if diag.chatty_flag > 25: s = s + ",exi %s -> %s" %(v, v2)
	    else:
		if diag.chatty_flag > 25: s = s + (", (%s is existential in kb)"%v)
	if diag.chatty_flag > 25:
	    progress("Variables regenerated: universal " + `poss`
		+ " existential: " +`self.conclusion.existentials()` + s)
	

        if diag.chatty_flag>19:
            progress("Concluding DEFINITELY" + bindingsToString(b2) )
        before = self.store.size
        delta = self.targetContext.loadFormulaWithSubsitution(
		    self.conclusion, b2, why=reason)
        if diag.chatty_flag>30:
            progress("Added %i, nominal size of store changed from %i to %i."%(delta, before, self.store.size))
        return delta #  self.store.size - before


##################################################################################


    def unify(query,
               queue,               # Set of items we are trying to match CORRUPTED
               variables,           # List of variables to match and return CORRUPTED
               existentials,        # List of variables to match to anything
                                    # Existentials or any kind of variable in subexpression
               bindings = {},       # Bindings discovered so far
               newBindings = {},    # New bindings not yet incorporated
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
        if diag.chatty_flag > 59:
            progress( "QUERY2: called %i terms, %i bindings %s, (new: %s)" %
                      (len(queue),len(bindings), `bindings`,
                       `newBindings`))
            if diag.chatty_flag > 90: progress( queueToString(queue))

        for pair in newBindings.items():   # Take care of business left over from recursive call
            if diag.chatty_flag>95: progress("    new binding:  %s -> %s" % (`pair[0]`, `pair[1]`))
            if pair[0] in variables:
                variables.remove(pair[0])
                bindings.update({pair[0]: pair[1]})  # Record for posterity
            else:      # Formulae aren't needed as existentials, unlike lists. hmm.
		if tracking: bindings.update({pair[0]: pair[1]})  # Record for proof only
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

            if (diag.chatty_flag > 90):
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
            if diag.chatty_flag>49:
                progress( "Looking at " + `item`)
                progress( "...with vars("+seqToString(variables)+")"
                         + " ExQuVars:("+seqToString(existentials)+")")
            con, pred, subj, obj = item.quad
            state = item.state
            if state == S_DONE:
                return total # Forget it -- must be impossible
            if state == S_LIGHT_UNS_GO:
		item.state = S_LIGHT_EARLY   # Unsearched, try builtin
                nbs = item.tryBuiltin(queue, bindings, heavy=0, evidence=evidence)
            elif state == S_LIGHT_GO:
		item.state = S_DONE   # Searched.
                nbs = item.tryBuiltin(queue, bindings, heavy=0, evidence=evidence)
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
                        if diag.chatty_flag > 40:
                                progress("**** Includes: Adding %i new terms and %s as new existentials."%
                                          (len(more_unmatched),
                                           seqToString(more_variables)))
                        item.state = S_SATISFIED
                    else:
                        progress("Include can only work on formulae "+`item`) #@@ was RuntimeError exception
                        item.state = S_DONE
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
		item.state = S_SATISFIED  # do not put back on list
            elif state ==S_HEAVY_WAIT or state == S_LIGHT_WAIT: # Can't
                if diag.chatty_flag > 49 :
                    progress("@@@@ Warning: query can't find term which will work.")
                    progress( "   state is %s, queue length %i" % (state, len(queue)+1))
                    progress("@@ Current item: %s" % `item`)
                    progress(queueToString(queue))
#                    raise RuntimeError, "Insufficient clues"
                return 0  # Forget it
            else:
                raise RuntimeError, "Unknown state " + `state`
            if diag.chatty_flag > 90: progress("nbs=" + `nbs`)
            if nbs == 0: return total
            elif nbs != []:
#		if nbs != 0 and nbs != []: pass
		# progress("llyn.py 2738:   nbs = %s" % nbs)
                for nb, reason in nbs:
		    assert type(nb) is types.DictType, nb
                    q2 = []
                    for i in queue:
                        newItem = i.clone()
                        q2.append(newItem)  #@@@@@@@@@@  If exactly 1 binding, loop (tail recurse)
		    
                    found = query.unify(q2, variables[:], existentials[:],
                                          bindings.copy(), nb, evidence = evidence + [reason])
		    if diag.chatty_flag > 80: progress(
			"Nested query returns %i fo %r" % (found, nb))
                    total = total + found
		    if query.justOne and total:
                        return total
# NO - more to do return total # The called recursive calls above will have generated the output @@@@ <====XXXX
	    if diag.chatty_flag > 80: progress("Item state %i, returning total %i" % (item.state, total))
            if item.state == S_DONE:
		return total
            if item.state != S_SATISFIED:   # state 0 means leave me off the list
                queue.append(item)
            # And loop back to take the next item

        if diag.chatty_flag>50: progress("QUERY MATCH COMPLETE with bindings: " + `bindings`)
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
	if diag.chatty_flag > 90:
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
        if diag.chatty_flag > 90: progress(string.join(messages, "\n"))
        if diag.chatty_flag > 90: progress("query matrix \"\"\""+rs.toString({'dataFilter' : None})+"\"\"\" .\n")

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

        if diag.chatty_flag > 10: progress("====> bindings from remote query:"+`nbs`)
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
		schema = pred.dereference(mode, self.query.workingContext)
		if schema != None:
		    if "a" in mode:
			if diag.chatty_flag > 95:
			    progress("Axiom processing for %s" % (pred))
			ns = pred.resource
			rules = schema.any(subj=ns, pred=self.store.docRules)
			rulefile = rulefile.dereference("m", self.query.workingContext)
		    self.service = schema.any(pred=self.store.definitiveService, subj=pred)
	    if self.service == None and self.query.meta != None:
		self.service = self.query.meta.any(pred=self.store.definitiveService, subj=pred)
		if self.service == None:
		    uri = pred.uriref()
		    if uri[:4] == "mysql:":
			j = uri.rfind("/")
			if j>0: self.service = meta.newSymbol(uri[:j])
	    if diag.chatty_flag > 90 and self.service:
		progress("We have a Remote service %s for %s." %(self.service, pred))
	    if not self.service:
		authDoc = None
		if schema != None:
		    authDoc = schema.any(pred=self.store.definitiveDocument, subj=pred)
		if authDoc == None and self.query.meta != None:
		    authDoc = self.query.meta.any(pred=self.store.definitiveDocument, subj=pred)
		if authDoc != None:
		    if diag.chatty_flag > 90:
			progress("We have a definitive document %s for %s." %(authDoc, pred))
		    authFormula = authDoc.dereference(mode, self.query.workingContext)
		    if authFormula != None:
			self.quad = (authFormula, pred, subj, obj)
			con = authFormula

        self.neededToRun = [ [], [], [], [] ]  # for each part of speech
        self.searchPattern = [con, pred, subj, obj]  # What do we search for?
        hasUnboundCoumpundTerm = 0
        for p in PRED, SUBJ, OBJ :
            x = self.quad[p]
            if x in allvars:   # Variable
                self.neededToRun[p] = [x]
                self.searchPattern[p] = None   # can bind this
            elif isinstance(x, Formula) or isinstance(x, List): # expr
                ur = x.occurringIn(allvars)
                self.neededToRun[p] = ur
                if ur != []:
                    hasUnboundCoumpundTerm = 1     # Can't search directly
		    self.searchPattern[p] = None   # can bind this if we recurse
		    
	    if diag.chatty_flag > 98: progress("        %s needs to run: %s"%(`x`, `self.neededToRun[p]`))
                
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
        if diag.chatty_flag > 80: progress("setup:" + `self`)
        if self.state == S_DONE: return 0
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
			self.state = S_SATISFIED # satisfied
                        if diag.chatty_flag > 80: progress("Builtin buinary relation operator succeeds")
			if tracking:
			    rea = BecauseBuiltIn(subj, pred, obj, proof)
			    evidence = evidence + [rea]
#			    return [([], rea)]  # Involves extra recursion just to track reason
			return []   # No new bindings but success in logical operator
		    else: return 0   # We absoluteley know this won't match with this in it
		else: 
		    if isinstance(pred, Function):
			if diag.chatty_flag > 97: progress("Builtin function call %s(%s)"%(pred, subj))
			result = pred.evalObj(subj, queue, bindings.copy(), proof, self.query)
			if result != None:
			    self.state = S_DONE
			    rea=None
			    if tracking: rea = BecauseBuiltIn(subj, pred, result, proof)
			    return [({obj: result}, rea)]
                        else:
			    if heavy: return 0
	    else:
		if (self.neededToRun[OBJ] == []):
		    if isinstance(pred, ReverseFunction):
			result = pred.evalSubj(obj, queue, bindings.copy(), proof, self.query)
			if result != None:
			    self.state = S_DONE
			    rea=None
			    if tracking:
				rea = BecauseBuiltIn(result, pred, obj, proof)
			    return [({subj: result}, rea)]
                        else:
			    if heavy: return 0
		else:
		    if isinstance(pred, FiniteProperty):
			result = pred.ennumerate()
			if result != 0:
			    self.state = S_DONE
			    rea=None
			    if tracking:
				rea = BecauseBuiltIn(result, pred, obj, proof)
			    return [({subj: result}, rea)]
                        else:
			    if heavy: return 0
	    if diag.chatty_flag > 30:
		progress("Builtin could not give result"+`self`)
    
	    # Now we have a light builtin needs search,
	    # otherwise waiting for enough constants to run
	    return []   # Keep going
        except (IOError, SyntaxError):
            raise BuiltInFailed(sys.exc_info(), self, pred ),None
        
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
            if diag.chatty_flag > 36:
                progress( "Can't deep search for %s" % `self`)
        else:
            if diag.chatty_flag > 36:
                progress( "Searching (S=%i) %i for %s" %(self.state, self.short, `self`))
            for s in self.myIndex :  # for everything matching what we know,
                nb = {}
                reject = 0
		if diag.chatty_flag > 106: progress("...checking %r" % s)
                for p in PRED, SUBJ, OBJ:
                    if self.searchPattern[p] == None: # Need to check
			x = self.quad[p]
			if self.neededToRun[p] == [x]:   # Normal case
			    nb1 = {x: s.quad[p]}
			else:  # Deep case
			    nbs1 = x.unify(s.quad[p], self.query.variables,
				self.query.existentials, {})  # Bindings have all been bound
			    if diag.chatty_flag > 70:
				progress( "Searching deep %s result binding %s" %(self, nbs1))
			    if nbs1 == 0:
				if diag.chatty_flag > 106: progress("......fail: %s" % self)
				break  # reject this statement
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
					break # reject
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
            self.state = S_DONE  # Done with this one: Do new bindings & stop
        elif self.canRun():
            self.state = S_HEAVY_READY
        else:
            self.state = S_HEAVY_WAIT
        if diag.chatty_flag > 90:
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
        if diag.chatty_flag > 90:
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
	else:
	    self.short = 7700+self.state  # Should not be used
	    self.myIndex = None
        if isinstance(self.quad[PRED], BuiltIn):
            if self.canRun():
                if self.state == S_LIGHT_EARLY: self.state = S_LIGHT_UNS_GO
                elif self.state == S_LIGHT_WAIT: self.state = S_LIGHT_GO
                elif self.state == S_HEAVY_WAIT: self.state = S_HEAVY_READY
        if diag.chatty_flag > 90:
            progress("...bound becomes ", `self`)
        if self.state == S_DONE: return 0
        return [] # continue

    def __repr__(self):
        """Diagnostic string only"""
        return "%3i) short=%i, %s" % (
                self.state, self.short,
                quadToString(self.quad, self.neededToRun, self.searchPattern))


##############
# Compare two cyclic subsystem sto see which should be done first

def compareCyclics(self,other):
    """Note the set indirectly affected is the same for any member of a cyclic subsystem"""
#    progress("Comparing %s to %s" % (self[0], other[0]))
    if other[0] in self[0].indirectlyAffects:
#	progress("less, do earlier")
	return -1  # Do me earlier
    if other[0] in self[0].indirectlyAffectedBy:
#	progress("more, do me later")
	return 1
#    progress("same")
    return 0
	


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


def lookupQuadRecursive(bindings, q, why=None):
	context, pred, subj, obj = q
	if diag.chatty_flag > 99: progress("\tlookupQuadRecursive:", q)
	return (
            context.substitution(bindings),
            pred.substitution(bindings),
            subj.substitution(bindings),
            obj.substitution(bindings) )

#   DIAGNOSTIC STRING OUTPUT
#
def queueToString(queue):
    str = ""
    for item in queue:
        str = str  +  `item` + "\n"
    return str


def setToString(set):
    str = ""
    for q in set:
        str = str+ "        " + quadToString(q) + "\n"
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

def seqToString(set):
#    return `set`
    
    str = ""
    for x in set[:-1]:
        str = str + `x` + ","
    for x in set[-1:]:
        str = str+ `x`
    return str

def bindingsToString(bindings):
#    return `bindings`

    str = ""
    for x, y in bindings.items():
        str = str + (" %s->%s " % ( `x`, `y`))
    return str

class BuiltInFailed(Exception):
    def __init__(self, info, item, pred):
        progress("@@@@@@@@@ BUILTIN %s FAILED" % pred, `info`)
        self._item = item
        self._info = info
	self._pred = pred
        
    def __str__(self):
        reason = indentString(self._info[1].__str__())
#        return "reason=" + reason
        return ("Error during built-in operation\n%s\nbecause:\n%s" % (
            `self._item`,
#            `self._info`))
            `reason`))
    


# ends
