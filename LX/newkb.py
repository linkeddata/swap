"""Provides the KB class, the heart of Knowledge Management.
"""
__version__ = "$Revision$"
# $Id$

import re

import LX

class KB:
    """A Knowledge Base, a list of implicitely conjoined sentences
    (logical formulas).  Can also be seen as a mutable logical
    formula.

    This is an extension of an RDF triplestore ("model" in Jena),
    because entries are full logic formulas, not just triples.  That
    is, we have function terms, n-ary predicates, and the full suite
    of logical connectives including quantifiers.

    Conceptually, it's slightly more than a list of formulas, in that
    we also have some "kb-wide" quantified variables, so you can use
    open formulas more easily.   That is, the KB as a formula looks
    like this:
    
       exists e1 e2 e3 ... (
          all x1 x2 x3 ... (
             formula1 & formula2 & formula3 ...
          )
       )

    and you can add edit the eN and xN lists separately from editing
    the formula list.  The toPrenex() and toUnPrenex() functions can
    be used to move variables out to the KB scope or in to the formula
    scope.  (toCNF(), toINF(), and toHorn() do this more dramatically,
    rewriting all variables out of all the formulas, and rearranging
    the whole KB.)

    An example.   More examples in the various functions....

    *** TRIVIAL EXAMPLE, USING INFERENCE:

    Create a default KB:
    
    >>> from LX.newkb import KB
    >>> kb = KB()     # maybe we really want the otter one?  Or XSB?

    Load it with some data, using a parsed for the "Lbase" language:
    
    >>> from LX.language.lbase import Parser
    >>> parser = Parser(sink=kb)
    >>> parser.parse("all ?x color(?x, red) -> Red(?x).")
    >>> parser.parse("all ?x color(?x, green) -> Green(?x).")
    >>> parser.parse("color(car1, blue).")
    >>> parser.parse("color(car2, red).")
    >>> parser.parse("color(apple1, red).")
    >>> parser.parse("color(apple2, green).")
    >>> print kb

    Query for things which are "Red":
    
    >>> q = kb.query(parser.parseToFormula("Red(?x)"))
    >>> for result in q.results:
    ...    print result


    *** PART 1: ADD AND DIRECTLY MANIPULATE THE DATA
    
    PART 1.1: Get ourselves an empty KB, available on this platform,
    with the features we want.
    
    x>>> from LX.newkb import KB
    x>>> kb = KB()

    PART 1.2: Load some data, using a Parser

    x>>> import LX.language.lbase
    x>>> parser = LX.language.lbase.Parser(sink=kb)
    x>>> parser.parse("all ?x color(?x, red) -> Red(?x)")
    x>>> parser.parse("all ?x color(?x, green) -> Green(?x)")
    x>>> kb

    PART 1.3: Load some more data by hand, from Python

    x>>> x = kb.newUniversal(suggestedName="?x")
    x>>> speed = kb.newPredicate(suggestedName="speed")
    x>>> fast = kb.newConstant(suggestedName="fast")
    x>>> fastThing = kb.newPredicate(suggestedName="FastThing")
    x>>> formula = LX.logic.implies(speed(x, fast), fastThing(x))
    x>>> formula
    x
    x>>> kb.append(formula)
    x>>> myCar = kb.newConstant(suggestedName="sandro's car")
    x>>> kb.append(speed(myCar, fast))
    x>>> kb
    x

    PART 1.4: Try some Python values

    x>>> maxmph = kb.newPredicate("maxmph")
    x>>> kb.append(maxmph(myCar, 120))
    x>>> owner = kb.newFunction("owner")
    x>>> name = kb.newFunction("name")
    x>>> kb.append(name(owner(myCar)) == "Sandro")   # operator == is overloaded
    x>>> kb[4]

    *  access values
    *  delete some stuff
    *  property interface, for when in RDF-normal form; access via properties/functions

    PART 6: PROPERTY QUERIES -- Based off Expresions owner by KB

    x>>> sandro.getFunctionValue(name)
    'Sandro Hawke'
    x>>> sandro[name]
    'Sandro Hawke'
    x>>> name(sandro).value
    'Sandro Hawke'
    x>>> myCar.getValues(maxmph)
    [120]

    PART 8: PROPERTY UPDATES

    x>>> sandro[name] = "Sandro D. Hawke"
    x>>> kb

    *** PART 2: TURN ON INFERENCING, QUERY FOR RESULTS

    PART 5: URIs and Spider KBs

    x>>> sandro = kb.newConstant(uri="http://www.w3.org/People/Sandro/data#sandro")
    x>>> kb.append(owner(myCar) == sandro)

    *: features: follow-uris-in-names, follow-seeAlso, follow-isDefinedBy
    x>>> officetel = kb.newConstant(uri="http://www.w3.org/People/Sandro/data#officetel")
    x>>> kb2 = KB(features=("spider"), copyFrom=kb)
    x>>> websandro = kb2.intern(sandro)
    x>>> websandro.getValues(officetel)
    '+1 617 ALE RATT'

    >>> #kb = KB(features=("rdfs", "fol"))     # give ontology uris?  LX.ns.rdfs   rdf-only
    >>> #kb.engine
    'otter with rdfs axioms'

    PART 7: PATTERN QUERIES

    x>>> x = kb.Variable("?x")
    x>>> y = kb.Variable("?y")
    x>>> pat = fastThing(x) & (y == name(owner(x)))
    x>>> q = kb.query(pat)
    x>>> for res in q.results:
    ...    print res


    * retract?
    * link in with lbase terms
    * serialize
    * modify datatype encoding
    * math
    * spidering
    
    """

    defaultScope = {
        ("legal",): re.compile(r"^[a-zA-Z0-9_]+$"),
        ("hint",): re.compile(r"(?:\/|#)([a-zA-Z0-9_]*)/?$")
        }

    def stdValuesFilter(obj):
        if isinstance(obj, type("")): return 1
        if isinstance(obj, type(1)): return 1
        if isinstance(obj, type(0.1)): return 1
        # we'd like this to only be acceptable as a predicate/function...
        if obj == LX.ns.lx.uri: return 1
        return 0
    stdValuesFilter = staticmethod(stdValuesFilter)

    ################################################################
    ###
    ###   SETUP
    ###
    
    def __init__(self, features=(), copyFrom=None, attachTo=None):
        """attachTo == uses URI and some subordinate impl?

        features = list of features to pick an engine?
             triples-only
             fol
             complete
             rdfs
             owl
             cwm
             ...?
        """
        self.exivars = []
        self.univars = []

    def clear(self):
        """Clear the KB of all its contents, like making a new one."""
        self.__init__()
        self[:] = []

    def prep(kb):
        """return a KB if possible, perhaps just the argument; throw
        an error we can't make a KB out of this thing"""
        if isinstance(kb, KB): return kb
        if isinstance(kb, list): return KB(copyFrom=kb)
        # nothing else for now
        raise RuntimeError, "Not convertable to a KB"
    prep = staticmethod(prep)

    ################################################################
    ###
    ###  INTERNING
    ###
        
    def intern(self, expr):
        """Return an internalized expr equivalent to the given one.

        When you construct a compound expr and the function part is
        intern'd, the result should be automatically intern'd.
        """
        # deepcopy and set owner on each one, unless in some intern map?
        return expr

    def constantFor(self, interpretation, suggestedName="<default>"):
        try:
            return self.__revInterpretation[interpretation][0]
        except KeyError:
            if suggestedName == "<default>":
                suggestedName = str(interpretation)
            c = LX.logic.Constant(suggestedName)
            self.interpret(c, interpretation)
            return c

    def newConstant(self, suggestedName=None):
        """Return a new Constant symbol.

        Shorthand for kb.intern(LX.logic.Constant(suggestedName=...)).
        """
        return self.intern(LX.logic.Constant(suggestedName=suggestedName))

    def newVariable(self, suggestedName=None):
        """Return a new Variable symbol.

        Shorthand for kb.intern(LX.logic.Variable(suggestedName=...)).
        """
        return self.intern(LX.logic.Variable(suggestedName=suggestedName))

    def newExistential(self, name=None):
        """Like newVariable, but the KB is surrounded by it.

        newSurroundingVariable...?
        """
        if name is None: name = "g"
        v = LX.logic.ExiVar(name)
        self.exivars.append(v)
        return v

    # newFunction, newIndividualConstant (0-arity Function application?)
    # newPredicate, newProposition
    

    ################################################################
    ###
    ###  SERIALIZATION
    ###
    
    def __str__(self):
        scope = defaultScope.copy()
        result = "\nKB Contents:"
        result+= "\n  exivars: "+", ".join(map(LX.expr.getNameInScope, self.exivars, [scope] * len(self.exivars)))
        result+= "\n  univars: "+", ".join(map(LX.expr.getNameInScope, self.univars, [scope] * len(self.univars)))
        result+= "\n  interpretation: "
        for (key,valueList) in self.__interpretation.iteritems():
            result+="\n     %s -->  %s"%(key.getNameInScope(scope), ", ".join(map(str, valueList)))
        result+= "\n  formulas: "
        result+= "\n     "
        result+= "\n     ".join(map(LX.expr.getNameInScope, self, [scope] * len(self)))
        result+= "\n"
        #result+= "\n  asFormulaString: "+self.asFormulaString()+"\n"
        #result+= "\n  asFormula:       "+str(self.asFormula())+"\n"
        return result
    


    def asFormulaString(self):
        scope = defaultScope.copy()
        result = ""
        if self.exivars: result += "exists "+" ".join(map(LX.expr.getNameInScope, self.exivars, [scope] * len(self.exivars)))
        if self.univars: result += "all "   +" ".join(map(LX.expr.getNameInScope, self.univars, [scope] * len(self.univars)))
        result += " (" + " &\n    ".join(map(LX.expr.getNameInScope, self, [scope] * len(self))) + ")"
        return result


    def asFormula(self):
        """Contrast with   kb.toFormula()[0]   which modifies the KB"""
        result = self[0]
        for s in self[1:]:
            result = LX.logic.AND(result, s)
        for v in self.univars:
            result = LX.logic.FORALL(v, result)
        for v in self.exivars:
            result = LX.logic.EXISTS(v, result)
        return result

    def serializeWithOperators(self, scope, ops):
        result = ""
        for f in self:
            result = result + f.serializeWithOperators(scope, ops) + ".\n"
        result = result[0:-1]
        return result


    ################################################################
    ###
    ###   MODIFICATION 
    ###

    # Hook on all the ways python modifies a List?
    #   file://home/sandro/local/doc/python/lib/typesseq.html
    #   file://home/sandro/local/doc/python/lib/typesseq-mutable.html
    # ['__add__', '__class__', '__contains__', '__delattr__',
    # '__delitem__', '__delslice__', '__dict__', '__eq__', '__ge__',
    # '__getattribute__', '__getitem__', '__getslice__', '__gt__',
    # '__hash__', '__iadd__', '__imul__', '__init__', '__le__',
    # '__len__', '__lt__', '__module__', '__mul__', '__ne__',
    # '__new__', '__reduce__', '__repr__', '__rmul__', '__setattr__',
    # '__setitem__', '__setslice__', '__str__', '__weakref__',
    # 'append', 'count', 'extend', 'index', 'insert', 'pop', 'remove',
    # 'reverse', 'sort']
    #
    #  or don't inherit from List; just implement the ones we want...

    def add(self, formula, p=None, o=None):
        """
        DEPRECATED: use append() instead
        
        SHOULD allow non-constants, and replace them with constants
        and user interp() to link to the other thing?   But also
        look up if we already have a symbol for that?

        needed for    rdf.py's    flatten kind of stuff.
        """
        if (p):
            raise RuntimeError, "Use LX.rdf.Statement instead"
            print formula, p, o
            self.append(LX.logic.RDF(formula ,p,o))
            # self.append(p(formula, o))
            return
        # assert(isinstance(formula, LX.Formula))
        #####assert(LX.fol.isFirstOrderFormula(formula))
        # could check that all its openVars are in are vars
        self.append(formula)

    def addFrom(self, kb):
        """DEPRECATED: use extend(self, other)
        """
        for formula in kb:
            self.add(formula)
        self.exivars.extend(kb.exivars)
        self.univars.extend(kb.univars)
        self.exIndex = self.exIndex + kb.exIndex



    ################################################################
    ###
    ###   QUERY / INFERENCE 
    ###

    ###      isComplete?
        
    def isSelfConsistent(self):
        # should also try mace, icgns, etc...
        try:
            proof = LX.engine.otter.run(self)
            return 0
        except LX.engine.otter.SOSEmpty:
            return 1
        # ... just let other exceptions bubble up, for now


    def query(pattern, mustBindVariables=None):
        """Return an activated Query object providing information about
        how the pattern matches the KB.  The query may be performed
        during this call OR later (lazy evaluation) when results are
        asked for.

        "pattern" is an expr, a formula, treated as a pattern or goal.
        The KB is asked "is it true that <pattern>?".  Any
        unquantified variables in the pattern are treated as
        existentially quantified and are by default returned as part
        of each match.

        x>>> import LX.kb
        x>>> kb=LX.kb.testKB1
        x>>> kb
        
        x>>> pattern=LX.kb.testPat1
        x>>> pattern
        
        x>>> q = kb.query(pattern)
        x>>> q

        x>>> for solution in q.results:
        ...    print solution
        ...    print expr.subst(solution.map)
        ...    print solution.proof           # ,...?
        ...    print

        The list mustBindVariables, if set, gives a list of variables
        which must each be bound to a Constant in each solution for
        the solution to be accepted.  By default, this list is all
        the open variables in the pattern, since users don't typically
        want to get back bindings to existential variables.
        """
        pass


    ################################################################
    ###
    ###   CONVERSIONS
    ###
    ###   There are many normal-forms for KBs.   Here are some
    ###   conversions between them.  Others would be CNF, INF,
    ###   unprenex, prenex, ...
    ###
    ###   kb.toPrenex
    ###   kb.toUnPrenex
    ###   kb.toCNF
    ###   kb.toINF
    ###   kb.toFlatbread   (all RDF Triples)  (method="reify" or "drop")
    ###   kb.toBreadfruit  (all p(s,o))
    ###   kb.to
    ###
    ###   kb.isFirstOrder
    ###   kb.isCNF
    ###   ...
        
    def reifyAsTrue(self):
        flat = KB()
        LX.rdf.flatten(self, flat, indirect=1)
        self.clear()
        self.addFrom(flat)

    def reifyAsTrueNonRDF(self):
        flat = KB()
        LX.rdf.flatten(self, flat, indirect=0)
        self.clear()
        self.addFrom(flat)

    ################################################################
    ###
    ###    PARSING/INPUT 
    ###
        
    def load(self, uri, allowedLanguages=["*"]):
        """NOT IMPLEMENTED: Add the formal meaning of identified document.

        @@@   languageOverrides={}
           a mapping from string->string, overriding self-identificat.

        In the simplest case, this might mean opening a local file,
        which we know to contain n3, read the contents, and parse them
        directly to the kb.

        In a more complex case, we do an HTTP GET to obtain the
        document, using allowedLanguages to help guide our content
        negotiation, get some content, figure out what language is
        actually used, [recursively] load that language's definition,
        use that definition to build a parser for the original content,
        and parse it.

        We end up with a logical formula which might or might not be
        RDF (depending on how the language definition is written), but
        we can convert it, of course.  If we want to load from an
        untrusted source, load to a temporary kb first, reify it to
        the main KB, then apply your trust rules.

        See Blindfold.

        Does something like:

           1.  Identify the language
                 from content-type, other headers, embedded emacs magic strings,
                 suffixes, 
                 and perhaps a pre-arranged list of allowed languages.
           2.  Look up its definition
                 from an allowed set of language definitions, and/or the web
           3.  Parse it, collecting the semantics
                 perhaps by compiling a parser for it
           4.  return the logic sentence it claims
                 with some latitude as to form; the sentence only guarantees
                 to be inconsistent (T=F) or to entail only the intended
                 expression's meaning and separable metadata. 

        """

