""" kifForm.g -- a Yapps grammar for KIF Forms

$Id$

References

  Yapps: Yet Another Python Parser System
  http://theory.stanford.edu/~amitp/Yapps/
  Sat, 18 Aug 2001 16:54:32 GMT
  Last modified 13:21 Sun 26 Nov 2000 , Amit Patel 

  Knowledge Interchange Format
  draft proposed American National Standard (dpANS)
  NCITS.T2/98-004
  http://logic.stanford.edu/kif/dpans.html
  Thu, 25 Jun 1998 22:31:37 GMT
"""


from string import *
import re
from yappsrt import *

class KIFParserScanner(Scanner):
    def __init__(self, str):
        Scanner.__init__(self,[
            ('"\\\\(\\s*exists"', '\\(\\s*exists'),
            ('"\\\\(\\s*forall"', '\\(\\s*forall'),
            ('"\\\\(\\s*<=>"', '\\(\\s*<=>'),
            ('"\\\\(\\s*<="', '\\(\\s*<='),
            ('"\\\\(\\s*=>"', '\\(\\s*=>'),
            ('"\\\\(\\s*or"', '\\(\\s*or'),
            ('"\\\\(\\s*and"', '\\(\\s*and'),
            ('"\\\\(\\s*not"', '\\(\\s*not'),
            ('"\\\\(\\s*holds"', '\\(\\s*holds'),
            ('"\\\\(\\s*/="', '\\(\\s*/='),
            ('"\\\\(\\s*="', '\\(\\s*='),
            ('"\\\\(\\s*cond"', '\\(\\s*cond'),
            ('"\\\\(\\s*if"', '\\(\\s*if'),
            ('"\\\\(\\s*listof"', '\\(\\s*listof'),
            ('"\\\\(\\s*value"', '\\(\\s*value'),
            ('"\\\\("', '\\('),
            ('"\'"', "'"),
            ('"\\\\)"', '\\)'),
            ('"\\\\(\\s*quote"', '\\(\\s*quote'),
            ('[ \\t\\r\\n\\f]+', '[ \\t\\r\\n\\f]+'),
            ('indvar', '\\?[A-Za-z0-9!$%&*+\\-\\./<=>?@_~]([A-Za-z0-9!$%&*+\\-\\./<=>?@_~]|\\\\[.\\n])*'),
            ('seqvar', '@?[A-Za-z0-9!$%&*+\\-\\./<=>?@_~]([A-Za-z0-9!$%&*+\\-\\./<=>?@_~]|\\\\[.\\n])*'),
            ('constant', '[A-Za-z0-9!$%&*+\\-\\./<=>_~]([A-Za-z0-9!$%&*+\\-\\./<=>?@_~]|(\\\\.))*'),
            ('word', '[A-Za-z0-9!$%&*+\\-\\./<=>?@_~]([A-Za-z0-9!$%&*+\\-\\./<=>?@_~]|(\\\\.))*'),
            ('charref', '#\\\\[.\\n]'),
            ('string', '"([^\\"\\\\]|\\\\.)*"'),
            ('block', '#\\d+.*'),
            ], ['[ \\t\\r\\n\\f]+'], str)

