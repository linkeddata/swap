#! /usr/bin/python
"""
Read an XML file and convert it into an RDF infoset.

Option flags
    u   The XML file if unordered, don't use lists
    s   Strip spaces from element data
"""
#import xmllib  # Comes with python 1.5 and greater
from swap import notation3 # http://www.w3.org/2000/10/swap/notation3.py

import urlparse  # Comes with python 1.6, lacks file<->url mapping
import urllib   # Opening resources in load()
import string
import xml  # python 2.0 and greater

# States:

List_NS = notation3.List_NS
#from notation3 import List_NS

SYMBOL = notation3.SYMBOL
LITERAL = notation3.LITERAL

RDF_NS_URI = notation3.RDF_NS_URI # As per the spec
RDF_Specification = "http://www.w3.org/TR/REC-rdf-syntax/" # Must come in useful :-)
DAML_ONT_NS = "http://www.daml.org/2000/10/daml-ont#"  # DAML early version
DPO_NS = "http://www.daml.org/2001/03/daml+oil#"  # DAML plus oil
chatty = 0

RDF_IS = SYMBOL, RDF_NS_URI + "is"   # Used with quoting

NS= "http://www.w3.org/2000/10/swap/xml#"  # Representation of XML document


from swap.notation3 import stringToN3
class streamSink():
    """This accepts some of the methods of a store, streams a single graph in N3 
    for speed. Uses N3's large strngs.
    """
    def __init__(self, ostream):
        self.stream = ostream;
        self.w = ostream.write;
        self.nextId = 0
        
    def bind(self,  prefix, ns):
        self.w('@prefix '+prefix+': <'+ns+'>.\n');
        return
        
    def startDoc(self):
        pass

    def endDoc(self):
        self.w('# ends\n');

    def newSymbol(self, uri):
        return '<' + uri + '>';
        
    def newLiteral(self, value):
        return stringToN3(value);

    def newBlankNode(self, s):
        if s: return '_:'+s;
        self.nextId += 1
        return '_:a%i' % self.nextId

    def newFormula(self,s):
        return ""; # This is only turtle

    def makeStatement(self, context, p, s, o):
        self.w(s + ' ' + p + ' ' + o + '.\n');
        return

# class XMToRDFInfoset(xmllib.XMLParser):
class XMToRDFInfoset(xml.sax.handler.ContentHandler):

#    def __init__(self, sink, thisURI, unordered = 0, **kw):

    def __init__(self, store,  thisDoc="", baseURI=None,
                 genPrefix = "", metaURI=None, flags="",
                 why=None, **kw):
        self.testdata = ""
        openFormula = None
        #apply(xmllib.XMLParser.__init__, (self,), kw)
        self._stack =[]  # Stack of states

        self._flags = flags
#        if thisDoc != "":
#            assert ':' in thisDoc, "Document URI not absolute: <%s>" % thisDoc
#           self._bindings[""] = thisDoc + "#"  # default

        self._store = store
        self._formula = store.newFormula()
        self._storeContext = self._formula
        self._context = self._formula
 
        self._thisURI = thisDoc
