"""


"""
import sys
sys.path.append('/home/syosi/SWAP/grammar')
import sparql_tokens
import time

try:
    from swap import webAccess, uripath, llyn, myStore, term, diag
    from swap.myStore import load, Namespace
    from swap.term import Literal
    from swap.diag import progress, chatty_flag
except ImportError:
    import webAccess, uripath, llyn, myStore, term, diag
    from myStore import load, Namespace
    from term import Literal
    from diag import progress, chatty_flag

BNF = Namespace("http://www.w3.org/2000/10/swap/grammar/bnf#")

def abbr(prodURI):
   if prodURI is None: return None
   return prodURI.split('#').pop()

class Rule(object):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def __getitem__(self, i):
        if i == len(self.rhs):
            return None
        return self.rhs[i]

    def __len__(self):
        return len(self.rhs)

    def end(self, num):
        return num >= len(self.rhs)

    def inrule(self, num):
        return num < len(self.rhs)

    def __repr__(self):
        return 'Rule(%s: %s)' % (repr(self.lhs), repr(self.rhs))

class Production(object):
    def __init__(self, lhs, choices):
        self.ors = [Rule(lhs, choice) for choice in choices]
        self.lhs = lhs

    def choices(self):
        return self.ors


class Earley_Set(object):
    def __init__(self):
        self.set = set()
        self.tokens = {}
        self.productions = {}

    def add(self, item):
        rule, loc, line, hist = item
        lhs = rule.lhs
        self.set.add(item)
        tok = abbr(rule[loc])
        if tok not in self.tokens:
            self.tokens[tok] = set()
        self.tokens[tok].add(item)
        if lhs not in self.productions:
            self.productions[lhs] = set()
        self.productions[lhs].add(item)

    def update(self, _iter):
        for _a in _iter:
            self.add(_a)

    def __iter__(self):
        return iter(self.set)

    def __repr__(self):
        return 'EarleySet(%s)' % repr(list(self.set))

def find_nulls(rules):
    class internal(object):
        def __init__(self, productions):
            self.productions = productions
            self.status = {}
        def run(self, rule):
            if rule in self.status:
                return self.status[rule]
            self.status[rule] = False
            if rule not in self.productions:
                self.status[rule] = False
                return False
            for choice in self.productions[rule].choices():
                for term in choice.rhs:
                    if not self.run(term): break
                else:
                    self.status[rule] = True
                    return True
    obj = internal(rules)
    for r in rules:
        obj.run(r)
    def nullable(table, term):
        return table.get(term, False)
    
    return nullable.__get__(obj.status)

def find_null_connected(productions, null):
    class internal(object):
        def __init__(self, productions, null):
            self.productions = productions
            self.null = null
            self.status = {}
        def run(self, rule):
            null = self.null
            jumps = set()
            self.status[rule] = jumps
            for choice in self.productions[rule].choices():
                n = 0
                k = True
                while k:
                    jumps.add((choice, n))
                    if choice.inrule(n) and null(choice[n]):
                        n = n+1
                    else:
                        k = False

        def deepen(self, rule):
            if rule not in self.productions:
                return set()
            for r, n in set(self.status[rule]):
                self.status[rule].update(self.status.get(r[n], set()))

        def followers(self, rule, loc):
            if rule.end(loc):
                return set()
            if (rule, loc) in self.status:
                return self.status[(rule, loc)]
            retVal = set()
            self.status[(rule, loc)] = retVal
            if self.null(rule[loc]):
                retVal.update(self.followers(rule, loc+1))
            if rule[loc] in self.productions:
                retVal.update(self.status[rule[loc]])
            return retVal

    obj = internal(productions, null)
    for r in productions:
        obj.run(r)
    for r in productions:
        for k in productions:
            obj.deepen(k)

    for p in productions:
        for r in productions[p].choices():
            for n in range(len(r)):
                obj.followers(r, n)
    return obj.status

def makeHistory(rule, loc, locEnd = None):
    if locEnd is None:
        locEnd = loc
        locStart = 0
    else:
        locStart = loc
    retVal = []
    for i in xrange(locStart, locEnd):
        retVal.append((rule[i],))
    return tuple(retVal)