class KIFParser(Parser):
    def variable(self):
        _token_ = self._peek('indvar', 'seqvar')
        if _token_ == 'indvar':
            indvar = self._scan('indvar')
        else: # == 'seqvar'
            seqvar = self._scan('seqvar')

    def term(self):
        _token_ = self._peek('indvar', 'constant', 'charref', 'string', 'block', '"\\\\(\\s*quote"', '"\'"', '"\\\\(\\s*value"', '"\\\\("', '"\\\\(\\s*listof"', '"\\\\(\\s*if"', '"\\\\(\\s*cond"')
        if _token_ == 'indvar':
            indvar = self._scan('indvar')
        elif _token_ == 'constant':
            constant = self._scan('constant')
        elif _token_ == 'charref':
            charref = self._scan('charref')
        elif _token_ == 'string':
            string = self._scan('string')
        elif _token_ == 'block':
            block = self._scan('block')
        elif _token_ in ['"\\\\(\\s*quote"', '"\'"']:
            quoterm = self.quoterm()
        elif _token_ not in ['"\\\\(\\s*listof"', '"\\\\(\\s*if"', '"\\\\(\\s*cond"']:
            funterm = self.funterm()
        elif _token_ == '"\\\\(\\s*listof"':
            listterm = self.listterm()
        else: # in ['"\\\\(\\s*if"', '"\\\\(\\s*cond"']
            logterm = self.logterm()

    def quoterm(self):
        _token_ = self._peek('"\\\\(\\s*quote"', '"\'"')
        if _token_ == '"\\\\(\\s*quote"':
            self._scan('"\\\\(\\s*quote"')
            listexpr = self.listexpr()
            self._scan('"\\\\)"')
        else: # == '"\'"'
            self._scan('"\'"')
            listexpr = self.listexpr()

    def listexpr(self):
        _token_ = self._peek('"\\\\("', 'word', 'charref', 'string', 'block')
        if _token_ != '"\\\\("':
            atom = self.atom()
        else: # == '"\\\\("'
            self._scan('"\\\\("')
            while self._peek() in ['"\\\\("', 'word', 'charref', 'string', 'block']:
                listexpr = self.listexpr()
            self._scan('"\\\\)"')

    def atom(self):
        _token_ = self._peek('word', 'charref', 'string', 'block')
        if _token_ == 'word':
            word = self._scan('word')
        elif _token_ == 'charref':
            charref = self._scan('charref')
        elif _token_ == 'string':
            string = self._scan('string')
        else: # == 'block'
            block = self._scan('block')

    def funterm(self):
        _token_ = self._peek('"\\\\(\\s*value"', '"\\\\("')
        if _token_ == '"\\\\(\\s*value"':
            self._scan('"\\\\(\\s*value"')
            term = self.term()
            while self._peek() in ['indvar', 'constant', 'charref', 'string', 'block', '"\\\\(\\s*quote"', '"\'"', '"\\\\(\\s*value"', '"\\\\("', '"\\\\(\\s*listof"', '"\\\\(\\s*if"', '"\\\\(\\s*cond"']:
                term = self.term()
            if self._peek('seqvar', '"\\\\)"') == 'seqvar':
                seqvar = self._scan('seqvar')
            self._scan('"\\\\)"')
        else: # == '"\\\\("'
            self._scan('"\\\\("')
            constant = self._scan('constant')
            while self._peek() in ['indvar', 'constant', 'charref', 'string', 'block', '"\\\\(\\s*quote"', '"\'"', '"\\\\(\\s*value"', '"\\\\("', '"\\\\(\\s*listof"', '"\\\\(\\s*if"', '"\\\\(\\s*cond"']:
                term = self.term()
            if self._peek('seqvar', '"\\\\)"') == 'seqvar':
                seqvar = self._scan('seqvar')
            self._scan('"\\\\)"')

    def listterm(self):
        self._scan('"\\\\(\\s*listof"')
        while self._peek() in ['indvar', 'constant', 'charref', 'string', 'block', '"\\\\(\\s*quote"', '"\'"', '"\\\\(\\s*value"', '"\\\\("', '"\\\\(\\s*listof"', '"\\\\(\\s*if"', '"\\\\(\\s*cond"']:
            term = self.term()
        if self._peek('seqvar', '"\\\\)"') == 'seqvar':
            seqvar = self._scan('seqvar')
        self._scan('"\\\\)"')

    def logterm(self):
        _token_ = self._peek('"\\\\(\\s*if"', '"\\\\(\\s*cond"')
        if _token_ == '"\\\\(\\s*if"':
            self._scan('"\\\\(\\s*if"')
            while 1:
                logpair = self.logpair()
                if self._peek() not in ['constant', '"\\\\(\\s*="', '"\\\\(\\s*/="', '"\\\\(\\s*holds"', '"\\\\("', '"\\\\(\\s*not"', '"\\\\(\\s*and"', '"\\\\(\\s*or"', '"\\\\(\\s*=>"', '"\\\\(\\s*<="', '"\\\\(\\s*<=>"', '"\\\\(\\s*forall"', '"\\\\(\\s*exists"']: break
            if self._peek() in ['indvar', 'constant', 'charref', 'string', 'block', '"\\\\(\\s*quote"', '"\'"', '"\\\\(\\s*value"', '"\\\\("', '"\\\\(\\s*listof"', '"\\\\(\\s*if"', '"\\\\(\\s*cond"']:
                term = self.term()
            self._scan('"\\\\)"')
        else: # == '"\\\\(\\s*cond"'
            self._scan('"\\\\(\\s*cond"')
            while self._peek('"\\\\)"', '"\\\\("') == '"\\\\("':
                logitem = self.logitem()
            self._scan('"\\\\)"')

    def logpair(self):
        sentence = self.sentence()
        term = self.term()

    def logitem(self):
        self._scan('"\\\\("')
        sentence = self.sentence()
        term = self.term()
        self._scan('"\\\\)"')

    def sentence(self):
        _token_ = self._peek('constant', '"\\\\(\\s*="', '"\\\\(\\s*/="', '"\\\\(\\s*holds"', '"\\\\("', '"\\\\(\\s*not"', '"\\\\(\\s*and"', '"\\\\(\\s*or"', '"\\\\(\\s*=>"', '"\\\\(\\s*<="', '"\\\\(\\s*<=>"', '"\\\\(\\s*forall"', '"\\\\(\\s*exists"')
        if _token_ == 'constant':
            constant = self._scan('constant')
        elif _token_ == '"\\\\(\\s*="':
            equation = self.equation()
        elif _token_ == '"\\\\(\\s*/="':
            inequality = self.inequality()
        elif _token_ in ['"\\\\(\\s*holds"', '"\\\\("']:
            relsent = self.relsent()
        elif _token_ not in ['"\\\\(\\s*forall"', '"\\\\(\\s*exists"']:
            logsent = self.logsent()
        else: # in ['"\\\\(\\s*forall"', '"\\\\(\\s*exists"']
            quantsent = self.quantsent()

    def equation(self):
        self._scan('"\\\\(\\s*="')
        term = self.term()
        term = self.term()
        self._scan('"\\\\)"')

    def inequality(self):
        self._scan('"\\\\(\\s*/="')
        term = self.term()
        term = self.term()
        self._scan('"\\\\)"')

    def relsent(self):
        _token_ = self._peek('"\\\\(\\s*holds"', '"\\\\("')
        if _token_ == '"\\\\(\\s*holds"':
            self._scan('"\\\\(\\s*holds"')
            term = self.term()
            while self._peek() in ['indvar', 'constant', 'charref', 'string', 'block', '"\\\\(\\s*quote"', '"\'"', '"\\\\(\\s*value"', '"\\\\("', '"\\\\(\\s*listof"', '"\\\\(\\s*if"', '"\\\\(\\s*cond"']:
                term = self.term()
            if self._peek('seqvar', '"\\\\)"') == 'seqvar':
                seqvar = self._scan('seqvar')
            self._scan('"\\\\)"')
        else: # == '"\\\\("'
            self._scan('"\\\\("')
            constant = self._scan('constant')
            while self._peek() in ['indvar', 'constant', 'charref', 'string', 'block', '"\\\\(\\s*quote"', '"\'"', '"\\\\(\\s*value"', '"\\\\("', '"\\\\(\\s*listof"', '"\\\\(\\s*if"', '"\\\\(\\s*cond"']:
                term = self.term()
            if self._peek('seqvar', '"\\\\)"') == 'seqvar':
                seqvar = self._scan('seqvar')
            self._scan('"\\\\)"')

    def logsent(self):
        _token_ = self._peek('"\\\\(\\s*not"', '"\\\\(\\s*and"', '"\\\\(\\s*or"', '"\\\\(\\s*=>"', '"\\\\(\\s*<="', '"\\\\(\\s*<=>"')
        if _token_ == '"\\\\(\\s*not"':
            self._scan('"\\\\(\\s*not"')
            sentence = self.sentence()
            self._scan('"\\\\)"')
        elif _token_ == '"\\\\(\\s*and"':
            self._scan('"\\\\(\\s*and"')
            while self._peek('constant', '"\\\\)"', 'indvar', 'charref', 'string', 'block', '"\\\\(\\s*="', '"\\\\(\\s*/="', '"\\\\(\\s*holds"', '"\\\\("', '"\\\\(\\s*not"', '"\\\\(\\s*and"', '"\\\\(\\s*or"', '"\\\\(\\s*=>"', '"\\\\(\\s*<="', '"\\\\(\\s*<=>"', '"\\\\(\\s*forall"', '"\\\\(\\s*exists"', '"\\\\(\\s*quote"', '"\'"', '"\\\\(\\s*value"', '"\\\\(\\s*listof"', '"\\\\(\\s*if"', '"\\\\(\\s*cond"') not in ['"\\\\)"', 'indvar', 'charref', 'string', 'block', '"\\\\(\\s*quote"', '"\'"', '"\\\\(\\s*value"', '"\\\\(\\s*listof"', '"\\\\(\\s*if"', '"\\\\(\\s*cond"']:
                sentence = self.sentence()
            self._scan('"\\\\)"')
        elif _token_ == '"\\\\(\\s*or"':
            self._scan('"\\\\(\\s*or"')
            while self._peek('constant', '"\\\\)"', 'indvar', 'charref', 'string', 'block', '"\\\\(\\s*="', '"\\\\(\\s*/="', '"\\\\(\\s*holds"', '"\\\\("', '"\\\\(\\s*not"', '"\\\\(\\s*and"', '"\\\\(\\s*or"', '"\\\\(\\s*=>"', '"\\\\(\\s*<="', '"\\\\(\\s*<=>"', '"\\\\(\\s*forall"', '"\\\\(\\s*exists"', '"\\\\(\\s*quote"', '"\'"', '"\\\\(\\s*value"', '"\\\\(\\s*listof"', '"\\\\(\\s*if"', '"\\\\(\\s*cond"') not in ['"\\\\)"', 'indvar', 'charref', 'string', 'block', '"\\\\(\\s*quote"', '"\'"', '"\\\\(\\s*value"', '"\\\\(\\s*listof"', '"\\\\(\\s*if"', '"\\\\(\\s*cond"']:
                sentence = self.sentence()
            self._scan('"\\\\)"')
        elif _token_ == '"\\\\(\\s*=>"':
            self._scan('"\\\\(\\s*=>"')
            while self._peek('constant', 'indvar', 'charref', 'string', 'block', '"\\\\)"', '"\\\\(\\s*="', '"\\\\(\\s*/="', '"\\\\(\\s*holds"', '"\\\\("', '"\\\\(\\s*not"', '"\\\\(\\s*and"', '"\\\\(\\s*or"', '"\\\\(\\s*=>"', '"\\\\(\\s*<="', '"\\\\(\\s*<=>"', '"\\\\(\\s*forall"', '"\\\\(\\s*exists"', '"\\\\(\\s*quote"', '"\'"', '"\\\\(\\s*value"', '"\\\\(\\s*listof"', '"\\\\(\\s*if"', '"\\\\(\\s*cond"') not in ['indvar', 'charref', 'string', 'block', '"\\\\)"', '"\\\\(\\s*quote"', '"\'"', '"\\\\(\\s*value"', '"\\\\(\\s*listof"', '"\\\\(\\s*if"', '"\\\\(\\s*cond"']:
                sentence = self.sentence()
            sentence = self.sentence()
            self._scan('"\\\\)"')
        elif _token_ == '"\\\\(\\s*<="':
            self._scan('"\\\\(\\s*<="')
            sentence = self.sentence()
            while self._peek('constant', '"\\\\)"', 'indvar', 'charref', 'string', 'block', '"\\\\(\\s*="', '"\\\\(\\s*/="', '"\\\\(\\s*holds"', '"\\\\("', '"\\\\(\\s*not"', '"\\\\(\\s*and"', '"\\\\(\\s*or"', '"\\\\(\\s*=>"', '"\\\\(\\s*<="', '"\\\\(\\s*<=>"', '"\\\\(\\s*forall"', '"\\\\(\\s*exists"', '"\\\\(\\s*quote"', '"\'"', '"\\\\(\\s*value"', '"\\\\(\\s*listof"', '"\\\\(\\s*if"', '"\\\\(\\s*cond"') not in ['"\\\\)"', 'indvar', 'charref', 'string', 'block', '"\\\\(\\s*quote"', '"\'"', '"\\\\(\\s*value"', '"\\\\(\\s*listof"', '"\\\\(\\s*if"', '"\\\\(\\s*cond"']:
                sentence = self.sentence()
            self._scan('"\\\\)"')
        else: # == '"\\\\(\\s*<=>"'
            self._scan('"\\\\(\\s*<=>"')
            sentence = self.sentence()
            sentence = self.sentence()
            self._scan('"\\\\)"')

    def quantsent(self):
        _token_ = self._peek('"\\\\(\\s*forall"', '"\\\\(\\s*exists"')
        if _token_ == '"\\\\(\\s*forall"':
            self._scan('"\\\\(\\s*forall"')
            self._scan('"\\\\("')
            while 1:
                varspec = self.varspec()
                if self._peek('indvar', 'seqvar', '"\\\\("', '"\\\\)"', 'constant') not in ['indvar', 'seqvar', '"\\\\("']: break
            self._scan('"\\\\)"')
            sentence = self.sentence()
            self._scan('"\\\\)"')
        else: # == '"\\\\(\\s*exists"'
            self._scan('"\\\\(\\s*exists"')
            self._scan('"\\\\("')
            while 1:
                varspec = self.varspec()
                if self._peek('indvar', 'seqvar', '"\\\\("', '"\\\\)"', 'constant') not in ['indvar', 'seqvar', '"\\\\("']: break
            self._scan('"\\\\)"')
            sentence = self.sentence()
            self._scan('"\\\\)"')

    def varspec(self):
        _token_ = self._peek('indvar', 'seqvar', '"\\\\("')
        if _token_ != '"\\\\("':
            variable = self.variable()
        else: # == '"\\\\("'
            self._scan('"\\\\("')
            variable = self.variable()
            constant = self._scan('constant')
            self._scan('"\\\\)"')

    def form(self):
        sentence = self.sentence()


def parse(rule, text):
    P = KIFParser(KIFParserScanner(text))
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