#        self._context = thisDoc + "#_formula"  # Context of current statements, change in bags
#        self._formula = SYMBOL, self._context
        self._subject = None
        self._predicate = None
        self._genPrefix = "#_g"    # @@@ allow parameter override
        self._nextId = 0        # For generation of arbitrary names for anonymous nodes
        self._data = ""
        self._store.startDoc()
        # version = "$Id$"

        self._root = self._generate("doc")
        self._cursor = self._root
        self._children = None
        self._store.bind("x", NS)
        self.unordered = ('u' in flags)
        self.strip = ('s' in flags)
        self.arcs = ('a' in flags)
        self.ns = {}

    def load(self, uri, _baseURI=""):
        if uri:
            _inputURI = urlparse.urljoin(_baseURI, uri) # Make abs from relative
            netStream = urllib.urlopen(_inputURI)
            self.feed(netStream.read())     # @ May be big - buffered in memory!
            self.close()
        else:
            _inputURI = urlparse.urljoin(_baseURI, "STDIN") # Make abs from relative
            self.feed(sys.stdin.read())     # May be big - buffered in memory!
            self.close()


    def handle_xml(self, encoding, standalone):
        self.flush()

    def handle_doctype(self, tag, pubid, syslit, data):
        doctype = self._generate("doctype")
        self._store.makeStatement(( self._context,
                                  self._store.newSymbol(NS+"doctype"),
                                  self._root,
                                  doctype))
        
        if pubid:
            self._store.makeStatement(( self._context,
                                  self._store.newSymbol(NS+"pubid"),
                                  doctype,
                                 self._store.newLiteral(pubid)))
        if syslit:
            self._store.makeStatement(( self._context,
                                  self._store.newSymbol(NS+"systemid"),
                                  doctype,
                                 self._store.newLiteral(syslit) ))
        if data:
            self._store.makeStatement(( self._context,
                                  self._store.newSymbol(NS+"data"),
                                  doctype,
                                 self._store.newLiteral(data) ))
        self.flush()
        #self.sink.makeComment('DOCTYPE:' +tag + `data`)

    def handle_data(self, data):
        self._data = self._data + data

    def handle_cdata(self, data):
        self._cdata = self._data + data  # Not sure how this works -tbl
        
    def flush(self):
        if self._data:
            if self.strip:
                self._data = self._data.strip()
            if self.unordered:
                if len(self._data) > 0:
                    self.psv(NS+"zdata", self._cursor, self._data)
            else:
                item = self._generate("i")
                self.psv(List_NS+"first", item, self._data)
                if self._children == None:
                    self.pso(NS+"zcontent", self._cursor, item)
                else:
                    self.pso(List_NS+"rest", self._children, item)
                self._children = item
            self._data = ""

    def handle_proc(self, name, data):
        pi = self._generate("pi")
        self.pso(NS+"pi", self._root, doctype)
        self.psv(NS+"name", pi, name)
        if syslit:
            self.psv(NS+"data", pi, data)
        if data:
            self.psv(NS+"data", doctype, syslit)

    def handle_comment(self, data):
        self.psv(NS+"comment", self._cursor, data)
    
    ######################### SAX
    
    def startDocument(self):
        # print "start"
        return
        
    def endDocument(self):
        return
        
    def startPrefixMapping(self, prefix, uri):
        self.ns[prefix] = uri #  @@@ no scoping -- ok for top-level only
        return

    def endPrefixMapping(self, prefix):
        return

    def startElement(self, name, attrs):   # @@ convert attrs?
        # print "start element: "+name

        return self.unknown_starttag(name, attrs)

    def endElement(self, name):
        return self.unknown_endtag(name);

    # name parameter contains the name of the element type as a (uri, localname) tuple, 
    # qname parameter contains the raw XML 1.0 name used in the source document, and
    # attrs parameter holds an instance of the AttributesNS interface

    def startElementNS(self, name, attrs):   # @@ convert attrs?
        return self.unknown_starttag(name, attrs)

    def endElementNS(self, name):
        return self.unknown_endtag(name);

    def characters(self, content):
        return self.handle_data(content)
        
    def ignorableWhitespace(self, whitespace):
        return
        
    def processingInstruction(self, target, data):
        return

    def skippedEntity(self, name):
        return
        

    ##################
    
    def error(self, e):
        print "@@@ Error:"+e
        return

    def fatalError(self, e):
        print "@@@ Error:"+e
        return

    def warning(self, e):
        print "@@@ Error:"+e
        return

    ###################

    def unknown_starttag(self, tag, attrs):
        """ Handle start tag. We register none so all are unknown
        """
        element = self._generate("e")

        x = string.find(tag, " ")
        if x>=0:
            ns = tag[:x]
            ln = tag[x+1:]
        else:
            ln = tag
            ns = ""      # Can't use none! Could use a rdf:type
        if 1: #not self.arcs:
            self.psv(NS+"ln", element, ln)
            if (ns): self.psv(NS+"ns", element, ns)

        if (self.arcs):
            p = self._store.newSymbol(NS+ tag)
            self.pso(p, self._cursor, element)
            self._stack.append(self._cursor)
        elif self.unordered:
            self.pso(NS+"child", self._cursor, element)
            self._stack.append(self._cursor)
        else:
            item = self._generate("i")
            self.pso(List_NS+"first", item, element)
            if self._children == None:
                self.pso(NS+"zcontent", self._cursor, item)
            else:
                self.pso(List_NS+"rest", self._children, item)
            self._children = item
            self._stack.append((self._cursor, self._children))
            self._children = None
                     
        self._cursor = element

        for name, value in attrs.items():
            x = string.find(name, " ")
            if x>=0:
                ns = name[:x]
                ln = name[x+1:]
            else:
                ln = name
                ns = ""      # Can't use none! Could use a rdf:type
            if (self.arcs):
                if (!ns): ns = NS;
                self.psv(ns + ln, self._cursor, value);
            else:
                a = self._generate("a")
                self.pso(NS+"attr", self._cursor,a)
                self.psv(NS+"ln", a, ln) 
                if ns: self.psv(NS+"ns", a, ns)
                self.psv(NS+"value",a,value)


        
    def unknown_endtag(self, tag):
        self.flush()
        if self.unordered:
            self._cursor =  self._stack.pop()
        else:
            if self._children != None:
                self.pso(List_NS+"rest", self._children, List_NS+"nil")
            else:
                self.pso(NS+"zcontent", self._cursor, List_NS+"nil")
                
            self._cursor, self._children =  self._stack.pop()

    def unknown_entityref(self, ref):
        pass

    def unknown_charref(self, ref):
        pass
    
    def close(self):
        self.flush()
        if self._children:
            self.pso(List_NS+"rest", self._children, List_NS+"nil")
        else:
            self.pso(NS+"zcontent", self._cursor, List_NS+"nil")
        #xmllib.XMLParser.close(self)
        self._store.endDoc(self._formula)


    def syntax_error(self, message):
        raise SyntaxError('error at line %d: %s' % (self.lineno, message))

    def tag2uri(self, str):
        """ Generate URI from tagname
        """
        x = string.find(str, " ")
        if x < 0: return str
        return str[:x]+ str[x+1:]
    
    def uriref(self, str):
        """ Generate uri from uriref in this document
        """ 
        return urlparse.urljoin(self._thisURI,str)

            
    def _generate(self, str=""):
            return  self._formula.newBlankNode();
            
            "The string is just a debugging hint really"
            generatedId = self._genPrefix + str + `self._nextId`  #
            self._nextId = self._nextId + 1
            self.pso(notation3.N3_forSome_URI, self._context, generatedId)
            return generatedId                

    def _blankNode(self, str=""):
        return self._formula.newBlankNode();

