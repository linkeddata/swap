"""Elements for making expressions be logic expressions (ie formulas).

All the standard terminology like Variables, Constants, Predicates,
etc, and the standard connectives like Conjunction, Disjunction,
Quantification, etc.

Also handly functions for handling these things.  They're not object
methods because the OO hierarchy is sometimes too dynamic here.

"""
__version__ = "$Revision$"
# $Id$

import LX.expr


################################################################

class Variable(LX.expr.AtomicExpr):
    pass

class ExiVar(Variable):
    pass

class UniVar(Variable):
    pass

class Proposition(LX.expr.AtomicExpr):
    """A boolean constant, but it's a very different thing from
    a term constant in FOL."""
    pass

class Constant(LX.expr.AtomicExpr):
    """
    This denotes something in the domain of discourse.  In FOL, it is
    quite distinct from a variable, predicate, or function   
    """
    pass

class Function(LX.expr.AtomicExpr):
    """
    This is a kind of mapping from a tuple of values
    to a (non-truth) value

    When used as a the function in an Expr, it makes the Expr be a
    function term.
    """

class Predicate(LX.expr.AtomicExpr):
    """A mapping from one or more terms to a truth value.

    When used as the function in an Expr, it makes the Expr be an
    Atomic Formula.
    """

################################################################
            
class Connective(LX.expr.AtomicExpr):
    """A function with specific logical semantics"""

class BinaryConnective(Connective):

    def checkArgs(self, args):
        assert(len(args) == 2)
        #for arg in args:
        #    assert(isFirstOrderFormula(arg))

class UnaryConnective(Connective):

    def checkArgs(self, args):
        assert(len(args) == 1)
        #for arg in args:
        #    assert(isFirstOrderFormula(arg))

class Quantifier(Connective):

    pass

    
class ExistentialQuantifier(Quantifier):

    def checkArgs(self, args):
        assert(len(args) == 2)
        assert(isinstance(args[0], ExiVar))
        #assert(isFirstOrderFormula(args[1]))

class UniversalQuantifier(Quantifier):

    def checkArgs(self, args):
        assert(len(args) == 2)
        assert(isinstance(args[0], UniVar))
        #assert(isFirstOrderFormula(args[1]))


def getOpenVariables(expr, unusedButQuantified=None):
    """Return A list of all the un-quantified variables and optionally
    also a list of those quantified but not used.

    >>> from LX.logic import *
    >>> a=Constant("a")
    >>> b=Constant("b")
    >>> f=Function("f")
    >>> fab=f(a,b)
    >>> print fab
    f(a, b)
    >>> x=Variable("?x")
    >>> fx=f(x)
    >>> fax=f(a,x)
    >>> print fx
    f(?x)
    >>> print fax
    f(a, ?x)
    >>> print getOpenVariables(fab)
    []
    >>> print getOpenVariables(fx)[0]
    ?x
    >>> print getOpenVariables(fax)[0]
    ?x

    >>> s1 = FORALL(x, fax)
    >>> print s1
    forall(?x, f(a, ?x))
    >>> print getOpenVariables(s1)
    []

    >>> y=Variable("?y")
    >>> s2 = FORALL(y, fax)
    >>> print s2
    forall(?y, f(a, ?x))
    >>> print getOpenVariables(s2)[0]
    ?x
    >>> unused=[]
    >>> print getOpenVariables(s2, unused)[0]
    ?x
    >>> print unused[0]
    ?y
    
    """

    if expr.isAtomic():
        if isinstance(expr, Constant):
            return []
        elif isinstance(expr, Function):
            return []
        elif isinstance(expr, Proposition):
            return []
        elif isinstance(expr, Predicate):
            return []
        elif isinstance(expr, Variable):
            return [expr]
        else:
            raise RuntimeError, "unknown atomic term: %s" % expr
    else:
        if isinstance(expr.function, Quantifier):
            assert(len(expr.args) == 2)
            result = getOpenVariables(expr.args[1])
            try:
                result.remove(expr.args[0])
            except ValueError:
                if unusedButQuantified is not None:
                    unusedButQuantified.append(expr.args[0])
                else:
                    pass    # the caller doesn't want to know
            return result
        else:
            result = []
            for child in expr.all:
                result.extend(getOpenVariables(child))
            return result

