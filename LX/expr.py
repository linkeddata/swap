"""Classes for storing and manipulating arbitrary expressions in the
form of abstract syntax trees (ASTs).

Expressions are always immutable.  If you want mutability, use a KB or
copy to/from a python list.  Use == for comparison instead of "is";
whether interning is done is an implementation issue.

The main hierarchy is:
   Expr
     CompoundExpr (an internal branch node in the AST)
        These are classified in several ways, such as by the number
        of arguments (operands) and the type of the function
        (operator), but we don't use Python classes for this.
        Still, it vaguely appears as if CompoundExpr's are grouped like
          Formula (function isLogicalOperator)
            isSentence (Formula with no free variables)
          LogicFunction (Non-Boolean; NonPredicate)
          
     SimpleExpr   (a leaf node)
       Proposition
       SimpleValueExpr
         Variable
           ExiVar
           UniVar
         Constant
           URIRef
           String
           Number
           RDFLiteral [?]

These are tightly linked to Functions, which are the essential part of
CompoundExpr's.

"""
__version__ = "$Revision$"
# $Id$

import LX
from string import split

def virtual():
    raise RuntimeError, "Function should have been implemented in subclass"

# Define these as names now; change the values down below, after some
# class definitions
AND = None
OR = None
IMPLIES = None
NOT = None

class Expr:

    def isFormula(self):
        """Is this a "logic formula", a predicate calculus expression?

        >>> from LX.expr import *
        >>> p = Proposition()
        >>> p.isFormula()
        1
        >>> q = Proposition()
        >>> f = p & q
        >>> f.isFormula()
        1
        >>> a = Constant()
        >>> a.isFormula()
        0
        >>> x = ExiVar()
        >>> x.isFormula()     # see isFirstOrder()
        0
        >>> a = Constant()
        >>> x(a).isFormula()
        1
        """
        virtual()

    def isSentence(self):
        """Is this a "sentence" (or WFF), a formula with no free variables?

        """
        virtual()

    def isFirstOrder(self):
        """Are all functions (logical connectives and logic functions)
        constants?

        >>> from LX.expr import *
        >>> p = Proposition()
        >>> q = Proposition()
        >>> pp = ConstantPredicate()
        >>> a = Constant()
        >>> (p & q).isFirstOrder()
        1
        >>> (p & q | pp(a)).isFirstOrder()
        1
        >>> x = ExiVar()
        >>> g = p & x(a)
        >>> g.isFirstOrder()
        0
        """
        virtual()

    def isRDF(self):
        """Is this a sentence using only functions AND, EXISTS, binary
        predicates, URIRefs, and RDFLiterals?
        
        """
        virtual()

    def __and__(self, other):    return CompoundExpr(AND, self, other)
    def __or__(self, other):     return CompoundExpr(OR,  self, other)
    def __rshift__(self, other): return CompoundExpr(IMPLIES, self, other)
    def __neg__(self, other):    return CompoundExpr(NOT,  self)
    def __call__(self, *args):   return apply(CompoundExpr, (self,)+args)

    def isPredicate(self): return 0
    
class CompoundExpr(Expr):

    def __init__(self, function, *args):
        assert(isinstance(function, SimpleValueExpr))
        self.__function = function
        for arg in args:
            assert(isinstance(function, Expr))
        if hasattr(function, "checkArgs"):
            function.checkArgs(args)
        self.__args = tuple(args)
        
    def getFunction(self):
        """Return the function (also called operator, predicate, functor,
        ...) of this expression; the function is a SimpleValueExpr.
        In first-order formulas, it's a Constant.

        """
        return self.__function

    function = property(getFunction)

    def getArgs(self):
        """Return a sequence of zero or more arguments (operands) to
        the function.

        Hows is a CompoundExpr with zero arguments different from a
        simpleExpr?  There's still a level of indirection, but I don't
        know when/why you'd want that.  Perhaps we should forbid it
        until we have a good reason for it.
        """
        return self.__args

    args = property(getArgs)

    def getAll(self):
        return (self.__function,) + self.__args

    all = property(getAll)
    
    def __str__(self):
        return str(self.function)+"("+", ".join(map(str, self.args))+")"

    def getOpenVariables(self):
        if function.isQuantifier():
            # this kind of makes us thing we should be instantiating a subclass
            raise RuntimeError, "Not Implemented"
        else:
            result = []
            for child in self.all:
                result.extend(child.getOpenVariables())
            return result

    def isFormula(self):
        if self.function.isPredicate():
            # trust that the function did type-checking on the way in...?
            return 1
        else:
            return 0

    def isFirstOrder(self):
        if isinstance(self.function, Constant):
            for arg in self.args:
                if not arg.isFirstOrder(): return 0
            return 1
        else:
            return 0
            
