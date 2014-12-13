"""regex.py

$ID:   $

Convert an n3 file of the regex ontology to a python regex

"""

from swap import myStore, term
regex = myStore.symbol('http://www.w3.org/2000/10/swap/grammar/regex')
from swap.RDFSink import RDF_NS_URI
rdf = myStore.symbol(RDF_NS_URI[:-1])

knownClasses = {regex['Dot']: u'.',
                regex['Start']: u'^',
                regex['End']: u'$'}

alreadyDone = {}

def processProduction(f, prod):
    if prod in alreadyDone:
        pass
    elif isinstance(prod, term.Literal):
        alreadyDone[prod] = escape(unicode(prod)), regex['Sequence']
    #print [x.asFormula().n3String() for x in f.statementsMatching(subj=prod)]
    else:
        for prop in knownProps:
            l = f.the(subj=prod, pred=prop)
            #print l
            if l:
                alreadyDone[prod] = knownProps[prop](f, prod, l)
                break
        else:
            try:
                alreadyDone[prod] = knownClasses[prod], regex['CharClass']
            except:
                print [x.asFormula().n3String() for x in f.statementsMatching(subj=prod)]
                raise
    return alreadyDone[prod]

knownModifications = {regex['Star'] : u'*',
                      regex['NonGreedyStar'] : u'*?',
                      regex['Plus'] : u'+',
                      regex['Optional'] : u'?',
                      regex['NonGreedyPlus'] : u'+?',
                      regex['NonGreedyOptional'] : u'??'}


def simpleModification(f, k, s):
    if s[-1:] in ')]':
        return s + k
    else:
        return u'(?:%s)%s' % (s, k)


def modifies(f, subj, obj):
    substring, cs = processProduction(f, obj)
    modification = f.the(subj=subj, pred=regex['modification'])
    if not modification:
        raise ValueError
    
    if modification in knownModifications:
        k = knownModifications[modification]
        return simpleModification(f, k, substring), regex['Modification']
    elif f.contains(subj=modification, pred=rdf['type'], obj=regex['GreedyMatchCounter']):
        pass
    elif f.contains(subj=modification, pred=rdf['type'], obj=regex['NonGreedyMatchCounter']):
        pass
    


def group_literal(f, subj, obj):
    substring, cs = processProduction(f, obj)
    return (u'[%s]' % substring), regex['ExplicitCharClass']

def complement(f, subj, obj):
    substring, cs = processProduction(f, obj)
    if cs is not regex['ExplicitCharClass']:
        raise ValueError
    return (u'[^%s]' % substring[1:-1]), regex['CharClass']

def disjunction(f, subj, obj):
    k = [(x, processProduction(f, x)) for x in obj]
    for c,d in k:
        if len(d) != 2:
            raise RuntimeError ((c,d))
    valuesAndTypes = [processProduction(f, x) for x in obj]
    def processSingleChar(x,y):
        if es_len(x) == 1 and y is not regex['CharClass']:
            return u'[' + x + u']'
        return x
    bigClass = []
    notClasses = []
    for x,y in valuesAndTypes:
        if y is regex['ExplicitCharClass'] or (es_len(x) == 1 and y is not regex['CharClass']):
            bigClass.append((x,y))
        else:
            notClasses.append(group((x,y), regex['Sequence']))

    bigClassString = u'[' + u''.join([processSingleChar(x,y)[1:-1] for x,y in bigClass]) + u']', regex['ExplicitCharClass']
    if not notClasses:
        return bigClassString
    if len(bigClass) == 1:
        notClasses.append(group(bigClass[0], regex['Bob']))
    elif bigClass:
        notClasses.append(group(bigClassString, regex['Sequence']))

    return u'(?:' + '|'.join(notClasses) + ')', regex['Disjunction']

def sequence(f, subj, obj):
    k = [(x, processProduction(f, x)) for x in obj]
    for c,d in k:
        if len(d) != 2:
            raise RuntimeError ((c,d))
    values = [group(processProduction(f, x), regex['Disjunction']) for x in obj]
    return u''.join(values), regex['Sequence']


def group((val, t), condition):
    if t is condition:
        return u'(?:%s)' % val
    return val

def lookAhead(f, subj, obj):
    substring, cs = processProduction(f, obj)
    return u'(?=%s)' % substring, regex['Regex']


def negativeLookAhead(f, subj, obj):
    substring, cs = processProduction(f, obj)
    return u'(?!%s)' % substring, regex['Regex']

def lookBehind(f, subj, obj):
    substring, cs = processProduction(f, obj)
    return u'(?<=%s)' % substring, regex['Regex']


def negativeLookBehind(f, subj, obj):
    substring, cs = processProduction(f, obj)
    return u'(?<!%s)' % substring, regex['Regex']


knownProps = {regex['group_literal']: group_literal,
              regex['modifies']: modifies,
              regex['complement']: complement,
              regex['sequence']: sequence,
              regex['or']: disjunction,
              regex['lookAhead']: lookAhead,
              regex['negativeLookAhead']: negativeLookAhead,
              regex['lookBehind']: lookBehind,
              regex['negativeLookBehind']: negativeLookBehind}

def makeRegex(f, base):
    s, _ = processProduction(f, base)
    for cls in f.each(subj=base, pred=rdf['type']):
        if cls is regex['CaseInsensitiveRegex']:
            return u'(?i)'+s
    return s

def escape(s):
    if s in '-<>':
        return u'\\' + s
    return s.replace('\\','\\\\').replace('.','\\.').replace('?','\\?').replace('+','\\+').replace("[", "\\[").replace("]", "\\]").replace("(", "\\(").replace(")", "\\)")

def es_len(s):
    if len(s) == 2 and s[0] == '\\' and s[1] in '\\abfnrtvxAbBdDsSwW.?+':
        return 1
    return len(s)

def main():
    import sys
    inputFile = sys.argv[1]
    baseRegex = sys.argv[2]
    f = myStore.load(inputFile)
    base = myStore.symbol(baseRegex)
    g = u'(?P<foo>%s)' % makeRegex(f, base)
    print `g`
    import re
    c = re.compile(g)
    print c.match('3.4E-4').groups()
    #print alreadyDone


if __name__ == '__main__':
    main()
