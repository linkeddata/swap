"""Goes with LX.expr, to give it nice First-Order-Logix operations.  I
haven't done any Higher-Order Logic; some stuff may factor out.

"""
__version__ = "$Revision$"
# $Id$

import LX.expr

class Connective(LX.expr.SimpleConstant):
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


class Predicate(LX.expr.SimpleConstant):

    """A function mapping from one or more terms to a truth value.

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

    Return false if it's not a Term *or* it's not first-order.
    """
    if expr.isVariable(): return 0 # it's HOL
    if expr.SimpleConstant: return 1 # @@@@ unless it's a proposition
    if not expr.function.isSimpleConstant(): return 0  # it's HOL
    if isinstance(expr.function, Connective): return 0
    if isinstance(expr.function, Predicate): return 0
    for arg in expr.args:
        if not arg.isFirstOrderTerm(): return 0
    return 1

def isFirstOrderFormula(expr):
    """Check whether this is a "Formula".

    Return false if it's not a Formula *or* it's not first-order.
    """
    if expr.isVariable(): return 0 # it's HOL
    if expr.SimpleConstant: return 0 # @@@ unless it's a proposition?
    if isinstance(expr.function, Connective):
        for arg in expr.args:
            if not arg.isFirstOrderFormula(): return 0
        return 1
    if isFirstOrderAtomicFormula(expr) return 1
    return 0 

def isFirstOrderAtomicFormula(expr):
    if isinstance(expr.function, Predicate):
        for arg in expr.args:
            if not arg.isFirstOrderTerm(): return 0
        return 1
    return 0 
    
def getOpenVariables(expr):

    if isinstance(expr, LX.expr.SimpleConstant):
        return []
    elif isinstance(expr, LX.expr.Variable):
        return [expr]
    elif isinstance(expr.function, Quantifier):
        # this kind of makes us thing we should be instantiating a subclass
        raise RuntimeError, "Not Implemented"
    else:
        result = []
        for child in expr.all:
            result.extend(getOpenVariables(child))
        return result

