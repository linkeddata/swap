"""Classes for storing and manipulating arbitrary expressions in the
form of abstract syntax trees (ASTs).

Expressions are always immutable.  If you want mutability, use a KB or
copy to/from a python list.  Use == for comparison instead of "is";
whether interning is done is an implementation issue.  Compound
expressions are equal if their parts are equal; atomic expressions can
only be assumed to be equal if they are the same python object.  (But
some subclasses might offer additional equality conditions.)

There's a fairly clear hierarchy split between CompoundExpr and
AtomicExpr, but there are many classifications one could do of Expr's
that do not fit a single hierarchy. 

TODO:
   redo as new-style class, inherit from list, with __slots__= []
   
"""
__version__ = "$Revision$"
# $Id$

from string import split

def virtual():
    raise RuntimeError, "Function should have been implemented in subclass"

class NotRDF(TypeError):
    """Something was treated as RDF, but it wasn't."""
    pass

pythonOperators = { }       # gets filled in later, using things not yet defined

class Expr:

    # or should these only be defined on certain subclasses...???
    def __and__(self, other):    return CompoundExpr(pythonOperators["and"], self, other)
    def __or__(self, other):     return CompoundExpr(pythonOperators["or"],  self, other)
    def __rshift__(self, other): return CompoundExpr(pythonOperators[">>"], self, other)
    def __neg__(self, other):    return CompoundExpr(pythonOperators["-"],  self)
    def __call__(self, *args):   return apply(CompoundExpr, (self,)+args)  # (need apply() the handle varargs)

    def isAtomic(self):
        return 0

    def serializeWithOperators(self, nameTable, operators,
                               parentLooseness=9999,
                               linePrefix="",
                               width=80):

        """An advanced __str__ function which uses infix and prefix
        operators, as provided in an operator table.

        The operator table idea and syntax are borrow from Prolog, as
        seen in
        http://www.forestro.com/kiev/kiev-187_4.html
        http://cs.wwc.edu/~aabyan/Logic/Prolog.html
        http://www.trinc-prolog.com/doc/pl_lang2.htm
        
        ##opTable = {
        ##    LX.IMPLIES:   [ 800, "xfx", "->" ],
        ##    LX.OR:        [ 790, "xfy", "|" ],
        ##    LX.AND:       [ 780, "xfy", "&" ],

        The first number is normally called the "priority" or
        "precidence" but I call it "looseness" since the higher
        numbers mean the operator binds more loosely.

        In strings like "xfx", f shows where the operator goes with
        respect to the arguments, x and/or y.  x means an argument
        (expression) with greater looseness, y means on with greater
        or equal looseness.   That is xfx means non-associative, xfy
        means right associative, and yfx means left-associative.

        All this is just to avoid printing some parentheses we don't
        really need, which would waste ink.  :-)
        
        Suitable for recursive use.  If told that the parent's
        operator has a higher looseness than the operator (if any)
        here, it can skip outer parentheses.

        When newlines are needed, the linePrefix is used.

        >>> import LX.expr
        >>> a=LX.expr.AtomicExpr("a")
        >>> b=LX.expr.AtomicExpr("b")
        >>> c=LX.expr.AtomicExpr("c")
        >>> p=LX.expr.AtomicExpr("modulo")
        >>> f1 = LX.expr.CompoundExpr(p,a,b)
        >>> print f1
        modulo(a, b)
        >>> ops= { p : [ 800, "xfx", "%" ] }
        >>> print f1.serializeWithOperators({},ops)
        a%b
        >>> f2 = LX.expr.CompoundExpr(p,c,f1)
        >>> print f2
        modulo(c, modulo(a, b))
        >>> print f2.serializeWithOperators({},ops)
        c%(a%b)

        """
    
