"""Goes with LX.expr, to give it nice First-Order-Logix operations. If
we ever do HOL, lots of stuff may factor out.
"""
__version__ = "$Revision$"
# $Id$

import LX.expr

################################################################

class Variable(LX.expr.AtomicExpr):
    """
    This is the kind of variable that can range over first-order
    kind of stuff, not predicates, functions, etc.

    """
    pass

class ExiVar(Variable):
    pass

class UniVar(Variable):
    pass


################################################################

class Proposition(LX.expr.AtomicExpr):
    """A boolean constant, but it's a very different thing from
    a term constant in FOL."""
    pass

################################################################

class Constant(LX.expr.AtomicExpr):
    """
    This denotes something in the domain of discourse, quite
    distinct from a variable, predicate, or function
    """
    pass


class Function(LX.expr.AtomicExpr):
    """
    This is a kind of mapping from a tuple of values
    to a (non-truth) value

    """

    def checkArgs(self, args):
        assert(len(args) == 2)
        for arg in args:
            assert(isFirstOrderTerm(arg))


class Predicate(LX.expr.AtomicExpr):
    """A mapping from one or more terms to a truth value.

    When used as the function in an Expr, it makes the Expr be an
    Atomic Formula.
    """
    
    def checkArgs(self, args):
        for arg in args:
            assert(isFirstOrderTerm(arg))

################################################################
            
class Connective(LX.expr.AtomicExpr):
    """A function with specific FOL semantics"""

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
        assert(isFirstOrderFormula(args[1]))

class UniversalQuantifier(Quantifier):

    def checkArgs(self, args):
        assert(len(args) == 2)
        assert(isinstance(args[0], UniVar))
        assert(isFirstOrderFormula(args[1]))


################################################################
        
# We could dispatch this off the Connective inheritance tree or something.
    
def isFirstOrderTerm(expr):
    """Check whether this is a "Term".

    >>> import LX.fol   
    >>> a = LX.fol.Constant("a")
    >>> LX.fol.isFirstOrderTerm(a)
    1
    >>> LX.fol.isFirstOrderFormula(a)
    0


    >>> b = LX.fol.Constant("b")
    >>> f = LX.fol.Function("f")
    >>> fab = LX.expr.CompoundExpr(f,a,b)
    >>> print fab
    f(a, b)
    >>> LX.fol.isFirstOrderTerm(fab)
    1
    >>> LX.fol.isFirstOrderFormula(fab)
    0

    >>> p = LX.fol.Proposition("p")
    >>> LX.fol.isFirstOrderTerm(p)
    0
    >>> LX.fol.isFirstOrderFormula(p)
    1

    >>> q = LX.fol.Proposition("q")
    >>> p_or_q = p | q
    >>> print p_or_q
    or(p, q)
    >>> LX.fol.isFirstOrderTerm(p_or_q)
    0
    >>> LX.fol.isFirstOrderFormula(p_or_q)
    1

    >>> h = LX.fol.Predicate("h")
    >>> LX.fol.isFirstOrderTerm(h)
    0
    >>> LX.fol.isFirstOrderFormula(h)
    0
    >>> hfab = h(fab)
    >>> print hfab
    h(f(a, b))
    >>> LX.fol.isFirstOrderTerm(hfab)
    0
    >>> LX.fol.isFirstOrderFormula(hfab)
    1
    
    Return false if it's not a Term *or* it's not first-order.
    """
    if expr.isAtomic():
        if isinstance(expr, Constant) or isinstance(expr, Variable):
            return 1
        else:
            return 0
    else:
        if isinstance(expr.function, Function):
            for arg in expr.args:
                if not isFirstOrderTerm(arg): return 0
            return 1
        else:
            return 0

def isFirstOrderFormula(expr):
    """Check whether this is a "Formula".

    Return false if it's not a Formula *or* it's not first-order.

    or raise exception if not a formula...???
    """
    if expr.isAtomic():
        if isinstance(expr, Proposition):
            return 1
        else:
            return 0
    else:
        if isinstance(expr.function, Predicate):
            for arg in expr.args:
                if not isFirstOrderTerm(arg): return 0
            return 1
        else:
            if isinstance(expr.function, ExistentialQuantifier):
                assert(isinstance(expr.args[0], ExiVar))
                return isFirstOrderFormula(expr.args[1])
            elif isinstance(expr.function, UniversalQuantifier):
                assert(isinstance(expr.args[0], UniVar))
                return isFirstOrderFormula(expr.args[1])
            elif isinstance(expr.function, Connective):
                for arg in expr.args:
                    if not isFirstOrderFormula(arg): return 0
                return 1
            else:
                return 0

def isFirstOrderAtomicFormula(expr):
    if isinstance(expr.function, Predicate):
        for arg in expr.args:
            if not arg.isFirstOrderTerm(): return 0
        return 1
    return 0 

def isFirstOrder(expr):
    return isFirstOrderFormula(expr) or isFirstOrderTerm(expr)

def getOpenVariables(expr):

    assert(isFirstOrder(expr))
    if isinstance(expr, Constant):
        return []
    elif isinstance(expr, Variable):
        return [expr]
    elif isinstance(expr.function, Quantifier):
        # this kind of makes us think we should be instantiating a subclass
        raise RuntimeError, "Not Implemented"
    else:
        result = []
        for child in expr.all:
            result.extend(getOpenVariables(child))
        return result

AND = BinaryConnective("and")
OR = BinaryConnective("or")
MEANS = BinaryConnective("means")
IMPLIES = BinaryConnective("implies")
NOT = UnaryConnective("not")
FORALL = UniversalQuantifier("forall")
EXISTS = ExistentialQuantifier("exists")
EQUALS = Predicate("=")
LX.expr.pythonOperators["and"] = AND
LX.expr.pythonOperators["or"] = OR

# this is our special predicate!  Oh yeah!
RDF = Predicate("rdf")


def _test():
    import doctest, fol
    return doctest.testmod(fol) 


if __name__ == "__main__": _test()

# $Log$
# Revision 1.4  2003-02-01 05:58:10  sandro
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

