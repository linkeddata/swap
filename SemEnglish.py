"""

transcribed from

http://robustai.net/mentography/SyntaxSemenglish7.gif
Last Modified: Sunday, 22-Jul-01 19:59:51 GMT

other sources:

  SemEnglish Primer 
  Created 2001/1/26 last revised 2001/3/25 
  pronounced `sem.Eng.lish 
  http://robustai.net/mentography/semenglish.html
"""


from string import *
import re
from yappsrt import *

class SemEnglishScanner(Scanner):
    def __init__(self, str):
        Scanner.__init__(self,[
            ('"exp"', 'exp'),
            ('"}"', '}'),
            ('"{"', '{'),
            ('","', ','),
            ('";"', ';'),
            ('"\\\\]"', '\\]'),
            ('"\\\\["', '\\['),
            ('"\\\\)"', '\\)'),
            ('"\\\\("', '\\('),
            ('"\\\\."', '\\.'),
            ('[ \\r\\n\\t\\f]+', '[ \\r\\n\\t\\f]+'),
            ('Dquote', '"[^\\"]*"'),
            ('Squote', "'[^\\']*'"),
            ('Number', '[0-9]+'),
            ('THAT', 'that'),
            ('Word', '[^ \\n\\r\\t\\f"\\)\\({}\\[\\];]*[^ \\n\\r\\t\\f"\\)\\({}\\[\\];\\.0-9]'),
            ('END', '\\Z'),
            ], ['[ \\r\\n\\t\\f]+'], str)

class SemEnglish(Parser):
    def document(self):
        while self._peek('END', 'Word', 'Number', '"}"', '"\\\\("', '"\\\\["') not in ['END', '"}"']:
            Statement = self.Statement()
        END = self._scan('END')

    def Statement(self):
        Subject = self.Subject()
        Predicate = self.Predicate()
        while self._peek() == '";"':
            AddPredicate = self.AddPredicate()
        if self._peek('"\\\\."', 'END', '"}"', 'Word', 'Number', '"\\\\("', '"\\\\["') == '"\\\\."':
            self._scan('"\\\\."')
        print "@@got one statement"

    def Subject(self):
        _token_ = self._peek('Word', 'Number', '"\\\\("', '"\\\\["')
        if _token_ == '"\\\\("':
            CompoundWords = self.CompoundWords()
        elif _token_ == 'Word':
            Word = self._scan('Word')
        elif _token_ == 'Number':
            Number = self._scan('Number')
        else: # == '"\\\\["'
            AnnNode = self.AnnNode()

    def CompoundWords(self):
        self._scan('"\\\\("')
        while 1:
            Word = self._scan('Word')
            if self._peek('Word', '"\\\\)"') != 'Word': break
        self._scan('"\\\\)"')

    def AnnNode(self):
        self._scan('"\\\\["')
        Predicate = self.Predicate()
        self._scan('"\\\\]"')

    def Predicate(self):
        Verb = self.Verb()
        Object = self.Object()
        while self._peek() == '","':
            AddObject = self.AddObject()

    def AddPredicate(self):
        self._scan('";"')
        Predicate = self.Predicate()

    def Verb(self):
        _token_ = self._peek('"\\\\("', 'Word')
        if _token_ == '"\\\\("':
            CompoundWords = self.CompoundWords()
        else: # == 'Word'
            Word = self._scan('Word')

    def Object(self):
        _token_ = self._peek('"\\\\("', 'Word', 'Number', '"\\\\["', '"exp"', 'THAT', '"{"', 'Dquote', 'Squote')
        if _token_ == '"\\\\("':
            CompoundWords = self.CompoundWords()
        elif _token_ != '"exp"':
            ExpObject = self.ExpObject()
        else: # == '"exp"'
            Expression = self.Expression()

    def AddObject(self):
        self._scan('","')
        Object = self.Object()

    def ExpObject(self):
        _token_ = self._peek('Word', 'Number', '"\\\\["', 'THAT', '"{"', 'Dquote', 'Squote')
        if _token_ == 'Word':
            Word = self._scan('Word')
        elif _token_ == 'Number':
            Number = self._scan('Number')
        elif _token_ == '"\\\\["':
            AnnNode = self.AnnNode()
        elif _token_ == 'THAT':
            ReifiedStatement = self.ReifiedStatement()
        elif _token_ == '"{"':
            Context = self.Context()
        else: # in ['Dquote', 'Squote']
            Literal = self.Literal()

    def ReifiedStatement(self):
        THAT = self._scan('THAT')
        self._scan('"\\\\("')
        Subject = self.Subject()
        Verb = self.Verb()
        Object = self.Object()
        self._scan('"\\\\)"')

    def Context(self):
        self._scan('"{"')
        while self._peek('"}"', 'Word', 'Number', 'END', '"\\\\("', '"\\\\["') not in ['"}"', 'END']:
            Statement = self.Statement()
        self._scan('"}"')

    def Literal(self):
        _token_ = self._peek('Dquote', 'Squote')
        if _token_ == 'Dquote':
            Dquote = self._scan('Dquote')
        else: # == 'Squote'
            Squote = self._scan('Squote')

    def Expression(self):
        self._scan('"exp"')
        Nexpression = self.Nexpression()

    def Nexpression(self):
        self._scan('"\\\\("')
        Verb = self.Verb()
        while 1:
            ExpObject_ = self.ExpObject_()
            if self._peek() not in ['Word', 'Number', '"\\\\["', '"\\\\("', 'THAT', '"{"', 'Dquote', 'Squote']: break
        self._scan('"\\\\)"')

    def ExpObject_(self):
        _token_ = self._peek('Word', 'Number', '"\\\\["', '"\\\\("', 'THAT', '"{"', 'Dquote', 'Squote')
        if _token_ != '"\\\\("':
            ExpObject = self.ExpObject()
        else: # == '"\\\\("'
            Nexpression = self.Nexpression()


def parse(rule, text):
    P = SemEnglish(SemEnglishScanner(text))
    return wrap_error_reporter(P, rule)

if __name__=='__main__':
    from sys import argv, stdin
    if len(argv) >= 2:
        if len(argv) >= 3:
            f = open(argv[2],'r')
        else:
            f = stdin
        print parse(argv[1], f.read())
    else: print 'Args:  <rule> [<filename>]'
