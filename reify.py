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
    Literal, Symbol, Fragment, FragmentNil, Anonymous, Term,\
    CompoundTerm, List, EmptyList, NonEmptyList
from formula import Formula, StoredStatement
SUBJ = 0
PRED = 1
OBJ  = 2
import uripath

reifyNS = 'http://www.w3.org/2004/06/rei#'
owlOneOf = 'http://www.w3.org/2002/07/owl#oneOf'

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
    F = reification(formula, a)
    a.add(F, a.store.type, a.store.Truth)
    a = a.close()
    return a

##def doListRecursively(formula, l, toDo):
##    store = formula.store
##    if isinstance(l, EmptyList):
##        return store.nil.newList([])
##    first = l.first
##    rest = 1.rest
##    

def reification(formula, sink):
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
        return (formulaURIs[obj], predList[0])

    def fragmentQuote(obj, predList):
        return (a.newLiteral(obj.uriref()), predList[1])

    def fragmentRepeat(obj, predList):
        return (obj, predList[0])
    
    def literalQuote(obj, predList):
        return (obj, predList[2])

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
            for predList, obj in (((reifySubj, reifySubjURI, reifySubjLit), x),
                                  ((reifyPred, reifyPredURI, reifyPredLit), y),
                                  ((reifyObj,  reifyObjURI,  reifyObjLit),  z)):
                obj2, pred = typeDispatch(dispatchDict,
                                         obj, predList)
                a.add(subj, pred, obj2)
            
            
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





def dereify(formula):
    sink = formula.newFormula()
    return dereification(formula,sink)

def dereification(formula,sink):
    store = formula.store
#There has got to be a better way.
    a = formula
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
        if universalClass != None:
            universalList = formula.any(subj=universalClass, pred=owlOneOf)
            if universalList != None:
                for x in universalList:
                    y = b.newSymbol(x.value())
                    bNodes[y] = b.newBlankNode()
                    b.declareUniversal(bNodes[y])
        existentialClass = formula.any(subj=c, pred=reifyExVars)
        if existentialClass != None:
            existentialList = formula.any(subj=existentialClass, pred=owlOneOf)
            if existentialList != None:
                for x in existentialList:
                    y = b.newSymbol(x.value())
                    bNodes[y] = b.newBlankNode()
                    b.declareExistential(bNodes[y])
        StatementClass = formula.any(subj=c, pred=reifyStatements)
        if StatementClass != None:
            StatementList = formula.any(subj=StatementClass, pred=owlOneOf)
            if StatementList != None:
##                import sys
##                sys.path.append('/home/syosi')
##                from apihelper import info
##                print info(StatementList[1],30)
                for subj in StatementList:
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
        else:
            assert 0, "How was I supposed to get here again?"
            
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
    
