#!/usr/bin/python
"""
Functions to reify and dereify a graph.
These functions should be perfect inverses of each other.

The strategy used is different from that of the reifier
in notation3.py, that tries to reify what it outputs.
This simply puts the reification into the sink given,
or a new one, depending on the function called.
$Id$
"""
from term import BuiltIn, LightBuiltIn, LabelledNode, \
    HeavyBuiltIn, Function, ReverseFunction, AnonymousNode, \
    Literal, Symbol, Fragment, FragmentNil, Term,\
    CompoundTerm, List, EmptyList, NonEmptyList, N3Set
from formula import Formula, StoredStatement
from RDFSink import CONTEXT, PRED, SUBJ, OBJ, PARTS, ALL4, RDF_type_URI
import uripath
import diag

reifyNS = 'http://www.w3.org/2004/06/rei#'
owlOneOf = 'http://www.w3.org/2002/07/owl#oneOf'

def flatten(formula):
    """Flatten a formula

    This will minimally change a formula to make it valid RDF
    flattening a flattened formula should thus be the unity
    """
    store = formula.store
    valid_triples = formula.statements[:]
    for triple in valid_triples:
        for part in SUBJ, PRED, OBJ:
            try:
                triple[part] = triple[part].close()
            except AttributeError:
                pass
    
    invalid_triples = []
    for a in formula.universals():
        new_invalid_triples = []
        for triple in valid_triples:
            for part in SUBJ, PRED, OBJ:
                if triple[part].doesNodeAppear(a):
                    new_invalid_triples.append(triple)
        for triple in new_invalid_triples:
            try:
                valid_triples.remove(triple)
            except ValueError:
                pass
        invalid_triples.extend(new_invalid_triples)
    still_needed_existentials = {}
    for a in formula.existentials():
        for triple in valid_triples:
            for part in SUBJ, PRED, OBJ:
                if triple[part].doesNodeAppear(a):
                    still_needed_existentials[a] = 1
                    break
            else:
                continue
            break
        else:
            print a
    returnFormula = formula.newFormula()
    for a in still_needed_existentials.keys():
        returnFormula.declareExistential(a)
    tempformula = formula.newFormula()
    for var in formula.universals():
        tempformula.declareUniversal(var)
    for var in formula.existentials():
        tempformula.declareExistential(var)
    for triple in invalid_triples:
        tempformula.add(triple[SUBJ],
                        triple[PRED],
                        triple[OBJ])
    #now for the stuff that isn't reified
    for triple in valid_triples:
        returnFormula.add(triple[SUBJ].flatten(returnFormula),
                        triple[PRED].flatten(returnFormula),
                        triple[OBJ].flatten(returnFormula))
    if tempformula.statements != []:
        x = tempformula.reification(returnFormula)
        returnFormula.add(x, store.type, store.Truth)
    return returnFormula.close()
    

def typeDispatch(typeDict, term, optional = None):
    """Dispatch which function to call based on type

    This can be less ugly that if statements, if done right
    """
    for thetype in typeDict:
        if isinstance(term, thetype):
            #print "calling:", typeDict[thetype], " for ", term, " of type ", thetype
            if optional == None:
                return typeDict[thetype](term)
            else:
                return typeDict[thetype](term, optional)
    print "how did I get here? ", term


def reify(formula):
    """Reify a formula

    Returns an RDF formula with the same semantics
    as the given formula
    """ 
    a = formula.newFormula()
    x = formula.reification(a)
    a.add(x, a.store.type, a.store.Truth)
    a = a.close()
    return a

##def doListRecursively(formula, l, toDo):
##    store = formula.store
##    if isinstance(l, EmptyList):
##        return store.nil.newList([])
##    first = l.first
##    rest = 1.rest
##    


