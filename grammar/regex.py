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


def group_literal(f, subj, obj):
    substring = processProduction(f, obj)
    return u'[%s]' % substring

def complement(f, subj, obj):
    substring = processProduction(f, obj)

def main():
    import sys
    inputFile = sys.argv[1]
    


if __name__ == '__main__':
    main()
