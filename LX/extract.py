from sys import stderr

import LX.kb
import LX.rdf
from LX.namespace import ns

class Extracted:
    """You can use this as a default or base target in the classMap

    """
    def __init__(self, term):
        self.fromTerm = term
        self.oneValue = { }
        self.allValues = { }
    def set(self, property, value):
        self.oneValue[property]=value
        self.allValues.setdefault(property, []).append(value)

class TooManyConstructors(RuntimeError):

    def __init__(self, term, classes):
        self.term = term
        self.classes = classes

    def __str__(self):
        return ("Term "+str(term)+" has too classes mapping to >1 constructor")
        #   ", ".join(map(str, classes))+
    
def extract(kb, classMap, classesOf=None, constructorArgs=(), constructorKWArgs={}):
    """Create Python instances for RDF instances of certain rdf types.

    classMap is a hash from rdf types (terms) to python classes
    (callables).  If an rdf instance has types which cause it to end
    up with two different callables, TooManyConstructors will be
    called.  (Or we could ignore that fact, and just return pointer to
    one of them).

    The constructor will be called with the term, then constructorArgs.

    Returns a mapping from terms to the created instances.

    TODO: better subclass logic, I think...
    """

    extracted = {}
    if classesOf is None:
        classesOf= {}

    for f in kb:
        if f.predicate == ns.rdf.type:
            classesOf.setdefault(f.object, {})[ns.rdfs.Class] = 1
            classesOf.setdefault(f.subject, {})[f.object] = 1
        classesOf.setdefault(f.predicate, {})[ns.rdf.Property] = 1

    for (term, classHash) in classesOf.iteritems():
        myConstructor = None
        for (classTerm, constructor) in classMap.iteritems():
            if classHash.has_key(classTerm):
                if myConstructor is None:
                    myConstructor = constructor
                elif myConstructor == constructor:
                    pass
                else:
                    raise TooManyConstructors(term, classHash.keys())
        if myConstructor:
            extracted[term] = apply(myConstructor,
                                    (term,)+tuple(constructorArgs),
                                    constructorKWArgs)

    for f in kb:
        try:
            subj = extracted[f.subject]
        except KeyError:
            continue
        if hasattr(f.object, "data"):
            subj.set(f.predicate, f.object.data)
        else:
            try:
                obj = extracted[f.object]
            except KeyError:
                continue
            else:
                subj.set(f.predicate, obj)
            
    return extracted                
