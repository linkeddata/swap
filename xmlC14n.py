#! /usr/bin/env python
'''XML Canonicalization

From: http://dev.w3.org/cvsweb/2001/xmlsec-python/c14n.py?rev=1.10
This module generates canonical XML of a document or element.
    http://www.w3.org/TR/2001/REC-xml-c14n-20010315
and includes a prototype of exclusive canonicalization
    http://www.w3.org/Signature/Drafts/xml-exc-c14n

This is based on Rich Salz's element node canonicalization which was
extended to support document node canonicalization. It also now
supports XPath subset node list canonicalization. However it presently
doesn't support:
    1. Unicode -- not sure how to get eg6 to work correctly in python. (Reagle)

Furthermore, it includes the following bugs thought to be in the DOM
implementation Ft.Lib.pDomlette: (Reagle)
    1. does not white space normalize attributes of type NMTOKEN and ID?
    2. seems to be include "\n" after importing external entities?

Note, this version processes a DOM tree, and consequently it processes
namespace nodes as attributes, not from a node's namespace axis. This
permits it to do simple document and element canonicalization without
XPath. When XPath is used, the XPath result node list is passed and used to
determine if the DOM node is in the XPath result list, but that is all.

Authors:
    "Joseph M. Reagle Jr." <reagle@w3.org>
    "Rich Salz" <rsalz@zolera.com>

$Date$ by $Author$
'''

_copyright = '''Copyright 2001, Zolera Systems Inc.  All Rights Reserved.
Copyright 2001, MIT. All Rights Reserved.

Distributed under the terms of:
  Python 2.0 License or later.
  http://www.python.org/2.0.1/license.html
or
  W3C Software License
  http://www.w3.org/Consortium/Legal/copyright-software-19980720
'''

from xml.dom import Node
#from ns import XMLNS        # http://mail.python.org/pipermail/xml-checkins/2001-May/000614.html
XMLNS = "http://www.w3.org/XML/1998/namespace"

import re
try:
    import cStringIO as StringIO
except:
    import StringIO

_attrs = lambda E: E.attributes or []
_children = lambda E: E.childNodes or []

# True/false
_true, _false = (1,0)

# Does a document/PI has lesser/greater document order than the
# first element?
_LesserElement, _Element, _GreaterElement = range(3)

# When xpath subset, has the namespace node inherited been rendered?
_NotRendered, _Rendered = range(2)

def _sorter(n1,n2):
    '''_sorter(n1,n2) -> int
    Sorting predicate for non-NS attributes.'''

    i = cmp(n1.namespaceURI, n2.namespaceURI)
    if i: return i
    return cmp(n1.localName, n2.localName)

def _sorter_ns(n1,n2):
    '''_sorter_ns((n,v),(n,v)) -> int
    "(an empty namespace URI is lexicographically least)."'''

    if n1[0] == 'xmlns': return -1
    if n2[0] == 'xmlns': return 1
    return cmp(n1[0], n2[0])

def _utilized((n,v), node, others, unsuppressedPrefixes=[]):
    '''_pertinent((n,v), node, others, unsuppressedPrefixes=[]) -> boolean
    Return true if that nodespace is utilized within the node'''

    import re
    n = re.sub('xmlns:?','',n)
##    print"@@@@ (n,v)", (n,v)
##    print"     node.prefix", node.prefix
##    print"     unsuppressedPrefixes", unsuppressedPrefixes
    if unsuppressedPrefixes.count(n) > 0:
##        print "     UTILIZED by unsuppressedPrefixes!!"
        return _true
    if n == node.prefix:
##        print "     UTILIZED by element!!", node.localName
        return _true
    for attr in others:
##        print"     (n,v), attr.prefix", (n,v), attr.prefix
        if n == attr.prefix:
##            print "     UTILIZED by attr!!", attr    
            return _true
##    print "     not utilized"
    return _false
    

