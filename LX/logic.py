"""Elements for making expressions be logic expressions (ie formulas).

All the standard terminology like Variables, Constants, Predicates,
etc, and the standard connectives like Conjunction, Disjunction,
Quantification, etc.

Also handly functions for handling these things.  They're not object
methods because the OO hierarchy is sometimes too dynamic here.



? split into   term.py    and    formula.py

or import bits into kb.py? ...?

"""
__version__ = "$Revision$"
# $Id$

from sys import stderr
import LX.expr
# from LX.namespace import ns    BELOW to avoid loop problem

################################################################

class Variable(LX.expr.AtomicExpr):
##     #__slots__ = [ ]
##     def __new__(class_, suggestedName="x"):
##         return LX.expr.AtomicExpr.__new__(class_)

##     def __init__(self, suggestedName):
##         pass
    pass

class ExiVar(Variable):
    #__slots__ = [ ]

##     def __new__(class_, suggestedName="x"):
##         return Variable.__new__(class_)

##     def __init__(self, suggestedName):
##         pass
    pass

class UniVar(Variable):
    #__slots__ = [ ]
    pass

class Proposition(LX.expr.AtomicExpr):
    """A boolean constant, but it's a very different thing from
    a term constant in FOL."""
    pass

constantsForURIs = { }


class Constant(LX.expr.AtomicExpr):
    """
    This denotes something in the domain of discourse.  In FOL, it is
    quite distinct from a variable, predicate, or function   
    """

    #__slots__ = []

    def __repr__(self):
        try:
            return "LX.logic.URIConstant(\""+self.uri+"\")"
        except AttributeError:
            return "LX.logic.Constant(#"+str(id(self))+")"

class URIConstant(Constant):

    __slots__ = ["uri"]

    def __new__(class_, uri):
        #print "New called, uri:",uri,"  uri(id):",id(uri)
        try:
            result = constantsForURIs[uri]
        except KeyError:
            result = Constant.__new__(class_)
            result.uri = uri
            constantsForURIs[uri] = result
            #print "  creating new"
        else:
            #print "  reusing"
            pass
        #print "  id(result)=",id(result)
        return result

    def __reduce__(self):
        """
         >>> filename="/tmp/sdfsdfsdf"
         >>> from LX.logic import *
         >>> c=URIConstant('http://www.w3.org/')
         >>> d=URIConstant('http://www.w3.org/')
         >>> c is d
         True
         >>> from cPickle import Pickler, Unpickler
         >>> f=file(filename, "w")
         >>> p=Pickler(f, -1)
         >>> dummy=p.dump((c,d))
         >>> f.close()
         >>> f=file(filename)
         >>> u=Unpickler(f)
         >>> r=u.load()
         >>> r[0] is r[1]
         True
         >>> r[0] is c
         True

        """
        return (__newobj__, (URIConstant, self.uri))
    
class DataConstant(Constant):

    __slots__ = ["lexrep", "value", "datatype"]

    def __init__(self, *args, **kwargs):
        pass

    def __new__(class_, value=None, lexrep=None, datatype=None):
        """Works in two modes: either:
                 (1) you specify the value and let us pick a lexrep
                     and datatype, or 
                 (2) specify a lexrep (and optional datatype) and
                     we'll figure out the value (if we can)

           In value-mode, what if we can't pick a lexrep?  That's
           an error, I think, because we couldn't send it as RDF.

           datatype can be given as a URI string or a URIConstant.  If
           None, then lexrep is taken to be a "plain literal" (ie
           xsd:string, I think.)
           
        """
        #print "NEW CALLED, lexrep:",lexrep

        if datatype is not None and not isinstance(datatype, URIConstant):
            datatype = URIConstant(datatype)
            
        if value is None:
            datapair = (lexrep, datatype)
        else:
            datapair = asDataPair(value)
            
        try:
            result = constantsForDTVs[datapair]
        except KeyError:
            #print "  creating new"
            result = Constant.__new__(class_)
            #print "  filling in"
            result.suggestedName = u"lit_"+datapair[0][:30]
            result.suggestedName = u"lit"
            result.lexrep  = datapair[0]
            result.datatype= datapair[1]
            if value is None:
                result.value = asValue(lexrep, datatype)
                #print "  Picked value: ", result.value, result.value.__class__
            else:
                result.value = value
            constantsForDTVs[datapair] = result
        else:
            #print "  reusing"
            pass
        #print "  id(result)=",id(result)
        return result

    #    def __getnewargs__(self):
    #        print >>stderr, "DATA getnewargs called"
    #        return (self.value, self.lexrep, self.datatype)

    def __reduce__(self):
        """
         >>> filename="/tmp/sdfsdfsdf"
         >>> from LX.logic import *
         >>> c=DataConstant('http://www.w3.org/')
         >>> d=DataConstant('http://www.w3.org/')
         >>> c is d
         True
         >>> from cPickle import Pickler, Unpickler
         >>> f=file(filename, "w")
         >>> p=Pickler(f, -1)
         >>> dummy=p.dump((c,d))
         >>> f.close()
         >>> f=file(filename)
         >>> u=Unpickler(f)
         >>> r=u.load()
         >>> r[0] is r[1]
         True
         >>> r[0] is c
         True

        """
        return (__newobj__, (DataConstant, self.value, self.lexrep, self.datatype))
    
    def __repr__(self):
        return ("LX.logic.DataConstant(value="+repr(self.value)+
                ", lexrep="+repr(self.lexrep)+", datatype="+
                repr(self.datatype)+"\")")

    def getData(self):
        return (self.lexrep, self.datatype)
    data=property(getData)
    