class SimpleExpr(Expr):

    def __init__(self, suggestedName="<unnamed>"):
        self.suggestedName = suggestedName
        
    def __str__(self):
        return self.suggestedName

    def getOpenVariables(self):
        return []

    def isFirstOrder(self): return 1

class Proposition(SimpleExpr):

    def isFormula(self):
        return 1

class SimpleValueExpr(SimpleExpr):

    def isFormula(self):
        return 0

class Variable(SimpleValueExpr):
    """

    sometimes these things (maybe expr's on the whole!) have URIRefs
    -- some symbol that identifies THEM (the expr).   That's what cwm
    handed us.   Where do we keep that info?
          - in some KB or other table, outside
            (mappings URIRef -> Expr, and Expr -> URIRef; note that
            a URIRef *is* and Expr, so we could get confused really
            easily.   What is the URIRef of a URIRef?)

    """
    
    # @@@ what to do with the URIRef???
    def __init__(self, name=None, uriref=None):
        self.name = name
        self.value = uriref

    def getOpenVariables(self):
        return [self]

    def isPredicate(self):
        """Variables are valid predicates (and functions) in HOL"""
        return 1
    
class ExiVar(Variable):
    pass

class UniVar(Variable):
    pass
             
class Constant(SimpleValueExpr):
    pass

class URIRef(Constant):
    """We know a URIRef which identifies the same thing as this
    Constant.  Should we allow many of these, therefor?"""

    def __init__(self, u):
        try:
            self.racine, self.fragment = split(u, "#")
            #print "initialized URIRef to %s, %s" % (self.racine, self.fragment)
        except ValueError:
            self.racine = u; self.fragment = None
        self.value = u

class String(Constant):

    def __init__(self, u):
        self._u = u

    def value(self):
        return self._u

    
class RDFLiteral(Constant):

    def __init__(self, text, lang=None, isXML=0):
        pass

class ConstantPredicate(Constant):

    def isPredicate(self):
        return 1
    

class BinaryLogicalOperator(ConstantPredicate):

    def checkArgs(self, args):
        assert(len(args) == 2)
        for arg in args:
            assert(arg.isFormula())

AND = BinaryLogicalOperator("and")
OR = BinaryLogicalOperator("or")

def _test_expr_setup():
    """
    >>> import LX.expr
    >>> print LX.expr._test_expr[1]
    or(and(p, q), pp(a))
    """
    p = Proposition("p")
    q = Proposition("q")
    pp = ConstantPredicate("pp")
    a = Constant("a")
    return {
        1: (p & q | pp(a)),
        }

_test_expr = _test_expr_setup()

def _test():
    import doctest, expr
    return doctest.testmod(expr) 

if __name__ == "__main__": _test()




# $Log$
# Revision 1.1  2002-08-31 19:43:23  sandro
# a new factoring, combining Term and Formula; not quite ready to replace the others, but passing its unit tests (I just discovered doctest)
#
# Revision 1.4  2002/08/29 21:56:54  sandro
# remove debugging print left in accidentally
#
# Revision 1.3  2002/08/29 21:02:13  sandro
# passes many more tests, esp handling of variables
#
# Revision 1.2  2002/08/29 16:39:55  sandro
# fixed various early typos and ommissions; working on logic bug which is manifesting in description loops
#
# Revision 1.1  2002/08/29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

 
