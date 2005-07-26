#!/usr/bin/env python
"""


"""

from pychinko import terms
from pychinko import N3Loader
from pychinko.helpers import removedups
from swap import term, formula
from rdflib import BNode, Store
from rdflib.constants import TYPE, FIRST, REST, LIST, NIL
LOG_IMPLIES = 'http://www.w3.org/2000/10/swap/log#'

try:
    reversed
except NameError:
    def reversed(l):
        ll = [a for a in l]
        b = len(l)
        while b > 0:
            b -= 1
            yield ll[b]

class ToPyStore(object):

    def __init__(self, pyStore):
        self.pyStore = pyStore
        self.typeConvertors = [ 
            (formula.Formula , self.formula),  
            (formula.StoredStatement, self.triple),
            (term.LabelledNode, self.URI), 
            (term.Fragment, self.URI), 
            (term.AnonymousNode, self.BNode),
            (term.Literal, self.literal),
            (term.List, self.list)]

    def lookup(self, node):
        for theType, function in self.typeConvertors:
            if isinstance(node, theType):
                return function(node)
        raise RuntimeError(`node` + '  ' + `node.__class__`)

    def formula(self, node):
        subFormulaRef = self.pyStore.create_clause()
        subFormula = self.pyStore.get_clause(subFormulaRef)
        subConvertor = self.__class__(subFormula)
        subConvertor.statements(node)
        return subFormulaRef

    def URI(self, node):
        return terms.URI(node.uriref())

    def BNode(self, node):
        return BNode.BNode(node.uriref())

    def literal(self, node):
        string = node.string
        dt = node.datatype
        if not dt:
            dt = ''
        lang = node.lang
        if not lang:
            lang = ''
        return terms.Literal(string, lang, dt)

    def list(self, node):
        newList = [].__class__
        next = NIL
        for item in reversed(newList(node)):
            bNode = BNode.BNode()
            self.pyStore.add((bNode, REST, next))
            self.pyStore.add((bNode, FIRST, self.lookup(item)))
            next = bNode
        return next

    def statements(self, formula):
        for var in formula.universals():
            self.pyStore.add_universal(self.lookup(var))
        for var in formula.existentials():
            if not isinstance(var, term.AnonymousNode):
                self.pyStore.add_existential(self.lookup(var))
        for statement in formula:
            self.triple(statement)
    
    def triple(self, statement):
        try:
            self.pyStore.add([self.lookup(item) for item in statement.spo()])
        except:
            raise

class FromPyStore(object):
    def __init__(self, formula, pyStore, parent=None):
        self.parent = parent
        self.formula = formula
        self.store = formula.store
        self.pyStore = pyStore
        self.bNodes = {}
        self.typeConvertors = [
            (Store.Store, self.subStore),
            (terms.Exivar, self.existential),
            (terms.Variable, self.variable),
            (terms.URIRef, self.URI),
            (BNode.BNode, self.BNode),
            (terms.Literal, self.literal)]
        self.stores = [
            (N3Loader.ClauseLoader, self.patterns),
            (N3Loader.N3Loader, self.facts_and_rules),
            (Store.Store, self.triples)]
        
    def lookup(self, node):
        for theType, function in self.typeConvertors:
            if isinstance(node, theType):
                return function(node)
        raise RuntimeError(`node` + '  ' + `node.__class__`)

    def run(self):
        node = self.pyStore
        for theType, function in self.stores:
            if isinstance(node, theType):
                return function(node)
        raise RuntimeError(`node` + '  ' + `node.__class__`)

    def URI(self, node):
        return self.formula.newSymbol(node)

    def variable(self, node):
        if self.pyStore.get_clause(node.name) is not None:
            return self.subStore(self.pyStore.get_clause(node.name))
        v = self.URI(node.name)
        self.parent.declareUniversal(v)
        return v

    def existential(self, node):
        if self.pyStore.get_clause(node.name) is not None:
            return self.subStore(self.pyStore.get_clause(node.name))
        v = self.URI(node.name)
        self.formula.declareExistential(v)
        return v
        
    def BNode(self, node):
        if self.pyStore.get_clause(node) is not None:
            return self.subStore(self.pyStore.get_clause(node))
        bNodes = self.bNodes
        if node not in bNodes:
            bNodes[node] = self.formula.newBlankNode(node)
        return bNodes[node]

    def literal(self, node):
        return self.formula.newLiteral(node, node.datatype or None, node.language or None)
    
    def subStore(self, node):
        f = self.formula.newFormula()
        self.__class__(f, node, self.formula).run()
        return f.close()

    def facts_and_rules(self, pyStore):
        patternMap = {}
        for nodeID in pyStore.list_clauses():
            patternMap[tuple(removedups(pyStore.get_clause(nodeID).patterns))] = pyStore.get_clause(nodeID)
        for fact in pyStore.facts:
            self.formula.add(
                self.lookup(fact.s),
                self.lookup(fact.p),
                self.lookup(fact.o))

        for rule in pyStore.rules:
            self.formula.add(
                self.subStore(patternMap[tuple(removedups(rule.lhs))]),
                self.store.implies,
                self.subStore(patternMap[tuple(removedups(rule.rhs))]))

    def patterns(self, pyStore):
        patternMap = {}
        for nodeID in pyStore.list_clauses():
            patternMap[tuple(removedups(pyStore.get_clause(nodeID).patterns))] = pyStore.get_clause(nodeID)
            
        for pattern in pyStore.patterns:
            if isinstance(pattern.s, terms.Rule):
                rule = pattern.s
                self.formula.add(
                    self.subStore(patternMap[tuple(removedups(rule.lhs))]),
                    self.store.implies,
                    self.subStore(patternMap[tuple(removedups(rule.rhs))]))
            else:
                self.formula.add(
                    self.lookup(pattern.s),
                    self.lookup(pattern.p),
                    self.lookup(pattern.o))

    def triples(self, pyStore):
        pass

if __name__ == '__main__':
    import sys
    #sys.path.append('/home/syosi')
    from swap import llyn
    #from pychinko.N3Loader import N3Loader
    store = llyn.RDFStore()
    from swap import webAccess
    f = webAccess.load(store, sys.argv[1])
    pyf = N3Loader.N3Loader()
    conv = ToPyStore(pyf)
    conv.statements(f)
    print "facts = " + ',\n'.join([repr(a) for a in pyf.facts])
    print "rules = " + ',\n'.join([repr(a) for a in pyf.rules])
    print '----'
    g = store.newFormula()
    reConv = FromPyStore(g, pyf)
    reConv.run()
    print g.close().n3String()

