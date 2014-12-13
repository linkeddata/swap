"""How to defeat a hosting service

There should be a rat race between programs like this and
spam-detection techniques for the hosting service.
"""

try:
    from swap import llyn
except ImportError:
    import sys
    sys.path.append('/home/syosi/CVS-local/WWW/2000/10')
    from swap import llyn

from random import choice, randint
from swap import toXML
wordList = [a.replace("'s", "") for a in file('/usr/share/dict/words', 'r')]
sink = llyn.RDFStore()

def randTerm(namespaces, fragments, inList = 0):
    if choice([1, 1, 0]):
        return randSymbol(namespaces, fragments)
    if choice([1,0, 0]) and not inList:
        return sink.nil.newList([randTerm(namespaces, fragments, 1) for a in range(randint(1,25))])
    return randLiteral(namespaces, fragments)

def randNonLiteral(namespaces, fragments, inList = 0):
    if choice([1, 1, 1, 0]):
        return randSymbol(namespaces, fragments)
    return sink.nil.newList([randTerm(namespaces, fragments, 1) for a in range(randint(1,25))])

def randLiteral(namespaces, fragments):
    global wordList
    word = choice(wordList)[:-1]
    return sink.newLiteral(word)

def randSymbol(namespaces, fragments):
    ns = choice(namespaces)
    return ns[choice(fragments[ns])]

def randURI():
    global wordList
    domain = [choice(wordList)[:-1]]
    fileName = []
    while choice([1, 1, 1, 0]):
        domain.append(choice(wordList)[:-1])
    domain.append(choice(['com', 'org', 'net', 'edu', 'co.uk', 'tv']))
    domain.append('example')
    while choice([1, 1, 1, 1, 1, 1, 0]):
        fileName.append(choice(wordList)[:-1])
    return 'http://' + '.'.join(domain) + '/' + '/'.join(fileName)
    

def makeFragments(ns, fragments):
    global wordList
    fragments[ns] = [choice(wordList)[:-1]]
    while choice([1, 1, 1, 1, 1, 1,  1, 1, 1, 1, 1,  1, 1, 1, 1, 1, 0]):
        fragments[ns].append(choice(wordList)[:-1])

def main():
    formula = sink.newFormula()
    namespaces = []
    fragments = {}
    classes = {}
    properties = {}
    
    owl = sink.newSymbol('http://www.w3.org/2002/07/owl')
    fragments[owl] = ['Class', 'Thing', 'Nothing', 'equivalentClass', 'disjointWith', 'equivalentProperty', \
                      'sameAs', 'differentFrom', 'AllDifferent', 'distinctMembers', 'unionOf', 'intersectionOf', \
                      'complementOf', 'oneOf', 'Restriction', 'onProperty', 'allValuesFrom', 'hasValue', \
                      'someValuesFrom', 'minCardinality', 'maxCardinality', 'cardinality', 'ObjectProperty', \
                      'DatatypeProperty', 'inverseOf', 'TransitiveProperty', 'SymmetricProperty', \
                      'FunctionalProperty', 'InverseFunctionalProperty', 'AnnotationProperty', 'Ontology', \
                      'OntologyProperty', 'imports', 'versionInfo', 'priorVersion', 'backwardCompatibleWith', \
                      'incompatibleWith', 'DeprecatedClass', 'DeprecatedProperty', 'DataRange']
    properties[owl] = ['equivalentClass', 'disjointWith', 'equivalentProperty', \
                      'sameAs', 'differentFrom', 'AllDifferent', 'distinctMembers', 'unionOf', 'intersectionOf', \
                      'complementOf', 'oneOf', 'Restriction', 'onProperty', 'allValuesFrom', 'hasValue', \
                      'someValuesFrom', 'minCardinality', 'maxCardinality', 'cardinality', 'inverseOf' 'imports', 'versionInfo', 'priorVersion', 'backwardCompatibleWith', \
                      'incompatibleWith']
    classes[owl] = ['Class', 'Thing', 'Nothing', 'ObjectProperty', \
                      'DatatypeProperty', 'TransitiveProperty', 'SymmetricProperty', \
                      'FunctionalProperty', 'InverseFunctionalProperty', 'AnnotationProperty', 'Ontology', \
                      'OntologyProperty', 'DeprecatedClass', 'DeprecatedProperty', 'DataRange']
    rdfs = sink.newSymbol('http://www.w3.org/2000/01/rdf-schema')
    fragments[rdfs] = []
    properties[rdfs] = ['Resource', 'subClassOf', 'subPropertyOf', 'comment', 'label', \
                       'range', 'seeAlso', 'isDefinedBy', 'member']
    classes[rdfs] = ['Class', 'Literal', 'Container', 'ContainerMembershipProperty', 'Datatype']
    rdf = sink.newSymbol('http://www.w3.org/1999/02/22-rdf-syntax-ns')
    fragments[rdf] = ['RDF']
    properties[rdf] = ['first', 'next']
    classes[rdf] = ['List', 'Property']
    class_on_class = [owl[a] for a in ['equivalentClass', 'disjointWith', 'sameAs', 'differentFrom', 'AllDifferent', 'distinctMembers', \
                      'complementOf', 'Restriction']]
    class_on_class.extend([rdfs[a] for a in ['Class', 'subClassOf']])
    namespaces = [rdf, owl, rdfs]
    my_namespaces = []

    
    while choice([1, 1, 1, 1, 1, 0]):
        a = sink.newSymbol(randURI())
        makeFragments(a, fragments)
        makeFragments(a, classes)
        makeFragments(a, properties)
        namespaces.append(a)
        my_namespaces.append(a)
        for b in fragments[a]:
            formula.add(a[b], rdf['type'], randSymbol(namespaces, classes))
        for b in classes[a]:
            formula.add(a[b], rdf['type'], choice([rdfs['Class'], owl['Class']]))
        for b in classes[a]:
            formula.add(a[b], rdfs['comment'], randLiteral(namespaces, fragments))

    for ns in my_namespaces:
        for frag in classes[ns]:
            while choice([1, 1, 1, 0]):
                formula.add(ns[frag], choice(class_on_class), randSymbol(my_namespaces, classes))
    
    #print fragments
    while randint(0,100) != 45:
        pred = randSymbol(namespaces, properties)
        subj = randNonLiteral(my_namespaces, fragments)
        obj = randTerm(my_namespaces, fragments)
        #print subj, obj, pred
        formula.add(subj, pred, obj)

    _outSink = toXML.ToRDF(sys.stdout)
    formula = formula.close()
    sink.dumpNested(formula, _outSink)
    
if __name__ == '__main__':
    main()
