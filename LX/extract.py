from sys import stderr

import LX.kb
import LX.rdf
import types
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

def findTypes(kb, typeMap=None):
    """Return a map from terms to a hash whose keys are their RDF
    types (also terms).

    Uses ns.rdf.type, assumes the object of those are themselves
    instances of ns.rdfs.Class, and assumes anything in the predicate
    position is an ns.rdf.Property.

    Will add to an existing map, if given it.
    """

    if typeMap is None:
        typeMap= {}

    for f in kb:
        if f.predicate == ns.rdf.type:
            typeMap.setdefault(f.object, {})[ns.rdfs.Class] = 1
            typeMap.setdefault(f.subject, {})[f.object] = 1
        typeMap.setdefault(f.predicate, {})[ns.rdf.Property] = 1

    return typeMap

def useSubClassOf(typemap, ontkb):
    """Expand a typemap based on all the rdfs:subClassOf arcs in a
    given ontology/schema kb."""
    raise NotImplemented
    

def gather(classes, ctorMap, depth=4):
    """Dive into module or list of modules or classes to find classes
    with an rdfType attribute; return mapping from rdfTypes to the
    associated classes (as dict keys)
    """
    if depth<=0: return
    if not hasattr(classes, "__iter__"): classes=(classes,)
    for x in classes:
        if type(x) is types.ModuleType:
            gather(x.__dict__.values(), ctorMap, depth=depth-1)
        elif type(x) is types.ClassType:
            try:
                uri = x.rdfType
            except AttributeError, error:
                continue
            print "U", uri, x
            ctorMap.setdefault(uri, []).append(x)
     
def extract(kb, classes,
            constructorArgs=(), constructorKWArgs={},
            typemap=None):
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

    if typemap is None:
        typemap = findTypes(kb)

    ctorMap = { }
    gather(classes, ctorMap)



    for (term, classHash) in typemap.iteritems():
        myConstructor = None
        ... for all term's types, gather up their constructors ...
        
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
