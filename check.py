"""Check a proof

This is a simple proof checker.  It hasn't itself been proved,
and there are probably lots of ways to fool it especially as a deliberate
malicious attack. That is because there are simple things I may have forgotten
to check.

Command line options for debug:
 -v50   Set verbosity to 50 (range is 0 -100)
 -c50   Set verbosity for inference done by cwm code to 50
 -p50   Set verobsity when parsing top 50    
"""
# check that proof

from swap.myStore import load, Namespace
from swap.RDFSink import CONTEXT, PRED, SUBJ, OBJ
from swap.term import List, Literal, CompoundTerm, BuiltIn
from swap.llyn import Formula #@@ dependency should not be be necessary
from swap.diag import verbosity, setVerbosity, progress

from swap.query import testIncludes

# Standard python
import sys, getopt
from sys import argv, exit

import swap.llyn # Chosen engine registers itself

reason = Namespace("http://www.w3.org/2000/10/swap/reason#")
log = Namespace("http://www.w3.org/2000/10/swap/log#")
rdf=Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
rei = Namespace("http://www.w3.org/2004/06/rei#")

chatty = 0
debugLevelForInference = 0
debugLevelForParsing = 0
nameBlankNodes = 0
proofSteps = 0

parsed = {} # Record of retrieval/parsings
checked = {} # Formulae from checked reasons

def fail(str, level=0):
    if chatty > 0:
	progress(" "*(level*4), "Proof failed: ", str)
    return None

def fyi(str, level=0, thresh=50):
    if chatty >= thresh:
	progress(" "*(level*4),  str)
    return None

def evidenceDiagnostics(subj, pred, obj, evidenceStatements, level):
    for p, part in (subj, "subject"), (obj, "object"):
	if isinstance(p, List):
	    fyi("Looking for %s: %s" %(part, `p`), level=level) 
	    for i in range(len(p)):
		fyi("   item %i = %s" %(i, `p[i]`), level=level)
    for t in evidenceStatements:
	if  t[PRED] is pred:
	    fyi("Evidence with right predicate: %s" %(t), level=level)
	    for p, part in (t[SUBJ], "subject"), (t[OBJ], "object"):
		if isinstance(p, List):
		    fyi("Found for %s: %s" %(part, `p`), level=level) 
		    for i in range(len(p)):
			fyi("   item %i = %s" %(i, `p[i]`), level=level)

def bind(x, bindings):
    return x.substitution(bindings)
#    for var, val in bindings:     #  DUH
#	if x is var: return val
#    return x
    
def parse(resourceURI):
    global parsed
    f = parsed.get(resourceURI, None)
    if f == None:
	setVerbosity(debugLevelForParsing)
	f = load(resourceURI, flags="B")
	setVerbosity(0)
	parsed[resourceURI] = f
    return f

def statementFromFormula(f):
    "Check just one statement and return it"
    if len(f) > 1:
	raise RuntimeError("Should be a single statement: %s" % f.statements)
    return f.statements[0]

def checkIncludes(f, g):
    # return testIncludes(f,g)
    x = f.unify(g)
    

def getSymbol(proof, x):
	"De-reify a symbol: get the informatuion identifying it from the proof"

	y = proof.the(subj=x, pred=rei.uri)
	if y != None: return proof.newSymbol(y.string)

	y = proof.the(subj=x, pred=rei.nodeId)
	if y != None:
	    fyi("Warning: variable is identified by nodeId: <%s>" %
			y.string, 20)
	    return proof.newSymbol(y.string)
	raise RuntimeError("Can't de-reify %s" % x)
	

def getTerm(proof, x):
	"De-reify a term: get the informatuion about it from the proof"
	if isinstance(x, (Literal, CompoundTerm)):
	    return x
	    
	val = proof.the(subj=x, pred=rei.value)
	if val != None:  return proof.newLiteral(val.string,
				val_value.datatype, val.lang)
	return getSymbol(proof, x)


def valid(proof, r=None, level=0):
    """Check whether this reason is valid.
    
    proof   is the formula which contains the proof
    
    r       is the reason to be checked, or none if the root reason
	    The root reason is the reason of type reason:Proof
    
    level   is just the nesting level for diagnostic output
    
    Returns the formula proved or None if not
    """
    
    if r == None:
        r = proof.the(pred=rdf.type, obj=reason.Proof)  #  thing to be proved
	
    f = checked.get(r, None)
    if f is not None:
	fyi("Cache hit: already proved")
	return f

    global proofSteps
    proofSteps += 1
        
    f = proof.any(r,reason.gives)
    if f != None:
	assert isinstance(f, Formula), \
			"%s gives: %s which should be Formula" % (`r`, f)
	if len(f) == 1:
#	s = statementFromFormula(f)
#	if s != None:
	    s = f.statements[0]
	    fs = " proof of {%s %s %s}" % (
				    s.subject(), s.predicate(), s.object())
	else:
	    fs = " proof of %s" % f
    else:
	fs = ""
#    fyi("Reason for %s is %s."%(f, r), level)

    if r == None:
	str = f.n3String()
	return fail("No reason for "+`f` + " :\n\n"+str +"\n\n", level=level)
    t = proof.any(subj=r, pred=rdf.type)
    fyi("%s %s %s"%(t,r,fs), level=level)
    level = level + 1
    
    if t is reason.Parsing:
	res = proof.any(subj=r, pred=reason.source)
	if res == None: return fail("No source given to parse", level=level)
	u = res.uriref()
	try:
	    v = verbosity()
	    setVerbosity(0)
	    g = parse(u)
	    setVerbosity(v)
	except:   #   ValueError:  #@@@@@@@@@@@@ &&&&&&&&
	    return fail("Can't retreive/parse <%s> because:\n  %s." 
				%(u, sys.exc_info()[1].__str__()), level)
	if f != None:  # Additional intermediate check not essential
	    for sf in f.statements:
		for sg in g.statements:
		    bindings = {f: g}
		    if (bind(sf[PRED], bindings) is sg[PRED] and
			bind(sf[SUBJ], bindings) is sg[SUBJ] and
			bind(sf[OBJ],  bindings) is sg[OBJ]):
			break
		else:
		    progress("Statements parsed from %s:\n%s" %
						    (u, `g.statements`))
		    return fail("Can't verify that <%s> says %s" %
						 (u, sf), level=level)
	checked[r] = g
	return g

    elif t is reason.Inference:
	evidence = proof.the(subj=r, pred=reason.evidence)
#	assert isinstance(evidence, List)
	bindings = {}
	for b in proof.each(subj=r, pred=reason.binding):
	    var_rei  = proof.the(subj=b, pred=reason.variable)
	    var = getSymbol(proof, var_rei)
	    val_rei  = proof.the(subj=b, pred=reason.boundTo)
	    # @@@ Check that they really are variables in the rule!
	    val = getTerm(proof, val_rei)
	    bindings[var] = val

	rule = proof.the(subj=r, pred=reason.rule)
	if not valid(proof, rule, level):
	    return fail("No justification for rule "+`rule`, level)
	for s in proof.the(rule, reason.gives).statements:  #@@@@@@ why look here?
	    if s[PRED] is log.implies:
		ruleStatement = s
		break
	else: return fail("Rule has %s instead of log:implies as predicate.", level)
	
	# Check the evidence is itself proved
	evidenceFormula = proof.newFormula()
	for e in evidence:
	    f2 = valid(proof, e, level)
	    if f2 == None:
		return fail("Evidence %s was not proved."%(e))
	    f2.store.copyFormula(f2, evidenceFormula)
	evidenceFormula = evidenceFormula.close()
	
	# Check: Every antecedent statement must be included as evidence
	antecedent = ruleStatement[SUBJ].substitution(bindings)
	if evidenceFormula is antecedent: fyi("Yahooo! #########  ")
	
#	if testIncludes(evidenceFormula, antecedent):
#	    fyi("Success: the antecedent can be found by indexed query", level)
#	else:
	if 1:
	    fyi("Ooooops: query fails to find match antecedent, try unification", level)
	    for s in antecedent:
		context, pred, subj, obj = s.quad
		if pred is context.store.includes:
		    fyi("(log:includes found in antecedent, assumed good)", level) 
		    continue
		if evidenceFormula.statementsMatching(pred=pred, subj=subj,
			obj=obj) != []:
		    fyi("Statement found in index: %s" % s, level)
		    continue

		for t in evidenceFormula.statements:
		    fyi("Trying unify evidence statement %s" %(`t`), level=level+1, thresh=70) 
		    if (t[PRED].unify(pred) != 0 and
		        t[SUBJ].unify(subj) != 0 and 
			t[OBJ].unify(obj) != 0):
			fyi("Statment unified: %s" % t, level) 
			break
		else:
		    evidenceDiagnostics(subj, pred, obj, evidenceFormula.statements, level)
		    return fail("""Can't find %s in evidence for rule %s:
Evidence:%s
Bindings:%s
"""
				  %((subj, pred,  obj), ruleStatement,
				evidenceFormula.statements, bindings),
				level=level)

	fyi("Rule %s conditions met" % ruleStatement, level=level)

