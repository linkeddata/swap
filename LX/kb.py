"""

I'm iffy about the whole idea of "interpretation" here for how URIs
work.  It was just an idea, at the time.


"""
__version__ = "$Revision$"
# $Id$

import LX
import re
defaultScope = {
    ("legal",): re.compile(r"^[a-zA-Z0-9_]+$"),
    ("hint",): re.compile(r"(?:\/|#)([a-zA-Z0-9_]*)/?$")
    }

class KB(list):
    """A Knowledge Base, a list of implicitely conjoined sentences.

    This is comparable to an RDF Graph if the Sentences here are all
    triples.

    Actually it's more complicated: we have a list of top level
    quantifications, too, so the elements can be open formulas iff
    their open variables are quantified by the kb. So the kb is a
    sentence of the form

       exists e1 e2 e3 ... (
          all x1 x2 x3 ... (
             formula1 & formula2 & formula3 ...
          )
       )

    (aka a sentence in "prenex" form.)
    """

    def __init__(self):
        self.exivars = []
        self.univars = []
        self.exIndex = 0
        self.interpretation = { }

    def clear(self):
        self.__init__()
        self[:] = []

    def __str__(self):
        scope = defaultScope.copy()
        result = "\nKB Contents:"
        result+= "\n  exivars: "+", ".join(map(LX.expr.getNameInScope, self.exivars, [scope] * len(self.exivars)))
        result+= "\n  univars: "+", ".join(map(LX.expr.getNameInScope, self.univars, [scope] * len(self.univars)))
        result+= "\n  interpretation: "
        for (key,valueList) in self.interpretation.iteritems():
            result+="\n     %s -->  %s"%(key.getNameInScope(scope), ", ".join(valueList))
        result+= "\n  formulas: "
        result+= "\n     "
        result+= "\n     ".join(map(LX.expr.getNameInScope, self, [scope] * len(self)))
        result+= "\n"
        #result+= "\n  asFormulaString: "+self.asFormulaString()+"\n"
        #result+= "\n  asFormula:       "+str(self.asFormula())+"\n"
        return result
    
    def interpret(self, term, object):
        try:
            self.interpretation[term].append(object)
        except KeyError:
            self.interpretation[term] = [object]

    def asFormulaString(self):
        scope = defaultScope.copy()
        result = ""
        if self.exivars: result += "exists "+" ".join(map(LX.expr.getNameInScope, self.exivars, [scope] * len(self.exivars)))
        if self.univars: result += "all "   +" ".join(map(LX.expr.getNameInScope, self.univars, [scope] * len(self.univars)))
        result += " (" + " &\n    ".join(map(LX.expr.getNameInScope, self, [scope] * len(self))) + ")"
        return result

    def asFormula(self):
        result = self[0]
        for s in self[1:]:
            result = LX.fol.AND(result, s)
        for v in self.univars:
            result = LX.fol.FORALL(v, result)
        for v in self.exivars:
            result = LX.fol.EXISTS(v, result)
        return result
       
    def prep(kb):
        """return a KB if possible, perhaps just the argument; throw
        an error we can't make a KB out of this thing"""
        if isinstance(kb, KB): return kb
        if isinstance(kb, list): return KB(kb)
        # nothing else for now
        raise RuntimeError, "Not convertable to a KB"
    prep = staticmethod(prep)

    def add(self, formula, p=None, o=None):
        if (p):
            self.append(LX.fol.RDF(s,p,o))
            return
        # assert(isinstance(formula, LX.Formula))
        assert(LX.fol.isFirstOrderFormula(formula))
        # could check that all its openVars are in are vars
        self.append(formula)

    def addFrom(self, kb):
        for formula in kb:
            self.add(formula)
        self.exivars.extend(kb.exivars)
        self.univars.extend(kb.univars)
        self.exIndex = self.exIndex + kb.exIndex

    def newExistential(self, name=None):
        if name is None: name = "g"
        v = LX.fol.ExiVar(name)
        self.exivars.append(v)
        return v

    def describeInterpretation(i, descriptionLadder=None):
        """For all the exprs in the kb which are keys in i, "describe"
        them as the value.

        >>> import LX.kb
        >>> import LX.expr
        >>> a=LX.expr.AtomicExpr("joe")
        >>> b=LX.expr.AtomicExpr("joe")
        >>> kb = LX.KB()
        >>> kb.add(a(b))
        >>> kb.describeInterpretation( {b:[a,b]} )   loop check?!
        """
        raise RuntimeError, "Not Implemented"
    
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

    def serializeWithOperators(self, scope, ops):
        result = ""
        for f in self:
            result = result + f.serializeWithOperators(scope, ops) + ".\n"
        result = result[0:-1]
        return result

        
    def isSelfConsistent(self):
        # should also try mace, icgns, etc...
        try:
            proof = LX.engine.otter.run(self)
            return 0
        except LX.engine.otter.SOSEmpty:
            return 1
        # ... just let other exceptions bubble up, for now

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
    import doctest, expr
    return doctest.testmod(expr) 

if __name__ == "__main__": _test()

 
# $Log$
# Revision 1.6  2003-01-29 20:59:34  sandro
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
# fixed various early typos and ommissions; working on logic bug which is manifesting in description loops
#
# Revision 1.1  2002/08/29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

  
