#! /usr/bin/python
"""

$Id$

Printing of N3 and RDF formulae

20003-8-20 split offf from llyn.py

This is or was http://www.w3.org/2000/10/swap/pretty.py
"""


import types
import string

import diag  # problems importing the tracking flag, must be explicit it seems diag.tracking
from diag import progress, progressIndent, verbosity, tracking
from term import   Literal, Symbol, Fragment, FragmentNil, \
    Anonymous, Term, CompoundTerm, List, EmptyList, NonEmptyList
from formula import Formula, compareTerm, StoredStatement

from RDFSink import Logic_NS, RDFSink, forSomeSym, forAllSym
from RDFSink import CONTEXT, PRED, SUBJ, OBJ, PARTS, ALL4
from RDFSink import N3_nil, N3_first, N3_rest, OWL_NS, N3_Empty, N3_List, List_NS
from RDFSink import RDF_NS_URI
from RDFSink import RDF_type_URI
from RDFSink import FORMULA, LITERAL, ANONYMOUS, SYMBOL

cvsRevision = "$Revision$"

# Magic resources we know about

from RDFSink import RDF_type_URI, DAML_equivalentTo_URI

STRING_NS_URI = "http://www.w3.org/2000/10/swap/string#"
META_NS_URI = "http://www.w3.org/2000/10/swap/meta#"
INTEGER_DATATYPE = "http://www.w3.org/2001/XMLSchema#integer"
FLOAT_DATATYPE = "http://www.w3.org/2001/XMLSchema#double"


class Serializer:
    """A serializer to serialize the formula F into the given
    abstract syntax sink
    """
    def __init__(self, F, sink, flags="", sorting=0):
	self.context = F
	assert F.canonical != None, "Formula to be printed must be canonical"
	self.store = F.store
	self.sink = sink
	self.defaultNamespace = None
	self.flags = flags
	self.sorting = sorting
	self._inContext ={}
	self._occurringAs = [{}, {}, {}, {}]

    def selectDefaultPrefix(self, context):

        """ Symbol whose fragments have the most occurrences.
        we suppress the RDF namespace itself because the XML syntax has problems with it
        being default as it is used for attributes."""

        counts = {}   # Dictionary of how many times each
        closure = self._subFormulae(context)    # This context and all subFormulae
	counts[self.store.implies.resource] = 0
        for con in closure:
	    for x in con.existentials() + con.universals():
		if self._inContext.get(x, "foo") != "foo": # actually mentioned
		    _anon, _incoming = self._topology(x, con)
		    if not _anon:
			r = x.resource
			total = counts.get(r, 0) + 1
			counts[r] = total
		    counts[self.store.forAll.resource] = counts[self.store.forAll.resource] + 1
            for s in con.statements:
                for p in PRED, SUBJ, OBJ:
                    x = s[p]
                    if (x is self.store.first or x is self.store.rest) and p == PRED:
                        continue  # ignore these - they tend to be in lists
                    if isinstance(x, Fragment):
                        _anon, _incoming = self._topology(x, con)
                        if not _anon and not isinstance(x, Formula):
                            r = x.resource
                            total = counts.get(r, 0) + 1
                            counts[r] = total
        best = 0
        mp = None
        for r, count in counts.items():
            if verbosity() > 25: progress("    Count is %3i for %s" %(count, r.uriref()))
            if (r.uri != RDF_NS_URI[:-1]
                and count > 0
		and (count > best or
                     (count == best and mp.uriref() > r.uriref()))) :  # Must be repeatable for retests
                best = count
                mp = r

        if verbosity() > 20:
            progress("# Most popular Namespace in %s is %s with %i" % (`context`, `mp`, best))

        if mp is None: return counts
        self.defaultNamespace = mp.uriref()+"#"
        return counts

    def _subFormulae(self, F, path = []):
        """Returns a sequence of the all the formulae nested within this one.
        
	slow... only used in pretty print functions.
        """

	set = [F]
        path2 = path + [ F ]     # Avoid loops
        for s in F.statements:
            for p in PRED, SUBJ, OBJ:
                if isinstance(s[p], Formula):
                    if s[p] not in path2:
                        set2 = self._subFormulae(s[p], path2)
                        for c in set2:
                            if c not in set: set.append(c)
        return set

        


    def dumpPrefixes(self, sink, counts=None):
	if self.defaultNamespace != None:
	    sink.setDefaultNamespace(self.defaultNamespace)
        prefixes = self.store.namespaces.keys()   #  bind in same way as input did FYI
        prefixes.sort()
