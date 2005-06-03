"""


"""

import re, traceback
from set_importer import Set, ImmutableSet

class ONCE(object): pass
class STAR(object): pass
class PLUS(object): pass
class OPTIONAL(object): pass

times = {'*' : STAR,
         '' : ONCE,
         '+': PLUS,
         '?': OPTIONAL }

class PatternList(object):
    def __init__(self):
        self.repeat = ONCE
        self.things = []
        self.ors = [self.things]
        self.pipe = False

    def newOr(self):
        self.things = []
        self.ors.append(self.things)
    def __repr__(self):
        return '(%s, %s): %s' % (`self.type`, `self.repeat`, `self.things`)

    def __str__(self):
        level = len(traceback.extract_stack())
        retVal = ""
        if self.repeat == ONCE:
            retVal += ""
        elif self.repeat == STAR:
            retVal += '\n' + "  "*level + " cfg:zeroOrMore ["
        elif self.repeat == PLUS:
            retVal += '\n' + "  "*level + " cfg:zeroOrMore ["
        elif self.repeat == OPTIONAL:
            retVal += '\n' + "  "*level + " cfg:mustBeOneSequence ( () ([ "
            level = level + 6
        else:
            raise RuntimeError('how did I get here? %s' & `self.repeat`)
        
        retVal += "cfg:mustBeOneSequence ( "
            
        for group in self.ors:
            retVal += '\n   '
            retVal += "  "*level
            retVal += '('
            for val in group:
                if isinstance(val, self.__class__):
                    retVal += '[ %s ]' % str(val)
                else:
                    retVal += ' %s ' % val            
            retVal += ' ) '
        retVal += '\n'
        retVal += "  "*level
        retVal += " ) "

        if self.repeat == ONCE:
            retVal += ""
        elif self.repeat == STAR:
            retVal += "]"
        elif self.repeat == PLUS:
            retVal += "]"
        elif self.repeat == OPTIONAL:
            retVal += "] ) )"

        return retVal


