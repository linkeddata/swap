#! /usr/bin/python
#
#   A parser for RDF/XML built on the xmllib XML parser.
#
#  To do: Passing on namesapce bindings!
#

import xmllib  # Comes with python 1.5 and greater
import notation3 # http://www.w3.org/2000/10/swap/notation3.py
import urlparse  # Comes with python 1.6, lacks file<->url mapping
import urllib   # Opening resources in load()
import string
# States:

STATE_NOT_RDF = "not RDF"   # Before <rdf:RDF>
STATE_NO_CONTEXT = "no context"  # @@@@@@@@@ use numbers for speed
STATE_DESCRIPTION = "Description (have subject)" #
STATE_LITERAL = "within literal"
STATE_VALUE = "plain value"
STATE_NOVALUE = "no value"
STATE_LIST =    "within list"

RESOURCE = notation3.RESOURCE
LITERAL = notation3.LITERAL

RDFNS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#" # As per the spec
RDF_Specification = "http://www.w3.org/TR/REC-rdf-syntax/" # Must come in useful :-)
DAML_ONT_NS = "http://www.daml.org/2000/10/daml-ont#"  # 
chatty = 0

class RDFXMLParser(xmllib.XMLParser):

    def __init__(self, sink, thisURI, **kw):
        self.testdata = ""
        apply(xmllib.XMLParser.__init__, (self,), kw)
        self._stack =[]  # Stack of states

        self.sink = sink
        self._thisURI = thisURI
        self._state = STATE_NOT_RDF  # Maybe should ignore RDF poutside <rdf:RDF>??
        self._context = thisURI         # Context of current statements, change in bags
        self._subject = None
        self._predicate = None
        self._genPrefix = "#_g"    # @@@ allow parameter override
        self._nextId = 0        # For generation of arbitrary names for anonymous nodes
        self.sink.startDoc()
        self.sink.makeComment("RDF parsed by $Id$")


    def load(self, uri, _baseURI=""):
        if uri:
            _inputURI = urlparse.urljoin(_baseURI, uri) # Make abs from relative
            print "# Input from ", _inputURI
            netStream = urllib.urlopen(_inputURI)
            self.feed(netStream.read())     # @ May be big - buffered in memory!
            self.close()
        else:
            print "# Taking N3 input from standard input"
            _inputURI = urlparse.urljoin(_baseURI, "STDIN") # Make abs from relative
            self.feed(sys.stdin.read())     # May be big - buffered in memory!
            self.close()


    def handle_xml(self, encoding, standalone):
        self.flush()
        print 'xml: encoding =',encoding,'standalone =',standalone

    def handle_doctype(self, tag, pubid, syslit, data):
        self.flush()
        print 'DOCTYPE:',tag, `data`

    def handle_data(self, data):
        if self._state == STATE_VALUE:
            self.testdata = self.testdata + data
        

    def flush(self):
        data = self.testdata
        if data:
            self.testdata = ""
            print '# flushed data:', `data`

    def handle_cdata(self, data):
        self.flush()
        print 'cdata:', `data`

    def handle_proc(self, name, data):
        self.flush()
        print 'processing:',name,`data`

    def handle_comment(self, data):
        self.flush()
        self.sink.makeComment(data)

    def syntax_error(self, message):
        print 'error at line %d:' % self.lineno, message

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

    def idAboutAttr(self, attrs):  #6.5
        """ set up subject and maybe context from attributes
        """
        self._subject = None
        self._state = STATE_DESCRIPTION
        self._subject = None

        for name, value in attrs.items():
            x = string.find(name, " ")
            if x>=0: name=name[x+1:]    # Strip any namespace on attributes!!! @@@@
            if name == "ID":
                if self._subject:
                    print "# oops - subject already", self._subject
                    raise syntaxError # ">1 subject"
                self._subject = self.uriref("#" + value)
            elif name == "about":
                if self._subject: raise syntaxError # ">1 subject"
                self._subject = self.uriref(value)
            elif name == "aboutEachPrefix":
                if value == " ":  # OK - a trick to make NO subject
                    self._subject = None
                else: raise ooops # can't do about each prefix yet
            if name == "bagid":
                c = self._context
                self._context = self.uriref("#" + value)
                if 0: self.sink.makeStatement((  # Note lexical nesting
                    (RESOURCE, c),                                 
                    (RESOURCE, notation3.N3_subExpression_URI),
                    (RESOURCE, c),
                    (RESOURCE, self._context) ))

        if self._subject == None:
            self._subject = self._generate()

            
    def _generate(self):
            generatedId = self._genPrefix + `self._nextId`  #
            self._nextId = self._nextId + 1
            self.sink.makeStatement(( (RESOURCE, self._context),                                 
                                      (RESOURCE, notation3.N3_forSome_URI),
                                      (RESOURCE, self._context),
                                      (RESOURCE, generatedId) )) #  Note this is anonymous node
            return generatedId

    def _obj(self, tagURI, attrs):  # 6.2
            if tagURI == RDFNS + "Description":
                self.idAboutAttr(attrs)  # Set up subject and context                

            elif ( tagURI == RDFNS + "Bag" or  # 6.4 container :: bag | sequence | alternative
                   tagURI == RDFNS + "Alt" or
                   tagURI == RDFNS + "Seq"):
                raise unimplemented
            else:  # Unknown tag within STATE_NO_CONTEXT: typedNode #6.13
                c = self._context   # (Might be change in idAboutAttr)
                self.idAboutAttr(attrs)
                if c == None: raise roof
                if self._subject == None:raise roof
                self.sink.makeStatement((  (RESOURCE, c),
                                      (RESOURCE, RDFNS+"Type"),
                                      (RESOURCE, self._subject),
                                      (RESOURCE, tagURI) ))
                self._state = STATE_DESCRIPTION
                

    def unknown_starttag(self, tag, attrs):
        """ Handle start tag. We register none so all are unknown
        """
        self.flush()
        
        tagURI = self.tag2uri(tag)

        if chatty:
            if not attrs:
                print '# State =', self._state, 'start tag: <' + tagURI + '>'
            else:
                print '# state =', self._state, 'start tag: <' + tagURI,
                for name, value in attrs.items():
                    print "    " + name + '=' + '"' + value + '"',
                print '>'


        self._stack.append([self._state, self._context, self._predicate, self._subject])

        if self._state == STATE_NOT_RDF:
            if tagURI == RDFNS + "RDF":
                self._state = STATE_NO_CONTEXT
                
                # HACK @@ to grab prefixes
                nslist = self._XMLParser__namespaces.items()
                for t, d, nst in self.stack:     # Hack
                    nslist = nslist + d.items()
  #              print "### Namespaces: ", `nslist`
                for prefix, nsURI in nslist:
                    if nsURI:
                        self.sink.bind(prefix, (RESOURCE, nsURI))
                    
            else:
                pass                    # Some random XML

        elif self._state == STATE_NO_CONTEXT:  # 6.2 obj :: desription | container
            self._obj(tagURI, attrs)
            
        elif self._state == STATE_DESCRIPTION:   # Expect predicate (property) PropertyElt
            self._predicate = tagURI # Declaration by class name [ a my:class ;... ]
            self._state = STATE_VALUE  # Propably looking for value but see parse type
            self.testdata = ""         # Flush value data
            
            # print "\n  attributes:", `attrs`

            for name, value in attrs.items():
                x = string.find(name, " ")
                if x>=0: name=name[x+1:]    # Strip any namespace on attributes!!! @@@@
                if name == "id":
                    print "# Warning: id=%s on <%s...> ignored" %  (value,) # Meaning?
                elif name == "parseType":
                    if value == "Literal":
                        self._state = STATE_LITERAL # That's an XML subtree not a string
                    elif value == "Resource":
                        c = self._context
                        s = self._subject
                        self.idAboutAttr(attrs)  # set subject and context for nested description
                        self.sink.makeStatement(( (RESOURCE, c),
                                                  (RESOURCE, self._predicate),
                                                  (RESOURCE, s),
                                                  (RESOURCE, self._subject) ))
                        self._state = STATE_DESCRIPTION  # Nest description
                    elif value[-11:] == ":collection":  # Is this a daml:collection qname?
                        pref = value[:-11]
                        nslist = self._XMLParser__namespaces.items()
                        for t, d, nst in self.stack:     # Hack - look inside parser
                            nslist = nslist + d.items()
                        for p, nsURI in nslist:
                            if p == pref and  nsURI == DAML_ONT_NS: 
                                self._state = STATE_LIST  # Linked list of obj's

                elif name == "resource":
                    self.sink.makeStatement(((RESOURCE, self._context),
                                             (RESOURCE, self._predicate),
                                             (RESOURCE, self._subject),
                                             (RESOURCE, self.uriref(value)) ))
                    self._state = STATE_NOVALUE  # NOT looking for value
                elif name == "value":
                    self.sink.makeStatement(((RESOURCE, self._context),
                                             (RESOURCE, self._predicate),
                                             (RESOURCE, self._subject),
                                             (LITERAL,  value) ))
                    self._state = STATE_NOVALUE  # NOT looking for value
                    
        elif self._state == STATE_LIST:   # damlCollection :: objs - make list
            # Subject and predicate are set and dangling. 
            c = self._context
            s = self._subject  # The tail of the list so far
            p = self._predicate
            pair = self._generate()        # The new pair
            self.sink.makeStatement(( (RESOURCE, c),   # Link in new pair
                                      (RESOURCE, p),
                                      (RESOURCE, s),
                                      (RESOURCE, pair) )) 
            self.idAboutAttr(attrs)  # set subject (the next item) and context 
            self.sink.makeStatement(( (RESOURCE, c),
                                      (RESOURCE, DAML_ONT_NS + "first"),
                                      (RESOURCE, pair),
                                      (RESOURCE, self._subject) )) # new item
            
            self._stack[-1][2] = DAML_ONT_NS + "rest"  # Leave dangling link
            self._stack[-1][3] = pair  # Underlying state tracks tail of growing list

         
        elif self._state == STATE_VALUE:   # Value :: Obj in this case # 6.17  6.2
            c = self._context
            p = self._predicate
            s = self._subject
            self._obj(tagURI, attrs)   # Parse the object thing's attributes
            self.sink.makeStatement(( (RESOURCE, c), # Link to new object
                                      (RESOURCE, p),
                                      (RESOURCE, s),
                                      (RESOURCE, self._subject) ))
            
            self._stack[-1][0] = STATE_NOVALUE  # When we return, cannot have literal now

        elif self._state == STATE_NOVALUE:
            raise syntaxError # Found tag, expected empty
        else:
            raise internalError # Unknown state

