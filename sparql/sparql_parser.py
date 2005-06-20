#!/usr/bin/env python
"""
N3P - An N3 Parser using n3.n3
Author: Sean B. Palmer, inamidst.com
Licence: GPL 2; share and enjoy!
Documentation: http://inamidst.com/n3p/
Derived from: 
   http://www.w3.org/2000/10/swap/grammar/predictiveParser.py
   - predictiveParser.py, Tim Berners-Lee, 2004
Issues: 
   http://lists.w3.org/Archives/Public/public-cwm-bugs/2005Jan/0006
   http://lists.w3.org/Archives/Public/public-cwm-talk/2005JanMar/0015
"""
from set_importer import Set

import sys, os, re, urllib
import sparql_tokens

tokens = Set(sparql_tokens.tokens)
import cPickle as pickle

try: set()
except NameError: 
   from sets import Set as set

try: 
   import sparql
   branches = sparql.branches
except ImportError: 
   for path in sys.path: 
      fn = os.path.join(path, 'n3meta.pkl')
      if os.path.isfile(fn): 
         f = open(fn, 'rb')
         n3meta = pickle.load(f)
         f.close()

         branches = n3meta['branches']
         break

start = 'http://www.w3.org/2000/10/swap/grammar/sparql#Query'


def abbr(prodURI): 
   return prodURI.split('#').pop()

class N3Parser(object): 
   def __init__(self, buffer, branches):
      lexer = sparql_tokens.Lexer()
      lexer.input(buffer)
      self.data = lexer.token
      self.newToken()
      self.branches = branches
      self.productions = []
      self.memo = {}

   def parse(self, prod):
      todo_stack = [[prod, None]]
      while todo_stack:
          #print todo_stack
          #prod = todo_stack.pop()
          if todo_stack[-1][1] is None:
              todo_stack[-1][1] = []
              tok = self.token
              # Got an opened production
              self.onStart(abbr(todo_stack[-1][0]))
              if not tok: 
                 return tok # EOF

              prodBranch = self.branches[todo_stack[-1][0]]
              print prodBranch
              sequence = prodBranch.get(tok, None)
              if sequence is None: 
                 print >> sys.stderr, 'prodBranch', prodBranch
                 raise Exception("Found %s when expecting a %s . todo_stack=%s" % (tok, todo_stack[-1][0], `todo_stack`))
              for term in sequence:
                 todo_stack[-1][1].append(term)
          while todo_stack[-1][1]:
             term = todo_stack[-1][1].pop(0)
             if abbr(term) in tokens: 
                j = self.pos + len(term)
                name, word, line = self.token
                if name == term: 
                   self.onToken(term, word)
                   self.newToken()
                else: raise Exception("Found %s; %s expected" % \
                             (self.data[self.pos:self.pos+10], term))
             else:
                todo_stack.append([term, None])
                
          while todo_stack[-1][1] == []:
              todo_stack.pop()
              self.onFinish()
      

   def newToken(self): 
      self.token = self.data()

   def onStart(self, prod): 
      print (' ' * len(self.productions)) + prod
      self.productions.append([prod])

   def onFinish(self): 
      prod = self.productions.pop()
      if self.productions:
          self.productions[-1].append(prod)
      print (' ' * len(self.productions)) + '/' + prod

   def onToken(self, prod, tok):
      self.productions[-1].append((prod, tok))
      print (' ' * len(self.productions)) + prod, tok

def main(argv=None): 
   if argv is None: 
      argv = sys.argv
   if len(argv) == 2: 
      p = N3Parser(file(argv[1], 'r'), branches)
      p.parse(start)

if __name__=="__main__": 
   main()
