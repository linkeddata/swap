""" SPARQL Client Query for cwm architecture

"""

QL_NS = "http://www.w3.org/2004/ql#"
from sparql2cwm import SPARQL_NS

#from set_importer import Set, ImmutableSet


#from OrderedSequence import merge, intersection, minus, indentString

import diag
from diag import chatty_flag, tracking, progress

def SparqlQuery(query, items, serviceURI):
    """Perform remote query as client on remote store.
	See $SWAP/query.py
    """
    diag.chatty_flag = 99    # @@@@@@
    if diag.chatty_flag > 0:
	progress("SPARQL Query on service %s,\n\tvariables: %s;\n\texistentials: %s" %
			    (serviceURI, query.variables, query.existentials))
	for item in items:
	    progress("\tSparql query line: %s" % (`item`))
    
    s = query.n3String()
    progress("QUERY IS ", s)
    raise NotImplementedError()

    queryString = "CONSTRUCT { %s } WHERE { %s }" % (constructions, patterns )

    return nbs   # No bindings for testing


# ends
