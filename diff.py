#! /usr/bin/python
"""
Find differences between two RDF graphs, using
functional and inverse functional properties to identify parts bnodes
in the patch file.

--from    -f uri     from-file
--to      -t uri     file against which to check for differences
--help    -h         print this help message
--verbose -v         verbose mode 

If from-file but not to-file is given, from-file is smushed and output
Uris are relative to present working directory.
$Id$
http://www.w3.org/2000/10/swap/diff.py
"""



import string, getopt
from sets import Set    # Python2.3 and on
import string
import sys




# http://www.w3.org/2000/10/swap/
import llyn
from myStore import loadMany
from diag import verbosity, setVerbosity, progress
import notation3    	# N3 parsers and generators


from RDFSink import FORMULA, LITERAL, ANONYMOUS, Logic_NS
import uripath
from uripath import base
from myStore import  Namespace
import myStore
from notation3 import RDF_NS_URI
from llyn import Formula, CONTEXT, PRED, SUBJ, OBJ

#daml = Namespace("http://www.daml.org/2001/03/daml+oil#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
LOG = Namespace("http://www.w3.org/2000/10/swap/log#")
DELTA = Namespace("http://www.w3.org/2004/delta#")

def lookUp(predicates):
    """Look up al lthe schemas for the predicates given"""
    global verbose
    schemas = Set()
    for pred in predicates:
	if verbose: progress("Predicate: %s" % `pred`)
	u = pred.uriref()
	hash = u.find("#")
	if hash <0:
	    if verbose: progress("Warning: Predicate <%s> looks like web resource not Property" % u)
	else:
	    schemas.add(u[:hash])
    if verbose:
	for r in schemas:
	    progress("Schema: ", r) 
    if schemas:
	return loadMany([(x) for x in schemas])
    return None
    
def nailFormula(f):
    """Smush the formula.
    Build a dictionary of nodes which are indirectly identified
    by [inverse] functonal properties."""
    global verbose
    cc, predicates, ss, oo = getParts(f)
    nodes = ss | oo
    sofar = {}
    bnodes = Set()
    for node in nodes:
	if node.generated() or node in f.existentials():
	    bnodes.add(node)
	    if verbose: progress("Blank node: %s" % `node`)
	else:
	    if verbose: progress("Fixed node: %s" % `node`)
	sofar[node] = []

    meta = lookUp(predicates)
    ifps = predicates & Set(meta.each(pred=RDF.type, obj=OWL.InverseFunctionalProperty))
    fps = predicates & Set(meta.each(pred=RDF.type, obj=OWL.FunctionalProperty))
    if verbose:
	for p in fps:  progress("Functional Property:", p)
	for p in ifps: progress("Inverse Functional: ", p)
    
    a = float(len(bnodes))/len(nodes)
    if verbose: progress("Proportion of bodes which are blank: %f", a)
    if a == 0: return

    loose = bnodes.copy()
    definitions = []
    equivs = Set()
    #  Note possible optmization: First pass only like this, 
    # future passes work from newNodes.
    while loose:
	newNailed = Set()
	for preds, inverse, char in ((fps, 0, "."), (ifps, 1, "^")):
	    for pred in preds:
		if verbose: progress("Predicate", pred)
		ss = f.statementsMatching(pred=pred)
		for s in ss:
		    if inverse: y, x = s.object(), s.subject()
		    else: x, y = s.object(), s.subject()
		    if not x.generated(): continue  # Only anchor bnodes
		    if y not in loose:  # y is the possible anchor
			defi = (x, inverse, pred, y)
			if x in loose:   # this node
			    if verbose: progress("   Nailed %s as %s%s%s" % (x, y, char, pred))
			    loose.discard(x)
			    newNailed.add(x)
			else:
			    if verbose: progress("   (ignored %s as %s%s%s)" % (x, y, char, pred))
			definitions.append(defi)
