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
from diag import progress, verbosity, tracking
from term import   Literal, Symbol, Fragment, AnonymousVariable, FragmentNil, \
     Term, CompoundTerm, List, EmptyList, NonEmptyList
from formula import Formula, StoredStatement

from RDFSink import Logic_NS, RDFSink, forSomeSym, forAllSym
from RDFSink import CONTEXT, PRED, SUBJ, OBJ, PARTS, ALL4
from RDFSink import N3_nil, N3_first, N3_rest, OWL_NS, N3_Empty, N3_List, List_NS
from RDFSink import RDF_NS_URI
from RDFSink import RDF_type_URI

cvsRevision = "$Revision$"

# Magic resources we know about

from RDFSink import RDF_type_URI, DAML_sameAs_URI

STRING_NS_URI = "http://www.w3.org/2000/10/swap/string#"
META_NS_URI = "http://www.w3.org/2000/10/swap/meta#"
INTEGER_DATATYPE = "http://www.w3.org/2001/XMLSchema#integer"
FLOAT_DATATYPE = "http://www.w3.org/2001/XMLSchema#double"

prefixchars = "abcdefghijklmnopqustuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

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
	self._topology_returns = {}

    def selectDefaultPrefix(self, printFunction):

        """ Symbol whose fragments have the most occurrences.
        we suppress the RDF namespace itself because the XML syntax has problems with it
        being default as it is used for attributes.
	
	This also outputs the prefixes."""

        if "d" in self.flags:
	    self.defaultNamespace = None
	    self.dumpPrefixes()
	    return

	dummySink = self.sink.dummyClone()
	dummySerializer = Serializer(self.context,
	    sink=dummySink, flags=self.flags+"d", sorting=self.sorting)
	printFunction(dummySerializer)


        best = 0
        mp = None
	counts = dummySink.namespaceCounts()
        for r, count in counts.items():
            if verbosity() > 25: progress("    Count is %3i for %s" %(count, r))
            if (r != RDF_NS_URI
                and count > 0
		and (count > best or
                     (count == best and mp > r))) :  # Must be repeatable for retests
                best = count
                mp = r

        if verbosity() > 20:
            progress("# Most popular Namespace is %s with %i" % ( mp, best))

	self.defaultNamespace = mp

        for r, count in counts.items():
	    if count > 1 and r != mp:
		if self.store.prefixes.get(r, None) == None:
		    p = r
		    if p[-1] in "/#": p = p[:-1]
		    slash = p.rfind("/")
		    if slash >= 0: p = p[slash+1:]
		    i = 0
		    while i < len(p):
			if p[i] in prefixchars:
			    i = i + 1
			else:
			    break
		    p = p[:i]
		    if len(p) <6 and self.store.namespaces.get(p, None) ==None:
			pref = p
		    else:
			p = p[:5]
			for l in (3, 2, 4, 1, 5):
			    if self.store.namespaces.get(p[:l], None) ==None:
				pref = p[:l]
				break	
			else:
			    n = 2
			    while 1:
				pref = p[:3]+`n`
				if self.store.namespaces.get(pref, None) ==None:
				    break
				n = n + 1			
    
		    self.store.bind(pref, r)
		    if verbosity() > 50: progress("Generated @prefix %s: <%s>." % (pref, r))

	if self.defaultNamespace != None:
	    self.sink.setDefaultNamespace(self.defaultNamespace)