def __newobj__(cls, *args):
    return cls.__new__(cls, *args)
      
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

#  So, why do it this way?
#
#  Alternative 1: have constant<->URI map be per-kb
#      Cons: then you can't use the same constant between KBs!
#
#  Alternative 2: have a Constant-With-URI be a special kind
#      of LX.logic.Constant...   Um.  That might be fine.  Hrm.
#      Still need some kind of lookup function and at least the
#      constantsForURIs table, assuming we want re-use, which I
#      know we do....


def gatherURIs(expr, set):
    if expr.isAtomic():
        try:
            set[expr.uri] = 1
        except AttributeError:
            pass
    else:
        for term in expr.all:
            gatherURIs(term, set)

# OLD OBSOLETE FORWARDERS

def ConstantForURI(uri):
    return URIConstant(uri)

def ConstantForDatatypeValue(lexrep, datatype=None):
    return DataConstant(lexrep=lexrep, datatype=datatype)

def ConstantForPlainLiterals(value):
    return ConstantForDatatypeValue(value)
                                    


################################################################

constantsForDTVs = {

    # this needs work, but its enough for surnia right now....
    ("0", "http://www.w3.org/2001/XMLSchema#nonNegativeInteger"):
    URIConstant("foo:zero")

    }

class NoSuitableDatatype(RuntimeError):
    pass

# put these on a DatatypeManager object, or something, which
# optionally gets passed to DataConstant.__new__ ?

def asDataPair(value):
    from LX.namespace import ns

    if isinstance(value, int):
        # do nonNegativeInteger sometimes, ...?
        return (str(value), ns.xsd.int)
    if isinstance(value, (str, unicode)):
        return (value, None)
    raise NoSuitableDatatype(value)

def asValue(lexrep, datatype):
    from LX.namespace import ns

    """Okay to return None if there is no suitable value."""
    if datatype is None:
        return lexrep
    if datatype is ns.xsd.int:
        return int(lexrep)
    return None


                                    
    
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
# Revision 1.11  2003-09-17 17:18:02  sandro
# changed how URIs and Datatypes are handled, mostly to supporting pickling
#
# Revision 1.10  2003/09/05 04:39:06  sandro
# changed handling of i18n chars
#
# Revision 1.9  2003/09/04 07:14:12  sandro
# fixed plain literal handling
#
# Revision 1.8  2003/08/28 11:40:50  sandro
# let Constants know their data, if they have any.  Still not complete
# literal handling.  Used by owl-systems/display.py right now.
#
# Revision 1.7  2003/08/25 21:10:27  sandro
# slightly nicer printing
#
# Revision 1.6  2003/08/22 20:49:41  sandro
# midway on getting load() and parser abstraction to work better
#
# Revision 1.5  2003/08/20 09:26:48  sandro
# update --flatten code path to work again, using newer URI strategy
#
# Revision 1.4  2003/08/01 15:27:21  sandro
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