#			if verbose: progress("   Definition[x] is now", definition[x])
			if inverse: equivalentSet = Set(f.each(obj=y, pred=pred))
			else: equivalentSet = Set(f.each(subj=y, pred=pred))
			if len(equivalentSet) > 1: equivs.add(equivalentSet)

	if not newNailed:
	    if verbose: progress("Failed for", loose)
	    raise ValueError("Graph insufficiently labelled for nodes: %s" % loose)
    if verbose: progress("Graph is solid.")
    f.reopen()
    for es in equivs:
	if verbose: progress("Equivalent: ", es)
	prev = None
	for x in es:
	    if prev:
		f.add(x, OWL.sameAs, prev)
	    prev = x
    return bnodes, definitions

def removeCommon(f, g, match):
    """Find common statements from f and g
    macth gives the dictionary mapping bnodes in f to bnodes in g"""
    only_f, common_g = Set(), Set()
    for st in f.statements[:]:
	s, p, o = st.spo()
	assert s not in f._redirections 
	assert o not in f._redirections
	if s.generated(): sg = match[s]
	else: sg = s
	if o.generated(): og = match[o]
	else: og = o
	gsts = g.statementsMatching(subj=sg, pred=p, obj=og)
	if len(gsts) == 1:
	    if verbose: progress("Statement in both", st)
	    common_g.add(gsts[0])
	else:
	    only_f.add(st)
    return only_f, Set(g.statements)-common_g

def patches(delta, f, only_f, originalBnodes, definitions, deleting=0):
    """Generate patches in patch formula, for the remaining statements in f
    given the bnodes and definitions for f."""
    todo = only_f.copy()
    if deleting:
	patchVerb = DELTA.deletion
    else:
	patchVerb = DELTA.insertion
    if verbose: progress("Patch:", patchVerb)
    while todo:

	# find a contiguous subgraph defined in the given graph
	bnodesToDo = Set()
	bnodes = Set()
	rhs = delta.newFormula()
	lhs = delta.newFormula()  # left hand side of patch
	newStatements = Set()
	for seed in todo: break # pick one #@2 fn?
	statementsToDo = Set([seed])
	if verbose: progress("Seed:", seed)
	subgraph = statementsToDo
	while statementsToDo or bnodesToDo:
	    for st in statementsToDo:
		s, p, o = st.spo()
		for x in s, p, o:
		    if x.generated() and x not in bnodes: # and x not in commonBnodes:
			if verbose: progress("   Bnode ", x)
			bnodesToDo.add(x)
			bnodes.add(x)
		rhs.add(s, p, o)
	    statementsToDo = Set()
	    for x in bnodesToDo:
		bnodes.add(x)
		ss = (f.statementsMatching(subj=x)
		    + f.statementsMatching(pred=x)
		    + f.statementsMatching(obj=x))
		for z in ss:
		    if z in only_f:
			newStatements.add(z)
		if verbose: progress("    New statements from %s: %s" % (x, newStatements))
		statementsToDo = statementsToDo | newStatements
		subgraph = subgraph |newStatements
	    bnodesToDo = Set()

	if verbose: progress("Subgraph of %i statements:\n\t%s\n" %(len(subgraph), subgraph))
	todo = todo - subgraph
	
	
	undefined = bnodes.copy()
	for x, inverse, pred, y in definitions:
	    if x in undefined:
		if inverse: s, p, o = x, pred, y
		else: s, p, o = y, pred, x
		if deleting:
		    delta.declareUniversal(x)
		    lhs.add(subj=s, pred=p, obj=o)
		else: # inserting
		    if x in originalBnodes:
			delta.declareUniversal(x)
			lhs.add(subj=s, pred=p, obj=o)
		    else:
			rhs.declareExistential(x)
		if y.generated():
		    undefined.add(y)
		undefined.discard(x)
	if undefined: raise RunTimeError("Still undefined", undefined)

	delta.add(subj=lhs.close(), pred=patchVerb, obj=rhs.close())
    return


def differences(f, g):
    """Smush the formulae.  Compare them, generating patch instructions."""
    