#  Internal methods to generate triples in destination formula

    def fix(self, par):
        if type(par) == type('foo'):
            return  self._store.newSymbol(par)
        return par

    def pso(self, pred, subj, obj):
        return self._store.makeStatement((self._storeContext,
                                  self.fix(pred),
                                   self.fix(subj),
                                   self.fix(obj) ))
        
    def psv(self, pred, subj, obj):
        return self._store.makeStatement((self._storeContext,
                                  self.fix(pred),
                                   self.fix(subj),
                                   self._store.newLiteral(obj) ))

##class MySaxErrorHandler(xml.sax.    

def test(args = None):
    import sys, getopt
    from time import time
    from swap import llyn, myStore
    flags = 'usa';

    store = llyn.RDFStore()
    myStore.setStore(store)

    if not args:
        args = sys.argv[1:]

    opts, args = getopt.getopt(args, 'sto:')
    klass = XMToRDFInfoset
    do_time = 0
    for o, a in opts:
        if o == '-s':
            klass = xmllib.XMLParser
        elif o == '-t':
            do_time = 1
        elif o == '-o':
            flags = a
            

    if args:
        file = args[0]
    else:
        file = 'test.xml'

    if file == '-':
        f = sys.stdin
    else:
        try:
            f = open(file, 'r')
        except IOError, msg:
            print file, ":", msg
            sys.exit(1)

    data = f.read()
    if f is not sys.stdin:
        f.close()
    # last boolean is unordered
    handler = klass(store, file, flags = flags)
    t0 = time()

    xml.sax.parseString(data, handler)
    
#    try:
#        if do_time:
#            x.feed(data)
#            x.close()
#        else:
#            for c in data:
#               x.feed(c)
#           x.close()
#    except RuntimeError, msg:
#        t1 = time()
#        print msg
#        if do_time:
#            print 'total time: %g' % (t1-t0)
#        sys.exit(1)
    t1 = time()
    if do_time:
        print 'total time: %g' % (t1-t0)
    # print "#results:"
    print  handler._formula.n3String()

if __name__ == '__main__':
    test()

# References:
#
# How to on xmllib:
# http://www.python.org/doc/howto/xml/node7.html
    
###################################### SAX pointers
# First hit on Python SAX parser
# http://www.gca.org/papers/xmleurope2000/papers/s28-04.html#N84395

# Howto use SAX in python:
# http://www.python.org/doc/howto/xml/SAX.html






    
