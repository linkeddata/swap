#!/usr/bin/env python2.2
"""
Stage 2 of web demo CGI: assumes error handling is set up.

$Id$

TODO:
   + install on swada
   + connect with Notation3.py and llyn
   + safety-ize llyn
   + connect with LX stuff
   + add convenient demo text
   + stylesheet
   + --why
   + switch from html.py to structured hypertext ontology
     and rdfpath
   + dynamically figure out parsers, logics, serializers


note the "think" view, where all inference is just rules;
vs owl-think, etc -- which logics should we use?



  parsers
      list of Parser, each with its documentation, etc,
      which we can display, etc

  reasoners
      where several might have the same code, but use different
      axioms.

  serializers.
  list of Serializers, ...
      
"""
from html import *
import cgi
import sys

parserModules = [ "wrap_n3", "wrap_sax2rdf" ]

def choice(f, modules, title, field):
    
    f << span(title)
    for m in modules
        thisOne = __import__(pm).Parser
        attrs = { "type": "radio", "value":m, "name":field }
        if m == parser:
            attrs["checked"]="yes"
        f << span(input(attrs=attrs), thisOne.name)
    f << br()

    
def main():
    print "Content-Type: text/html"
    print 

    fields = cgi.FieldStorage()

    parser = fields.getfirst("parser", parserModules[0])
    
    d = Document()
    d.head << title("cwm demo")
    d.head << stylelink("http://www.w3.org/2000/10/swap/cwmdemostyle.css")
    #d.head.append(stylelink("file:/home/sandro/0/10/swap/cwmdemostyle.css"))

    d << h1("cwm demo")

    # links to pre-populated demos



    # ask URI or input text
    # ask its Parser
    f = form(method="GET", class_="f")

    f << span("Select input parser:")
    for pm in parserModules:
        thisParser = __import__(pm).Parser
        attrs = { "type": "radio", "value":pm, "name":"parser" }
        if pm == parser:
            attrs["checked"]="yes"
        f << span(input(attrs=attrs), thisParser.name)
    f << br()
        

    f << "Input text:"
    f << br()
    text="Foo!"
    f << textarea(text, cols="80", rows="10", name="input")
    f << br()
    f << "(optional) URI of additional input:"
    f << br()
    f << input(type="text", size="80", name="inputURI1")
    f << br()
    f << "(optional) URI of additional input:"
    f << br()
    f << input(type="text", size="80", name="inputURI2")

    f << span("Select input parser:")
    for pm in parserModules:
        thisParser = __import__(pm).Parser
        attrs = { "type": "radio", "value":pm, "name":"parser" }
        if pm == parser:
            attrs["checked"]="yes"
        f << span(input(attrs=attrs), thisParser.name)
    f << br()

    f << "Optional Filter:"
    f << br()
    text="Foo!"
    f << textarea(text, cols="80", rows="6", name="filter")
    f << br()

    f << span("Select output serializer:")
    for pm in parserModules:
        thisParser = __import__(pm).Parser
        attrs = { "type": "radio", "value":pm, "name":"parser" }
        if pm == parser:
            attrs["checked"]="yes"
        f << span(input(attrs=attrs), thisParser.name)
    f << br()

    f << span(input(type="checkbox", name="raw"),
           "raw output (otherwise pretty-print results below)")

    f << br()
    f << p(input(type="submit", value="Run"))

    f << br()


    d << f

    # flag [ ] raw (to link this)
    # --- output text, if we have values, and stage 2....

    # outout include PROOF link?

    # button for "ADD FILTER EXPRESSION"
    #   (query / transformation rules)

    print d

