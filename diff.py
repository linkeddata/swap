#! /usr/bin/python
"""
$Id$

Find differences between two webs

"""



import string


import llyn

from diag import verbosity, setVerbosity, progress


import notation3    	# N3 parsers and generators
# import toXML 		#  RDF generator

from RDFSink import FORMULA, LITERAL, ANONYMOUS, Logic_NS
import uripath
import string
import sys
from uripath import join
from term import  Namespace
from notation3 import RDF_NS_URI

from llyn import Formula, CONTEXT, PRED, SUBJ, OBJ

daml = Namespace("http://www.daml.org/2001/03/daml+oil#")
owl = Namespace("http://www.daml.org/2001/03/daml+oil#")   # Same thing for now

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
		if not y.generated(): return t # sucesss§
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

def tryList(node, f, list, already=[]):
    """ The tree is a list of branches, each branch being (direction, statement and subtree).
    If subtree is None, the tree has not been elaborated.
    A list element is a statement and another list, or s statement and unnailed node.
    Returns a path of statements, or None if no path, or 1 if tree just elaborated.
    """
    for i in range(len(list)):
	dirn, statement, node = list[i]
	if node == None: # Not elaborated yet? 
	    x = statement[dirn] # far end of link
	    if not x.generated():
		return [ statement ]
	    branch = tryNode(x, f, already)
	    if branch == None:
		pass
	    elif type(branch) = type([]):
		list2.append((dir, statement, branch))
	    else:
		return [statement, branch]
	else:
	    branch = tryList(statement[dirn], f, node, already + [ statement[dirn] ])
	    if branch == None:
		pass
	    elif branch == 1:
		list2.append((dirn, statement, node)
	    else
		branch.append(statement)
		return branch
    return 1


def getParts(f):
    """Make lists of all node IDs and arc types
    """
    values = [[],[],[],[]]
    if meta == None: meta == f
	for s in s.statements():
	for p in SUBJ, PRED, OBJ:
	    x = s[p]
	    values[p].append(x)
    for p in SUBJ, PRED, OBJ:
	values[p].sort()
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
    for st in f.statments():
	context, pred, subj, obj = s.quad
	if p in equivalent:
	    if subj < obj: pairs.append((subj, obj))
	    else: pairs.append((obj,subj))
	if pred in unique:
	    for s in f.each(pred=pred, obj=s[OBJ])
		if s < subj: pairs.append((s, subj))
		else: paits.append((subj, s)) 
	if pred in unambiguous:
	    for o in f.each(subj=t[SUBJ], pred=pred)
		if o < obj: pairs.append((o, obj))
		else: pairs.append((obj, o))
    pairs.sort()
    # May contain duplicates - this would waste time
    # We build an index of a pointer for each member of an equivalence class,
    # the chosen (smallest) representative member
	
    cannonical = {}
    last = None, None
    for hi, lo in pairs:
	if not hi, lo = last: 
	    cannonical[hi] = cannonical.get(lo, lo)
	last = hi, lo
	
    # Now do change the actual formula
    for hi in cannonical.keys():
	if verbosity() > 30: progress("smush: %s becomes %s", `hi`, `lo`)
	f.replaceWith(hi, lo)


def crossIdentify(f,g, meta=None):
    assert isinstance(f, Formula)
    assert isinstance(g, Formula)
    assert  f.store is g.store
    store = f.store

def diff(f,g, meta=None):
    assert isinstance(f, Formula)
    assert isinstance(g, Formula)
    assert  f.store is g.store
    store = f.store

    fs = f.statements[:]
    N = len(fs)
    
    inserted = store.newFormula()
    deleted  = store.newFormula()
    
    for i in range(N):
	statement = fs[i]
	for part in PRED, SUBJ, OBJ:
	    x = statement[PART]
		@@@@@@@@@@@@@@@@@@
		
		
		#   
		
	