#Note that the following is depricated and referenced nowhere.
def reification(formula, sink, bnodes={}):
    """Create description of formula in sink

    Returns bNode corresponding to the reification

    """
    toDo = [formula]
    listToDo = []
    alreadyDone = {}
    formulaURIs = {}
    bNodes      = {}
    if sink == None:
        a = store.newFormula()
    else:
        a = sink
    store = formula.store
    owlOneOf = a.newSymbol('http://www.w3.org/2002/07/owl#oneOf')
    reifyPredURI = a.newSymbol(reifyNS+'predURI')
    reifyPred    = a.newSymbol(reifyNS+'pred')
    reifyPredLit = a.newSymbol(reifyNS+'predValue')
    reifySubjURI = a.newSymbol(reifyNS+'subjURI')
    reifySubj    = a.newSymbol(reifyNS+'subj')
    reifySubjLit = a.newSymbol(reifyNS+'subjValue')
    reifyObjURI  = a.newSymbol(reifyNS+'objURI')
    reifyObj     = a.newSymbol(reifyNS+'obj')
    reifyObjLit  = a.newSymbol(reifyNS+'objValue')
    reifyExVars  = a.newSymbol(reifyNS+'existentials')
    reifyUniVars = a.newSymbol(reifyNS+'universals')
    reifyStatements = a.newSymbol(reifyNS+'statements')

###########################
#
#What follow are some local functions, to be used with the typeDispatcher.
#      First, the typedispatcher.

#
#Next are all of the inner loop dispatches
#
    def formulaQuote(obj, predList):
        if obj not in alreadyDone and obj not in toDo:
            toDo.append(obj)
        if obj not in formulaURIs:
            formulaURIs[obj] = store.newBlankNode(a)
        return formulaURIs[obj]

    def fragmentQuote(obj, predList):
	z = sink.newBlankNode()
	sink.add(subj=z, pred=rei["uri"], obj=sink.newLiteral(obj.uriref()))
        return z

    def fragmentRepeat(obj, predList):
        return obj
    
    def literalQuote(obj, sink):
	z = sink.newBlankNode()
	sink.add(subj=z, pred=rei["value"], obj=obj)
        return z

    def bNodeQuote(obj, predList):
        if obj not in bNodes:
            bNodes[obj] = a.newBlankNode()
        return (bNodes[obj], predList[0])

    def listQuote(currentList, predList):
        if isinstance(currentList, EmptyList):
            formulaURIs[currentList] = store.nil.newList([])
        elif currentList not in formulaURIs:
            formulaURIs[currentList] = store.nil.newList([typeDispatch(listDispatch, elt, predList)[0]
                                                          for elt in currentList])
        return (formulaURIs[currentList], predList[2])
    
    dispatchDict = {Formula:  formulaQuote,
                List:     listQuote,
                LabelledNode: fragmentQuote,
                Literal:  literalQuote,
                AnonymousNode:     bNodeQuote}
    
    listDispatch = dispatchDict.copy()
    listDispatch[LabelledNode] = fragmentRepeat
        
    def reifyFormula(currentFormula):
    #Bookkeeping on the current formula
        if currentFormula not in formulaURIs:
            formulaURIs[currentFormula] = store.newBlankNode(a)
        F = formulaURIs[currentFormula]
    #Existentials class and universals class
        existentialList = store.nil.newList([a.newLiteral(x.uriref())
                                             for x in currentFormula.existentials()])
        existentialClass = store.newBlankNode(a)
        a.add(existentialClass, owlOneOf, existentialList)

        
        universalList = store.nil.newList([a.newLiteral(x.uriref())
                                           for x in currentFormula.universals()])
        universalClass = store.newBlankNode(a)
        a.add(universalClass, owlOneOf, universalList)

    #The great list of statements
    #Lists have to be done depth first
        statementList = []
        for s in currentFormula.statements:
            subj = a.newBlankNode()
            statementList.append(subj)
            x, y, z = s.spo()
            for p, obj in (("subj", x),
                                  ("pred", y),
                                  ("obj",  z)):
                obj2 = typeDispatch(dispatchDict, obj)
                a.add(subj, rei[p], obj2)
            
            
    #The great class of statements
        StatementClass = a.newBlankNode()
        realStatementList = store.nil.newList(statementList)
        a.add(StatementClass, owlOneOf, realStatementList)
    #We now know something!
        a.add(F, reifyExVars, existentialClass)
        a.add(F, reifyUniVars, universalClass)
        a.add(F, reifyStatements, StatementClass)