#	progress("&&&& Counts: ", counts)
        prefixes = self.store.namespaces.keys()   #  bind in same way as input did FYI
        prefixes.sort()   # For repeatability of test results
	for pfx in prefixes:
	    r = self.store.namespaces[pfx]
	    try:
		count = counts[r]
		if count > 0:
		    self.sink.bind(pfx, r)
	    except KeyError:
		pass
	return


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


    def dumpPrefixes(self):
	if self.defaultNamespace != None:
	    sink.setDefaultNamespace(self.defaultNamespace)
        prefixes = self.store.namespaces.keys()   #  bind in same way as input did FYI
        prefixes.sort()
	for pfx in prefixes:
	    uri = self.store.namespaces[pfx]
	    self.sink.bind(pfx, uri)


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

	    for x in s.predicate(), s.subject(), s.object():
		if isinstance(x, NonEmptyList):
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
        self.dumpPrefixes()
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

    def _outputStatement(self, sink, quad, aWorks = 1):
        sink.makeStatement(self.extern(quad), aIsPossible=aWorks)

    def notAsExtern(self, t):
        return(t[CONTEXT],
                            t[PRED],
                            t[SUBJ],
                            t[OBJ],
                            )

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
	    uv.sort(Term.compareAnyTerm)
	    ev = context.existentials()[:]
	    ev.sort(Term.compareAnyTerm)
	else:
	    uv = context.universals()
	    ev = context.existentials()
	if not dataOnly:
	    for v in uv:
		self._outputStatement(sink, (context, self.store.forAll, context, v))
	for v in ev:
            aWorks = 0
	    if pretty:
		_anon, _incoming = self._topology(v, context)
	    else:
		_anon = 0
	    if not _anon:
		self._outputStatement(sink, (context, self.store.forSome, context, v), \
                                      canItbeABNode(context, v))

    def dumpBySubject(self, sorting=1):
        """ Dump one formula only by order of subject except forSome's first for n3=a mode"""
        
	context = self.context
	uu = context.universals()[:]
	sink = self.sink
	self._scan(context)
        sink.startDoc()
        self.selectDefaultPrefix(Serializer.dumpBySubject)        
	self.dumpVariables(context, sink, sorting)
	self.dumpLists()

	ss = context.statements[:]
	ss.sort(StoredStatement.compareSubjPredObj)
        for s in ss:
	    for p in SUBJ, PRED, OBJ:
		x = s[p]
		if isinstance(x, Formula) or x in uu:
		    break
	    else:
		self._outputStatement(sink, s.quad)
		    
	if 0:  # Doesn't work as ther ei snow no list of bnodes
	    rs = self.store.resources.values()
	    if sorting: rs.sort(Term.compareAnyTerm)
	    for r in rs :  # First the bare resource
		statements = context.statementsMatching(subj=r)
		if sorting: statements.sort(StoredStatement.comparePredObj)
		for s in statements :
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
# An intersting alternative is to use the reverse syntax to the max, which
# makes the DLG an undirected labelled graph. s and o above merge. The only think which
# then prevents us from dumping the graph without new bnode ids is the presence of cycles.
#
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
	"Does this appear in just one context, and if so counts how many times as object"
	z = self._inContext.get(x, None)
	if z == "many": return # forget it
	if z == None:
	    self._inContext[x] = context
	elif z is not context:
	    self._inContext[x] = "many"
	    return
	    
	if isinstance(x, AnonymousVariable) or (isinstance(x, Fragment) and x.generated()): 
	    y = self._occurringAs[OBJ].get(x, 0) + 1
	    self._occurringAs[OBJ][x] = y
	    if verbosity() > 98:
                progress(
                    "scan: %s, a %s, now has %i occurrences as %s" 
                    %(x, x.__class__,y,"CPSOq"[y]))
#	else:
#	    if x == None: raise RuntimeError("Weird - None in a statement?")
#	    progress("&&&&&&&&& %s has class %s " %(`z`, `z.__class__`))

    def _scan(self, x, context=None):
#	progress("Scanning ", x, " &&&&&&&&")
#	assert self.context._redirections.get(x, None) == None, "Should not be redirected: "+`x`
	if verbosity() > 98: progress("scanning %s a %s in context %s" %(`x`, `x.__class__`,`context`),
			x.generated(), self._inContext.get(x, "--"))
	if isinstance(x, NonEmptyList):
	    for y in x:
		self._scanObj(context, y)
	if isinstance(x, Formula):
	    for s in x.statements:
		for p in PRED, SUBJ, OBJ:
		    y = s[p]
		    if (isinstance(y, AnonymousVariable) 
			or (isinstance(y, Fragment) and y.generated())): 
			z = self._inContext.get(y, None)
			if z == "many": continue # forget it
			if z == None:
			    self._inContext[y] = x
			elif z is not x:
			    self._inContext[y] = "many"
			    continue
			z = self._occurringAs[p].get(y, 0)
			self._occurringAs[p][y] = z + 1
