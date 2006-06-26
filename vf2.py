#!/usr/bin/env python
""" Graph isomorphism algorithm

as described in
http://amalfi.dis.unina.it/people/vento/lavori/iciap99.pdf

I hope to modify it to match
http://amalfi.dis.unina.it/graph/db/papers/vf-algorithm.pdf

Note that what I am doing here is not as simple as either.
"""

from swap import uripath
from swap.diag import progress

verbose = False
if verbose:
    progress = progress
else:
    progress2 = progress
    def progress(*x): pass

class Problem(object):
    def __new__(cls, **keywords):
        self = object.__new__(cls)
        for k, v in keywords.items():
            setattr(self, k, v)
        return self

class BindingTree(object):
    """
    An or and ands of bindings that are needed before we go on
    
    >>> b1 = BindingTree()
    >>> b1
    BindingTree([[]])
    >>> b1.int_and([1,2,3])
    >>> b1
    BindingTree([[1, 2, 3]])
    >>> b1.int_or([[6,7],[3]])
    >>> b1
    BindingTree([[1, 2, 3, 6, 7], [1, 2, 3, 3]])
"""
    def __init__(self):
        self._b = [[]]

    def ext_or(self, l):
        self._b.extend(l)

    def int_or(self, l):
        new_b = []
        for choice in self._b:
            for choice2 in l:
                if isinstance(choice2, (set, list)):
                    choice2 = list(choice2)
                if not isinstance(choice2, list):
                    choice2 = [choice2]
                new_b.append(choice + choice2)
        self._b = new_b

    def int_and(self, l):
        for choice in self._b:
            choice.extend(list(l))

    def choices(self):
        for choice in self._b:
            yield choice

    def P(self):
        for choice in self._b:
            n, m = choice.pop()
            yield n, m, choice

    __iter__ = choices

    def __repr__(self):
        return u'%s(%s)' % (self.__class__.__name__, self._b)

    def __len__(self):
        return len(self._b)

    def isDefault(self):
        return self._b == [[]]

regular = []

class OrderedNodeSet(set):
    """A set with a first() method
    
    >>> o = OrderedNodeSet([5,3,1])
    >>> o.first()
    1
"""
    def first(self):
        return iter(sorted(self)).next()


class State(object):
    """ The state of a match problem

    It stores the current mapping, and creates values based on that
    """
    def __init__(self, problem, oldDict={}, u=True):
        self.problem = problem
        self.map = oldDict.copy()
        if u:
            self._update()

    def addNode(self, v1, v2):
        k = State(self.problem, self.map, False)
        k.map[v1] = v2
        k._update()
        return k

    def undo(self):
        pass

    def _update(self):
        G1, G2 = self.problem.G1, self.problem.G2
        self.reverseMap = {}
        for k, v in self.map.items():
            self.reverseMap[v] = k
        self.t1_in = OrderedNodeSet()
        self.t1_out = OrderedNodeSet()
        self.t2_in = OrderedNodeSet()
        self.t2_out = OrderedNodeSet()
        
        for node1, node2 in self.map.items():
            self.t1_in.update(x for x in G1.predecessors(node1).keys() if x not in self.map)
            self.t1_out.update(x for x in G1.followers(node1).keys() if x not in self.map)
            self.t2_in.update(x for x in G2.predecessors(node2).keys() if x not in self.reverseMap)
            self.t2_out.update(x for x in G2.followers(node2).keys() if x not in self.reverseMap)

        self.G1_not_taken = OrderedNodeSet(G1.nodes() - set(self.map))
        self.G2_not_taken = OrderedNodeSet(G2.nodes() - set(self.reverseMap))        

            
def match(s, extras=BindingTree()):
    """
Input: an intermediate state s
Output: the mapping between the two graphs

When a match forces a predicate match, we add that
to extras --- we go through all of those before continuing
on our regularly scheduled P(s)
    """
    progress( 'starting match')
    progress('s.map=%s' % s.map)
    G2 = s.problem.G2
    for choice in extras:
        if not choice:
            if set(s.map.values()) >= G2.allNodes():
                yield s.map
            elif set(s.map.values()) >= G2.nodes():
                yield finish(s, s.map)

            nodeList = P(s)
                
        else:
            n, m = choice[0]
            nodeList = [(n, m, choice[1:])]

        nodeList = [x for x in nodeList]
        progress('nodeList=', nodeList)
        for n,m, realExtras in nodeList:
            progress('... trying n,m=%s,%s' % (n,m))
            newExtras = BindingTree()
            newExtras.int_and(realExtras)
            if F(s,n,m, newExtras):
                s2 = s.addNode(n,m)
                for x in match(s2, newExtras): yield x
                s2.undo()

