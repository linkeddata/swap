
# check that proof

from thing import load, Namespace
from RDFSink import CONTEXT, PRED, SUBJ, OBJ
from diag import verbosity, setVerbosity, progress
from sys import argv, exit

import llyn # Chosen engine registers itself

reason = Namespace("http://www.w3.org/2000/10/swap/reason#")
log = Namespace("http://www.w3.org/2000/10/swap/log#")
rdf=Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")


def fail(str, level=0):
    if verbosity() > 10:
	progress(" "*(level*4), "Proof failed: ", str)
    return None

def fyi(str, level=0):
    if verbosity() > 50:
	progress(" "*(level*4),  str)
    return None

def bind(x, bindings):
    for var, val in bindings:
	if x is var: return val
    return x
    
def parse(resourceURI):
    global parsed
    f = parsed.get(resourceURI, None)
    if f == None:
	f = load(resourceURI)
	parsed[resourceURI] = f
    return f

def statementFromFormula(f):
    s = None
    for x in f.statements:
	if x[PRED] not in (log.forAll, log.forSome):
	    if s != None: raise RuntimeError("Statement formula has >1 statement")
	    s = x
    return s

def valid(f, level=0):
    fyi("target"+`f`, level)

    r = proof.any(subj=f, pred=reason.because)
    if r == None:
	v = verbosity()
	setVerbosity(0)
	str = f.n3String()
	setVerbosity(v)
	return fail("No reason for "+`f` + " :\n\n"+str +"\n\n", level=level)
    t = proof.any(subj=r, pred=rdf.type)
    fyi("Validating a "+`t`, level=level)
    
    if t is reason.Parsing:
	res = proof.any(subj=r, pred=reason.source)
	if res == None: return fail("No source given to parse", level=level)
	u = res.uriref()
#	try:
	v = verbosity()
	setVerbosity(15)
	g = parse(u)
	setVerbosity(v)
#	except:
#	    return fail("Can't retreive/parse <%s>." %u, level)
	for sf in f.statements:
	    for sg in g.statements:
		bindings = [(f, g)]
		if (bind(sf[PRED], bindings) is sg[PRED] and
		    bind(sf[SUBJ], bindings) is sg[SUBJ] and
		    bind(sf[OBJ],  bindings) is sg[OBJ]):
		    break
	    else:
		progress("@@@"+`g.statements`)
		return fail("Can't verify that <%s> says %s" %(u, sf), level=level)
	return 1

    elif t is reason.Inference:
	evidence = proof.each(subj=r, pred=reason.given)
	bindings = []
	for b in proof.each(subj=r, pred=reason.binding):
	    var  = proof.the(subj=b, pred=reason.variable)
	    val  = proof.the(subj=b, pred=reason.boundTo) # @@@ Check that tey really are variables in the rule!
	    bindings.append((var, val))

	rule = proof.any(subj=r, pred=reason.rule)
	if not valid(rule, level+1):
	    return fail("No justification for rule"+`rule`, level)
	for s in rule.statements:
	    if s[PRED] is log.implies:
		ruleStatement = s
		break
	else: return fail("Rule has %s instead of log:implies as predicate.", level)
	evidenceStatements = []
	for e in evidence: evidenceStatements.append(statementFromFormula(e))
	for s in ruleStatement[SUBJ]: # Antecedent
	    context, pred, subj, obj = s.quad
	    pred = bind(pred, bindings)
	    subj = bind(subj, bindings)
	    obj  = bind(obj, bindings) 
	    for t in evidenceStatements:
		if t[SUBJ] == subj and t[PRED]==pred and t[OBJ]==obj:
		    break
	    else:
		return fail("Can't find %s in evidence for rule %s: \nEvidence:%s\nBindings:%s\n"
			      %((subj, pred,  obj), ruleStatement, evidenceStatements, bindings),
			    level=level)

	for e in evidence:
	    if not valid(e, level+1):
		return fail("Evidence could not be proved: " + `e`, level=level)
	fyi("Rule %s conditions met" % ruleStatement, level=level)

	conclusions = []
	for s in ruleStatement[OBJ]:
	    context, pred, subj, obj = s.quad
	    pred = bind(pred, bindings)
	    subj = bind(subj, bindings)
	    obj  = bind(obj, bindings)
	    conclusions.append((f, pred, subj, obj))
	for t in f.statements:
	    if t.quad not in conclusions:
		progress("@@@@@ f.statements: "+`f.statements`)
		return fail("Statement %s not justified by \n conclusions %s\nof rule %s." %
			    (t, conclusions, ruleStatement), level=level)
	return 1
	
    elif t is reason.Conjunction:
	evidence = proof.each(subj=r, pred=reason.given)
	conclusions = []
	for e in evidence:
	    if not valid(e, level+1):
		return fail("Evidence could not be proved:"+`e`, level=level)
	return 1
    return fail("Reason is of unknown type "+`t`, level=level)

# Main program 
	    
parsed = {}
setVerbosity(15)

inputURI = argv[1]
progress("Taking input from"+inputURI)
proof = load(inputURI)
setVerbosity(100)
fyi("Length of proof: "+`len(proof)`)
qed = proof.the(pred=rdf.type, obj=reason.QED)  # the thing to be prooved


if valid(qed):
    fyi("Proof valid.")
    exit(0)
fyi("Proof invalid.")
exit(-1)

#ends