class _implementation:
    '''Implementation class for C14N. This accompanies a node during it's
    processing and includes the parameters and processing state.'''

    # Handlers for each node, by node type. List is populated during
    # module instantiation
    handlers = {}

    # pattern/replacement list for whitespace stripping.
    repats = (
        ( re.compile(r'[ \t]+'), ' ' ),
        ( re.compile(r'[\r\n]+'), '\n' ),
    )

    def __init__(self, node, write, nsdict={}, stripspace=0, comments=0,
                 subset=[], exclusive=0, unsuppressedPrefixes=[]):
        '''Create and run the implementation.'''

        self.write, self.stripspace, self.comments = \
                write, stripspace, comments
        self.subset, self.exclusive, self.unsuppressedPrefixes = \
                subset, exclusive, unsuppressedPrefixes

        if not nsdict:
            nsdict = { 'xml': XMLNS.XML, 'xmlns': XMLNS.BASE }

        self.ns_stack = [ nsdict ]  # Stack of nsnodes
        self.rendered_ns_stack = [] # Stack of nodes rendered by ancestor

        # For keys in nsdict, set to NotRendered
        self.__init_rendered_ns = {}
        for key in nsdict.keys():
            self.__init_rendered_ns[key] = _NotRendered
        # But namespace of of 'xml' is already rendered
        self.__init_rendered_ns['xml'] = _Rendered
        # Create the first entry in the rendered_ns_stack
        self.rendered_ns_stack.append(self.__init_rendered_ns)

        # Stack of xml:foo attributes that need to be rendered
        self.xml_attrs_stack = [[]]

        if node.nodeType == Node.DOCUMENT_NODE:
            self.documentOrder = _LesserElement  # Before document element
            self._do_document(node)
        elif node.nodeType == Node.ELEMENT_NODE:
            self.documentOrder = _Element        # At document element
            inherited = self._inherit_context(node, exclusive,
                                              unsuppressedPrefixes=[])
            self._do_element(node, inherited)
            self.ns_stack.pop()
	elif node.nodeType == Node.DOCUMENT_TYPE_NODE:
	    pass
        else:
            #print node.nodeName, node.nodeType, node
            raise TypeError, 'Not an element or document node (%d)' % \
		node.nodeType


    def _inherit_context(self, node, exclusive, unsuppressedPrefixes):
        '''_inherit_context(self, node, exclusive, unsuppressedPrefixes)
                            -> list
        (Salz) scan ancestors of attribute and namespace context.
        Used only for single element node canonicalization, not for
        subset canonicalization.'''

        inherited=[]
        if not exclusive:
            # Collect the initial list of xml:foo attributes.
            xmlattrs = []
            for a in _attrs(node):
                if a.namespaceURI == XMLNS.XML:
                    n = a.localName
                    xmlattrs.append(n)

            # Walk up and get all xml:XXX attributes we inherit.
            parent, inherited = node.parentNode, []
            while parent:
                if parent.nodeType != Node.ELEMENT_NODE: break
                for a in _attrs(parent):
                    if a.namespaceURI != XMLNS.XML: continue
                    n = a.localName
                    if n not in xmlattrs:
                        xmlattrs.append(n)
                        inherited.append(a)
                parent = parent.parentNode
        return inherited


    def _do_document(self, node):
        '''_do_document(self, node) -> None
        Process a document node. documentOrder holds whether the document
        element has been encountered such that PIs/comments can be written
        as specified.'''

        inherited = []              # Document has no context
        for child in node.childNodes:
            if child.nodeType == Node.ELEMENT_NODE:
                self.documentOrder = _Element        # At document element
                self._do_element(child,inherited)
                self.documentOrder = _GreaterElement # After document element
            elif child.nodeType == Node.PROCESSING_INSTRUCTION_NODE:
                self._do_pi(child)
            elif child.nodeType == Node.COMMENT_NODE:
                self._do_comment(child)
	    elif child.nodeType == Node.DOCUMENT_TYPE_NODE:
		pass
            else:
                raise TypeError, \
		    'Unrecognized NodeType Child of DOCUMENT node (%d).' % \
		    child.nodeType
    handlers[Node.DOCUMENT_NODE] =_do_document


    def _do_text(self, node):
        '''_do_text(self, node) -> None'''
        if self.subset and node not in self.subset: return
        s = node.data \
                .replace("&", "&amp;") \
                .replace("<", "&lt;") \
                .replace(">", "&gt;") \
                .replace("\015", "&#xD;")
        if self.stripspace:
            for pat,repl in _implementation.repats: s = re.sub(pat, repl, s)
        if s: self.write(s)
    handlers[Node.TEXT_NODE] =_do_text
    handlers[Node.CDATA_SECTION_NODE] =_do_text


    def _do_pi(self, node):
        '''_do_pi(self, node) -> None
        Process a PI node. Render a leading or trailing #xA if the
        document order of the PI is greater or lesser (respectively)
        than the document element.
        '''
        if self.subset and node not in self.subset: return
        W = self.write
        if self.documentOrder == _GreaterElement: W('\n')
        W('<?')
        W(node.nodeName)
        s = node.data
        if s:
            W(' ')
            W(s)
        W('?>')
        if self.documentOrder == _LesserElement: W('\n')
    handlers[Node.PROCESSING_INSTRUCTION_NODE] = _do_pi


    def _do_comment(self, node):
        '''_do_comment(self, node) -> None
        Process a comment node. render a leading or trailing #xA if the
        document order of the comment is greater or lesser (respectively)
        than the document element.
        '''
        if self.subset and node not in self.subset: return
        if self.comments:
            W = self.write
            if self.documentOrder == _GreaterElement: W('\n')
            W('<!--')
            W(node.data)
            W('-->')
            if self.documentOrder == _LesserElement: W('\n')
    handlers[Node.COMMENT_NODE] = _do_comment


    def _do_attr(self, n, value):
        ''''_do_attr(self, node) -> None
        Process an attribute.'''

        W = self.write
        W(' ')
        W(n)
        W('="')
        s = value \
            .replace("&", "&amp;") \
            .replace("<", "&lt;") \
            .replace('"', '&quot;') \
            .replace('\011', '&#x9') \
            .replace('\012', '&#xA') \
            .replace('\015', '&#xD')
        W(s)
        W('"')


    def _do_element(self, node, initialattrlist = []):
        '''_do_element(self, node, initialattrlist = []) -> None
        Process an element (and its children).'''

        name = node.nodeName
        W = self.write
