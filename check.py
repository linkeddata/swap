
# check that proof

from thing import load, Namespace
from RDFSink import CONTEXT, PRED, SUBJ, OBJ
from diag import verbosity, setVerbosity, progress
from sys import argv, exit

import llyn # Chosen engine registers itself

reason = Namespace("http://www.w3.org/2000/10/swap/reason#")
log = Namespace("http://www.w3.org/2000/10/swap/log#")
rdf=Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")

chatty = 0

def fail(str, level=0):
    if chatty > 10:
	progress(" "*(level*4), "Proof failed: ", str)
    return None

def fyi(str, level=0):
    if chatty > 50:
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

def valid(r, level=0):
    """Check whether this reason is valid. Returns the formula proved or None is not"""
    f = proof.any(r,reason.gives)
    fyi("Reason for %s is %s."%(f, r), level)

    if r == None:
	str = f.n3String()
	return fail("No reason for "+`f` + " :\n\n"+str +"\n\n", level=level)
    t = proof.any(subj=r, pred=rdf.type)
    fyi("Validating a "+`t`, level=level)
    
    if t is reason.Parsing:
	res = proof.any(subj=r, pred=reason.source)
	if res == None: return fail("No source given to parse", level=level)
	u = res.uriref()
	try:
	    v = verbosity()
	    setVerbosity(0)
	    g = parse(u)
	    setVerbosity(v)
	except:
	    return fail("Can't retreive/parse <%s>." %u, level)
	if f != None:  # Additional intermediate check not essential
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
	return g

    elif t is reason.Inference:
	evidence = proof.each(subj=r, pred=reason.evidence)
	bindings = []
	for b in proof.each(subj=r, pred=reason.binding):
	    var  = proof.the(subj=b, pred=reason.variable)
	    val  = proof.the(subj=b, pred=reason.boundTo) # @@@ Check that they really are variables in the rule!
	    bindings.append((var, val))

	rule = proof.any(subj=r, pred=reason.rule)
	if not valid(rule, level+1):
	    return fail("No justification for rule"+`rule`, level)
	for s in proof.the(rule, reason.gives).statements:
	    if s[PRED] is log.implies:
		ruleStatement = s
		break
	else: return fail("Rule has %s instead of log:implies as predicate.", level)
	evidenceStatements = []
	for e in evidence:
	    f2 = valid(e, level+1)
	    if f2 == None:
		return fail("Evidence %s was not proved."%(e))
	    evidenceStatements.append(f2)
	for s in ruleStatement[SUBJ]: # Antecedent
	    context, pred, subj, obj = s.quad
	    pred = bind(pred, bindings)
	    subj = bind(subj, bindings)
	    obj  = bind(obj, bindings) 
	    for x in evidenceStatements:
		for t in x.statements:
		    if t[SUBJ] == subj and t[PRED]==pred and t[OBJ]==obj:
			break
		else: continue
		break
	    else:
		return fail("Can't find %s in evidence for rule %s: \nEvidence:%s\nBindings:%s\n"
			      %((subj, pred,  obj), ruleStatement, evidenceStatements, bindings),
			    level=level)

	for e in evidence:
	    if not valid(e, level+1):
		return fail("Evidence could not be proved: " + `e`, level=level)
	fyi("Rule %s conditions met" % ruleStatement, level=level)

	proved = proof.newFormula()
	for s in ruleStatement[OBJ]: # Conclusion
	    context, pred, subj, obj = s.quad
	    pred = bind(pred, bindings)
	    subj = bind(subj, bindings)
	    obj  = bind(obj, bindings)
	    proved.add(subj, pred, obj)
	proved=proved.close()
	return proved
	
    elif t is reason.Conjunction:
	components = proof.each(subj=r, pred=reason.component)
	proved = []
	for e in components:
	    if not valid(e, level+1):
		return fail("In Conjunction %s, evidence %s could not be proved."%(r,e), level=level)
	    proved.append(proof.the(subj=e, pred=reason.gives))
	
	return f
	
    elif t is reason.Extraction:
	r2 = proof.the(r, reason.because)
	f2 = valid(r2, level+1)
	if f2 == None:
	    return fail("Extraction: validation of source forumla failed.")
#	setchatty
	if not f2.includes(f):
	    return fail("""Extraction %s not included in formula  %s.\n______________\n%s\n______________not included in formula ______________\n%s"""
		    %(f, f2, f.n3String(), f2.n3String()), level=level)
	return f

    s = ""
    for x in proof.statementsMatching(subj=r): s = `x` + "\n"
    return fail("Reason %s is of unknown type %s.\n%s"%(r,t, s), level=level)

# Main program 
	    
parsed = {}
setVerbosity(0)

inputURI = argv[1]
fyi("Reading proof from "+inputURI)
proof = load(inputURI)
#setVerbosity(60)
fyi("Length of proof: "+`len(proof)`)
proof2 = proof.the(pred=rdf.type, obj=reason.Proof)  # the thing to be proved


proved = valid(proof2)
if proved != None:
    fyi("Proof looks OK.")
    print proved.n3String()
    exit(0)
progress("Proof invalid.")
exit(-1)

#ends