class CompoundExpr(Expr):
    """An internal branch node in an abstract syntax tree,
    representing the application of some function (or operator or
    connective) to one or more expressions.

    """

    def __init__(self, function, *args):
        """Initialize the compound expression (immutably) with
        a function expression and one or more argument expressions.

        Why don't we allow nullary functions?  Because it confuses me
        and I can't think of a reason for it.  Since functions can't
        have side effects, the value of f() is always some constant,
        so just use that constant.

        Why do we allow CompoundExpr's to be the function?  Because
        I'm brave, and I want to allow things like Currying.

        Why do we use the term "function" instead of "operator",
        "connective", "functor", ...?   It seems like the most common
        term and not too confusing. 
        """
        assert(isinstance(function, Expr))
        self.__function = function
        assert(len(args) >= 1) 
        for arg in args:
            if not isinstance(arg, Expr):
                raise RuntimeError, "What's %s doing here?"%arg
        #if hasattr(function, "checkArgs"):
        #    function.checkArgs(args)
        self.__args = tuple(args)
        
    def getFunction(self):
        """Return the function (also called operator, connective,
        predicate, functor, ...) of this expression.
        """
        return self.__function

    function = property(getFunction)

    def getArgs(self):
        """Return a sequence of zero or more arguments (operands) to
        the function.

        Hows is a CompoundExpr with zero arguments different from a
        atomicExpr?  There's still a level of indirection, but I don't
        know when/why you'd want that.  Perhaps we should forbid it
        until we have a good reason for it.
        """
        return self.__args

    args = property(getArgs)

    ################################################################
    # RDF Terminology

    def getSubject(self):
        if len(self.__args) != 2:
            raise NotRDF(self)
        return self.__args[0]
    subject = property(getSubject)

    def getObject(self):
        if len(self.__args) != 2:
            raise NotRDF(self)
        return self.__args[1]
    object = property(getObject)

    def getPredicate(self):
        if len(self.__args) != 2:
            raise NotRDF(self)
        return self.__function
    predicate = property(getPredicate)

    def getSPO(self):
        if len(self.__args) != 2:
            raise NotRDF(self)
        return (self.__args[0], self.__args[1], self.__function)
    spo = property(getSPO)

    def getAll(self):
        return (self.__function,) + self.__args

    all = property(getAll)
    
    def __str__(self):
        """
        >>> import LX.expr
        >>> a=LX.expr.AtomicExpr("joe")
        >>> b=LX.expr.AtomicExpr("joe")
        >>> e = LX.expr.CompoundExpr(a,b,a)
        >>> print e
        joe(joe2, joe)
        """
        return self.getNameInScope({})

    def getNameInScope(self, nameTable):
        names = []
        for arg in self.all:
            names.append(arg.getNameInScope(nameTable))
        return names[0]+"("+", ".join(names[1:])+")"

    def dump(self, levels=32):
        """Like __str__ but it gives useful output before dying on
        badly-formed structures."""
        if levels <= 0:
            print "<MAXDEPTH>"
            return
        print "(",
        for arg in self.all:
            #print str(type(arg))+":",
            arg.dump(levels-1)
            print " ",
        print ")",
        
    def serializeWithOperators(self, nameTable, operators,
                               parentLooseness=9999,
                               linePrefix="",
                               width=80):

        try:
            op = operators[self.__function]
            prec = op[0]
            form = op[1]
            text = op[2]
            prefix = ""; suffix = ""
        except KeyError:
            return self.getNameInScope(nameTable)

        # my first attempt at writing this, so I'm not thinking about
        # the difference between "x" and "y", so we'll get some extra
        # parens.    It's pretty lousy code right now, but it's important
        # to do someday because it's damn hard to read complex expressions
        # and this should provide pretty-printing.
        
        if prec >= parentLooseness:
            prefix = "("; suffix = ")"
        if callable(form):
            result = prefix+apply(form, [text, self, nameTable, operators, prec, linePrefix])+suffix
        elif form == "xfx" or form == "xfy" or form == "yfx":
            if (len(self.__args) == 2):
                left = self.__args[0].serializeWithOperators(nameTable, operators, prec, linePrefix)
                right = self.__args[1].serializeWithOperators(nameTable, operators, prec, linePrefix)
                if 1 or (len(left) + len(right) < width):
                    result = prefix + left + text + right + suffix
                else:
                    linePrefix = "  " + linePrefix
                    left = self.__args[0].serializeWithOperators(nameTable, operators, prec, linePrefix)
                    right = self.__args[1].serializeWithOperators(nameTable, operators, prec, linePrefix)
                    result = (prefix + "\n" + linePrefix + left + text +
                          "\n" + linePrefix + right + suffix)
            else:
                raise RuntimeError, ("%s args on a binary operator %s" %
                                     (len(self.__args), self.__args[0]))
        elif form == "fxy":
            assert(len(self.__args) == 2)
            result = (prefix + text + self.__args[0].serializeWithOperators(nameTable, operators, prec, linePrefix)
                      + " " + self.__args[1].serializeWithOperators(nameTable, operators, prec, linePrefix) + suffix)
        elif form == "fx" or form == "fy":
            assert(len(self.__args) == 1)
            result = prefix + text + self.__args[0].serializeWithOperators(nameTable, operators, prec, linePrefix)
        else:
            raise RuntimeError, "unknown associativity form in table of operators"
        return result

        