###########################
#  End Functions.
#  Here is where the main loop is
        
#Loop through thr toDo list
    while toDo != []:
#What do we have to deal with next?
        currentTerm = toDo.pop(0)
        if currentTerm in alreadyDone:
            continue
        alreadyDone[currentTerm] = 1
        reifyFormula(currentTerm)
            
    F = formulaURIs[formula]    
    return F


###############################################################################


def dereify_old(formula):
    sink = formula.newFormula()
    return dereification(formula,sink)

def dereification_old(formula,sink):
    store = formula.store
#There has got to be a better way.
    a = formula
    owlOneOf = a.newSymbol('http://www.w3.org/2002/07/owl#oneOf')
    
    for p in "subj", "pred", "obj":
	vocab[p] = {}
	for q in "", "URI", "Value":
	    vocab[q] = a.newSymbol(reifyNS + p + q)
	    
    reifyPredURI = a.newSymbol(reifyNS+'predURI')
    reifyPred    = a.newSymbol(reifyNS+'pred')
    reifyPredLit = a.newSymbol(reifyNS+'predValue')
    reifySubjURI = a.newSymbol(reifyNS+'subjURI')
    reifySubj    = a.newSymbol(reifyNS+'subj')
    reifySubjLit = a.newSymbol(reifyNS+'subjValue')
    reifyObjURI  = a.newSymbol(reifyNS+'objURI')
    reifyObj     = a.newSymbol(reifyNS+'obj')
    reifyObjLit  = a.newSymbol(reifyNS+'objValue')
    reifyExVars  = a.newSymbol(reifyNS+'existentials')
    reifyUniVars = a.newSymbol(reifyNS+'universals')
    
    reifyStatements = a.newSymbol(reifyNS+'statements')
#end there  has got to be a better way.
    formulaBNodeList = formula.each(pred=reifyStatements)
    bNodes = {}
    quads = {}

####
# Lists need something recursive to work.
####
    def dereifyList(b, currentList):
        returnList = []
        for elt in currentList:
            if isinstance(elt, List):
                q = dereifyList(b, elt)
            elif elt in bNodes:
                q = bNodes[elt]
            elif isinstance(elt, Literal) or isinstance(elt, Fragment):
                q = elt
            else:
                bNodes[elt] = b.newBlankNode()
                q = bNodes[elt]
            returnList.append(q)
        return store.nil.newList(returnList)
    
    for c in formulaBNodeList:
        bNodes[c] = formula.newFormula()
    for c in formulaBNodeList:
        b = bNodes[c]
        universalClass = formula.any(subj=c, pred=reifyUniVars)
	
        if universalClass == None:
	    raise ValueError, "Underspecified formula %s no universals list" % c
	universalList = formula.the(subj=universalClass, pred=owlOneOf)
	if universalList != None:
	    for x in universalList:
		y = b.newSymbol(x.value())
#		bNodes[y] = b.newBlankNode() # @@ needed? - Tim  -not a bnode
		b.declareUniversal(bNodes[y])

        existentialClass = formula.the(subj=c, pred=reifyExVars)
        if existentialClass == None:
	    raise ValueError, "Underspecified formula %s no existentials list" % c
	existentialList = formula.any(subj=existentialClass, pred=owlOneOf)
	if existentialList != None:
	    for x in existentialList:
		y = b.newSymbol(x.value())
#		bNodes[y] = b.newBlankNode()  # @@ needed? - Tim  -not a bnode
		b.declareExistential(bNodes[y])

        StatementClass = formula.the(subj=c, pred=reifyStatements)

        if StatementClass == None:
	    raise ValueError, "Underspecified formula %s no statements list ??!!!" % c
	StatementList = formula.the(subj=StatementClass, pred=owlOneOf)
	if StatementList != None:
##                import sys
##                sys.path.append('/home/syosi')
##                from apihelper import info
##                print info(StatementList[1],30)
	    for subj in StatementList:
		part = {}
		for p in "subject", "predicate", "objject":
		    obj = formula.any(subj=subj, pred=vocab[p]["URI"])
		    if obj != None:
			part[p] = b.newSymbol(obj)  # Thing with a URI
			continue
		    obj = formula.any(subj=subj, pred=vocab[p]["Value"])
		    if obj != None:
			if isinstance(obj,List):
			    part[p] = dereifyList(b, obj)
			else:
			    part[p] = obj
			continue
		    obj = formula.any(subj=subj, pred=vocab[p][""])
		    if obj != None:   # bnode or Formula
			if isinstance(obj, Fragment) and obj not in bNodes:
			    value = obj
			else:
			    if obj not in bNodes:
				bNodes[obj] = b.newBlankNode()
			    value = bNodes[obj]
			continue
			
		b.add(subj=part["subj"], pred=part["pred"], obj=part["obj"])
		
###
		for pred in (reifyPredURI, reifyPred, reifyPredLit, \
				reifySubjURI, reifySubj, reifySubjLit, \
				reifyObjURI,  reifyObj,  reifyObjLit):
		    obj = formula.any(subj=subj, pred=pred)
		    if obj == None:
			continue   #Be very careful
		    predURI = str(pred.uriref())
		    if subj not in quads:
			quads[subj] = [None, None, None, b]
	    #Find out what value we are actually using
		    if "URI" in predURI:
			value = b.newSymbol(obj.value())
		    elif "Value" in predURI:
			if isinstance(obj,List):
			    value = dereifyList(b, obj)
			else:
			    value = obj
		    else:
			if isinstance(obj, Fragment) and obj not in bNodes:
			    value = obj
			else:
			    if obj not in bNodes:
				bNodes[obj] = b.newBlankNode()
			    value = bNodes[obj]
	#Put it into the triples we are building
		    if "subj" in predURI:
			quads[subj][SUBJ] = value
		    elif "pred" in predURI:
			quads[subj][PRED] = value
		    elif "obj" in predURI:
			quads[subj][OBJ] = value
		    else:
			assert 0, "I don't know how to get here either " + predURI + ' that was predURI'
            
#Time to compute the dependency graph
    depends = {}
    for d in formulaBNodeList:
        c = bNodes[d]
        depends[c] = {}
    for subject, predicate, object, context in quads.values():
        if object in depends:
            depends[context][object]=1
        if subject in depends:
            depends[context][subject] = 1
#time to slowly go down dependency graph
    while depends != {}:
        for c in depends:
            if depends[c] != {}: continue
            for subject, predicate, object, context in quads.values():
                if context != c: continue
#                print subject, predicate, object, context
                if isinstance(subject,Formula): subject = subject.close()
                if isinstance(object,Formula): object= object.close()
                context.add(subject, predicate, object)
            del depends[c]
            for d in depends:
                if c in depends[d]:
                    del depends[d][c]
            c.close()
            break
    weKnowList = formula.each(pred=store.type, obj=store.Truth)
    for weKnow in weKnowList:
        if weKnow in bNodes and isinstance(bNodes[weKnow],Formula):
            sink.loadFormulaWithSubsitution(bNodes[weKnow])
    return sink


