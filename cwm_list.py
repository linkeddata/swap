#! /usr/bin/python
"""


$Id$

List and set built-ins for cwm
http://www.w3.org/2000/10/swap/cwm_list.py

See cwm.py and the os module in python

"""


from term import LightBuiltIn, Function, ReverseFunction,\
    List, EmptyList, NonEmptyList

from diag import verbosity, progress
import uripath

from RDFSink import List_NS, Logic_NS

ListOperationsNamespace = "http://www.w3.org/2000/10/swap/list#"

###############################################################################################
#
#                    List handling   B U I L T - I N s
#
#
#   Light Built-in classes


class BI_first(LightBuiltIn, Function):
    def evalObj(self, subj, queue, bindings, proof, query):
	if not isinstance(subj, NonEmptyList): return None
	return subj.first

class BI_rest(LightBuiltIn, Function):
    def evalObj(self, subj, queue, bindings, proof, query):
	if not isinstance(subj, NonEmptyList): return None
	return subj.rest

class BI_last(LightBuiltIn, Function):
    def evalObj(self, subj, queue, bindings, proof, query):
	if not isinstance(subj, NonEmptyList): return None
	x = subj
	while 1:
	    last = x
	    x = x.rest
	    if isinstance(x, EmptyList): return last.first


class BI_in(LightBuiltIn):
    """Is the subject in the object?
    Thsi is a wimpy implementation, because the built-in 
    system can only return single values right now.  It ought to be
    able in the future return all subjects wjich are in the object."""
    def eval(self, subj, obj, queue, bindings, proof, query):
	if not isinstance(obj, List): return None
	return subj in obj


#  Register the string built-ins with the store

def register(store):

#    Done explicitly in llyn
#    list = store.internURI(List_NS[:-1])
#    list.internFrag("first", BI_first)
#    list.internFrag("rest", BI_rest)

    ns = store.internURI(ListOperationsNamespace[:-1])
    ns.internFrag("in", BI_in)
    ns.internFrag("last", BI_last)
# ends