#	proved = proof.newFormula()
#	for s in ruleStatement[OBJ]: # Conclusion
#	    context, pred, subj, obj = s.quad
#	    pred = bind(pred, bindings)
#	    subj = bind(subj, bindings)
#	    obj  = bind(obj, bindings)
#	    proved.add(subj, pred, obj)
#	proved=proved.close()
	f = ruleStatement[OBJ].substitution(bindings)
	checked[r] = f
	return f
	
    elif t is reason.Conjunction:
	components = proof.each(subj=r, pred=reason.component)
	proved = []
	for e in components:
	    if not valid(proof, e, level):
		return fail("In Conjunction %s, evidence %s could not be proved."%(r,e), level=level)
	    proved.append(proof.the(subj=e, pred=reason.gives))
	
	checked[r] = f
	return f
	
    elif t is reason.Fact:
	con, pred, subj, obj = statementFromFormula(f).quad
	fyi("Built-in: testing fact {%s %s %s}" % (subj, pred, obj), level=level)
	if not isinstance(pred, BuiltIn):
	    return fail("Claimed as fact, but predicate is %s not builtin" % pred, level)
	    if not pred.eval(subj, obj, None, None, None, None):
		return fail("Built-in fact does not give correct results", level)
	checked[r] = f
	return f
	
    elif t is reason.Extraction:
	r2 = proof.the(r, reason.because)
	if r2 == None:
	    return fail("Extraction: no source formula given for %s." % (`r`), level)
	f2 = valid(proof, r2, level)
	if f2 == None:
	    return fail("Extraction: couldn't validate formula to be extracted from.", level)
	setVerbosity(debugLevelForInference)
	nbs = f.n3EntailedBy(f2)
	if nbs == 0:
#	if not testIncludes(f2, f):
	    return fail("""Extraction %s not included in formula  %s.
	    _____________________________________________
	    %s
	    ______________not included in: ______________
	    %s
	    _____________________________________________
"""
		    %(f, f2, f.debugString(), f2. debugString()), level=level)
	setVerbosity(0)
	checked[r] = f
	return f

    s = ""
    for x in proof.statementsMatching(subj=r): s = `x` + "\n"
    return fail("Reason %s is of unknown type %s.\n%s"%(r,t, s), level=level)

# Main program 

def usage():
    sys.stderr.write(__doc__)
    
def main():
    global chatty
    global parsed
    global debugLevelForInference
    global debugLevelForParsing
    global nameBlankNodes
    setVerbosity(0)
    
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hv:c:p:B",
	    [ "help", "verbose=", "chatty=", "parsing=", "nameBlankNodes"])
    except getopt.GetoptError:
	sys.stderr.write("check.py:  Command line syntax error.\n\n")
        usage()
        sys.exit(2)
    output = None
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-v", "--verbose"):
	    chatty = int(a)
        if o in ("-p", "--verboseParsing"):
	    debugLevelForParsing = int(a)
        if o in ("-c", "--chatty"):
	    debugLevelForInference = int(a)
        if o in ("-B", "--nameBlankNodes"):
	    nameBlankNodes = 1
    if nameBlankNodes: flags="B"
    else: flags=""
    
    if args:
        fyi("Reading proof from "+args[0])
        proof = load(args[0], flags=flags)
    else:
	fyi("Reading proof from standard input.", thresh=5)
	proof = load(flags=flags)

    # setVerbosity(60)
    fyi("Length of proof formula: "+`len(proof)`, thresh=5)
    
    proved = valid(proof)
    if proved != None:
	fyi("Proof looks OK.   %i Steps" % proofSteps, thresh=5)
	setVerbosity(0)
	print proved.n3String()
	exit(0)
    progress("Proof invalid.")
    exit(-1)

if __name__ == "__main__":
    """This trick prevents the pydoc from actually running the script"""
    main()
#ends

