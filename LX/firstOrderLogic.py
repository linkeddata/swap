"""Goes with LX.expr, to give it nice First-Order-Logix operations. If
we ever do HOL, lots of stuff may factor out.
"""
__version__ = "$Revision$"
# $Id$

import LX.expr

class Proposition(LX.expr.AtomicConstant):
    """A boolean constant"""
    pass

class Variable(LX.expr.AtomicExpr):
    """

    UGLY NOTE:
    sometimes these things (maybe expr's on the whole!) have URIRefs
    -- some symbol that identifies THEM (the expr).   That's what cwm
    handed us.   Where do we keep that info?
          - in some KB or other table, outside
            (mappings URIRef -> Expr, and Expr -> URIRef; note that
            a URIRef *is* and Expr, so we could get confused really
            easily.   What is the URIRef of a URIRef?)

           **** URI SHOULD GO INTO METADATA
    """
    
    def __init__(self, name=None, uriref=None):
        self.name = name
        self.value = uriref

class ExiVar(Variable):
    pass

class UniVar(Variable):
    pass
             
class Connective(LX.expr.AtomicConstant):
    """A function with specific FOL semantics"""

class BinaryConnective(Connective):

    def checkArgs(self, args):
        assert(len(args) == 2)
        for arg in args:
            assert(isFirstOrderFormula(arg))

class UnaryConnective(Connective):

    def checkArgs(self, args):
        assert(len(args) == 1)
        for arg in args:
            assert(isFirstOrderFormula(arg))

class Quantifier(Connective):

    pass

    
class ExistentialQuantifier(Quantifier):

    def checkArgs(self, args):
        assert(len(args) == 2)
        assert(isInstance(args[0], LX.expr.ExiVar))
        assert(isFirstOrderFormula(args[1]))

class UniveralQuantifier(Quantifier):

    def checkArgs(self, args):
        assert(len(args) == 2)
        assert(isInstance(args[0], LX.expr.UniVar))
        assert(isFirstOrderFormula(args[1]))


class Predicate(LX.expr.AtomicConstant):

    """A mapping from one or more terms to a truth value.

    When used as the function in an Expr, it makes the Expr be an
    Atomic Formula.
    """
    
    def checkArgs(self, args):
        assert(len(args) == 2)
        for arg in args:
            assert(isFirstOrderTerm(arg))


# We could dispatch this off the Connective inheritance tree or something.
    
def isFirstOrderTerm(expr):
    """Check whether this is a "Term".

    >>> import LX.fol   
    >>> a = LX.expr.AtomicConstant("a")
    >>> LX.fol.isFirstOrderTerm(a)
    1
    >>> LX.fol.isFirstOrderFormula(a)
    0


    >>> b = LX.expr.AtomicConstant("b")
    >>> f = LX.expr.AtomicConstant("f")
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
    h(f(a,b))
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
        else:
            return 0

def isFirstOrderFormula(expr):
    """Check whether this is a "Formula".

    Return false if it's not a Formula *or* it's not first-order.
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
        raise RuntimeError("Not Implemented")
    else:
        result = []
        for child in expr.all:
            result.extend(getOpenVariables(child))
        return result

AND = BinaryConnective("and")
OR = BinaryConnective("or")
LX.expr.opTable["and"] = AND
LX.expr.opTable["or"] = OR

def _test():
    import doctest, fol
    return doctest.testmod(fol) 


if __name__ == "__main__": _test()

# $Log$
# Revision 1.2  2002-10-02 23:32:20  sandro
# not sure
#