def unflatten(formula, sink=None):
    """Undo the effects of the flatten function.

    Note that this still requires helper methods scattered throughout the
    Term heriarchy. 
    
    Our life is made much more difficult by the necessity of removing all
    triples that have been dereified --- this required a modification to dereification()

    """
    store = formula.store
    if sink == None:
	sink = formula.newFormula()
    bNodes = {}     #to track bNodes that bacome formulae
    rei = formula.newSymbol(reifyNS[:-1])
    formulaList = formula.each(pred=rei["statements"])

    #on the next line, we are filtering Truths because those will be included later
    formulaList = [a for a in formulaList if formula.the(pred=store.type, obj=store.Truth) == None]
    skipNodeList=[]
    for a in formulaList:
        xList = []
        bNodes[a] = dereification(a, formula, sink, xList=xList)
        skipNodeList.extend(xList[1:])
    dereify(formula, sink, xList=skipNodeList)
    for triple in formula.statements:
        if triple[PRED] != rei["statements"] and \
           triple[PRED] != rei["universals"] and \
           triple[PRED] != rei["value"] and \
           triple[PRED] != rei["existentials"] and \
           triple[SUBJ] not in skipNodeList and \
           triple[PRED] not in skipNodeList and \
           triple[OBJ] not in skipNodeList:
            sink.add(triple[SUBJ].unflatten(sink, bNodes),
                     triple[PRED].unflatten(sink, bNodes),
                     triple[OBJ].unflatten(sink, bNodes))        
    return sink.close()

#### Alternative method
# Shortcuts are too messy and don't work with lists
#
def dereify(formula, sink=None, xList=[]):
    store = formula.store
    if sink == None:
	sink = formula.newFormula()
    weKnowList = formula.each(pred=store.type, obj=store.Truth)
    for weKnow in weKnowList:
	f = dereification(weKnow, formula, sink, xList=xList)
	sink.loadFormulaWithSubsitution(f)
    return sink

def dereification(x, f, sink, bnodes={}, xList=[]):
    rei = f.newSymbol(reifyNS[:-1])
    xList.append(x)
    
    if x == None:
	raise ValueError, "Can't dereify nothing. Suspect missing information in reified form."
    y = f.the(subj=x, pred=rei["uri"])
    if y != None: return sink.newSymbol(y.value())
	
    y = f.the(subj=x, pred=rei["value"])
    if y != None: return y
    
    y = f.the(subj=x, pred=rei["items"])
    if y != None:
        if isinstance(y, N3Set):
            yy = [z for z in y]
            yy.sort(Term.compareAnyTerm)
            return sink.store.newSet([dereification(z, f, sink, bnodes, xList) for z in yy])
        return sink.newList([dereification(z, f, sink, bnodes, xList) for z in y])
    
    y = f.the(subj=x, pred=rei["statements"])
    if y != None:
	z = sink.newFormula()
	zbNodes = {}  # Bnode map for this formula
	
	uset = f.the(subj=x, pred=rei["universals"])
	xList.append(uset)
	ulist = uset #f.the(subj=uset, pred=f.newSymbol(owlOneOf))
	xList.append(ulist)
	from diag import progress
	if diag.chatty_flag > 54:
            progress("universals = ",ulist)
	for v in ulist:
	    z.declareUniversal(f.newSymbol(v.value()))

	uset = f.the(subj=x, pred=rei["existentials"])
	xList.append(uset)
	ulist = uset #f.the(subj=uset, pred=f.newSymbol(owlOneOf))
	xList.append(ulist)
	if diag.chatty_flag > 54:
            progress("existentials %s =  %s"%(ulist, ulist.value()))
	for v in ulist:
            if diag.chatty_flag > 54:
                progress("Variable is ", v)
	    z.declareExistential(f.newSymbol(v.value()))
	yy = y #f.the(subj=y, pred=f.newSymbol(owlOneOf))
	xList.append(yy)
	if diag.chatty_flag > 54:
            progress("Statements:  set=%s, list=%s = %s" %(y,yy, yy.value()))
	for stmt in yy:
	    z.add(dereification(f.the(subj=stmt, pred=rei["subject"]), f, sink, zbNodes, xList),
		dereification(f.the(subj=stmt, pred=rei["predicate"]), f, sink, zbNodes, xList),
		dereification(f.the(subj=stmt, pred=rei["object"]), f, sink, zbNodes, xList))
	return z.close()
    y = f.the(subj=x, pred=f.newSymbol(RDF_type_URI))
    if y is not None:
        if x in bnodes:
            return bnodes[x]
        z = sink.newBlankNode()
        bnodes[x] = z
        return z
    
    raise ValueError, "Can't dereify %s - no clues I understand in %s" % (x, f)
