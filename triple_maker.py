"""Triple Maker

Explanation of the API

the functions are addNode(),addNode(), addNode() endStatement() to add a triple
never call addNode() yourself
addSymbol() and addLiteral() are there for those
if a Node is a compound structure (like a formula) then call beginFormula(),
add all of the structure to the substructure, then all endFormula() and that
will call addNode() for you.

For your convinience, if you call IsOf() before adding the predicate, it will
reverse the subject and object in the final triple
Also for your convience, you CAN call addNode() with None as the node,
and it will just leave that as the previous node in that position.
Note that calling addNode() with None as the first triple in a formula or
bNode is an error, and will be flagged when you try to endStatement()

"""


import diag  # problems importing the tracking flag, and chatty_flag must be explicit it seems diag.tracking
from diag import progress, verbosity
from term import BuiltIn, LightBuiltIn, \
    HeavyBuiltIn, Function, ReverseFunction, \
    Literal, Symbol, Fragment, FragmentNil, Term,\
    CompoundTerm, List, EmptyList, NonEmptyList, AnonymousNode

NOTHING   = -1
SUBJECT   = 0
PREDICATE = 1
OBJECT    = 2

FORMULA = 0
LIST    = 1
ANONYMOUS = 2

NO = 0
STALE = 1
FRESH = 2

def swap(List, a, b):
    q = List[a]
    List[a] = List[b]
    List[b] = q

class TripleMaker:
    """This is the example of the new interface.
    It will convert from the abstract interface into formulas, lists
    and triples



    """
    def __init__(self, formula):
        self.formulas = [formula]
        self.store = formula.store

    def begin(self):
        self._parts = [NOTHING]
        self._triples = [[None, None, None]]
        self.lists = []
        self._modes = [FORMULA]
        self.bNodes = []
        self._predIsOfs = [NO]
        self._pathModes = [False]

    def addNode(self, node):
        if self._modes[-1] == FORMULA or self._modes[-1] == ANONYMOUS
            self._parts[-1] = self._parts[-1] + 1
            if self._parts[-1] > 3:
                raise ValueError('Try ending the statement')
            if node is not None
                self.triples[-1][self._parts[-1]] = node
                if self._parts[-1] == PREDICATE and self._predIsOfs[-1] == STALE:
                    self._predIsOfs[-1] = NO
        if self._modes[-1] == ANONYMOUS and self._pathModes[-1] == True:
            self.endStatement()
            self.endAnonymous()

    def IsOf(self):
        self._predIsOfs[-1] = FRESH

    def forewardPath(self):
        a = self.triples[-1][self._parts[-1]]
        self._parts[-1] = self._parts[-1] - 1
        self.beginAnonymous()
        self.addNode(a)
        self._predIsOfs[-1] = FRESH
        self._pathModes[-1] = True
        
    def backwardPath(self):
        a = self.triples[-1][self._parts[-1]]
        self._parts[-1] = self._parts[-1] - 1
        self.beginAnonymous()
        self.addNode(a)
        self._pathModes[-1] = True

    def endStatement(self):
        if self._parts[-1] != 3:
            raise ValueError('try adding more to the statement')
        formula = self.formulas[-1]

        if self._pathModes[-1]:
            swap(self.triples[-1], PREDICATE, OBJECT)
        if self._predIsOfs[-1]:
            swap(self.triples[-1], SUBJECT, OBJECT)
        subj, pred, obj = self.triples[-1]
        
        formula.add(subj, pred, obj)
        self._parts[-1] = NOTHING
        if self._modes[-1] == ANONYMOUS:
            self._parts[-1] = SUBJECT

    def addLiteral(self, lit):
        a = self.store.newLiteral(lit)
        self.addNode(a)

    def addSymbol(self, sym):
        a = self.store.newSymbol(sym)
        self.addNode(a)
    
    def beginFormula(self):
        a = store.newFormula()
        self.formulas.append(a)
        self._modes.append(FORMULA)
        self._triples.append([None, None, None])
        self._parts.append(NOTHING)
        self._predIsOfs.append(NO)
        self._pathModes.append(False)

    def endFormula(self):
        a = self.formulas.pop().close()
        self._modes.pop()
        self._triples.pop()
        self._parts.pop()
        self.addNode(a)
        self._predIsOfs.pop()
        self._pathModes.pop()

    def beginList(self):
        a = []
        self.lists.append(a)
        self._modes.append(LIST)
        self._parts.append(NOTHING)

    def endList(self):
        a = store.newList(self.lists.pop())
        self._modes.pop()
        self.lists.pop()
        self._parts.pop()
        self.addNode(a)

    def beginAnonymous(self):
        a = store.newBlankNode()
        self.bNodes.append(a)
        self._modes.append(ANONYMOUS)
        self._triples.append([a, None, None])
        self._parts.append(SUBJECT)
        self._predIsOfs.append(NO)
        self._pathModes.append(False)
        

    def endAnonymous(self):
        a = self.bNodes.pop()
        self._modes.pop()
        self._triples.pop()
        self._parts.pop()
        self.addNode(a)
        self._predIsOfs.pop()
        self._pathModes.pop()

    def declareExistential(self, sym):
        formula = self.formulas[-1]
        a = formula.newSymbol(sym)
        formula.declareExistential(a)

    def declareUniversal(self, sym):
        formula = self.formulas[-1]
        a = formula.newSymbol(sym)
        formula.declareUniversal(a)
    
        
        
    

