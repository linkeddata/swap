"""


"""

import re, traceback, string as string_stuff
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
        return '(%s): %s' % (repr(self.repeat), repr(self.things))

    def __str__(self):
        if len(self.ors) == 1 and len(self.ors[0]) == 1 and self.repeat != ONCE:
            many = False
        else:
            many = True
        
        level = len(traceback.extract_stack())
        retVal = ""
        if self.repeat == ONCE:
            retVal += ""
        elif self.repeat == STAR:
            retVal += '\n' + "  "*level + " cfg:zeroOrMore "
        elif self.repeat == PLUS:
            retVal += '\n' + "  "*level + " cfg:zeroOrMore "
        elif self.repeat == OPTIONAL:
            retVal += '\n' + "  "*level + " cfg:mustBeOneSequence ( () ( "
            level = level + 6
        else:
            raise RuntimeError('how did I get here? %s' & repr(self.repeat))

        if many and self.repeat != ONCE:
            retVal += '\n   ' + "  "*level + '['
        if many:
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
        else:
            val = self.ors[0][0]
            if isinstance(val, self.__class__):
                retVal += '[ %s ]' % str(val)
            else:
                retVal += ' %s ' % val

        if many and self.repeat != ONCE:
            retVal += ']'
            
        if self.repeat == ONCE:
            retVal += ""
        elif self.repeat == STAR:
            retVal += ""
        elif self.repeat == PLUS:
            retVal += ""
        elif self.repeat == OPTIONAL:
            retVal += " ) )"

        return retVal

web = False

def makeGrammar():
    import urllib.request, urllib.parse, urllib.error
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
    if web:
        File = urllib.request.urlopen('http://www.w3.org/2005/01/yacker/uploads/sparqlTest/bnf')
        this = ""
        ws = re.compile(r'\S')
        for string in File:
            if ws.search(string) and string[0] != '#':
                this += string
        #this = File.read()#.replace('\n', ' ')
        that = None
        while that != this:
            that = this
            this = this.replace('  ', ' ')
        i = this.find('@terminals')
        first_half = this[:i]
        #i2 = this.find('\n', i+2)
        #second_half = this[i2:]
        whole = first_half # + second_half
        next_rule = re.compile(r';\s')
        rules = next_rule.split(whole)
        rules = rules[:-1]
    else:
        File = file('/home/syosi/CVS-local/perl/modules/W3C/Grammar/bin/bnf.out')
        this = ""
        ws = re.compile(r'\S')
        for string in File:
            if ws.search(string) and string[0] != '#':
                this += string
        #this = File.read()#.replace('\n', ' ')
        that = None
        while that != this:
            that = this
            this = this.replace('  ', ' ')
        i = this.find('%%')
        i2 = this.find('%%', i+5)
        whole = this[i:i2]
        next_rule = re.compile(r'\n(?=\w)')
        rules = next_rule.split(whole)
        rules = rules[1:]
    rules[0] = rules[0] + ' cfg:eof'
    rules = [a.replace('\t', '').replace('\r', '').replace('\n', ' ').replace('  ', ' ') for a in rules]
    rules = [a for a in rules if a]
##    print "[" + ",\n".join(rules) + "]"
    rules = [tuple([b.strip() for b in a.split(': ')]) for a in rules]
##    print "[" + ",\n".join(["(" + `a` + ")" for a in rules]) + "]"
##    return
    rules = [(a[0], makeList(a[1].split(' '), a[0])) for a in rules]
    retVal += '. \n\n'.join([b[0] + ' ' + str(b[1]) for b in rules])
    print("[" + ",\n".join(["(" + repr(a) + ")" for a in rules]) + "]")
    retVal += '. \n\n\n'
    #
    # Here comes the hard part. I gave up
    #

    #regexp_rules = ['%s cfg:matches %s; \n       cfg:canStartWith "a" .' % a for a in regexps.iteritems()]
    #retVal += '\n\n'.join(regexp_rules)
    retVal += """#____________________________________________________

#  Axioms reducing the shortcut CFG terms to cfg:musBeOneSequence.

{ ?x cfg:zeroOrMore ?y } => {?x cfg:mustBeOneSequence ( () (?y ?x) ) }.

"""
    return retVal

def makeList(matchString, ww):
    patterns = [PatternList()]
    for string in matchString:
#        if ww == 'LANGTAG':
#            print string
        if string == '': pass
        elif string == '|':
            patterns[-1].newOr()
        else:
            if string[0:1] == '(':
                newPattern = PatternList()
                patterns[-1].things.append(newPattern)
                patterns.append(newPattern)
                string = string[1:]
            elif string[0:1] not in '"\'' + string_stuff.ascii_letters: #regexp
                pass
                #extras[name] = '"' + quote(string) + '"'

            k = string.rfind(')')
            r = None
            if k >= 0 and string[k-1:k+2] != "')'":
                string = string[:k]
                r = string[k:]
            if False: #string[0:1] and string[0:1] not in '"\')' + string_stuff.ascii_letters: #regexp
                name = newToken()
                patterns[-1].things.append(name)
                extras[name] = '"' + quote(string.replace('#x','\\u')) + '"'
            elif string:
                string = string.replace("'", '"')
                if string[:1] == '"' and string[-1:] == '"':
                    string = '"' + quote(string[1:-1]) + '"'
                if string[0:2] == '#x':
                    string = '"\\u%s"' % string[2:]
                if string[-1:] in '+?*':
                    if not string[:-1]: string = patterns[-1].things.pop() + string[-1:]
                    newPattern = PatternList()
                    newPattern.things.append(string[:-1])
                    newPattern.repeat = times[string[-1:]]
                    if newPattern.repeat == PLUS:
                        patterns[-1].things.append(string[:-1])
                    patterns[-1].things.append(newPattern)
                else:
                    if not string: raise RutimeError
                    patterns[-1].things.append(string)
            if r is not None:
                #print 'I\'m here'
                patterns[-1].repeat = times[r[1:]]
                patterns.pop()
    if len(patterns) == 1:
        return patterns[0]
    print(patterns[1])
    return None

class l(object): pass

def counter():
    m = l()
    m.n = 0
    def f():
        m.n += 1
        return 'token%s' %m.n
    return f

newToken = counter()

r_unilower = re.compile(r'(?<=\\u)([0-9a-f]{4})|(?<=\\U)([0-9a-f]{8})')
r_hibyte = re.compile(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F-\xFF]')
def quote(s): 
   if not isinstance(s, str): 
      s = str(s, 'utf-8') # @@ not required?
   if not ('\\'.encode('unicode-escape') == '\\\\'): 
      s = s.replace('\\', r'\\')
   s = s.replace('"', r'\"')
   # s = s.replace(r'\\"', r'\"')
   s = r_hibyte.sub(lambda m: '\\u00%02X' % ord(m.group(0)), s)
   s = s.encode('unicode-escape')
   s = r_unilower.sub(lambda m: (m.group(1) or m.group(2)).upper(), s)
   return str(s)



def writeGrammar():
    b = file('sparql.n3', 'w')
    b.write(makeGrammar())
    b.close()

if __name__ == '__main__':
    print('Overwriting sparql.n3')
    writeGrammar()
