""" These classes represent the different kinds of operators we have
in LX, but they probably don't do much.  They are used kind of more
like an enumeration, which happens to have a class hierarchy.

"""
__version__ = "$Revision$"
# $Id$

class Operator:
    """Some sort of operator or metasyntactic element in LX"""

    __slots__ = ["name"]
    
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "LX.operator."+self.name

    def __repr__(self):
        return "LX.operator."+self.name


# Are these just used like enums, or do we care about the type
# hierarchy and the instance data?
AND = Operator("AND")
OR  = Operator("OR")
NOT = Operator("NOT")
IMPLIES  = Operator("IMPLIES")
IS_IMPLIED_BY = Operator("IS_IMPLIED_BY")
MEANS = Operator("MEANS")
ATOMIC_SENTENCE = Operator("ATOMIC_SENTENCE")
ALL = Operator("ALL")
EXISTS = Operator("EXISTS")

# $Log$
# Revision 1.1  2002-08-29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