# aboutEachprefix { <#> forall r . { r startsWith ppp } l:implies ( zzz } ) 
# aboutEach { <#> forall r . { ppp rdf:li r } l:implies ( zzz } )

        
    def unknown_endtag(self, tag):
        if self._state == STATE_VALUE:
            buf = ""
            for c in self.testdata:
                if c != "\r": buf = buf + c  # Strip CRs
            self.sink.makeStatement(( (RESOURCE, self._context),
                                       (RESOURCE, self._predicate),
                                       (RESOURCE, self._subject),
                                       (LITERAL,  buf) ))
            self.testdata = ""
            
        elif self._state == STATE_LIST:
            self.sink.makeStatement(( (RESOURCE, self._context),
                                      (RESOURCE, DAML_ONT_NS + "rest"),
                                      (RESOURCE, self._subject),
                                      (RESOURCE, DAML_ONT_NS + "null") ))


        l =  self._stack.pop() # [self._state, self._context, self._subject])
        self._state = l[0]
        self._context = l[1]
        self._predicate = l[2]
        self._subject = l[3]
        self.flush()
        # print '\nend tag: </' + tag + '>'

    def unknown_entityref(self, ref):
        self.flush()
        print '#*** unknown entity ref: &' + ref + ';'

    def unknown_charref(self, ref):
        self.flush()
        print '#*** unknown char ref: &#' + ref + ';'

    def close(self):
        xmllib.XMLParser.close(self)
        self.flush()
        self.sink.endDoc()

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






    
