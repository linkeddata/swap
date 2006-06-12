"""regex.py

$ID:   $

Convert an n3 file of the regex ontology to a python regex

"""

from swap import myStore
regex = myStore.symbol('http://www.w3.org/2000/10/swap/grammar/regex')

knownProps = {regex['group_literal']: group_literal,
              regex['modifies']: modifies,
              regex['complement']: complement,
              regex['sequence']: sequence,
              regex['or']: disjunction,
              regex['lookAhead']: lookAhead,
              regex['negativeLookAhead']: negativeLookAhead,
              regex['lookBehind']: lookBehind,
              regex['negativeLookBehind']: negativeLookBehind}

knownClasses = {regex['Dot']: u'.',
                regex['Start']: u'^',
                regex['End']: u'$'}

def processProduction(f, prod):
    if isinstance(prod, Literal):
        return unicode(prod), regex['Regex']
    for prop in knownProps:
        l = f.the(subj=prod, pred=prop)
        if l:
            return knownProps[prop](f, prod, l)
    return knownClasses[prod], regex['CharClass']

def modifies(f, subj, obj):
    substring, cs = processProduction(f, obj)
    modification = f.the(subj=subj, pred=regex['modification'])
    if not modification:
        raise ValueError
    if modification in knownModifications:
        return knownModifications[modification](f, substring)
    elif f.contains(subj=modification, pred=rdf['type'], obj=rejex['GreedyMatchCounter']):
        pass
    elif f.contains(subj=modification, pred=rdf['type'], obj=rejex['NonGreedyMatchCounter']):
        pass
    


def group_literal(f, subj, obj):
    substring, cs = processProduction(f, obj)
    return (u'[%s]' % substring), regex['CharClass']

def complement(f, subj, obj):
    substring, cs = processProduction(f, obj)
    if cs if not regex['CharClass']:
        raise ValueError
    return (u'[^%s]' % substring[1:-1]), regex['CharClass']

def disjunction(f, subj, obj):
    values = [processProduction(f, x)[0] for x in obj]
    return '(?:' + '|'.join(values) + ')'


def main():
    import sys
    inputFile = sys.argv[1]
    


if __name__ == '__main__':
    main()