def makeGrammar():
    import urllib
    retVal = """#SPARQL in Notation3
# Context Free Grammar without tokenization
#
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
@prefix cfg: <http://www.w3.org/2000/10/swap/grammar/bnf#>.
@prefix rul: <http://www.w3.org/2000/10/swap/grammar/bnf-rules#>.
@prefix : <http://www.w3.org/2000/10/swap/grammar/sparql#>.
@prefix n3: <http://www.w3.org/2000/10/swap/grammar/n3#>.
@prefix list: <http://www.w3.org/2000/10/swap/list#>.
@prefix string: <http://www.w3.org/2000/10/swap/string#>.
@keywords a, is, of.

    """
    regexps = {'EXPONENT': '"([eE][+-]?[0-9]+)"',
           'STRING_LITERAL_LONG1': '"\\"\\"\\"([^\\"\\\\\\\\]|(\\\\\\\\[^\\\\n\\\\r])|(\\"[^\\"])|(\\"\\"[^\\"]))*\\"\\"\\""',
           'NCCHAR1': '"[A-Za-z\\u00c0-\\u00d6\\u00d8-\\u00f6\\u00f8-\\u02ff' +
               '\\u0370-\\u037d\\u037f-\\u1fff\\u200c-\\u200d\\u2070-\\u218f\\' +
               'u2c00-\\u2fef\\u3001-\\ud7ff\\uf900-\\uffff\\U00010000-\\U000effff]"',
           'DECIMAL': '"([0-9]+\\\\.[0-9]*)|(\\\\.[0-9]+)"',
           'FLOATING_POINT': '"([0-9]+\\\\.[0-9]*([eE][+-]?[0-9]+)?)|' +
               '(\\\\.([0-9])+([eE][+-]?[0-9]+)?)|(([0-9])+([eE][+-]?[0-9]+))"',
           'QuotedIRIref': '"<[^>]*>"',
           'STRING_LITERAL_LONG2': '"\'\'\'([^\'\\\\\\\\]|(\\\\\\\\[^\\\\n\\\\r])|(\'[^\'])|(\'\'[^\']))*\'\'\'"',
           'INTEGER': '"[0-9]+"',
            'LANGTAG': '"@[a-zA-Z]+(-[a-zA-Z0-9]+)*"',
           'STRING_LITERAL2': '"\\"(([^\\"\\\\\\\\\\\\n\\\\r])|(\\\\\\\\[^\\\\n\\\\r]))*\\""',
           'STRING_LITERAL1': '"\'(([^\'\\\\\\\\\\\\n\\\\r])|(\\\\\\\\[^\\\\n\\\\r]) )*\'"',
           'DIGITS' : '"[0-9]"'}

    canStartWith = {'EXPONENT': '"e", "E"',
           'STRING_LITERAL_LONG1': '\"\\"\\"\\"\"',
           'NCCHAR1': '"A"',
           'DECIMAL': '"0", "+", "-"',
           'FLOATING_POINT': '"0", "+", "-"',
           'QuotedIRIref': "\"<\"",
           'STRING_LITERAL_LONG2': "\"'''\"",
           'INTEGER': '"0", "+", "-"',
           'LANGTAG': '"@"',
           'STRING_LITERAL2': r'"\""',
           'STRING_LITERAL1': "\"'\"",
           'DIGITS' : '"0"'}
    
    File = urllib.urlopen('http://www.w3.org/2005/01/yacker/uploads/sparqlTest/bnf')

    this = File.read().replace('\n', ' ')
    that = None
    while that != this:
        that = this
        this = this.replace('  ', ' ')
    i = this.find('@terminals')
    first_half = this[:i]
    i2 = this.find('[', i+2)
    second_half = this[i2:]
    whole = first_half + second_half
    next_rule = re.compile(r'\[\d+\]')
    rules = next_rule.split(whole)
    rules = [a.replace('\t', '').replace('\r', '')
            for a in rules]
    rules = [tuple([b.strip() for b in a.split('::=')]) for a in rules]
    rules = rules[1:]
    rules = [(a[0], makeList(a[1].split(' '))) for a in rules if a[0] not in regexps]
    retVal += '. \n\n'.join([b[0] + ' ' + str(b[1]) for b in rules])

    retVal += '. \n\n\n'
    #
    # Here comes the hard part. I gave up
    #

    regexp_rules = ['%s cfg:matches %s; \n       cfg:canStartWith %s .' % (a, regexps[a], canStartWith[a]) for a in regexps]
    retVal += '\n\n'.join(regexp_rules)
    retVal += """#____________________________________________________

#  Axioms reducing the shortcut CFG terms to cfg:musBeOneSequence.

{ ?x cfg:zeroOrMore ?y } => {?x cfg:mustBeOneSequence ( () (?y ?x) ) }.

"""
    return retVal

def makeList(matchString):
    patterns = [PatternList()]
    for string in matchString:
        if string == '': pass
        elif string == '(':
            newPattern = PatternList()
            patterns[-1].things.append(newPattern)
            patterns.append(newPattern)
        elif string[0] == ')':
            patterns[-1].repeat = times[string[1:]]
            patterns.pop()
        elif string == '|':
            patterns[-1].newOr()           
        else:
            if string[0:2] == '#x':
                string = '"\\u%s"' % string[2:]
            if string == '[0-9]':
                string = 'DIGITS'
            string = string.replace("'", '"')
            if string[-1] in '+?*':
                newPattern = PatternList()
                newPattern.things.append(string[:-1])
                newPattern.repeat = times[string[-1]]
                if newPattern.repeat == PLUS:
                    patterns[-1].things.append(string[:-1])
                patterns[-1].things.append(newPattern)
            else:
                patterns[-1].things.append(string)
    if len(patterns) == 1:
        return patterns[0]
    return None

def counter():
    def f():
        global n
        n = n+1
        return 'token%s' % n
    n = 0
    return f

newToken = counter()


def writeGrammar():
    b = file('sparql.n3', 'w')
    b.write(makeGrammar())
    b.close()

if __name__ == '__main__':
    print 'Overwriting sparql.n3'
    writeGrammar()
