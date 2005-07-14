#!/usr/bin/env python
"""
Builtins for doing SPARQL queries in CWM

$Id$

"""

from term import LightBuiltIn, Function, ReverseFunction, MultipleFunction,\
    MultipleReverseFunction, typeMap, \
    CompoundTerm, N3Set, List, EmptyList, NonEmptyList, \
    Symbol, Fragment, Literal
from set_importer import Set

import uripath

try:
    from decimal import Decimal
except ImportError:
    from local_decimal import Decimal


SPARQL_NS = 'http://yosi.us/2005/sparql'


def toBool(val, dt=None):
    if dt == 'boolean':
        if val == 'false' or val == 'False' or val == '0':
            return False
        return toBool(val)
    if dt in typeMap:
        return bool(typeMap[dt](val))
    return bool(val)

class BI_equals(LightBuiltIn, Function, ReverseFunction):
    def eval(self, subj, obj, queue, bindings, proof, query):
        xsd = self.store.integer.resource
        if isinstance(subj, Symbol) and isinstance(obj, Symbol):
            return subj is obj
        if isinstance(subj, Fragment) and isinstance(obj, Fragment):
            return subj is obj
        if isinstance(subj, Literal) and isinstance(obj, Literal):
            if subj.datatype == xsd['boolean'] or obj.datatype == xsd['boolean']:
                return (toBool(str(subj), subj.datatype.resource is xsd and subj.datatype.fragid or None) ==
                        toBool(str(obj), obj.datatype.resource is xsd and obj.datatype.fragid or None))
            if not subj.datatype and not obj.datatype:
                return str(subj) == str(obj)
            if subj.datatype.fragid in typeMap and obj.datatype.fragid in typeMap:
                return subj.value() == obj.value()
            if subj.datatype != obj.datatype:
                raise TypeError(subj, obj)
            return str(subj) == str(obj)
                
        

    def evalSubj(self, obj, queue, bindings, proof, query):
        return obj

    def evalObj(self,subj, queue, bindings, proof, query):
        return subj


def register(store):
    ns = store.newSymbol(SPARQL_NS)
    ns.internFrag('equals', BI_equals)