#	if counts:
#	    for pfx in prefixes:
#		uri = self.store.namespaces[pfx]
#		r = self.store.symbol(uri[:-1])  # Remove trailing slash
#		n = counts.get(r, -1)
#		if verbosity()>20: progress("   Prefix %s has %i" % (pfx, n))
#		if n > 0:
#		    sink.bind(pfx, uri)	    
#	else:
	for pfx in prefixes:
	    uri = self.store.namespaces[pfx]
	    sink.bind(pfx, uri)


    def _listsWithinLists(self, L, lists):
	if L not in lists:
	    lists.append(L)
	for i in L:
	    if isinstance(i, NonEmptyList):
		self._listsWithinLists(i, lists)

    def dumpLists(self):
	context = self.context
	sink = self.sink
	lists = []
	for s in context.statements:
#	    progress("&&&& cehck ", `s`)

	    for x in s.predicate(), s.subject(), s.object():
		if isinstance(x, NonEmptyList):
#		    progress("&&&&", x)
		    self._listsWithinLists(x, lists)
		    
	for l in lists:
	    list = l
	    while not isinstance(list, EmptyList):
		self._outputStatement(sink, (context, self.store.forSome, context, list))
		list = list.rest

	for l in lists:
	    list = l
	    while not isinstance(list, EmptyList):
		self._outputStatement(sink, (context, self.store.first, list, list.first))
		self._outputStatement(sink, (context, self.store.rest,  list, list.rest))
		list = list.rest


    def dumpChronological(self):
	"Fast as possible. Only dumps data. No formulae or universals."
	context = self.context
	sink = self.sink
        sink.startDoc()
        self.dumpPrefixes(sink, None)
	self.dumpVariables(context, sink, sorting=0, dataOnly=1)
	uu = context.universals()

	self.dumpLists()
	
        for s in context.statements:
	    for p in SUBJ, PRED, OBJ:
		x = s[p]
		if isinstance(x, Formula) or x in uu:
		    break
	    else:
		self._outputStatement(sink, s.quad)
		    
        sink.endDoc()

    def _outputStatement(self, sink, quad):
        sink.makeStatement(self.extern(quad))

    def extern(self, t):
        return(t[CONTEXT].asPair(),
                            t[PRED].asPair(),
                            t[SUBJ].asPair(),
                            t[OBJ].asPair(),
                            )

    def dumpVariables(self, context, sink, sorting=1, pretty=0, dataOnly=0):
	"""Dump the forAlls and the forSomes at the top of a formula"""
	if sorting:
	    uv = context.universals()[:]
	    uv.sort(compareTerm)
	    ev = context.existentials()[:]
	    ev.sort(compareTerm)
	else:
	    uv = context.universals()
	    ev = context.existentials()
	if not dataOnly:
	    for v in uv:
		self._outputStatement(sink, (context, self.store.forAll, context, v))
	for v in ev:
	    if pretty:
		_anon, _incoming = self._topology(v, context)
	    else:
		_anon = 0
	    if not _anon:
		self._outputStatement(sink, (context, self.store.forSome, context, v))

    def dumpBySubject(self, sorting=1):
        """ Dump by order of subject except forSome's first for n3=a mode"""
        
	context = self.context
	sink = self.sink
	self._scan(context)
        counts = self.selectDefaultPrefix(context)        
        sink.startDoc()
        self.dumpPrefixes(sink, counts)

	self.dumpVariables(context, sink, sorting)
	
	self.dumpLists()
	
        rs = self.store.resources.values()
        if sorting: rs.sort(compareTerm)
        for r in rs :  # First the bare resource
            statements = context.statementsMatching(subj=r)
            if sorting: statements.sort(StoredStatement.comparePredObj)
            for s in statements :
#                if not(context is s.quad[SUBJ]and s.quad[PRED] is self.store.forSome):
                    self._outputStatement(sink, s.quad)
            if not isinstance(r, Literal):
                fs = r.fragments.values()
                if sorting: fs.sort
                for f in fs :  # then anything in its namespace
                    statements = context.statementsMatching(subj=f)
                    if sorting: statements.sort(StoredStatement.comparePredObj)
                    for s in statements:
                        self._outputStatement(sink, s.quad)
        sink.endDoc()
#
#  Pretty printing
#
#   x is an existential if there is in the context C we are printing
# is a statement  (C log:forSome x). If so, the anonymous syntaxes follow.
#
# An intersting alternative is to use the reverse syntax to the max, which
# makes the DLG an undirected labelled graph. s and o above merge. The only think which
# then prevents us from dumping the graph without new bnode ids is the presence of cycles.

# Blank nodes can be represented using the implicit syntax [] or rdf/xml equivalent
# instead of a dummy identifier iff
# - they are blank nodes, ie are existentials whose id has been generated, and
# - the node only occurs directly in one formula in the whole thing to be printed, and
# - the node occurs at most once as a object or list element within that formula

