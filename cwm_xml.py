#
#  Note - see also times for string-oriented versions
#
# TODO:
# - extraction os fields should extend date time if necessary
#
# See http://www.python.org/doc/current/lib/module-time.html
#

"""
The time built-ins concern dates and times expressed in a specific
version of ISO date-time format.  These functions allow the various
parts of the date and time to be compared, and converted
into interger second GMT era format for arithmetic.

Be aware that ISo times carry timezone offset information:  they cannot be
converted to integer second times without a valid timezone offset, such as "Z".
"""

import string
import re
import notation3    # N3 parsers and generators, and RDF generator
import isodate	    # Local, by mnot. implements <http://www.w3.org/TR/NOTE-datetime>


from diag import progress, verbosity
from term import LightBuiltIn, Function, ReverseFunction
import time, calendar # Python standard distribution


XMLBI_NS_URI = "http://www.w3.org/2007/ont/xml#"


__version__ = "0.1"


#   Node properties   -- see http://www.python.org/doc/current/lib/dom-node-objects.html


class BI_nodeType(LightBuiltIn, Function):
    """An integer representing the node type
    """
    def evaluateObject(self, subj_py):
	return subj_py.nodeType

class BI_parentNode(LightBuiltIn, Function):
    """The parent of the current node, or None for the document node.
     The value is always a Node object or None. For Element nodes,
      this will be the parent element, except for the root element,
     in which case it will be the Document object. For Attr nodes, this is always None.
    """
    def evaluateObject(self, subj_py):
	return subj_py.parentNode

class BI_attributes(LightBuiltIn, Function):
    """A NamedNodeMap of attribute objects. Only elements have
     actual values for this.
    """
    def evaluateObject(self, subj_py):
	return subj_py.attributes

class BI_previousSibling(LightBuiltIn, Function):
    """The node that immediately precedes this one with the same parent.
    For instance the element with an end-tag that comes just before the
     self element's start-tag. Of course, XML documents are made up of
      more than just elements so the previous sibling could be text, 
    a comment, or something else.
     If this node is the first child of the parent, this property will not exist.
    """
    def evaluateObject(self, subj_py):
	return subj_py.previousSibling

class BI_nextSibling(LightBuiltIn, Function):
    """The node that immediately follows this one with the same parent. See also previousSibling.
    If this is the last child of the parent, this property will not exist.
    """
    def evaluateObject(self, subj_py):
	return subj_py.nextSibling

class BI_childNodes(LightBuiltIn, Function):
    """A list of nodes contained within this node.
    """
    def evaluateObject(self, subj_py):
	return subj_py.childNodes

class BI_firstChild(LightBuiltIn, Function):
    """The first child of the node, if there are any.
    """
    def evaluateObject(self, subj_py):
	return subj_py.firstChild

class BI_lastChild(LightBuiltIn, Function):
    """The last child of the node, if there are any.
    """
    def evaluateObject(self, subj_py):
	return subj_py.lastChild

class BI_localName(LightBuiltIn, Function):
    """The part of the tagName following the colon if there is one, else the entire tagName
    """
    def evaluateObject(self, subj_py):
	return subj_py.localName

class BI_prefix(LightBuiltIn, Function):
    """The part of the tagName preceding the colon if there is one, else the empty string
    """
    def evaluateObject(self, subj_py):
	return subj_py.prefix

class BI_namespaceURI(LightBuiltIn, Function):
    """The namespace associated with the element name.
    """
    def evaluateObject(self, subj_py):
	return subj_py.namespaceURI

class BI_nodeName(LightBuiltIn, Function):
    """This has a different meaning for each node type; see the DOM 
    specification for details. You can always get the information you would
     get here from another
     property such as the tagName property for elements or 
     the name property for attributes.
    """
    def evaluateObject(self, subj_py):
	return subj_py.nodeName

class BI_nodeValue(LightBuiltIn, Function):
    """This has a different meaning for each node type;
     see the DOM specification for details. 
     The situation is similar to that with nodeName
    """
    def evaluateObject(self, subj_py):
	return subj_py.nodeValue

class BI_hasAttributes(LightBuiltIn, Function):
    """True if the node has any attributes.
    """
    def evaluateObject(self, subj_py):
	return subj_py.hasAttributes()

class BI_hasChildNodes(LightBuiltIn, Function):
    """True if the node has any child nodes
    """
    def evaluateObject(self, subj_py):
	return subj_py.hasChildNodes()

class BI_isSameNode(LightBuiltIn):
    """Returns true if other refers to the same node as this node.
     This is especially useful for DOM implementations which use
     any sort of proxy architecture (because more than one object can refer to the same node).
    """
    def evaluate(self, subj_py, obj_py):
	return subj_py.sSameNode(obj_py)



#  Register the string built-ins with the store
def register(store):
    str = store.symbol(XMLBI_NS_URI[:-1])
    str.internFrag("nodeType", BI_nodeType)
    str.internFrag("parentNode", BI_parentNode)
    str.internFrag("attributes", BI_attributes)
    str.internFrag("previousSibling", BI_previousSibling)
    str.internFrag("nextSibling", BI_nextSibling)
    str.internFrag("childNodes", BI_childNodes)
    str.internFrag("firstChild", BI_firstChild)
    str.internFrag("lastChild", BI_lastChild)
    str.internFrag("localName", BI_localName)
    str.internFrag("prefix", BI_prefix)
    str.internFrag("namespaceURI", BI_namespaceURI)
    str.internFrag("nodeName", BI_nodeName)
    str.internFrag("nodeValue", BI_nodeValue)
    str.internFrag("hasAttributes", BI_hasAttributes)
    str.internFrag("hasChildNodes", BI_hasChildNodes)
    str.internFrag("isSameNode", BI_isSameNode)


# ends
