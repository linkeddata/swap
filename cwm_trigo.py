"""Trigonometrical Built-Ins for CWM

Allows CWM to do do trigonometrical
http://www.python.org/doc/2.3/lib/module-math.html

This module is inspired by the math module.
See http://www.w3.org/2000/10/swap/cwm_math.py

cf. http://www.w3.org/2000/10/swap/cwm.py
See http://ilrt.org/discovery/chatlogs/rdfig/2003-09-23.html#T22-37-54
http://rdfig.xmlhack.com/2003/09/23/2003-09-23.html#1064356689.846120


"""

__author__ = 'Karl Dubost'
__cvsid__ = '$Id$'
__version__ = '$Revision$'
__all__ = ["evaluateObject"]

from math import sin, acos, asin, atan, atan2, cos, cosh, degrees, radians, sinh, tan, tanh
from term import LightBuiltIn, Function, ReverseFunction
import types
from diag import progress
from cwm_math import *

MATH_NS_URI = 'http://www.w3.org/2000/10/swap/math#'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# Trigonometrical Features
#
#
# Light Built-in classes - these are all reverse functions
#
# cosine, arc cosine, hyperbolic or not
# sine, arc sine, hyperbolic or not
# tangent, arc tangent, arc tangent (y/x)
#

class BI_acos(LightBuiltIn, Function):
    def evaluateObject(self, subj_py):      
        """acos(x)
        
        Return the arc cosine (measured in radians) of x."""
        return acos(numeric(subj_py))

class BI_asin(LightBuiltIn, Function):
    def evaluateObject(self, subj_py):
        """asin(x)
        
        Return the arc sine (measured in radians) of x."""
        return asin(numeric(subj_py))

class BI_atan(LightBuiltIn, Function):
    def evaluateObject(self, subj_py):
        """atan(x)
        
        Return the arc tangent (measured in radians) of x."""
        return atan(numeric(subj_py))

class BI_atan2(LightBuiltIn, Function):
    def evaluateObject(self, subj_py):
        """atan2(y, x)
        
        Return the arc tangent (measured in radians) of y/x.
        Unlike atan(y/x), the signs of both x and y are considered.""" 
        if len(numeric(subj_py)) == 2:
        	return atan2(numeric(subj_py[0]),numeric(subj_py[1]))
        else: return None

class BI_cos(LightBuiltIn, Function):
    def evaluateObject(self, subj_py):
        """cos(x)
        
        Return the cosine of x (measured in radians)."""
        return cos(numeric(subj_py))

class BI_cosh(LightBuiltIn, Function):
    def evaluateObject(self, subj_py):
        """cosh(x)
        
        Return the hyperbolic cosine of x."""
        return cosh(numeric(subj_py))

class BI_degrees(LightBuiltIn, Function, ReverseFunction):
    def evaluateObject(self, subj_py):
        """degrees(x) -> converts angle x from radians to degrees"""
        return degrees(numeric(subj_py))
    def evaluateSubject(self, obj_py): 
        """radians(x) -> converts angle x from degrees to radians"""
        return radians(numeric(obj_py))

class BI_sin(LightBuiltIn, Function):
    def evaluateObject(self, subj_py):
        """sin(x)
        
        Return the sine of x (measured in radians)."""
        return sin(numeric(subj_py))

class BI_sinh(LightBuiltIn, Function):
    def evaluateObject(self, subj_py):
        """sinh(x)
        
        Return the hyperbolic sine of x."""
        return sinh(numeric(subj_py))

class BI_tan(LightBuiltIn, Function):
    def evaluateObject(self, subj_py):
        """tan(x)
        
        Return the tangent of x (measured in radians)."""
        return tan(numeric(subj_py))

class BI_tanh(LightBuiltIn, Function):
    def evaluateObject(self, subj_py):
        """tanh(x)
        
        Return the hyperbolic tangent of x."""
        return tanh(numeric(subj_py))

#  Register the string built-ins with the store

def register(store):
    str = store.internURI(MATH_NS_URI[:-1])
    str.internFrag('acos', BI_acos)
    str.internFrag('asin', BI_asin)
    str.internFrag('atan', BI_atan)
    str.internFrag('atan2', BI_atan2)
    str.internFrag('cos', BI_cos)
    str.internFrag('cosh', BI_cosh)
    str.internFrag('degrees', BI_degrees)
    str.internFrag('sin', BI_sin)
    str.internFrag('sinh', BI_sinh)
    str.internFrag('tan', BI_tan)
    str.internFrag('tanh', BI_tanh)
 
if __name__=="__main__": 
   print __doc__.strip()
