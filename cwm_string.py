#! /usr/bin/python 
"""

$Id$

String built-ins for cwm
This started as http://www.w3.org/2000/10/swap/string.py

See cwm.py
"""



import string
import re

import thing

import notation3    # N3 parsers and generators, and RDF generator
# import sax2rdf      # RDF1.0 syntax parser to N3 RDF stream

import urllib # for hasContent
import md5, binascii  # for building md5 URIs

from thing import *

LITERAL_URI_prefix = "data:application/n3;"

# Should the internal representation of lists be with DAML:first and :rest?
DAML_LISTS = notation3.DAML_LISTS    # If not, do the funny compact ones

# Magic resources we know about

RDF_type_URI = notation3.RDF_type_URI # "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
DAML_equivalentTo_URI = notation3.DAML_equivalentTo_URI


STRING_NS_URI = "http://www.w3.org/2000/10/swap/string#"


###############################################################################################
#
#                               S T R I N G   B U I L T - I N s
#
# This should be in a separate module, imported and called once by the user
# to register the code with the store
#
#   Light Built-in classes

class BI_GreaterThan(LightBuiltIn):
    def evaluate(self, store, context, subj, subj_py, obj, obj_py):
        return (subj.string > obj.string)

class BI_NotGreaterThan(LightBuiltIn):
    def evaluate(self, store, context, subj, subj_py, obj, obj_py):
        return (subj.string <= obj.string)

class BI_LessThan(LightBuiltIn):
    def evaluate(self, store, context, subj, subj_py, obj, obj_py):
        return (subj.string < obj.string)

class BI_NotLessThan(LightBuiltIn):
    def evaluate(self, store, context, subj, subj_py, obj, obj_py):
        return (subj.string >= obj.string)

class BI_StartsWith(LightBuiltIn):
    def evaluate(self, store, context, subj, subj_py, obj, obj_py):
        return subj.string.startswith(obj.string)

# Added, SBP 2001-11:-

class BI_Contains(LightBuiltIn):
    def evaluate(self, store, context, subj, subj_py, obj, obj_py):
        return string.find(subj.string, obj.string) >= 0

class BI_DoesNotContain(LightBuiltIn): # Converse of the above
    def evaluate(self, store, context, subj, subj_py, obj, obj_py):
        return string.find(subj.string, obj.string) < 0

class BI_equalIgnoringCase(LightBuiltIn):
    def evaluate(self, store, context, subj, subj_py, obj, obj_py):
        return (string.lower(subj.string) == string.lower(obj.string))

class BI_notEqualIgnoringCase(LightBuiltIn):
    def evaluate(self, store, context, subj, subj_py, obj, obj_py):
        return (string.lower(subj.string) != string.lower(obj.string))

#  String Constructors - more light built-ins

class BI_concat(LightBuiltIn, ReverseFunction):
    def evaluateSubject(self, store, context, obj, obj_py):
        if thing.verbosity() > 80: progress("Concat input:"+`obj_py`)
        str = ""
        for x in obj_py:
            if type(x) != type(''): return None # Can't
            str = str + x 
        return store._fromPython(str)

class BI_concatenation(LightBuiltIn, Function):
    def evaluateObject(self, store, context, subj, subj_py):
        if thing.verbosity() > 80: progress("Concatenation input:"+`subj_py`)
        str = ""
        for x in subj_py:
            if type(x) != type(''): return None # Can't
            str = str + x 
        return store._fromPython(str)

#  Register the string built-ins with the store

def register(store):
    str = store.internURI(STRING_NS_URI[:-1])
    
    str.internFrag("greaterThan", BI_GreaterThan)
    str.internFrag("notGreaterThan", BI_NotGreaterThan)
    str.internFrag("lessThan", BI_LessThan)
    str.internFrag("notLessThan", BI_NotLessThan)
    str.internFrag("startsWith", BI_StartsWith)
    str.internFrag("concat", BI_concat)
    str.internFrag("concatenation", BI_concatenation)
    str.internFrag("contains", BI_Contains)
    str.internFrag("doesNotContain", BI_DoesNotContain)
    str.internFrag("equalIgnoringCase", BI_equalIgnoringCase)
    str.internFrag("notEqualIgnoringCase", BI_notEqualIgnoringCase)

    