def getNameInScope(thing, nameTable):
    return thing.getNameInScope(nameTable)
    
class AtomicExpr(Expr):

    def isAtomic(self):
        return 1

    def __init__(self, suggestedName="x"):
        self.suggestedName = suggestedName

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self is other
    
    def __str__(self):
        return self.suggestedName

    def dump(self, levels):
        print self.suggestedName,
        
    def getNameInScope(self, nameTable):
        """return a string which names this thing unambiguously in
        some scoping context (the nameTable).

        >>> import LX.expr
        >>> a=LX.expr.AtomicExpr("joe")
        >>> b=LX.expr.AtomicExpr("joe")
        >>> scope={}
        >>> print a.getNameInScope(scope)
        joe
        >>> print b.getNameInScope(scope)
        joe2
        >>> print a.getNameInScope(scope)
        joe
        >>> print b.getNameInScope(scope)
        joe2

        if the scope has a key ("legal",) it should be a regexp to
        match against; if match fails, suggested name wont be used.
        The first group in the regexp at the key ("hint",) will be
        used, if available.  Note that these keys are separated from
        the normal keys by being strings inside tuples.

        """
        try:
            return nameTable[self]
        except KeyError: pass
        n = self.suggestedName
        try:
            legal = nameTable[("legal",)]
            if not legal.match(n):
                n = "xx"
                hint = nameTable[("hint",)]
                m = hint.search(self.suggestedName)
                if m:
                    n = m.group(1)
        except KeyError: pass
        for extra in xrange(1, 100000000):
            if extra == 1:
                newName = n
            else:
                newName = n + str(extra)
            if newName not in nameTable.values():      # @ linear performance hit
                nameTable[self] = newName
                return newName
        raise RuntimeError, "wayyyyy to many similarly named expressions"


    def serializeWithOperators(self, nameTable, operators,
                               parentLooseness=9999,
                               linePrefix="",
                               width=80):
        return self.getNameInScope(nameTable)

class AtomicConstant(AtomicExpr):
    pass

#import LX.firstOrderLogic

#pythonOperators["and"] = LX.firstOrderLogic.AND
# ... or something.

#def _test_expr_setup():
#    """
#    >>> import LX.expr
#    >>> print LX.expr._test_expr[1]
#    or(and(p, q), pp(a))
#    """
#    p = Proposition("p")
#    q = Proposition("q")
#    pp = ConstantPredicate("pp")
#    a = Constant("a")
#    return {
#        1: (p & q | pp(a)),
#        }
#
#_test_expr = _test_expr_setup()

def _test():
    import doctest, expr
    return doctest.testmod(expr) 

if __name__ == "__main__": _test()




# $Log$
# Revision 1.10  2003-09-10 20:12:04  sandro
# added some get-as-RDF functions
#
# Revision 1.9  2003/08/01 15:27:21  sandro
# kind of vaguely working datatype support (for xsd unsigned ints)
#
# Revision 1.8  2003/07/31 18:25:15  sandro
# some unknown earlier changes...
# PLUS increasing support for datatype values
#
# Revision 1.7  2003/02/01 05:58:10  sandro
# intermediate lbase support; getting there but buggy; commented out some fol chreccks
#
# Revision 1.6  2003/01/29 06:09:18  sandro
# Major shift in style of LX towards using expr.py.  Added some access
# to otter, via --check.  Works as described in
# http://lists.w3.org/Archives/Public/www-archive/2003Jan/0024
# I don't like this UI; I imagine something more like --engine=otter
# --think, and --language=otter (instead of --otterDump).
# No tests for any of this.
#
# Revision 1.5  2003/01/08 12:38:38  sandro
# Added serializeWithOperators(), taken from the old language/abstract.py
#
# Revision 1.4  2002/10/03 16:13:02  sandro
# some minor changes to LX-formula stuff, but it's still broken in ways
# that don't show up on the regression test.
#
# mostly: moved llyn-LX conversion stuff out of llyn.py, into
# LX.engine.llynInterface.py
#
# Revision 1.3  2002/09/18 19:56:46  sandro
# more refactoring, added some unit tests, stricter notion of typing
#
# Revision 1.2  2002/09/02 20:10:44  sandro
# factored FOL code out of expr.py (and into firstOrderLogic.py), to try to keep it simple enough.  Lost propositions, doctests.
#
# Revision 1.1  2002/08/31 19:43:23  sandro
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

 
