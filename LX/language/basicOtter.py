#  Basic parser for Otter, just turning string into trees.   We'll need
#  to wrap this to make it be a suitable LX parser.
#  Copied from http://www.w3.org/2002/05/positive-triples/otterlang.parse.g
#  (which I wrote last year).    -- sandro
#
# $Id$
# see log at end of .g file
#
# REFERENCES
# Yapps: Yet Another Python Parser System
# http://theory.stanford.edu/~amitp/Yapps/
# Sat, 18 Aug 2001 16:54:32 GMT
# Last modified 13:21 Sun 26 Nov 2000 , Amit Patel 
#
import string


from string import *
import re
from yappsrt import *

class ParseFormulaScanner(Scanner):
    patterns = [
        ('%.*\\r?\\n', re.compile('%.*\\r?\\n')),
        ('DOT', re.compile('\\.\\s*')),
        ('\\s+', re.compile('\\s+')),
        ('OP10', re.compile('<->|->')),
        ('OP20', re.compile('\\|')),
        ('OP30', re.compile('&')),
        ('OP40', re.compile('-')),
        ('OP50', re.compile('=')),
        ('QUANT', re.compile('(all|exists) ')),
        ('SYMBOLOPEN', re.compile("(('[^']*')|([^(),. %\\n<>|&=-]+))\\(")),
        ('SYMBOL', re.compile("('[^']*')|([^(),. %\\n<>|&=-]+)")),
        ('OPEN', re.compile('\\(')),
        ('CLOSE', re.compile('\\)')),
        ('COMMA', re.compile(',\\s*')),
        ('SP', re.compile('\\s')),
        ('END', re.compile('$')),
    ]
    def __init__(self, str):
        Scanner.__init__(self,None,['%.*\\r?\\n', '\\s+'],str)

class ParseFormula(Parser):
    def inputDocument(self):
        res = []
        while self._peek('END', 'SP', 'SYMBOL', 'OPEN', 'OP40', 'CLOSE', 'COMMA', 'SYMBOLOPEN', 'QUANT') != 'END':
            assertion = self.assertion()
            res.append(assertion)
        END = self._scan('END')
        return res

    def assertion(self):
        sp = self.sp()
        term10 = self.term10()
        DOT = self._scan('DOT')
        return term10

    def formula(self):
        sp = self.sp()
        term10 = self.term10()
        sp = self.sp()
        return term10

    def term10(self):
        term20 = self.term20()
        _token_ = self._peek('OP10', 'DOT', 'SP', 'SYMBOL', 'CLOSE', 'OPEN', 'COMMA', 'OP40', 'SYMBOLOPEN', 'QUANT')
        if _token_ == 'OP10':
            OP10 = self._scan('OP10')
            term10 = self.term10()
            return [string.strip(OP10), term20, term10]
        else:
            return term20

    def term20(self):
        term30 = self.term30()
        _token_ = self._peek('OP20', 'OP10', 'DOT', 'SP', 'SYMBOL', 'CLOSE', 'OPEN', 'COMMA', 'OP40', 'SYMBOLOPEN', 'QUANT')
        if _token_ == 'OP20':
            OP20 = self._scan('OP20')
            term20 = self.term20()
            return [string.strip(OP20), term30, term20]
        else:
            return term30

    def term30(self):
        term40 = self.term40()
        _token_ = self._peek('OP30', 'OP20', 'OP10', 'DOT', 'SP', 'SYMBOL', 'CLOSE', 'OPEN', 'COMMA', 'OP40', 'SYMBOLOPEN', 'QUANT')
        if _token_ == 'OP30':
            OP30 = self._scan('OP30')
            term30 = self.term30()
            return [string.strip(OP30), term40, term30]
        else:
            return term40

    def term40(self):
        _token_ = self._peek('OP40', 'SYMBOL', 'OPEN', 'SYMBOLOPEN', 'QUANT')
        if _token_ == 'OP40':
            OP40 = self._scan('OP40')
            term40 = self.term40()
            return [string.strip(OP40), term40]
        else:# in ['SYMBOL', 'OPEN', 'SYMBOLOPEN', 'QUANT']
            term50 = self.term50()
            return term50

    def term50(self):
        term90 = self.term90()
        _token_ = self._peek('OP50', 'OP30', 'OP20', 'OP10', 'DOT', 'SP', 'SYMBOL', 'CLOSE', 'OPEN', 'COMMA', 'OP40', 'SYMBOLOPEN', 'QUANT')
        if _token_ == 'OP50':
            OP50 = self._scan('OP50')
            term50 = self.term50()
            return [string.strip(OP50), term90, term50]
        else:
            return term90

    def term90(self):
        _token_ = self._peek('SYMBOL', 'OPEN', 'SYMBOLOPEN', 'QUANT')
        if _token_ == 'SYMBOLOPEN':
            function = self.function()
            return function
        elif _token_ == 'SYMBOL':
            SYMBOL = self._scan('SYMBOL')
            return string.strip(SYMBOL)
        elif _token_ == 'QUANT':
            quant = self.quant()
            return quant
        else:# == 'OPEN'
            OPEN = self._scan('OPEN')
            formula = self.formula()
            CLOSE = self._scan('CLOSE')
            return formula

    def function(self):
        SYMBOLOPEN = self._scan('SYMBOLOPEN')
        result = string.strip(SYMBOLOPEN)[:-1]
        list = self.list()
        return([result] + list)

    def list(self):
        formula = self.formula()
        t = [formula]
        while self._peek('COMMA', 'CLOSE') == 'COMMA':
            COMMA = self._scan('COMMA')
            formula = self.formula()
            t.append(formula)
        CLOSE = self._scan('CLOSE')
        return t

    def quant(self):
        QUANT = self._scan('QUANT')
        sp = self.sp()
        type=string.strip(QUANT); vars = []
        while self._peek('SYMBOL', 'OPEN', 'CLOSE', 'OP40', 'COMMA', 'SYMBOLOPEN', 'QUANT') == 'SYMBOL':
            SYMBOL = self._scan('SYMBOL')
            vars.append(string.strip(SYMBOL))
            sp = self.sp()
        OPEN = self._scan('OPEN')
        formula = self.formula()
        CLOSE = self._scan('CLOSE')
        return (["$Quantified", type]+vars+[formula])

    def sp(self):
        _token_ = self._peek('SP', 'SYMBOL', 'OPEN', 'CLOSE', 'OP40', 'COMMA', 'SYMBOLOPEN', 'QUANT')
        if _token_ == 'SP':
            SP = self._scan('SP')
        else:
            pass


def parse(rule, text):
    P = ParseFormula(ParseFormulaScanner(text))
    return wrap_error_reporter(P, rule)

if __name__ == '__main__':
    from sys import argv, stdin
    if len(argv) >= 2:
        if len(argv) >= 3:
            f = open(argv[2],'r')
        else:
            f = stdin
        print parse(argv[1], f.read())
    else: print 'Args:  <rule> [<filename>]'
