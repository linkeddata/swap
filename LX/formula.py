"""

TODO: switch to binary, unary, quant, with dispacth in __new__

"""
__version__ = "$Revision$"
# $Id$

import LX
from LX.language.otter import serialize


class Formula(tuple):
    """An immutable logical formula (much like a boolean expression).

    This may be used as a tuple with the first element being the
    logical operator: this is a very traditional LISPy approach,
    where a formula might look like:
       (all, x, (and, (predicate, rdf, a, b, x),
                      (predicate, rdf, d, e, x)))
    or someting.   (maybe no "predicate", maybe it's in a sublist...?)

    We may override "__new__"
    (see http://www.python.org/2.2.1/descrintro.html)
    so that x=Formula([and, a, b])
    can return a Conjunction and a Sentence.  If we care; I'm not
    sure there's much desire to use the natural class hierarchy of
    logical expressions.
    
    """

    def __init__(self, *args):
        self.openVars()     # used for the side-effect of checking types


    def __and__(self, other):    return Formula([LX.AND, self, other])
    def __or__(self, other):     return Formula([LX.OR,  self, other])
    def __rshift__(self, other): return Formula([LX.IMPLIES, self, other])
    def __neg__(self, other):    return Formula([LX.NOT,  self])

    def __str__(self):
        return serialize(self)

    def collectLeft(self):
        """Return a pair (leftTermList, finalRightChild) from
        a nested structure like a Quantification
        """
        left = self[1]    
        right = self[2]
        leftList = [left]
        if left.operator is self.operator:
            moreLeftList, right = right.collectLeft()
            leftList.extend(moreLeftList)
        return leftList, right

    def collectedOperands(self):
        """Return a list of all the operands to all the children
        of this formula which are connected by the same operator.
        This make a binary tree look like an n-ary tree, all the
        operands to nested conjunctions and disjunctions come back at once.

        Might be interesting to try doing via 'yeild'.
        """
        result = []
        for child in self.operands:
            if child.operator is self.operator:
                result.extend(child.collectedOperands())
        return result

    # convertToKB   (with narrowed scopes?)

    def getOperator(self):
        return self[0]
    operator = property(getOperator)
    
    def getOperands(self):
        return self[1:]
    operands = property(getOperands)

    varClass = { LX.ALL: LX.UniVar,
                 LX.EXISTS: LX.ExiVar }

    def isSentence(self):
        return len(self.openVars()) == 0
    
    def openVars(self):
        """Return the unquantified variables in this formula"""
        if self.operator in (LX.ALL, LX.EXISTS):
            var = self[1]
            varClass = self.varClass[self.operator]
            result = self[2] .openVars()
            if not isinstance(var, varClass):
                msg = "found a %s expecting a %s" % (var.__class__, varClass)
                raise TypeError, msg
            if var not in result:
                # maybe this should only be a warning?
                raise RuntimeError, "Variable does not occur in child"
            result.remove(var)
        elif self.operator is LX.ATOMIC_SENTENCE:
            result = []
            for operand in self.operands:
                result.extend(operand.openVars())
        else:
            result = []
            for operand in self.operands:
                result.extend(operand.openVars())

        return result

    def nameVars(self, nameOverridesTable={}, namesUsedOutside=()):
        """Make the names dict have a name for each variable which is
        unique in its scope in this formula.
        """
        if self.operator in (LX.ALL, LX.EXISTS):
            var = self[1]
            # varClass = self.varClass[self.operator]
            name = var.getName()
            if name in namesUsedOutside:
                # We could do:   and name not in self.openVars()
                # to allow:  all x ( P(x) & all x ( Q(x) ) )
                # which makes sense, but is too confusing for humans
                for x in xrange(2, 100000000):
                    newname = "%s_%d" % (name, x)
                    if newname not in namesUsedOutside:
                        break
                nameOverridesTable[var] = newname
            self.nameVars(nameOverridesTable, namesUsedOutside+(newname,))
        elif self.operator is LX.ATOMIC_SENTENCE:
            pass   # there wont be any quantifications in here
        else:
            for operand in self.operands:
                operand.nameVars(names)

        
        


# This is kind of backwards; Formula should dispatch to Triple, so that
# isinstance will still work, I think.   But I dunno....

class Triple(Formula):

    def __new__(self, s, p, o):
        return Formula([LX.ATOMIC_SENTENCE, s, p, o])

class AtomicFormula(Formula):

    def __new__(self, *args):
        l = [LX.ATOMIC_SENTENCE]
        l.extend(args)
        return Formula(l)

class Conjunction(Formula):

    def __new__(self, left, right):
        return Formula([LX.AND, left, right])

class Conditional(Formula):

    def __new__(self, left, right):
        return Formula([LX.IMPLIES, left, right])

class Biconditional(Formula):

    def __new__(self, left, right):
        return Formula([LX.MEANS, left, right])

class Negation(Formula):

    def __new__(self, f):
        return Formula([LX.NEGATION, f])
    
class UniversalQuantification(Formula):

    def __new__(self, var, child):
        assert(isinstance(var, LX.UniVar))
        return Formula([LX.ALL, var, child])

class ExistentialQuantification(Formula):

    def __new__(self, var, child):
        assert(isinstance(var, LX.ExiVar))
        return Formula([LX.EXISTS, var, child])


# $Log$
# Revision 1.3  2002-10-02 22:56:35  sandro
# Switched cwm main-loop to keeping state in llyn AND/OR an LX.formula,
# as needed by each command-line option.  Also factored out common
# language code in main loop, so cwm can handle more than just "rdf" and
# "n3".  New functionality is not thoroughly tested, but old functionality
# is and should be fine.  Also did a few changes to LX variable
# handling.
#
# Revision 1.2  2002/10/02 20:40:56  sandro
# make --flatten recognize log:means as the biconditional and
# log:Falsehood for a formula as its negation.
#
# Revision 1.1  2002/08/29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

 
