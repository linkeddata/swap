#! /usr/bin/python
#
#   A parser for XML built on the xmllib XML parser.
#   Hacked down from Dan Connolly's RDF parser which is much more complicated!
#   To do:
#         Option of ordered listing with daml list of children  and/or attrs!!
#         Option of replacing ln and ns with rdf:type ns#e_ln and ns#a_ln - see TAG issue (6?)
#         maybe think about some real connection to XPath or infoset models and vocabulary

import xmllib  # Comes with python 1.5 and greater
import notation3 # http://www.w3.org/2000/10/swap/notation3.py
import urlparse  # Comes with python 1.6, lacks file<->url mapping
import urllib   # Opening resources in load()
import string
# States:

STATE_NOT_RDF =     "not RDF"     # Before <rdf:RDF>
STATE_NO_SUBJECT =  "no context"  # @@@@@@@@@ use numbers for speed
STATE_DESCRIPTION = "Description (have subject)" #
STATE_LITERAL =     "within literal"
STATE_VALUE =       "plain value"
STATE_NOVALUE =     "no value"
STATE_LIST =        "within list"

SYMBOL = notation3.SYMBOL
LITERAL = notation3.LITERAL

RDF_NS_URI = notation3.RDF_NS_URI # As per the spec
RDF_Specification = "http://www.w3.org/TR/REC-rdf-syntax/" # Must come in useful :-)
DAML_ONT_NS = "http://www.daml.org/2000/10/daml-ont#"  # DAML early version
DPO_NS = "http://www.daml.org/2001/03/daml+oil#"  # DAML plus oil
chatty = 0

RDF_IS = SYMBOL, RDF_NS_URI + "is"   # Used with quoting

NS= "http://www.w3.org/2000/10/swap/xml-unordered#"  # Unordered representation of XML document


class RDFXMLParser(xmllib.XMLParser):

    def __init__(self, sink, thisURI, **kw):
        self.testdata = ""
        apply(xmllib.XMLParser.__init__, (self,), kw)
        self._stack =[]  # Stack of states

        self.sink = sink
        self._thisURI = thisURI
        self._state = STATE_NOT_RDF  # Maybe should ignore RDF poutside <rdf:RDF>??
        self._context = thisURI + "#_formula"  # Context of current statements, change in bags
        self._formula = SYMBOL, self._context
        self._subject = None
        self._predicate = None
        self._genPrefix = "#_g"    # @@@ allow parameter override
        self._nextId = 0        # For generation of arbitrary names for anonymous nodes
        self._data = ""
        self.sink.startDoc()
        version = "$Id$"
        self.sink.makeComment("RDF parsed by "+version[1:-1])

        self._root = self._generate("doc")
        self._cursor = self._root
        self.sink.bind("x", (SYMBOL, NS))        


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
        #self.sink.makeComment('xml parse: encoding ='+`encoding`+'standalone ='+`standalone`)

    def handle_doctype(self, tag, pubid, syslit, data):
        doctype = self._generate("doctype")
        self.sink.makeStatement(( (SYMBOL, self._context),
                                  (SYMBOL, NS+"doctype"),
                                  (SYMBOL, self._root),
                                  (SYMBOL, doctype) ))
        
        if pubid:
            self.sink.makeStatement(( (SYMBOL, self._context),
                                  (SYMBOL, NS+"pubid"),
                                  (SYMBOL, doctype),
                                  (LITERAL, pubid) ))
        if syslit:
            self.sink.makeStatement(( (SYMBOL, self._context),
                                  (SYMBOL, NS+"systemid"),
                                  (SYMBOL, doctype),
                                  (LITERAL, syslit) ))
        if data:
            self.sink.makeStatement(( (SYMBOL, self._context),
                                  (SYMBOL, NS+"data"),
                                  (SYMBOL, doctype),
                                  (LITERAL, syslit) ))
        self.flush()
        #self.sink.makeComment('DOCTYPE:' +tag + `data`)

    def handle_data(self, data):
        self._data = self._data + data

    def handle_cdata(self, data):
        if data:
            self.sink.makeStatement(( (SYMBOL, self._context),
                                  (SYMBOL, NS+"cdata"),
                                  (SYMBOL, self._cursor),
                                  (LITERAL, data) ))
        
    def flush(self):
        if self._data:
            self.sink.makeStatement(( (SYMBOL, self._context),
                                  (SYMBOL, NS+"data"),
                                  (SYMBOL, self._cursor),
                                  (LITERAL, self._data) ))
            self._data = ""
        return

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
        
#        self.sink.makeComment(data)    An alternative.

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
            "The string is just a debugging hint really"
            generatedId = self._genPrefix + str + `self._nextId`  #
            self._nextId = self._nextId + 1
            self.pso(notation3.N3_forSome_URI, self._context, generatedId) #  Note this is anonymous node
            return generatedId                

    def unknown_starttag(self, tag, attrs):
        """ Handle start tag. We register none so all are unknown
        """
        element = self._generate("e")
        self.pso(NS+"child", self._cursor, element)
        self._stack.append(self._cursor)
        self._cursor = element

        x = string.find(tag, " ")
        if x>=0:
            ns = tag[:x]
            ln = tag[x+1:]
        else:
            ln = tag
            ns = ""      # Can't use none! Could use a rdf:type
        self.psv(NS+"ln", element, ln)
        self.psv(NS+"ns", element, ns)

        for name, value in attrs.items():
            x = string.find(name, " ")
            if x>=0:
                ns = name[:x]
                ln = name[x+1:]
            else:
                ln = name
                ns = ""      # Can't use none! Could use a rdf:type
            a = self._generate("a")
            self.pso(NS+"attr", self._cursor,a)
            self.psv(NS+"ln", a, ln) 
            self.psv(NS+"ns", a, ns)
            self.psv(NS+"value",a,value)


        
    def unknown_endtag(self, tag):
        self.flush()
        self._cursor =  self._stack.pop()

    def unknown_entityref(self, ref):
        pass

    def unknown_charref(self, ref):
        pass
    
    def close(self):
        xmllib.XMLParser.close(self)
        self.sink.endDoc(self._formula)

#  Internal methods to generate triples in destination formula

    def pso(self, pred, subj, obj):
        return self.sink.makeStatement(( (SYMBOL, self._context),
                                  (SYMBOL, pred),
                                  (SYMBOL, subj),
                                  (SYMBOL, obj) ))
        
    def psv(self, pred, subj, obj):
        return self.sink.makeStatement(( (SYMBOL, self._context),
                                  (SYMBOL, pred),
                                  (SYMBOL, subj),
                                  (LITERAL, obj) ))
    
def test(args = None):
    import sys, getopt
    from time import time

    if not args:
        args = sys.argv[1:]

    opts, args = getopt.getopt(args, 'st')
    klass = RDFXMLParser
    do_time = 0
    for o, a in opts:
        if o == '-s':
            klass = xmllib.XMLParser
        elif o == '-t':
            do_time = 1

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

    x = klass(notation3.ToN3(sys.stdout.write), "file:/test.rdf") # test only!
    t0 = time()
    try:
        if do_time:
            x.feed(data)
            x.close()
        else:
            for c in data:
                x.feed(c)
            x.close()
    except RuntimeError, msg:
        t1 = time()
        print msg
        if do_time:
            print 'total time: %g' % (t1-t0)
        sys.exit(1)
    t1 = time()
    if do_time:
        print 'total time: %g' % (t1-t0)


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






    
