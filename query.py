""" Query for cwm architecture

2003-09-07 split off from llyn.py
"""

from RDFSink import Logic_NS, RDFSink, forSomeSym, forAllSym
from RDFSink import CONTEXT, PRED, SUBJ, OBJ, PARTS, ALL4
from RDFSink import N3_nil, N3_first, N3_rest, OWL_NS, N3_Empty, N3_List, List_NS
from RDFSink import RDF_NS_URI

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

INFINITY = 1000000000           # @@ larger than any number occurences


# State values as follows, high value=try first:
S_UNKNOWN = 	99  # State unknown - to be [re]calculated by setup.
S_FAIL =   	80  # Have exhausted all possible ways to saitsfy this item. stop now.
S_LIGHT_UNS_GO= 70  # Light, not searched yet, but can run
S_LIGHT_GO =  	65  # Light, can run  Do this!
S_NOT_LIGHT =   60  # Not a light built-in, haven't searched yet.
S_LIGHT_EARLY=	50  # Light built-in, not enough constants to calculate, haven't searched yet.
S_NEED_DEEP=	45  # Can't search because of unbound compound term, could do recursive unification
S_HEAVY_READY=	40  # Heavy built-in, search done, but formula now has no vars left. Ready to run.
S_LIGHT_WAIT=	30  # Light built-in, not enough constants to calculate, search done.
S_HEAVY_WAIT=	20  # Heavy built-in, too many variables in args to calculate, search failed.
S_HEAVY_WAIT_F=	19  # Heavy built-in, too many vars within formula args to calculate, search failed.
S_REMOTE =	10  # Waiting for local query to be resolved as much as possible
S_LIST_UNBOUND = 7  # List defining statement, search failed, unbound variables in list.?? no
S_LIST_BOUND =	 5  # List defining statement, search failed, list is all bound.
S_DONE =	 0  # Item has been staisfied, and is no longer a constraint


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
	
	self.workingContext, self.targetContext, self.mode, self.repeat = workingContext, targetContext, mode, repeat
	self.store = self.workingContext.store

    def analyse(self):
	rules= self.ruleFor.values()
	for r1 in rules:
	    for r2 in rules:
		for s1 in r1.conclusion.statements:
		    for s2 in r2.template.statements:
			for p in PRED, SUBJ, OBJ:
			    if ((s1[p] nor in r1.variables)
				and (s2[p] not in r2.variables)
				and (s1[p] is not s2[p])):
				    progress("...can't effect")
				    break
			else:
			    r1.affects[r2] = 1
			    if verbosity > 40: progress("%s can affect %s because %s can trigger %s" %
					    (`r1`, `r2`, `s1`, `s2`)
			    break # can affect
		    else:  # that statement couldn't but
			continue # try next one
		    break # can

    def run(self):
	"""Perform task.
	Return number of  new facts"""
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
		if (diag.chatty_flag >40):
		    progress( "Found %i new stmts on for rule %s" % (found, rule))
		_total = _total+found
		if found and (rule.meta or self.targetContext._closureMode):
		    needToCheckForRules = 1
	    if diag.chatty_flag > 5: progress("Total of %i new statements on iteration %i." %
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
		self.ruleFor[s] = Rule(self, s,  v2)
		if (diag.chatty_flag >10):
		    progress( "Found rule for statement %s " % (s))

	for F in ruleFormula.each(pred=self.store.implies, obj=self.store.Truth): #@@ take out when truth in
	    self.gatherRules(F)  #See test/rules13.n3, test/schema-rules.n3 etc

#	    else:   # does anyone really use this? If so, watch that universal vaibles are different
#		if pred is workingContext.store.type and obj is workingContext.store.Truth:
#		    rules.extend(self.gatherRules(subj, workingContext, targetContext, mode))


class Rule:

    def __init__(self, task, rule, _variables,):
	"""Try a rule
	
	Beware lists are corrupted. Already list is updated if present.
	"""
	self.task = task
	self.template = rule[SUBJ]
	self.conclusion = rule[OBJ]
	self.store = self.template.store
	self.rule = rule
	self.meta = self.conclusion.contains(pred=self.conclusion.store.implies) #generate rules?
	if task.repeat: self.already = []
	else: self.already = None
	
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
	    progress("\nNew Rule ============ (mode=%s) looking for:" % task.mode)
	    progress( setToString(self.unmatched))
	    progress("Universals declared in outer " + seqToString(_variables))
	    progress(" mentioned in template       " + seqToString(variablesMentioned))
	    progress(" also used in conclusion     " + seqToString(self.variablesUsed))
	    progress("Existentials in template     " + seqToString(self.templateExistentials))
	return

    def once(self):
    # The smartIn context was the template context but it has been mapped to the workingContext.
	if diag.chatty_flag >20:
	    progress("\n=================== tryRule ============ " )
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
			rule = self.rule,
			smartIn = [task.workingContext],    # (...)
			meta = task.workingContext,
			mode = task.mode)
    
	total = query.resolve()
	if diag.chatty_flag > 20:
	    progress("Rule try generated %i new statements" % total)
	return total
    
    
    
def testIncludes(f, g, _variables=[],  bindings={}):
    """Return whether or nor f contains a top-level formula equvalent to g.
    Just a test: no bindings returned."""
    if diag.chatty_flag >30: progress("\n\n=================== testIncludes ============")

    # When the template refers to itself, the thing we are
    # are looking for will refer to the context we are searching

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
#        diag.chatty_flag = diag.chatty_flag-100
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



    def conclude(self, bindings, evidence = []):
	"""When a match found in a query, add conclusions to target formula.

	Returns the number of statements added."""
	if self.justOne: return 1   # If only a test needed
	assert type(bindings) is type({})

        if diag.chatty_flag >60: progress( "\nConcluding tentatively..." + bindingsToString(bindings))

        if self.already != None:
            if bindings in self.already:
                if diag.chatty_flag > 30: progress("@@Duplicate result: ", bindingsToString(bindings))
                return 0
            if diag.chatty_flag > 30: progress("Not duplicate: ", bindingsToString(bindings))
            self.already.append(bindings)   # A list of dicts

	if tracking:
	    reason = BecauseOfRule(self.rule, bindings=bindings, evidence=evidence)
	else:
	    reason = None

	es, exout = self.workingContext.existentials(), []
	for var, val in bindings.items():
	    if val in es:
		exout.append(val)
		if diag.chatty_flag > 25:
		    progress("Match found to that which is only an existential: %s -> %s" % (var, val))
		self.targetContext.declareExistential(val)

        b2 = bindings.copy()
	b2[self.conclusion] = self.targetContext
        ok = self.targetContext.universals()  # It is actually ok to share universal variables with other stuff
        poss = self.conclusion.universals()[:]
        for x in poss[:]:
            if x in ok: poss.remove(x)

        vars = self.conclusion.existentials() + poss  # Terms with arbitrary identifiers
#        clashes = self.occurringIn(targetContext, vars)    Too slow to do every time; play safe
	if diag.chatty_flag > 25:
	    progress("Variables regenerated: universal " + `poss`
		+ " existential: " +`self.conclusion.existentials()`)
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
	    progress(s)
	

        if diag.chatty_flag>10:
            progress("Concluding definitively" + bindingsToString(b2) )
        before = self.store.size
        self.targetContext.loadFormulaWithSubsitution(
		    self.conclusion, b2, why=reason)
        if diag.chatty_flag>30:
            progress("Size of store changed from %i to %i."%(before, self.store.size))
        return self.store.size - before


##################################################################################


    def unify(query,
               queue,               # Set of items we are trying to match CORRUPTED
               variables,           # List of variables to match and return CORRUPTED
               existentials,        # List of variables to match to anything
                                    # Existentials or any kind of variable in subexpression
               bindings = {},       # Bindings discovered so far
               newBindings = {},    # New bindings not yet incorporated
               level = 0,           # Nesting level for diagnostic indentation only
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
                      (len(queue),len(bindings),bindingsToString(bindings),
                       bindingsToString(newBindings)))
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
                progress( "Looking at " + `item`
                         + "\nwith vars("+seqToString(variables)+")"
                         + " ExQuVars:("+seqToString(existentials)+")")
            con, pred, subj, obj = item.quad
            state = item.state
            if state == S_FAIL:
                return total # Forget it -- must be impossible
            if state == S_LIGHT_UNS_GO or state == S_LIGHT_GO:
		item.state = S_LIGHT_EARLY   # Assume can't run
                nbs = item.tryBuiltin(queue, bindings, heavy=0, evidence=evidence)
		# progress("llyn.py 2706:   nbs = %s" % nbs)
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
                                progress(
                                          "**** Includes: Adding %i new terms and %s as new existentials."%
                                          (len(more_unmatched),
                                           seqToString(more_variables)))
                        item.state = S_DONE
                    else:
                        progress("Include can only work on formulae "+`item`) #@@ was RuntimeError exception
                        item.state = S_FAIL
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
		item.state = S_DONE  # do not put back on list
            elif state == S_LIST_UNBOUND: # Lists with unbound vars
                if diag.chatty_flag>70:
                        progress("List left unbound, returing")
                return total   # forget it  (this right?!@@)
            elif state == S_LIST_BOUND: # bound list
                if diag.chatty_flag>60: progress(
		    "QUERY FOUND MATCH (dropping lists) with bindings: "
		    + bindingsToString(bindings))
                return total + query.conclude(bindings, evidence=evidence)  # No non-list terms left .. success!
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
            if diag.chatty_flag > 90: progress("    nbs=" + `nbs`)
            if nbs == 0: return total
            elif nbs != []:
                total = 0
#		if nbs != 0 and nbs != []: pass
		# progress("llyn.py 2738:   nbs = %s" % nbs)
                for nb, reason in nbs:
		    assert type(nb) is types.DictType, nb
                    q2 = []
                    for i in queue:
                        newItem = i.clone()
                        q2.append(newItem)  #@@@@@@@@@@  If exactly 1 binding, loop (tail recurse)
		    
                    total = total + query.unify(q2, variables[:], existentials[:],
                                          bindings.copy(), nb, evidence = evidence + [reason])
                    if query.justOne and total:
                        return total
		return total # The called recursive calls above will have generated the output
            if item.state == S_FAIL: return total
            if item.state != S_DONE:   # state 0 means leave me off the list
                queue.append(item)
            # And loop back to take the next item

        if diag.chatty_flag>50: progress("QUERY MATCH COMPLETE with bindings: " + bindingsToString(bindings))
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
        if self.state == S_FAIL: return 0
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
			self.state = S_DONE # satisfied
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
			    self.state = S_FAIL
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
			    self.state = S_FAIL
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
			    self.state = S_FAIL
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
            raise BuiltInFailed(sys.exc_info(), self ),None
        
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
		if diag.chatty_flag > 106: progress("...checking %s" % self)
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
            self.state = S_FAIL  # Done with this one: Do new bindings & stop
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

        if isinstance(self.quad[PRED], BuiltIn):
            if self.canRun():
                if self.state == S_LIGHT_EARLY: self.state = S_LIGHT_UNS_GO
                elif self.state == S_LIGHT_WAIT: self.state = S_LIGHT_GO
                elif self.state == S_HEAVY_WAIT: self.state = S_HEAVY_READY
        elif (self.state == S_LIST_UNBOUND
              and self.neededToRun[SUBJ] == []
              and self.neededToRun[OBJ] == []):
            self.state = S_LIST_BOUND
	if self.state == S_LIST_BOUND and self.searchPattern[SUBJ] != None:  # @@@@@@ 20030807
	    if diag.chatty_flag > 50:
		progress("Rejecting list already searched and now bound", self)
	    self.state = S_FAIL    # see test/list-bug1.n3
	    return []  #@@@@ guess 20030807
        if diag.chatty_flag > 90:
            progress("...bound becomes ", `self`)
        if self.state == S_FAIL: return 0
        return [] # continue

    def __repr__(self):
        """Diagnostic string only"""
        return "%3i) short=%i, %s" % (
                self.state, self.short,
                quadToString(self.quad, self.neededToRun, self.searchPattern))

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
    str = ""
    for x in set[:-1]:
        str = str + `x` + ","
    for x in set[-1:]:
        str = str+ `x`
    return str

def bindingsToString(bindings):
    str = ""
    for x, y in bindings.items():
        str = str + (" %s->%s " % ( `x`, `y`))
    return str



# ends
