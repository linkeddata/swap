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
from swap.term import List, Literal, CompoundTerm, BuiltIn, Function
from swap.llyn import Formula #@@ dependency should not be be necessary
from swap.diag import verbosity, setVerbosity, progress
from swap import diag
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

def n3Entails(f, g, skipIncludes=0, level=0):
    """Does f N3-entail g?
    
    First try indexed graph match algorithm, and if that fails,
    unification."""

    v = verbosity()
    setVerbosity(debugLevelForInference)
	
    if f is g:
	fyi("Yahooo! #########  ")
	setVerbosity(v)
	return 1
	
    if testIncludes(f,g):
	fyi("Indexed query works looking in %s for %s" %(f,g), level)
	setVerbosity(v)
 	return 1
	
    fyi("Indexed query fails to find match, try unification", level)
    for s in g:
	context, pred, subj, obj = s.quad
	if skipIncludes and pred is context.store.includes:
	    fyi("(log:includes found in antecedent, assumed good)", level) 
	    continue
	if f.statementsMatching(pred=pred, subj=subj,
		obj=obj) != []:
	    fyi("Statement found in index: %s" % s, level)
	    continue

	for t in f.statements:
	    fyi("Trying unify  statement %s" %(`t`), level=level+1, thresh=70) 
	    if (t[PRED].unify(pred) != [] and
		t[SUBJ].unify(subj) != [] and 
		t[OBJ].unify(obj) != []):
		fyi("Statement unified: %s" % t, level) 
		break
	else:
	    fyi("""n3Entailment failure.\nCan't find: %s=%s\nin formula: %s=%s\n""" %
			    (g, g.n3String(), f, f.n3String()), level, thresh=1)
	    setVerbosity(v)
	    return 0
    setVerbosity(v)
    return 1

    

def getSymbol(proof, x):
	"De-reify a symbol: get the informatuion identifying it from the proof"

	y = proof.the(subj=x, pred=rei.uri)
	if y != None: return proof.newSymbol(y.string)

	y = proof.the(subj=x, pred=rei.nodeId)
	if y != None:
	    fyi("Warning: variable is identified by nodeId: <%s>" %
			y.string, level=0, thresh=20)
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
	fyi("Cache hit: already checked reason for %s is %s."%(f, r), level, 80)
	return f

    global proofSteps
    proofSteps += 1
        
    f = proof.any(r,reason.gives)
    if f != None:
	assert isinstance(f, Formula), \
			"%s gives: %s which should be Formula" % (`r`, f)
	fs = " proof of %s" % f
    else:
	fs = ""
#    fyi("Validating: Reason for %s is %s."%(f, r), level, 60)

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
	v = verbosity()
	setVerbosity(debugLevelForParsing)
	try:
	    g = parse(u)
	except:   #   ValueError:  #@@@@@@@@@@@@ &&&&&&&&
	    return fail("Can't retreive/parse <%s> because:\n  %s." 
				%(u, sys.exc_info()[1].__str__()), level)
	setVerbosity(v)
	if f != None:  # Additional intermediate check not essential
	    if f.unify(g) == []:
		return fail("""Parsed data does not match that given.\n
		Parsed: <%s>\n\n
		Given: %s\n\n""" % (g,f) , level=level)
	checked[r] = g
	return g

    elif t is reason.Inference:
	evidence = proof.the(subj=r, pred=reason.evidence)
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
	else: return fail("Rule has %s instead of log:implies as predicate.",
	    level)
	
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
	fyi("Bindings: %s\nAntecedent after subst: %s" % (
	    bindings, antecedent.debugString()),
	    level, 195)
	if not n3Entails(evidenceFormula, antecedent,
			skipIncludes=1, level=level+1):
	    return fail("""Can't find %s in evidence for
Rule %s:
Evidence:%s
Bindings:%s
"""
			  %((s[SUBJ], s[PRED],  s[OBJ]), ruleStatement,
			evidenceFormula.n3String(), bindings),
			level=level)

	fyi("Rule %s conditions met" % ruleStatement, level=level)

	g = ruleStatement[OBJ].substitution(bindings)
	
	
    elif t is reason.Conjunction:
	components = proof.each(subj=r, pred=reason.component)
	fyi("Conjunction:  %i components" % len(components))
	g = r.store.newFormula()
	for e in components:
	    g1 = valid(proof, e, level)
	    if not g1:
		return fail("In Conjunction %s, evidence %s could not be proved."
		    %(r,e), level=level)
	    before = len(g)
	    g.loadFormulaWithSubstitution(g1)
	    fyi("Conjunction: adding %i statements, was %i, total %i\nAdded: %s" %
			(len(g1), before, len(g), g1.n3String()), level, thresh=80) 
	g = g.close()
	
    elif t is reason.Fact:
	con, pred, subj, obj = statementFromFormula(f).quad
	fyi("Built-in: testing fact {%s %s %s}" % (subj, pred, obj), level=level)
	if not isinstance(pred, BuiltIn):
	    return fail("Claimed as fact, but predicate is %s not builtin" % pred, level)
	if  pred.eval(subj, obj, None, None, None, None):
	    checked[r] = f
	    return f

	if isinstance(pred, Function) and isinstance(obj, Formula):
	    result =  pred.evalObj(subj, None, None, None, None)
	    fyi("Re-checking builtin %s  result %s against quoted %s"
		%(pred, result, obj))
	    if n3Entails(obj, result) and n3Entails(result, obj):
		fyi("Re-checked OK builtin %s  result %s against quoted %s"
		%(pred, result, obj))
		checked[r] = f
		return f
	s, o = subj, obj
	if isinstance(subj, Formula): s = subj.n3String()
	if isinstance(obj, Formula): o = obj.n3String()
		
	return fail("""Built-in fact does not give correct results:
	subject: %s
	predicate: %s
	object: %s
	""" % (s, pred, o), level)
	
    elif t is reason.Extraction:
	r2 = proof.the(r, reason.because)
	if r2 == None:
	    return fail("Extraction: no source formula given for %s." % (`r`), level)
	f2 = valid(proof, r2, level)
	if f2 == None:
	    return fail("Extraction: couldn't validate formula to be extracted from.", level)
	
	if not n3Entails(f2, f):
	    return fail("""Extraction %s not included in formula  %s."""
#    """ 
		    %(f, f2), level=level)
	checked[r] = f
	return f

    elif t is reason.CommandLine:
	raise RuntimeError("shouldn't get here: command line a not a proof step")
	return
    elif t is reason.Premise:
	g = proof.the(r, reason.gives)
	if g is None: return fail("No given input for %s" % r)
	fyi("Premise is: %s" % g.n3String(), level, thresh=25) 
	
    else:
	s = ""
	for x in proof.statementsMatching(subj=r): s = `x` + "\n"
	return fail("Reason %s is of unknown type %s.\n%s"%(r,t, s), level=level)

    if g.occurringIn(g.existentials()) != g.existentials(): # Check integrity
	raise RuntimeError(g.debugString())

    if f is not None and f.unify(g) == []:
	setVerbosity(150)
	f.unify(g)
	setVerbosity(0)
	return fail("%s: Calculated formula: %s\ndoes not match given: %s" %
		(t, g.debugString(), f.debugString()))

    checked[r] = g
    fyi("\n\nRESULT of %s %s is:\n%s\n\n" %(t,r,g.n3String()), level, thresh=100)
    return g



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

