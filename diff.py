#! /usr/bin/python
"""
Find differences between two RDF graphs

-f uri     from-file
-d uri     file against which to check fro differences
-h         print this help message
-v         verbose mode 

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
from uripath import join
from myStore import  Namespace
import myStore
from notation3 import RDF_NS_URI
from llyn import Formula, CONTEXT, PRED, SUBJ, OBJ

#daml = Namespace("http://www.daml.org/2001/03/daml+oil#")
OWL = Namespace("http://www.w3.org/2002/07/owl#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
LOG = Namespace("http://www.w3.org/2000/10/swap/log#")
def tryNode(x, f, already=[]):
    """The nailing of a term x within a graph f is the set s of statements
    taken from f such that when one is given s, one can uniquely determine the identity of x.
    
    returns EITHER a sequence of possible branches. A possible branch give sthe statement
	    by which, if the otherend was nailed, x would be.
	OR a statement which nails x 
	or None - impossible, sorry.
    Possible future enhancements:  Multi-field keys -- connects to multi-property functions.
    """
    if not x.generated():
	return []
    possible = []
    ss = f.statementsMatching(subj=x)
    for t in ss:
	if meta.contains(subj=t[PRED], pred=rdf.type, obj=owl.InverseFunctionalProperty):
	    y = t[OBJ]
	    if not y.generated(): return t # success
	    if y not in already:
		possible.append((OBJ, t, None)) # Could nail it by this branch
    ss = f.statementsMatching(obj=x)
    for t in ss:
	if meta.contains(subj=t[PRED], pred=rdf.type, obj=owl.FunctionalProperty):
	    y = t[SUBJ]
	    if not y.generated(): return t
	    if y not in already:
		possible.append((SUBJ, t, None)) # Could nail it by this branch
    if possible == []: return None # Failed to nail it
    return possible

def tryPossibles(node, f, tree, already=[]):
    """ The tree is a list of branches, each branch being (direction, statement and subtree).
    If subtree is None, the tree has not been elaborated.
    A tree element is a statement and another list, or s statement and unnailed node.
    Returns a path of statements, or None if no path, or 1 if tree just elaborated.
    """
    for i in range(len(tree)):
	dirn, statement, node = tree[i]
	if node == None: # Not elaborated yet? 
	    x = statement[dirn] # far end of link
	    if not x.generated():
		return [ statement ]   # Success!
	    branch = tryNode(x, f, already)
	    if branch == None:
		pass
	    elif type(branch) == type([]):
		tree2.append((dir, statement, branch))
	    else:
		return [statement, branch]
	else:
	    branch = tryPossibles(statement[dirn], f, node, already + [ statement[dirn] ])
	    if branch == None:
		pass
	    elif branch == 1:
		tree2.append((dirn, statement, node))
	    else:
		branch.append(statement)
		return branch
    return 1


def lookUp(predicates):
    """Look up al lthe schemas for the predicates given"""
    global verbose
    schemas = Set()
    for pred in predicates:
	if verbose: progress("Predicate: %s" % `pred`)
	u = pred.uriref()
	hash = u.find("#")
	if hash <0: progress("Warning: Predicate <%s> looks like web resource not Property" % u)
	else: schemas.add(u[:hash])
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
	if node.generated():
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
		ss = f.statementsMatching(pred=pred)
		for s in ss:
		    if inverse: y, x = s.object(), s.subject()
		    else: x, y = s.object(), s.subject()
		    if not x.generated(): continue  # Only anchor bnodes
		    if y not in loose:  # y is the possible anchor
			defi = (x, inverse, pred, y)
			progress("   Defi is ", defi)
			if x in loose:   # this node
			    if verbose: progress("Nailed %s as %s%s%s" % (x, y, char, pred))
			    loose.discard(x)
			    newNailed.add(x)
			else:
			    if verbose: progress("Re-Nailed %s as %s%s%s" % (x, y, char, pred))
			definitions.append(defi)
#			progress("   Definition[x] is now", definition[x])
			if inverse: equivalentSet = Set(f.each(obj=y, pred=pred))
			else: equivalentSet = Set(f.each(subj=y, pred=pred))
			if len(equivalentSet) > 1: equivs.add(equivalentSet)

	if not newNailed:
	    progress("Failed for", loose)
	    break
    progress("Graph 1 is solid.")
    f.reopen()
    for es in equivs:
	progress("Equivalent: ", es)
	prev = None
	for x in es:
	    if prev:
		f.add(x, OWL.sameAs, prev)
	    prev = x
#    f = f.close()
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
	    progress("Statement in both", st)
	    common_g.add(gsts[0])
	else:
	    only_f.add(st)
    progress("Common parts removed, leaves %i in f and %i in g" %(len(f), len(g)))
    return only_f, Set(g.statements)-common_g

def patches(delta, f, only_f, originalBnodes, definitions, deleting=0):
    """Generate patches in patch formula, for the remaining statements in f
    giveb the bnodes and definitions for f."""
    todo = only_f.copy()
    if deleting:
	patchVerb = LOG.deletes
    else:
	patchVerb = LOG.inserts
    progress("Patch:", patchVerb)
    while todo:

	# find a contiguous subgraph defined in the given graph
	bnodesToDo = Set()
	bnodes = Set()
	rhs = delta.newFormula()
	lhs = delta.newFormula()  # left hand side of patch
	newStatements = Set()
	for seed in todo: break # pick one #@2 fn?
	statementsToDo = Set([seed])
	progress("Seed:", seed)
	subgraph = statementsToDo
	while statementsToDo or bnodesToDo:
	    for st in statementsToDo:
		s, p, o = st.spo()
		for x in s, p, o:
		    if x.generated() and x not in bnodes: # and x not in commonBnodes:
			progress("   Bnode ", x)
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
		progress("    New statements from %s: %s" % (x, newStatements))
		statementsToDo = statementsToDo | newStatements
		subgraph = subgraph |newStatements
	    bnodesToDo = Set()

	progress("Subgraph of %i statements:\n\t%s\n" %(len(subgraph), subgraph))
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
    unmatched = bnodes.copy()
    match = {}  # Mapping of nodes in f to nodes in g
    for x, inverse, pred, y in definitions:
	if x in match: continue # done already
#       for x in bnodes:
	if x in f._redirections:
	    progress("Redirected %s to %s. Ignoring" % (x, f._redirections[x]))
	    unmatched.discard(x)
	    continue

	progress("Definition %s = inverse:%i pred=%s y=%s", (x, inverse, pred, y))

	if y.generated():
	    yg = match.get(y, None)
	    if yg == None:
		progress("Had definition for %s in terms of %s which is not matched"%(x,y))
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
	progress("Failed to match all nodes")
	raise RuntimError("bnode match by canonicalization not implemented yet")

    # Find common parts
    only_f, only_g = removeCommon(f,g, match)

    delta = f.newFormula()
    if len(f) == 0 and len(g) == 0:
	return delta

    f = f.close()    #  We are not going to mess with them any more
    g = g.close()
    
    definitions.reverse()  # go back down list

#    progress("f left:- %s\ng left:- %s\n" % (f.n3String(), g.n3String()))
    # Find contiguous bits to express as differences:

    common = Set([match[x] for x in match])
#    common = common & g_bnodes
    progress("Comon nodes (in g)", common)
    patches(delta, f, only_f, Set(), definitions, deleting=1)
    patches(delta, g, only_g, common, g_definitions, deleting=0)
    

#@@@@
    return delta
#    print f.n3String()
	
     
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
        opts, args = getopt.getopt(sys.argv[1:], "hf:d:iv",
	    ["help", "from=", "diff=" "ignoreErrors", "verbose"])
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
        if o in ("-i", "--ignoreErrors"):
	    ploughOn = 1
	if o in ("-f", "--from"):
	    testFiles.append(a)
	if o in ("-d", "--diff"):
	    diffFiles.append(a)

    

#    if testFiles == []: testFiles = [ "/dev/stdin" ]
    if testFiles == [] or diffFiles == []:
	usage()
	sys.exit(2)
    graph = loadFiles(testFiles)
    graph2 = loadFiles(diffFiles)
#    nailFormula(graph2)    # Smush equal nodes in g 
    delta = differences(graph, graph2)
    if verbose: print "# Defferences by $Id$"
    print delta.close().n3String("i")
    sys.exit(len(delta))
    


	
		
if __name__ == "__main__":
    main()


	