class Earley(object):
    def __init__(self, start, productions, followers, null):
        #self.productions = productions
        self.null = null
        self.followers = followers
        self.start = start

    def parse(self, tokenSource):
        self.tokens = tokenSource
        self.sets = []
        self.zeroset()
        tok = self.tokens()
        while tok:
            self.scan(tok)
            self.predict()
            self.complete()
            tok = self.tokens()
        return self.sets

    def zeroset(self):
        set0 = Earley_Set()
        prod = self.followers[self.start]
        for rule, loc in prod:
            set0.add((rule, loc, 0, makeHistory(rule, loc)))
        self.sets.append(set0)
        self.complete()
        self.predict()

    def scan(self, token):
        name, term, line = token
        oldSet = self.sets[-1]
        newSet = Earley_Set()
        #print oldSet.set
        #print "set " + `len(self.sets) -1` + ': ' + `oldSet.tokens.keys()`
        #print '====='
        for rule, loc, num, hist in oldSet.tokens[name]:
            newSet.add((rule, loc+1, num, hist + (token,)))
            #Here is where I call something for matching a token. A fourth piece of the
            #items might work best...
        self.sets.append(newSet)

    def predict(self):
        theSet = self.sets[-1]
        line = len(self.sets) - 1
        newSet = set()
        for rule, loc, num, hist in theSet.set:
            tok = rule[loc]
            if tok is not None and tok in self.followers:
                newSet.update([(rule, loc, line, makeHistory(rule, loc)) for rule, loc in self.followers[tok]])
        theSet.update(newSet)

    def complete(self):
        theSet = self.sets[-1]
        now = len(self.sets) - 1
        a = 0
        while theSet.tokens.get(None, False):
            newSet = Earley_Set()
            mSet = set()
            for rule, loc, num, hist in theSet.tokens[None]:
                #print rule.lhs, num
                for r2, l2, n2, h2 in self.sets[num].tokens[abbr(rule.lhs)]:
                    #print '  ' + `(r2, l2)`
                    newSet.add((r2, l2+1, n2, h2 + ((rule.lhs,) + hist,)))
                    k = 1
                    while self.null(r2[l2+k]):
                        newSet.add((r2, l2+k+1, n2, h2 + ((rule.lhs,) + hist,) + makeHistory(r2, l2+1, l2+1+k)))
                        k += 1
                    #print '\nl2 = ' + `l2`
                    if r2.inrule(l2+1):
                        mSet.update([(r3, l3, now, makeHistory(r3, l3)) for r3, l3 in self.followers[(r2, l2+1)]])
            #print '%s: Added = %s' % (a, newSet.set)
            #print '%s: TheSet = %s' % (a, theSet.set)
            self.sets[-1].update(mSet)
            a += 1
            if theSet.set >= newSet.set:
                self.sets[-1].update(newSet)
                return
            self.sets[-1].update(newSet)
            theSet = newSet
            


class AST(object):
    def __init__(self, ast):
        self.ast = ast
        self.sink = self
    def prod(self, thing):
        return thing[0]
    def run(self):
        self.productions = []
        stack = [[self.ast, 0]]
        while stack:
            if len(stack[-1][0]) == 3 and type(stack[-1][0][1]) is not tuple:
                self.onToken(stack[-1][0][0], stack[-1][0][1])
                stack.pop()
            elif stack[-1][1] >= len(stack[-1][0]):
                self.onFinish()
                stack.pop()
            else:
                k = stack[-1][1]
                stack[-1][1] = k + 1
                if k == 0:
                    self.onStart(stack[-1][0][0])
                else:
                    stack.append([stack[-1][0][k], 0])
                
        

    def onStart(self, prod): 
      print (' ' * len(self.productions)) + `prod`
      self.productions.append([prod])

    def onFinish(self): 
      prod = self.sink.prod(self.productions.pop())
      if self.productions:
          self.productions[-1].append(prod)
      print (' ' * len(self.productions)) + '/' + `prod`
      return prod

    def onToken(self, prod, tok):
      self.productions[-1].append((prod, tok))
      print (' ' * len(self.productions)) + `(prod, tok)`

def get_productions(uri):
    g = load(uri)
    rules = {}
    for triple in g.statementsMatching(pred=BNF.mustBeOneSequence):
        lhs, p, rhs = triple.spo()
        lhs = lhs.uriref()
        rhs = [[y.uriref() for y in x] for x in rhs]
        rules[lhs] = Production(lhs, rhs)
    return rules

def parse(uri, start, productions, followers, null):
    k0 = time.time()
    lexer = sparql_tokens.Lexer()
    k1 = time.time()
    ip = webAccess.urlopenForRDF(uri, None)
    lexer.input(ip)
    parser = Earley(start,productions,followers, null)
    print 'ready to parse\n\n'
    k2 = time.time()
    return (parser.parse(lexer.token)[-1].productions[start], k1 - k0, k1)


def make_table(out, f, predict):
    import pprint
    pp = pprint.PrettyPrinter()
    print >> out, '#!/usr/bin/env python'
    print >> out, '"""tables - For use with earley.py."""'
    print >> out, '# Automatically generated by earley.py'
    print >> out
    print >> out, 'predict =', pp.pformat(predict)
    print >> out, 'def nullable(table, term):'
    print >> out, '    return table.get(term, False)'
    print >> out, 'nullTable = ', pp.pformat(f.im_self)
    print >> out, 'null = nullable.__get__(nullTable)'
    print >> out
    print >> out, 'if __name__=="__main__": '
    print >> out, '   print __doc__'

if __name__ == '__main__':
    p = get_productions(sys.argv[1])
    f = find_nulls(p)
    
    predict = find_null_connected(p, f)

    out = file('earley_tables.py', 'w')
    make_table(out, f, predict)
##    for m in sorted(predict.items()):
##        print '\t%s: %s\n' % m
##    sys.exit(0)
    print 'ready to lex'
    results, t1, k2 = parse(sys.argv[3], sys.argv[2], p, predict, f)
    t2 = time.time() - k2
    
    #print '\n\n\t'.join([`a` for a in results])
    for a in results:
        AST((sys.argv[2],) + a[3]).run()
    print t1,t2,t1+t2
    