# We used to work this out on the fly, but it is faster to build an index of the
# whole formula to be printed first.
#
# Note when we scan a list we do it in the context of the formula in which we found
# it.  It may occcur in many formulae.

    def _scanObj(self, context, x):
	z = self._inContext.get(x, None)
	if z == "many": return # forget it
	if z == None:
	    self._inContext[x] = context
	elif z is not context:
	    self._inContext[x] = "many"
	    return
	if isinstance(x, Fragment) and x.generated(): 
	    y = self._occurringAs[OBJ].get(x, 0) + 1
	    self._occurringAs[OBJ][x] = y

    def _scan(self, x, context=None):
#	assert self.context._redirections.get(x, None) == None, "Should not be redirected: "+`x`
	if verbosity() > 98: progress("scanning %s in context %s" %(`x`, `context`),
			x.generated(), self._inContext.get(x, "--"))
	if isinstance(x, NonEmptyList):
	    for y in x:
		self._scanObj(context, y)
	if isinstance(x, Formula):
	    for s in x.statements:
		for p in PRED, SUBJ, OBJ:
		    y = s[p]
		    if isinstance(y, Fragment) and y.generated(): 
			z = self._inContext.get(y, None)
			if z == "many": continue # forget it
			if z == None:
			    self._inContext[y] = x
			elif z is not x:
			    self._inContext[y] = "many"
			    continue
			z = self._occurringAs[p].get(y, 0)
			self._occurringAs[p][y] = z + 1
		    self._scan(y, x)
		


    def _topology(self, x, context): 
        """ Can be output as an anonymous node in N3. Also counts incoming links.
        Output tuple parts:

        1. True iff can be represented as anonymous node in N3, [] or {}
        2. Number of incoming links: >0 means occurs as object or pred, 0 means as only as subject.
            1 means just occurs once
            >1 means occurs too many times to be anon
        
        Returns  number of incoming links (1 or 2) including forSome link
        or zero if self can NOT be represented as an anonymous node.
        Paired with this is whether this is a subexpression.
        """

        _isExistential = x in context.existentials()
        _loop = context.any(subj=x, obj=x)  # does'nt count as incomming
	_asPred = self._occurringAs[PRED].get(x, 0)
	_asObj = self._occurringAs[OBJ].get(x, 0)
        if isinstance(x, Literal):
            _anon = 0     #  Never anonymous, always just use the string
	elif isinstance(x, Formula):
	    _anon = 2	# always anonymous, represented as itself
		
	elif isinstance(x, List):
	    if isinstance(x, EmptyList):
		_anon = 0     #  Never anonymous, always just use the string
	    else:
		_anon = 2	# always anonymous, represented as itself
		_isExistential = 1
	elif not x.generated():
	    _anon = 0	# Got a name, not anonymous
        else:  # bnode
	    ctx = self._inContext.get(x, "weird")
	    _anon = ctx == "weird" or (ctx is context and
			_asObj < 2 and _asPred == 0 and
			(not _loop) and
			_isExistential)
	    if verbosity() > 98:
		progress( "Topology %s in %s is: ctx=%s,anon=%i obj=%i, pred=%i loop=%s ex=%i "%(
		`x`, `context`, `ctx`, _anon, _asObj, _asPred, _loop, _isExistential))
	    return ( _anon, _asObj+_asPred )  

        if verbosity() > 98:
            progress( "Topology %s in %s is: anon=%i obj=%i, pred=%i loop=%s ex=%i "%(
            `x`, `context`,  _anon, _asObj, _asPred, _loop, _isExistential))

        return ( _anon, _asObj+_asPred )  


  
    def dumpNested(self):
        """ Iterates over all URIs ever seen looking for statements
        """
	context = self.context
        assert context.canonical != None
	self._scan(context)
	counts = self.selectDefaultPrefix(context)        
        self.sink.startDoc()
        self.dumpPrefixes(self.sink, counts)
        self.dumpFormulaContents(context, self.sink, sorting=1)
        self.sink.endDoc()

    def dumpFormulaContents(self, context, sink, sorting):
        """ Iterates over statements in formula, bunching them up into a set
        for each subject.
        We dump "this" first before everything else
        """
        if sorting: context.statements.sort(StoredStatement.compareSubjPredObj)
