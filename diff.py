#! /usr/bin/python
"""
$Id$

Find differences between two webs

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


def nailFormula(f):
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
	meta = loadMany([(x) for x in schemas])
    ifps = predicates & Set(meta.each(pred=RDF.type, obj=OWL.InverseFunctionalProperty))
    fps = predicates & Set(meta.each(pred=RDF.type, obj=OWL.FunctionalProperty))
    if verbose:
	for p in fps:  progress("Functional Property:", p)
	for p in ifps: progress("Inverse Functional: ", p)
    
    a = float(len(bnodes))/len(nodes)
    if verbose: progress("Proportion of bodes which are blank: %f", a)
    if a == 0: return

    loose = bnodes.copy()
    nailing = {}
    equivs = Set()
    while loose:
	newNailed = Set()
	for pred in fps:
	    ss = f.statementsMatching(pred=pred)
	    for s in ss:
		x = s.object()
		y = s.subject()
		if y not in loose:
		    if x in loose:
			loose.discard(x)
			newNailed.add(x)
			nailing[x] = s
			if verbose: progress("Nailed %s as %s!%s" % (x, y, pred))
		    else:
			if verbose: progress("Re-Nailed %s as %s!%s" % (x, y, pred))
		    equivalentSet = Set(f.each(subj=y, pred=pred))
		    if len(equivalentSet) > 1: equivs.add(equivalentSet)

	for pred in ifps:
	    ss = f.statementsMatching(pred=pred)
	    for s in ss:
		x = s.subject()
		y = s.object()
		if y not in loose:
		    if x in loose:
			loose.discard(x)
			newNailed.add(x)
			nailing[x] = s
			if verbose: progress("Nailed %s as %s.%s" % (x, y, pred))
		    else:
			if verbose: progress("Re-Nailed %s as %s.%s" % (x, y, pred))
		    equivalentSet = Set(f.each(obj=y, pred=pred))
		    if len(equivalentSet) > 1: equivs.add(equivalentSet)
			
	if not newNailed:
	    progress("Failed for", loose)
	    break

    f.reopen()
    for es in equivs:
	progress("Equivalent: ", es)
	prev = None
	for x in es:
	    if prev:
		f.add(x, OWL.sameAs, prev)
	    prev = x
    f = f.close()
    print f.n3String()

     
def getParts(f, meta=None):
    """Make lists of all node IDs and arc types
    """
    values = [Set([]),Set([]),Set([]),Set([])]
    if meta == None: meta == f
    for s in f.statements:
	for p in SUBJ, PRED, OBJ:
	    x = s[p]
	    values[p].add(x)
    return values

def smush(f, meta=None):
    """Munge a formula so that equivalent nodes are replaced by a single node.
    Equivalence is deduced from "=" or from unique (functional) or unambiguous 
    (inverse functional) properties.
    The equivalent pairs are described by direcetd relations
    """
    if meta == None: meta == f
    values = getParts(f)
    predicates = values[PRED]
    subjects = values[SUBJ]
    objects = values[OBJ]
    for p in pred:
	if meta.contains(subj=p, pred=rdf.type, obj=owl.UniqueProperty):
	    unique.append(p)
	if meta.contains(subj=p, pred=rdf.type, obj=owl.UnambiguousProperty):
	    unambiguous.append(p)
    equavalent = [daml.sameAs]

    # Make an list of equivalent nodes:
    pairs = []
    for st in f.statments:
	context, pred, subj, obj = s.quad
	if p in equivalent:
	    if subj < obj: pairs.append((subj, obj))
	    else: pairs.append((obj,subj))
	if pred in unique:
	    for s in f.each(pred=pred, obj=s[OBJ]):
		if s < subj: pairs.append((s, subj))
		else: paits.append((subj, s)) 
	if pred in unambiguous:
	    for o in f.each(subj=t[SUBJ], pred=pred):
		if o < obj: pairs.append((o, obj))
		else: pairs.append((obj, o))
    pairs.sort()
    # May contain duplicates - this would waste time
    # We build an index of a pointer for each member of an equivalence class,
    # the chosen (smallest) representative member
	
    cannonical = {}
    last = None, None
    for hi, lo in pairs:
	if (hi, lo) != last: 
	    cannonical[hi] = cannonical.get(lo, lo)
	last = hi, lo
	
    # Now do change the actual formula
    for hi in cannonical.keys():
	if verbosity() > 30: progress("smush: %s becomes %s", `hi`, `lo`)
	f.replaceWith(hi, lo)



def loadFiles(files):
    graph = myStore.formula()
    graph.setClosureMode("e")    # Implement sameAs by smushing
    graph = myStore.loadMany(files, openFormula=graph)
    if verbose: progress("Loaded", graph, graph.__class__)
    return graph
    
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
    graph = loadFiles(testFiles)
    nailFormula(graph)
    sys.exit(0)
    
    if diffFiles != []:
	graph2 = loadFiles(diffFiles)
	graph2 = canonicalize(graph2)
	d = compareCanonicalGraphs(graph, graph2)
	if d != 0:
	    sys.exit(d)
    else:
        serialize(graph)


	
		
if __name__ == "__main__":
    main()


	