# Cross-map nodes:

    g_bnodes, g_definitions = nailFormula(g)
    bnodes, definitions = nailFormula(f)

    definitions.reverse()  # go back down list @@@ revers eth g list too? @@@

    unmatched = bnodes.copy()
    match = {}  # Mapping of nodes in f to nodes in g
    for x, inverse, pred, y in definitions:
	if x in match: continue # done already
#       for x in bnodes:
	if x in f._redirections:
	    if verbose: progress("Redirected %s to %s. Ignoring" % (x, f._redirections[x]))
	    unmatched.discard(x)
	    continue

	if verbose: progress("Definition %s = %s%s%s"% (x,  pred, ".^"[inverse], y))

	if y.generated():
	    while y in f._redirections:
		y = f._redirections[y]
		if verbose: progress(" redirected to  %s = %s%s%s"% (x,  pred, ".^"[inverse], y))
	    yg = match.get(y, None)
	    if yg == None:
		if verbose: progress("  Had definition for %s in terms of %s which is not matched"%(x,y))
		continue
	else:
	    yg = y

	if inverse:  # Innverse functional property like ssn
	    matches = Set(g.each(obj=yg, pred=pred))
	else: matches = Set(g.each(subj=yg, pred=pred))
	if len(matches) == 0:
	    raise RuntimeError("Can't match %s" % x)
	if len(matches) > 1:
	    raise RuntimeError("More than 1 match for %s: 6s" % (x, matches))
	for q in matches:  # pick only one  @@ python function?
	    z = q
	    break
	if verbose:
	    progress("Found match for %s in %s " % (x,z))
	match[x] = z
	unmatched.discard(x)

    if len(unmatched) > 0:
	if verbose: progress("Failed to match all nodes:", unmatched)
	raise RuntimeError(
	    "@@@ TBC - bnode match by canonicalization not implemented yet. Failed to match:",
	    unmatched)

    # Find common parts
    only_f, only_g = removeCommon(f,g, match)

    delta = f.newFormula()
    if len(only_f) == 0 and len(only_g) == 0:
	return delta

    f = f.close()    #  We are not going to mess with them any more
    g = g.close()
    
    common = Set([match[x] for x in match])

    if verbose: progress("Comon nodes (in g)", common)
    patches(delta, f, only_f, Set(), definitions, deleting=1)
    patches(delta, g, only_g, common, g_definitions, deleting=0)
    
    return delta

	
     
def getParts(f, meta=None):
    """Make lists of all node IDs and arc types
    """
    values = [Set([]),Set([]),Set([]),Set([])]
    for s in f.statements:
	for p in SUBJ, PRED, OBJ:
	    x = s[p]
	    values[p].add(x)
    return values


def loadFiles(files):
    graph = myStore.formula()
    graph.setClosureMode("e")    # Implement sameAs by smushing
    graph = myStore.loadMany(files, openFormula=graph)
    if verbose: progress("Loaded", graph, graph.__class__)
    return graph

def usage():
    sys.stderr.write(__doc__)
    
def main():
    testFiles = []
    diffFiles = []
    global ploughOn # even if error
    ploughOn = 0
    global verbose
    verbose = 0
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:t:v",
	    ["help", "from=", "to=", "verbose"])
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)
    output = None
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-v", "--verbose"):
	    verbose = 1
	if o in ("-f", "--from"):
	    testFiles.append(a)
	if o in ("-t", "--to"):
	    diffFiles.append(a)

    

#    if testFiles == []: testFiles = [ "/dev/stdin" ]
    if testFiles == []:
	usage()
	sys.exit(2)
    graph = loadFiles(testFiles)
    version = "$Id$"[1:-1]
    if diffFiles == []:
	nailFormula(graph)
	if verbose: print "# Smush by " + version
	print graph.close().n3String(base=base(), flags="a")
	sys.exit(0)
	
    graph2 = loadFiles(diffFiles)
    delta = differences(graph, graph2)
    if verbose: print "# Differences by " + version
    print delta.close().n3String(base=base())
    sys.exit(len(delta))
    
	
		
if __name__ == "__main__":
    main()


	