# @@ necessary?
	self.dumpVariables(context, sink, sorting, pretty=1)

	statements = context.statementsMatching(subj=context)  # context is subject
        if statements:
	    progress("@@ Statement with context as subj?!", statements,)
            self._dumpSubject(context, context, sink, sorting, statements)

        currentSubject = None
        statements = []
        for s in context.statements:
            con, pred, subj, obj =  s.quad
            if subj is con: continue # Done them above
            if currentSubject == None: currentSubject = subj
            if subj != currentSubject:
                self._dumpSubject(currentSubject, context, sink, sorting, statements)
                statements = []
                currentSubject = subj
            statements.append(s)
        if currentSubject != None:
            self._dumpSubject(currentSubject, context, sink, sorting, statements)


    def _dumpSubject(self, subj, context, sink, sorting, statements=[]):
        """ Dump the infomation about one top level subject
        
        This outputs arcs leading away from a node, and where appropriate
     recursively descends the tree, by dumping the object nodes
     (and in the case of a compact list, the predicate (rest) node).
     It does NOTHING for anonymous nodes which don't occur explicitly as subjects.

     The list of statements must be sorted if sorting is true.     
        """
        _anon, _incoming = self._topology(subj, context)    # Is anonymous?
        if _anon and  _incoming == 1 and not isinstance(subj, Formula): return   # Forget it - will be dealt with in recursion

	if isinstance(subj, List): li = subj
	else: li = None
	
        if isinstance(subj, Formula) and subj is not context:
            sink.startBagSubject(subj.asPair())
            self.dumpFormulaContents(subj, sink, sorting)  # dump contents of anonymous bag
            sink.endBagSubject(subj.asPair())       # Subject is now set up
            # continue to do arcs
            
        elif _anon and (_incoming == 0 or 
	    (li != None and not isinstance(li, EmptyList))):    # Will be root anonymous node - {} or [] or ()
		
            if subj is context:
                pass
            else:     #  Could have alternative syntax here

                if sorting: statements.sort(StoredStatement.comparePredObj)    # @@ Needed now Fs are canonical?

                if li != None and not isinstance(li, EmptyList):
                    for s in statements:
                        p = s.quad[PRED]
                        if p is not self.store.first and p is not self.store.rest:
			    if verbosity() > 90: progress("@ Is list, has values for", `p`)
                            break # Something to print (later)
                    else:
			if subj.generated(): return # Nothing.
                    sink.startAnonymousNode(subj.asPair(), li)
		    self.dumpStatement(sink, (context, self.store.first, subj, subj.first), sorting)
		    self.dumpStatement(sink, (context, self.store.rest, subj,  subj.rest), sorting)
		    sink.endAnonymousNode(subj.asPair())
                    for s in statements:
                        p = s.quad[PRED]
                        if p is not self.store.first and p is not self.store.rest:
                            self.dumpStatement(sink, s.quad, sorting) # Dump the rest outside the ()
                    return
                else:
		    if verbosity() > 90: progress("%s Not list, has values for" % `subj`)
                    sink.startAnonymousNode(subj.asPair())
                    for s in statements:  #   [] color blue.  might be nicer. @@@$$$$  Try it!
                        self.dumpStatement(sink, s.quad, sorting)
                    sink.endAnonymousNode()
                    return  # arcs as subject done


        if sorting: statements.sort(StoredStatement.comparePredObj)
        for s in statements:
            self.dumpStatement(sink, s.quad, sorting)

                
    def dumpStatement(self, sink, triple, sorting):
	"Dump one statement, including structure within object" 

        context, pre, sub, obj = triple
        if (sub is obj and not isinstance(sub, CompoundTerm))  \
           or (isinstance(obj, EmptyList)) \
           or isinstance(obj, Literal):
            self._outputStatement(sink, triple) # Do 1-loops simply
            return


        if isinstance(obj, Formula):
            sink.startBagObject(self.extern(triple))
            self.dumpFormulaContents(obj, sink, sorting)  # dump contents of anonymous bag
            sink.endBagObject(pre.asPair(), sub.asPair())
            return

	if isinstance(obj, NonEmptyList):
	    if verbosity()>90:
		progress("List found as object of dumpStatement " + `obj` + context.debugString())
	    sink.startAnonymous(self.extern(triple), isList=1)
	    self.dumpStatement(sink, (context, self.store.first, obj, obj.first), sorting)
	    self.dumpStatement(sink, (context, self.store.rest, obj, obj.rest), sorting)
	    sink.endAnonymous(sub.asPair(), pre.asPair()) # Restore parse state
	    return

        _anon, _incoming = self._topology(obj, context)
        if _anon and _incoming == 1:  # Embedded anonymous node in N3
	    sink.startAnonymous(self.extern(triple))
	    ss = context.statementsMatching(subj=obj)
	    if sorting: ss.sort(StoredStatement.comparePredObj)
	    for t in ss:
		self.dumpStatement(sink, t.quad, sorting)
	    sink.endAnonymous(sub.asPair(), pre.asPair()) # Restore parse state
            return

        self._outputStatement(sink, triple)
	

#ends