##        print "########", name

        # Get parent namespace, make a copy for us to inherit.
        parent_ns = self.ns_stack[-1]
        my_ns = parent_ns.copy()

        # Get which ns's have already been rendered
        rendered_ns = self.rendered_ns_stack[-1].copy()
##        print "         rendered_ns", rendered_ns

        # If not exclusive c14n, get ancestor XMLNS.XML
        # elements not yet rendered
        if self.exclusive:
            xml_attrs = []
        else:        
            xml_attrs = self.xml_attrs_stack[-1][:]
            
        # Divide attributes into NS definitions and others.
        nsnodes, others = [], initialattrlist[:]
        for a in _attrs(node):
            if a.namespaceURI == XMLNS.BASE:
                nsnodes.append(a)   # Add to ns nodes list
            elif a.namespaceURI == XMLNS.XML:
                xml_attrs.append(a) # Add to an XML attribute list
            else:
                others.append(a)    # Add to orindary attribute list

        # Update my_ns dictionary based on nsnodes
        for a in nsnodes:
            n = a.nodeName

            # 'if' fixes a DOM implementaiton error
            if n == "xmlns:": n = "xmlns"

            # Create/rewrite my_ns[n] with new values
            v = my_ns[n] = a.nodeValue

            # Set rendered state for new nodes
            if rendered_ns.get(n,None) == None:
                rendered_ns[n] = _NotRendered

        # Serialize the nodeset
        if not self.subset or node in self.subset:
            W('<')
            W(name)

            # Create list of nodes to render: render_ns_nodes
            render_ns_nodes = []
##            print "@@ my_ns.items() is", my_ns.items()
            for (n,v) in my_ns.items():
##                print "@@ (n,v) is", (n,v), "rendered_ns[n]", rendered_ns[n]
                pval = parent_ns.get(n, None)
##                print "   pval is", pval

                # Default namespace is empty, skip
                if n == "xmlns" and v in [ XMLNS.BASE, '' ] \
                and pval in [ XMLNS.BASE, '' ] \
                and rendered_ns[n] == _Rendered:
##                    print "   passing"
                    pass
                # If different from parent, or parent didn't render
                elif v != pval or rendered_ns[n] == _NotRendered:
##                    print "   checking to see if utilized"
                    # If ns is used within node, or unsuppressed
                    if not self.exclusive or \
                           _utilized((n,v), node, others, self.unsuppressedPrefixes):
##                        print "appending", (n,v), "on render_ns_nodes"
                        render_ns_nodes.append((n,v))
                        rendered_ns[n] = _Rendered
                    else:
                        rendered_ns[n] = _NotRendered
                        
            # Sort and render the render_ns_nodes
            render_ns_nodes.sort(_sorter_ns)
            for (n,v) in render_ns_nodes:
                self._do_attr(n, v)
                
            # Other attributes: sort and output.
            others += xml_attrs # Join others with xml:XXX
            xml_attrs = []      # Don't pass to children
            others.sort(_sorter)
            for a in others:
                self._do_attr(a.nodeName, a.value)
            W('>')

        # Append ns, rendered_ns, and xml_attrs (empty if rendered) onto the stack 
        self.ns_stack.append(my_ns)
        self.xml_attrs_stack.append(xml_attrs)
        self.rendered_ns_stack.append(rendered_ns)

        for c in _children(node):
            _implementation.handlers[c.nodeType](self, c)

        self.ns_stack.pop()
        self.rendered_ns_stack.pop()
        self.xml_attrs_stack.pop()

        if not self.subset or node in self.subset: W('</%s>' % name)
    handlers[Node.ELEMENT_NODE] = _do_element

def Canonicalize(node, output=None, **kw):
    '''Canonicalize(node, output=None, **kw) -> UTF-8

    Canonicalize a DOM document/element node and all descendents.
    Return the text; if output is specified then output.write will
    be called to output the text and None will be returned
    Keyword parameters:
        stripspace: (Salz) remove extra (almost all) whitespace from
                text nodes
        nsdict: (Salz) a dictionary of prefix:uri namespace entries
                assumed to exist in the surrounding context
        comments: (Salz) keep comments if non-zero (default is '0')
        subset: Canonical XML subsetting resulting from XPath
                (default is [])
        exclude: exclusive canonicalization (default is '0')
        unsuppressedPrefixes: prefixes that should be inherited
                despite exclusive canonicalization.
    '''

    if not output: s = StringIO.StringIO()

    _implementation(node,
        (output and output.write) or s.write,
        nsdict=kw.get('nsdict', {}),
        stripspace=kw.get('stripspace', 0),
        comments=kw.get('comments', 0),
        subset=kw.get('subset', []),
        exclusive=kw.get('exclusive', 0),
        unsuppressedPrefixes=kw.get('unsuppressedPrefixes', [])
    )

    if not output: return s.getvalue()

