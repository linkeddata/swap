#!/usr/bin/python 
"""
Matematical Built-Ins for CWM/Llyn

Allows CWM to do addition, multiplication, subtraction, division, 
remainders, negation, exponentiation, count the members in a DAML 
list, and do the normal truth checking functions, only sub classed 
for numeric values.

cf. http://www.w3.org/2000/10/swap/cwm.py and 
http://ilrt.org/discovery/chatlogs/rdfig/2001-12-01.txt from 
"01:20:58" onwards.
"""

__author__ = 'Sean B. Palmer'
__cvsid__ = '$Id$'
__version__ = '$Revision$'

import sys, string, re, urllib
import thing, notation3

from thing import *

LITERAL_URI_prefix = 'data:application/n3,'
DAML_LISTS = notation3.DAML_LISTS

RDF_type_URI = notation3.RDF_type_URI
DAML_equivalentTo_URI = notation3.DAML_equivalentTo_URI

MATH_NS_URI = 'http://www.w3.org/2000/10/swap/math#'

def tidy(x): return string.replace(str(x), '.0', '')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# M A T H E M A T I C A L   B U I L T - I N s
#
# Some mathematical built-ins: the heaviest one gets the amount of list 
# members in a DAML list.
# 
# Thanks to deltab, bijan, and oierw for helping me to name the 
# properties, and to TimBL for CWM and the built-in templates in the 
# first place.
#
# Light Built-in classes - these are all reverse functions

# add, take, multiply, divide

class BI_sumOf(LightBuiltIn, ReverseFunction):
    def evaluateSubject(self, store, context, obj, obj_py): 
        t = 0
        for x in obj_py: t += float(x)
        return store.intern((LITERAL, tidy(t)))

class BI_differenceOf(LightBuiltIn, ReverseFunction):
    def evaluateSubject(self, store, context, obj, obj_py): 
        t = None
        if len(obj_py) == 2: t = float(obj_py[0]) - float(obj_py[1])
        if t is not None: return store.intern((LITERAL, tidy(t)))

class BI_productOf(LightBuiltIn, ReverseFunction):
    def evaluateSubject(self, store, context, obj, obj_py): 
        t = 1
        for x in obj_py: t *= float(x)
        return store.intern((LITERAL, tidy(t)))

class BI_quotientOf(LightBuiltIn, ReverseFunction):
    def evaluateSubject(self, store, context, obj, obj_py): 
        t = None
        if len(obj_py) == 2: t = float(obj_py[0]) / float(obj_py[1])
        if t is not None: return store.intern((LITERAL, tidy(t)))

# remainderOf and negationOf

class BI_remainderOf(LightBuiltIn, ReverseFunction):
    def evaluateSubject(self, store, context, obj, obj_py): 
        t = None
        if len(obj_py) == 2: t = float(obj_py[0]) % float(obj_py[1])
        if t is not None: return store.intern((LITERAL, tidy(t)))

class BI_negationOf(LightBuiltIn, Function, ReverseFunction):
    def evaluateSubject(self, store, context, obj, obj_py): 
        t = -float(obj.string)
        if t is not None: return store.intern((LITERAL, tidy(t)))
    def evaluateObject(self, store, context, subj, subj_py): 
        t = -float(subj.string)
        if t is not None: return store.intern((LITERAL, tidy(t)))

# Power

class BI_exponentiationOf(LightBuiltIn, ReverseFunction):
    def evaluateSubject(self, store, context, obj, obj_py): 
        t = None
        if len(obj_py) == 2: t = float(obj_py[0]) ** float(obj_py[1])
        if t is not None: return store.intern((LITERAL, tidy(t)))

# Math greater than and less than etc., modified from cwm_string.py
# These are truth testing things

class BI_greaterThan(LightBuiltIn):
    def evaluate(self, store, context, subj, subj_py, obj, obj_py):
        return (float(subj.string) > float(obj.string))

class BI_notGreaterThan(LightBuiltIn):
    def evaluate(self, store, context, subj, subj_py, obj, obj_py):
        return (float(subj.string) <= float(obj.string))

class BI_lessThan(LightBuiltIn):
    def evaluate(self, store, context, subj, subj_py, obj, obj_py):
        return (float(subj.string) < float(obj.string))

class BI_notLessThan(LightBuiltIn):
    def evaluate(self, store, context, subj, subj_py, obj, obj_py):
        return (float(subj.string) >= float(obj.string))

class BI_equalTo(LightBuiltIn):
    def evaluate(self, store, context, subj, subj_py, obj, obj_py):
        return (float(subj.string) == float(obj.string))

class BI_notEqualTo(LightBuiltIn):
    def evaluate(self, store, context, subj, subj_py, obj, obj_py):
        return (float(subj.string) != float(obj.string))

# memberCount - this is a proper forward function

class BI_memberCount(LightBuiltIn, Function):
    def evaluateObject(self, store, context, subj, subj_py): 
        t = len(subj_py)
        return store.intern((LITERAL, tidy(t)))

#  Register the string built-ins with the store

def register(store):
    str = store.internURI(MATH_NS_URI[:-1])
    str.internFrag('sumOf', BI_sumOf)
    str.internFrag('differenceOf', BI_differenceOf)
    str.internFrag('productOf', BI_productOf)
    str.internFrag('quotientOf', BI_quotientOf)
    str.internFrag('remainderOf', BI_remainderOf)
    str.internFrag('negationOf', BI_negationOf)
    str.internFrag('greaterThan', BI_greaterThan)
    str.internFrag('notGreaterThan', BI_notGreaterThan)
    str.internFrag('lessThan', BI_lessThan)
    str.internFrag('notLessThan', BI_notLessThan)
    str.internFrag('equalTo', BI_equalTo)
    str.internFrag('notEqualTo', BI_notEqualTo)
    str.internFrag('memberCount', BI_memberCount)
    str.internFrag('exponentiationOf', BI_exponentiationOf)

if __name__=="__main__": 
   print string.strip(__doc__)