#!/usr/bin/env python
"""

still pretty drafty, but it works on
test/stripe-skipping/[1-4].xml

just runs standalone now, and just writes to
one particular sink.  needs reworking on that
front.

   @@@ switch to Span objects with plain literal values, for all
   character content.

      Leaf elements have a .text which is a str lit
      Tree elements have first/rest which are trees or leaves.

      Nah, use literals directly...

  DO use   <author><sandro/></author>
   
"""
__version__ = "$Revision$"
# $Id$

import sys
import inspect
import re
import xml.sax
from NTriplesSink import FormulaSink

class Error(RuntimeError):
   pass

################################################################

## counter = 1

## def Class(uri=None):
##     global counter
##     result = "_:g" + str(counter)
##     counter += 1
##     if uri:
##         print "("+result+" rdf:type <"+uri+">)"
##     return result

## def Property(uri=None):
##     return "[has "+str(uri)+"]"

## class Sink:
##     def add(self, *arg):
##         print arg



#
#

class docHandler(xml.sax.ContentHandler):

    """

    Parse an XML file into triples of URIs and bNodes.  No literals.
    Plain string literals are turned into rdf:List objects containing
    the characters, where each character is identified by a URI.  This
    allows markup to be mixed into the strings.

    An XML element whose name (after ns prefix) starts with an uppercase letter is
    taken to stand for an individual instance of the class named by the element.

    An XML element whose name (after ns prefix) starts with a lowercase letter is:
       * if no child elements of or text content:   <unknown>
       * if exactly one child or one text char: a property linking to that
         element
       * if more than one: a property linking to an rdf:List of those elements


    """
    def __init__(self):
        self.sink = FormulaSink()
        self.document = self.sink.termFor(uri="")
        self.parents = [ "root", self.document ]
        self.parentsLenStack = []
        self.expectingIndividual = 1
        self.rdftype = self.sink.termFor(uri="http://...#type")
        self.rdfli = self.sink.termFor(uri="http://...#li")
        self.awaitingFirstValue = 0
        self.firstValueBuffer = None

    def instanceOf(self, uri=None):
        result = self.sink.termFor();
        if uri is not None:
            self.sink.insert((result, self.rdftype, self.sink.termFor(uri=uri)))
        return result

    def startElementNS(self, name, qname, attrs):
        self.parentsLenStack.insert(0, len(self.parents))
        
        if name[0].endswith("/") or name[0].endswith("#"):
            uri = name[0] + name[1]
        else:
            uri = name[0] + "/" + name[1]

        char1 = name[1][0:1]
        if char1.isupper():
            self.prepareForIndividual()
            me = self.instanceOf(uri)
            self.gotIndividual(me)
            self.parents.insert(0, me)
        elif char1.islower():
            self.prepareForProperty()
            me = self.sink.termFor(uri=uri)
            self.parents.insert(0, me)
            self.awaitingFirstValue = 1
        else:
            raise RuntimeError, "not upper or lower?"

    def prepareForIndividual(self):
        if len(self.parents) % 2 == 1:
            print "# need to infer a property stripe"
            self.parents.insert(0, self.rdfli)

    def prepareForProperty(self):
        if len(self.parents) % 2 == 0:
            print "# need to infer an individual stripe"
            i = self.instanceOf()
            self.parents.insert(0, i)
            self.sink.insert((self.parents[2], self.parents[1], self.parents[0]))

    def endElementNS(self, name, qname):
        if self.awaitingFirstValue:
            raise Error, "property with no value given"   # use this syntax for named things?
        if self.firstValueBuffer is not None:
            self.sink.insert((self.parents[1], self.parents[0], self.firstValueBuffer))
            self.firstValueBuffer = None
        finalLen = self.parentsLenStack[0]
        del self.parentsLenStack[0]
        while len(self.parents) > finalLen:
            del self.parents[0]
        
    def characters(self, content):
        self.prepareForIndividual()
        #for char in content:
        #    self.gotIndividual(self.sink.termFor(char))
        self.gotIndividual(self.sink.termFor(content))
        # append it to the string buffer, which gets
        # converted at the end or next individual.

    def gotIndividual(self, term):
        if self.awaitingFirstValue:
            self.awaitingFirstValue = 0
            self.firstValueBuffer = term
            return
        
        if self.firstValueBuffer is not None:
            # we have multiple values; we need a list!
            self.prepareForProperty()   # say it's a List?
            self.prepareForIndividual()
            self.sink.insert((self.parents[1], self.parents[0], self.firstValueBuffer))
            self.firstValueBuffer = None

        self.sink.insert((self.parents[1], self.parents[0], term))
            

if __name__ == '__main__':
    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, 1)
    dh = docHandler()
    parser.setContentHandler(dh)
    parser.parse(sys.stdin)

   
#if __name__ == "__main__":
#    import doctest, sys
#    doctest.testmod(sys.modules[__name__])

# $Log$
# Revision 1.3  2003-08-01 15:35:03  sandro
# added some comments
#
# Revision 1.2  2003/04/04 12:52:10  sandro
# added quoting of newlines
# made characters be RDF literals, grouped together
#
# Revision 1.1  2003/04/03 21:55:06  sandro
# First cut prototype of a parser which reads plain XML as if it were RDF.
#
