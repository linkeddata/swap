
from LX.namespace import Namespace

# See http://www.w3.org/TR/rdf-syntax-grammar/#section-Namespace
#  (we'll want special handling of _n with a subclass)
rdfns  = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns",
                   ["type", "nil", "first", "rest", "XMLLiteral"])
#
# See http://www.w3.org/TR/rdf-schema/
rdfsns = Namespace("http://www.w3.org/2000/01/rdf-schema",
                   ["Resource", "Class", "Datatype", "seeAlso"])
#
lx2ns  = Namespace("http://www.w3.org/2002/08/LX/RDF/v2", strict=0)
lxns   = Namespace("http://www.w3.org/2003/02/04/LX", strict=0)