def _test():
    import doctest, newkb
    return doctest.testmod(newkb) 

if __name__ == "__main__": _test()

 
# $Log$
# Revision 1.3  2003-02-25 16:17:15  sandro
# a little cleanup
#
# Revision 1.2  2003/02/21 05:19:34  sandro
# some doctexts
#
# Revision 1.1  2003/02/20 22:16:20  sandro
# deep revamp
#
# Revision 1.10  2003/02/14 17:21:59  sandro
# Switched to import-as-needed for LX languages and engines
#
# Revision 1.9  2003/02/14 00:36:37  sandro
# added constantFor() method
#
# Revision 1.8  2003/02/13 19:48:31  sandro
# a little more thinking/comment about interpretations
#
# Revision 1.7  2003/02/01 05:58:10  sandro
# intermediate lbase support; getting there but buggy; commented out
# some fol checks 
#
# Revision 1.6  2003/01/29 20:59:34  sandro
# Moved otter language support back from engine/otter to language/otter
# Changed cwm.py to use this, and [ --engine=otter --think ] instead of
# --check.
#
# Revision 1.5  2003/01/29 06:09:18  sandro
# Major shift in style of LX towards using expr.py.  Added some access
# to otter, via --check.  Works as described in
# http://lists.w3.org/Archives/Public/www-archive/2003Jan/0024
# I don't like this UI; I imagine something more like --engine=otter
# --think, and --language=otter (instead of --otterDump).
# No tests for any of this.
#
# Revision 1.4  2002/10/03 16:13:02  sandro
# some minor changes to LX-formula stuff, but it's still broken in ways
# that don't show up on the regression test.
#
# mostly: moved llyn-LX conversion stuff out of llyn.py, into
# LX.engine.llynInterface.py
#
# Revision 1.3  2002/10/02 23:32:20  sandro
# not sure
#
# Revision 1.2  2002/08/29 16:39:55  sandro
# fixed various early typos and ommissions; working on logic bug which
# is manifesting in description loops  
#
# Revision 1.1  2002/08/29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

  
