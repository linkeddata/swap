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

    def __and__(self, other):    return Formula([LX.AND, self, other])
    def __or__(self, other):     return Formula([LX.OR,  self, other])
    def __rshift__(self, other): return Formula([LX.IMPLIES, self, other])
    def __neg__(self, other):    return Formula([LX.NOT,  self])

    def __str__(self):
        return serialize(self)

    def collectLeft(self, op):
        if self[0] is op:
            leftList, right = self[2].collectLeft(op)
            return ([self[1]]+leftList, right)
        else:
            return ([], self)

    # convertToKB   (with narrowed scopes?)

    def getOperator(self):
        return self[0]
    operator = property(getOperator)
    
    def getOperands(self):
        return self[1:]
    operands = property(getOperands)



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
        return Formula([LX.ALL, var, child])

class ExistentialQuantification(Formula):

    def __new__(self, var, child):
        return Formula([LX.EXISTS, var, child])


# $Log$
# Revision 1.2  2002-10-02 20:40:56  sandro
# make --flatten recognize log:means as the biconditional and
# log:Falsehood for a formula as its negation.
#
# Revision 1.1  2002/08/29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

 