#			progress("&&&&&&&&& %s now occurs %i times as %s" %(`y`, z+1, "CPSO"[p]))
#		    else:
#			progress("&&&&&&&&& yyyy  %s has class %s " %(`y`, `y.__class__`))
		    if x is not y: self._scan(y, x)
		


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
    # This function takes way too long. My attempts to speed it up using a try / except
    # loop were clearly misguided, because this function does very little as is.
    # why does this take .08 seconds per function call to do next to nothing?
##        try:
##            return self._topology_returns[x]
##        except KeyError:
##            pass
#	progress("&&&&&&&&& ", `self`,  self._occurringAs)
#        _isExistential = x in context.existentials()
        _isExistential = context.existentialDict.get(x,0)
#        return (0, 2)
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
	    if verbosity() > 97:
		progress( "Topology %s in %s is: ctx=%s,anon=%i obj=%i, pred=%i loop=%s ex=%i "%(
		`x`, `context`, `ctx`, _anon, _asObj, _asPred, _loop, _isExistential))
	    return ( _anon, _asObj+_asPred )  

        if verbosity() > 98:
            progress( "Topology %s in %s is: anon=%i obj=%i, pred=%i loop=%s ex=%i "%(
            `x`, `context`,  _anon, _asObj, _asPred, _loop, _isExistential))

##        self._topology_returns[x] = ( _anon, _asObj+_asPred )
        return ( _anon, _asObj+_asPred )  


  
    def dumpNested(self):
        """ Iterates over all URIs ever seen looking for statements
        """

	context = self.context
        assert context.canonical != None
	self._scan(context)
        self.sink.startDoc()
        self.selectDefaultPrefix(Serializer.dumpNested)        
        self.dumpFormulaContents(context, self.sink, sorting=1, equals=1)
        self.sink.endDoc()

    def dumpFormulaContents(self, context, sink, sorting, equals=0):
        """ Iterates over statements in formula, bunching them up into a set
        for each subject.
        """

	allStatements = context.statements[:]
	if equals:
	    for x, y in context._redirections.items():
		if not x.generated() and x not in context.variables():
		    allStatements.append(StoredStatement(
			(context, context.store.sameAs, x, y)))
        allStatements.sort(StoredStatement.compareSubjPredObj)
#        context.statements.sort(StoredStatement.compareSubjPredObj)
	# @@ necessary?
	self.dumpVariables(context, sink, sorting, pretty=1)

#	statements = context.statementsMatching(subj=context)  # context is subject
#        if statements:
#	    progress("@@ Statement with context as subj?!", statements,)
#            self._dumpSubject(context, context, sink, sorting, statements)

        currentSubject = None
        statements = []
        for s in allStatements:
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
		    if verbosity() > 90: progress("%s Not list, has property values." % `subj`)
                    sink.startAnonymousNode(subj.asPair())
                    for s in statements:  #   "[] color blue."  might be nicer. @@@  Try it?
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
	    if verbosity()>99:
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

	
def canItbeABNode(formula, symbol):   # @@@@ Really slow -tbl
    def returnFunc():
        for quad in formula.statements:
            for s in PRED, SUBJ, OBJ:
                if isinstance(quad[s], Formula):
                    if quad[s].doesNodeAppear(symbol):
                        return 0
        return 1
    return returnFunc

##    toplayer = 1
##    otherlayers = 1
##    statementList = formula.statements[:]
##    parentList.append(formula)
##    while statementList:
##        quad = statementList.pop(0)
##        for s in SUBJ, OBJ:
##            if quad[s] == symbol:
##                toplayer = 0
##            elif isinstance(quad[s], List):
##                for elt in quad[s]:
##                    statementList.append(elt)
##            elif isinstance(quad[s], Formula):
##                top, other = canItbeABNode(parentList, quad[s], symbol)
##                otherlayers = otherlayers and top and other
##            else:
##                pass
##    return toplayer, otherlayers


#ends