def finish(s, mapping):
    """ Wrap up never seen bNode edges
    Not written

    We should never get here
    """
    raise RuntimeError(s.problem.G2.allNodes() - set(mapping.values()), mapping)
        
def P(s):
    """
    Input: a state s
    Output: possible pairs to add to the mapping
    """
    G1 = s.problem.G1
    G2 = s.problem.G2
    t1_out_size, t2_out_size, t1_in_size, t2_in_size = (
        len(s.t1_out), len(s.t2_out), len(s.t1_in), len(s.t2_in))
    progress('P(s) %s %s %s %s' % (t1_out_size, t2_out_size, t1_in_size, t2_in_size))
    if t1_out_size and t2_out_size:
        progress(', case 1')
        m = s.t2_out.first()
        if representsSelf(m):
            if m in s.t1_out:
                yield m, m, regular
        else:
            for n in s.t1_out:
                yield n, m, regular
    elif not t1_out_size and not t2_out_size and t1_in_size and t2_in_size:
        progress(', case 2')
        m = s.t2_in.first()
        if representsSelf(m):
            if m in s.t1_in:
                yield m, m, regular
        else:
            for n in s.t1_in:
                yield n, m, regular
    elif not t1_out_size and not t2_out_size and not t1_in_size and not t2_in_size:
        progress(', case 3')
        m = s.G2_not_taken.first()
        if representsSelf(m):
            if m in s.G1_not_taken:
                yield m, m, regular
        else:
            for n in s.G1_not_taken:
                yield n, m, regular
    

def F(s, n, m, extras):
    """
    Input: a state s, and a pair of node n and m
    Output: Whether adding n->m is worth persuing
    """
##    extras = BindingTree()
    try:
        hash(n)
        hash(m)
    except TypeError:
        return True
    if n in s.map or m in s.reverseMap:
        if extras is False:
            progress(' -- failed because of used already')
            return False
        return True
    
    if not easyMatches(s, n, m):
        progress(' -- failed because of easymatches')
        return False
    G1 = s.problem.G1
    G2 = s.problem.G2
    
    termin1, termout1, termin2, termout2, new1, new2 = 0,0,0,0,0,0
    
    for obj, preds in G1.followers(n).items():
        if obj in s.map:
            image = s.map[obj]
            e = G2.edge(m, image)
            newBindings = BindingTree()
            if not e or not easyMatches(s, preds, e, newBindings):
                progress(' -- failed because of edge')
                return False
            if newBindings:
                extras.int_or(newBindings)
        else:
            if obj in s.t1_in:
                termin1 += 1
            if obj in s.t1_out:
                termout1 += 1
            if obj not in s.t1_in and obj not in s.t1_out:
                new1 += 1

    for subj, preds in G1.predecessors(n).items():
        if subj in s.map:
            image = s.map[subj]
            e = G2.edge(image, m)
            newBindings = BindingTree()
            if not e or not easyMatches(s, preds, e, newBindings):
                progress(' -- failed because of edge')
                return False
            if newBindings:
                extras.int_or(newBindings)
        else:
            if subj in s.t1_in:
                termin1 += 1
            if subj in s.t1_out:
                termout1 += 1
            if subj not in s.t1_in and subj not in s.t1_out:
                new1 += 1


    for obj, preds in G2.followers(m).items():
        progress("checking out %s's follower %s" % (m, obj))
        if obj in s.reverseMap:
            image = s.reverseMap[obj]
            e = G1.edge(n, image)
            newBindings = BindingTree()
            if not e or not easyMatches(s, preds, e, newBindings):
                progress(' -- failed because of edge')
                return False
##            if newBindings:
##                extras.int_or(newBindings)
        else:
            if obj in s.t2_in:
                termin2 += 1
            if obj in s.t2_out:
                termout2 += 1
            if obj not in s.t2_in and obj not in s.t2_out:
                new2 += 1

    for subj, preds in G2.predecessors(m).items():
        if subj in s.reverseMap:
            image = s.reverseMap[subj]
            e = G1.edge(image, n)
            newBindings = BindingTree()
            if not e or not easyMatches(s, preds, e, newBindings):
                progress(' -- failed because of edge')
                return False
##            if newBindings:
##                extras.int_or(newBindings)
        else:
            if subj in s.t2_in:
                termin2 += 1
            if subj in s.t2_out:
                termout2 += 1
            if subj not in s.t2_in and subj not in s.t2_out:
                new2 += 1