################################################################

# or do as   Constant(uri=None, value=None)     using __new__
# for object re-use?

constantsForURIs = { }

def ConstantForURI(uri):
    try:
        return constantsForURIs[uri]
    except KeyError:
        tt = Constant(uri)
        constantsForURIs[uri] = tt
        # kb.interpret(tt, LX.uri.Describedthing(uri))
        #     # t[0] = constants.setdefault(t[1], LX.fol.Constant(t[1]))
        return tt


constantsForDTVs = {
    ("0", "http://www.w3.org/2001/XMLSchema#nonNegativeInteger"):
    ConstantForURI("foo:zero")
    }
valuesForConstants = { }
for (key, value) in constantsForDTVs:
    valuesForConstants[value] = key


def ConstantForDatatypeValue(dtv, dtURI=None):
    """
    Basically we'd like to handle python types and RDF/XSD types
    in the same place.  Hrm.
    """
    if dtURI is None:
        dtURI = "::native"

    dtv = (dtv, dtURI)
    try:
        return constantsForDTVs[dtv]
    except KeyError:
        tt = Constant(suggestedName=("lit"+str(dtv[0])))
        constantsForDTVs[dtv] = tt
        valuesForConstants[tt] = dtv
        return tt

    
################################################################
        
AND = BinaryConnective("and")
OR = BinaryConnective("or")
MEANS = BinaryConnective("means")
IFF = MEANS
IMPLIES = BinaryConnective("implies")
NOT = UnaryConnective("not")
FORALL = UniversalQuantifier("forall")
EXISTS = ExistentialQuantifier("exists")
EQUALS = Predicate("=")

LX.expr.pythonOperators["and"] = AND
LX.expr.pythonOperators["or"] = OR

# this is our special predicate!  Oh yeah!   Why do we want one of these?!
# ... because sometimes we use synhol (syntactic higher-order logic)
RDF = Predicate("rdf")

def _test():
    import doctest, logic
    return doctest.testmod(logic) 


if __name__ == "__main__": _test()

# $Log$
# Revision 1.4  2003-08-01 15:27:21  sandro
# kind of vaguely working datatype support (for xsd unsigned ints)
#
# Revision 1.3  2003/07/31 18:25:15  sandro
# some unknown earlier changes...
# PLUS increasing support for datatype values
#
# Revision 1.2  2003/02/03 17:20:40  sandro
# factored logic.py out of fol.py
#
# Revision 1.1  2003/02/03 17:07:34  sandro
# Factored logic out of fol (first order logic), now that I need some
# higher-order syntax for handling lbase.
#
# Revision 1.4  2003/02/01 05:58:10  sandro
# intermediate lbase support; getting there but buggy; commented out some fol chreccks
#
# Revision 1.3  2003/01/29 06:09:18  sandro
# Major shift in style of LX towards using expr.py.  Added some access
# to otter, via --check.  Works as described in
# http://lists.w3.org/Archives/Public/www-archive/2003Jan/0024
# I don't like this UI; I imagine something more like --engine=otter
# --think, and --language=otter (instead of --otterDump).
# No tests for any of this.
#
# Revision 1.2  2002/10/03 16:13:02  sandro
# some minor changes to LX-formula stuff, but it's still broken in ways
# that don't show up on the regression test.
#
# mostly: moved llyn-LX conversion stuff out of llyn.py, into
# LX.engine.llynInterface.py
#
# Revision 1.1  2002/09/18 19:56:46  sandro
# more refactoring, added some unit tests, stricter notion of typing
#