## For subgraph, change to <=
    if not isoCheck(termin1,termin2,termout1,termout2,new1,new2):
        progress(' -- failed because of secondary')
        progress('termin1=%s\ntermin2=%s\ntermout1=%s\ntermout2=%s\nnew1=%s\nnew2=%s\n' %
                 (termin1,termin2,termout1,termout2,new1,new2))
        return False
    
    return hardMatches(s, n, m)

def isoCheck(termin1,termin2,termout1,termout2,new1,new2):
    return termin1 == termin2 and \
            termout1 == termout2 and \
            new1 == new2


###################### everything after this begins to be implementation specific
def easyMatches(s, n1, n2, newBindings=BindingTree(), boring=True):
##    progress('easymatches on %s and %s' % (n1, n2))
    if isinstance(n1, set):
        n1 = frozenset(n1)
    if isinstance(n2, set):
        n2 = frozenset(n2)
    if n1 in s.map:
        progress('Already known case')
        return s.map[n1] == n2
    if not boring:
        newBindings.int_and([(n1,n2)])
    progress('newBindings=%s' % newBindings)
    if isLiteral(n1) and isLiteral(n2):
        return n1 == n2
    if isSymbol(n1) and isSymbol(n2):
        return n1 == n2
    if isExistential(n1) and isExistential(n2):
        return True
    if isList(n1) and isList(n2):
        n3 = n1.first
        n4 = n2.first
        if easyMatches(s, n3, n4, newBindings, False):
            return easyMatches(s, n1.rest, n2.rest, newBindings)
    if isFormula(n1) and isFormula(n2):
        matches = match(n1, n2)
        if not matches:
            return False
        newBindings.int_or([x.items() for x in matches])
        return True
    if isSet(n1) and isSet(n2):
###  set matching
###  This is annoying. We mostly will try to do anything to
###  avoid this
###
        progress('Starting set matching on %s=?%s' % (n1, n2))
    ## first test length
        if len(n1) != len(n2):
            progress('Different sizes!')
            return False
    ## easy cases are easy
        if len(n1) == 1:
            progress('Size 1 --- easy')
            return easyMatches(s, iter(n1).next(), iter(n2).next(), newBindings, False)
    ## knock out everything we know
        for x1 in n1:
            if x1 in s.map and s.map[x1] not in n2:
                progress('map failed --- s[%s] == %s, couldn\'t find it' % (x1, s.map[x1]))
                return False
        n1 = set([x for x in n1 if x not in s.map])
        n2 = set([x for x in n2 if x not in s.reverseMap])
    ## redundant, hopefully
        if len(n1) != len(n2):
            progress('How did I get here?')
            return False

    ## sort into classes
        tests = isLiteral, isSymbol, isExistential, isUniversal, isList, isFormula, isSet
        g1 = tuple([set() for x in tests])
        g2 = tuple([set() for x in tests])
        for g, n3 in (g1, n1), (g2, n2):
            for x in n3:
                for i in range(len(tests)):
                    test = tests[i]
                    if test(x):
                        g[i].add(x)
                        break
                else:
                    raise TypeError(x)

        progress('Sort got us %s,%s' % (g1,g2))
    ## make sure every class works
        if [len(x) for x in g1] != [len(x) for x in g2]:
            progress('One class had a length mismatch!')
            return False
    ## literals and symbols must match themselves
        for s1, s2 in (g1[0], g2[0]), (g1[1], g2[1]):
            for x in s1:
                if x not in s2:
                    progress("Failed to find `%s' in s2=%s" % (x, s2))
                    return False
                newBindings.int_and([(x,x)])

    ## rest are harder to do
    ## do we ever want to enumerate this?
        for s1, s2 in zip(g1[2:], g2[2:]):
            b = []
            s1 = list(s1)
            for k in orderings(list(s2)):
                b.append(zip(s1, k))
            newBindings.int_or(b)

        progress('After that, newBindings=%s' % newBindings)
        return True
    return False

def orderings(l):
    if not l:
        yield l
    else:
        for i in range(len(l)):
            l2 = l[:i] + l[i+1:]
            x = [l[i]]
            for o2 in orderings(l2):
                yield x + o2    

def memoizeEasyMatches(f):
    saved = {}
    def f2(s, n1, n2, *args, **keywords):
        if isinstance(n1, set):
            n11 = frozenset(n1)
        else:
            n11 = n1
        if isinstance(n2, set):
            n22 = frozenset(n2)
        else:
            n22 = n2
        if (n11, n22) not in saved:
            saved[(n11, n22)] = f(s, n1, n2, *args, **keywords)
        return saved[(n11, n22)]
    return f2

## easyMatches = memoizeEasyMatches(easyMatches)

def representsSelf(x):
    return isLiteral(x) or isSymbol(x)

def isLiteral(x):
    return isinstance(x, (str, unicode)) and x[0:1] == '"'
def isSymbol(x):
    return isinstance(x, (str, unicode)) and x[0:1] == '<'
def isExistential(x):
    return isinstance(x, (str, unicode)) and x[0:1] == '_'
def isUniversal(x):
    return False
def isList(x):
    return False
def isFormula(x):
    return False
def isSet(x):
    return isinstance(x, (set, frozenset))

def hardMatches(s, n1, n2, newBindings=BindingTree()):
    return True


### stolen from cant.py
import re, os, urllib
from sys import stderr

name = "[A-Za-z][A-Za-z0-9]*" #http://www.w3.org/TR/rdf-testcases/#ntriples
nodeID = '_:' + name
uriref = r'<[^>]*>'
language = r'[a-z0-9]+(?:-[a-z0-9]+)?'
string_pattern = r'".*"'   # We know in ntriples that there can only be one string on the line
langString = string_pattern + r'(?:@' + language + r')?'
datatypeString = langString + '(?:\^\^' + uriref + r')?' 
#literal = langString + "|" + datatypeString
objec =  r'(' + nodeID + "|" + datatypeString + "|" + uriref + r')'
ws = r'[ \t]*'
com = ws + r'(#.*)?[\r\n]*' 
comment = re.compile("^"+com+"$")
statement = re.compile( ws + objec + ws + objec + ws + objec  + com) # 


from sys import exit

class Graph(object):
    """A NTriples Graph

This implementation is optimized for this algorithm.
Any implementation used with this algorithm needs
those methods implemented as O(1) operations.
    """
    def __init__(self, fname):
        self.f = {}
        self.p = {}
        self.e = {}
        self.triples = set()
        self.nodeSet = set()
        self.predSet = set()
        for triple in self.parseFile(fname):
            s, p, o = triple
            self.nodeSet.add(s)
            self.nodeSet.add(o)
            self.predSet.add(p)
            if s not in self.f:
                self.f[s] = {}
            if o not in self.p:
                self.p[o] = {}
            if (s,o) not in self.e:
                self.e[(s,o)] = set()
            if o not in self.f[s]:
                self.f[s][o] = set()
            if s not in self.p[o]:
                self.p[o][s] = set()
            self.f[s][o].add(p)
            self.p[o][s].add(p)
            self.e[(s,o)].add(p)


            
    def edge(self, subj, obj):
        return set(self.e.get((subj, obj), set()))
    
    def followers(self, subj):
        return dict(self.f.get(subj, {}))
    
    def predecessors(self, obj):
        return dict(self.p.get(obj, {}))

    def nodes(self):
        return self.nodeSet

    def allNodes(self):
        return self.nodeSet | self.predSet
    
    def parseFile(self, name):
        graph = []
        WD = "file://" + os.getcwd() + "/"

	if verbose: stderr.write("Loading data from %s\n" % name)

	uri = uripath.join(WD, name)
	inStream = urllib.urlopen(uri)
	for line in inStream:
	    if line == "" : break	    
#	    if verbose: stderr.write("%s\n" % line)
	    m = comment.match(line)
	    if m != None: continue
	    m = statement.match(line)
	    if m == None:
		stderr.write("Syntax error: "+line+"\n")
		if verbose:
                    [stderr.write('%2x ' % ord(c)) for c in line]
                    stderr.write('\n')
		exit(-1)
	    triple = m.group(1), m.group(2), m.group(3)
	    if verbose: stderr.write( "Triple: %s  %s  %s.\n" % (triple[0], triple[1], triple[2]))
	    yield triple

def unifyFormulae(f1, f2):
    """unify two graphs

    It was for this function that this file was written
    However, it cannot stand alone
    """
    m = {}
    pr = Problem(G1=f1,G2=f2)
    s = State(pr,m)
    matches = [m for m in match(s)]
    return matches
            
def _test():
    import doctest
    progress = progress2
    doctest.testmod()

### testing stuff
def main():
    import sys
    g1 = Graph(sys.argv[1])
    g2 = Graph(sys.argv[2])
    m = {}
    for n1 in g1.allNodes():
        if n1 in g2.allNodes() and \
           representsSelf(n1):
            m[n1]=n1
        elif representsSelf(n1):
            return False
    pr = Problem(G1=g1,G2=g2)
    s = State(pr)
    for m in match(s):
        print m

if __name__ == '__main__':
    import sys
    if sys.argv[1:2] == ['--test']:
        _test()
    else:
        main()
