"""

Build and output an HTML web page, in a programming style that helps
keep the page well-formed, valid, and generally pleasant.  Why I'm
writing this in 2003 instead of 1993 is anyone's guess.  I must be
bored or procrastinating.

   >>> from html import *
   >>> print span("Hello, World!")
   <span>Hello, World!</span>

span() is just shorthand for Element("span", ...., inline=1)

   >>> print Element("span", "Hello, World!", inline=1)
   <span>Hello, World!</span>

   
The inline=1 keeps the output on the same line, without it we get
newlines before and after the element (and indenting, which we don't
see here).

   >>> print prefixEveryLine("* ", Element("span", "Hello, World!"))
   * 
   * <span>Hello, World!</span>
   * 

The content is often a sequence...

   >>> print Element("span", ["Hello, ", "World!"], inline=1)
   <span>Hello, World!</span>

Attributes are supported, of course...

   >>> e = Element("span", ["Hello, ", "World!"], { "class": "bright" }, inline=1)
   >>> print e
   <span class="bright">Hello, World!</span>

append() appends to the content...

   >>> e.append(" Goodnight, Moon! ")
   >>> print e
   <span class="bright">Hello, World! Goodnight, Moon! </span>

If the content was not a list, append turns it into one, first

   >>> s = span("Hello")
   >>> s.append(", World!")
   >>> print s
   <span>Hello, World!</span>

Elements may be nested, of course...

   >>> e.content = ["Good ", em("Morning"), " Everyone!"]
   >>> print e
   <span class="bright">Good <em>Morning</em> Everyone!</span>

The Document class handle doctype, html/head/body.

   >>> d = Document()
   >>> d.head.append(title("Test Document"))
   >>> d.append(h1("Test Document"))
   >>> print prefixEveryLine("* ", d)
   * <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
   *           "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
   * <html lang="en" xml:lang="en" xmlns="http://www.w3.org/1999/xhtml">
   *   <head>
   *     <title>Test Document</title>
   *   </head>
   * 
   *   <body>
   *     <h1>Test Document</h1>
   *   </body>
   * </html>
   * 

Pseudo-elements using the class= attribute can be handled nicely:

   >>> def StatusParagraph(content, attrs=None):
   ...    e =  p(content, attrs=attrs)
   ...    e.attrs.setdefault('class', 'status')
   ...    return e

   >>> d.body.content[0:0]=[StatusParagraph("This is a Demonstration Document")]
   >>> print prefixEveryLine("* ", d)
   * <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
   *           "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
   * <html lang="en" xml:lang="en" xmlns="http://www.w3.org/1999/xhtml">
   *   <head>
   *     <title>Test Document</title>
   *   </head>
   * 
   *   <body>
   *     <p class="status">This is a Demonstration Document</p>
   *   
   *     <h1>Test Document</h1>
   *   </body>
   * </html>
   * 

.......


Why not use DOM instead?   I dunno.

@@@ needs more content escaping functions, in various places

"""
__version__ = "$Revision$"
# $Id$

import cStringIO

class Streamer:
    """An base class for things which implement writeTo instead of
    __str__."""
    def __str__(self):
        s = cStringIO.StringIO()
        self.writeTo(s)
        return s.getvalue()

class Document(Streamer):

   def __init__(self):
       self.html = Element('html',
                           attrs={ 'xmlns':'http://www.w3.org/1999/xhtml',
                                   'lang':'en', 'xml:lang':'en' })
       self.head = Element('head')
       self.html.append(self.head)
       self.body = Element('body')
       self.html.append(self.body)

   def writeTo(self, s):
       s.write('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"\n')
       s.write('          "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">')
       self.html.writeTo(s)

   def append(self, content):
       return self.body.append(content)
    

class Element(Streamer):

    def __init__(self, tag, content=None, attrs=None, inline=0):
        self.tag=tag
        self.content=content
        self.attrs=attrs
        if self.attrs is None: self.attrs = {}
        self.inline = inline

    prefixLength = 2

    def writeTo(self, s, prefix=""):
        if not self.inline:
            s.write("\n")
            s.write(prefix)
        s.write("<")
        s.write(self.tag)
        keys = self.attrs.keys()
        keys.sort()
        for key in keys:
            if self.attrs[key] is not None:
                s.write(" ")
                s.write(key)
                s.write("=\"")
                s.write(self.attrs[key])
                s.write("\"")
        if self.content:
            s.write(">")
            try:
                for child in self.content:
                    try:
                        child.writeTo(s, prefix+(" "*self.prefixLength))
                    except AttributeError:
                        s.write(str(child))
            except TypeError:   # iteration over non-sequence
                child = self.content
                try:
                    child.writeTo(s, prefix+(" "*self.prefixLength))
                except AttributeError:
                    s.write(str(child))
            s.write("</")
            s.write(self.tag)
            s.write(">")
        else:
            s.write("/>")
        if not self.inline:
            s.write("\n")
            s.write(prefix[0:-self.prefixLength])

    def append(self, content):
        if self.content is None:
            self.content = []
        try:
            self.content.append(content)
        except AttributeError:
            self.content = [ self.content ]
            self.content.append(content)
        
class Comment:
    def __init__(self, content=None, inline=0):
        self.content=content
        if self.content is None: self.content = []
        self.inline = inline

    def __str__(self):
        s = cStringIO.StringIO()
        self.writeTo(s)
        return s.getvalue()
    
    def writeTo(self, s, prefix=""):
        if not self.inline:
            s.write("\n")
            s.write(prefix)
        s.write("<!-- ")
        s.write(self.content)       ## @@@ escaping?
        s.write(" -->")
        if not self.inline:
            s.write("\n")
            s.write(prefix[0:-2])
   
def em(content, attrs=None):
    return Element('em', content=content, attrs=attrs, inline=1)

def strong(content, attrs=None):
    return Element('strong', content=content, attrs=attrs, inline=1)

def span(content, attrs=None):
    return Element('span', content=content, attrs=attrs, inline=1)



def p(content, attrs=None):
    return Element('p', content=content, attrs=attrs)


def h1(content, attrs=None):
    return Element('h1', content=content, attrs=attrs)

def h2(content, attrs=None):
    return Element('h2', content=content, attrs=attrs)

def h3(content, attrs=None):
    return Element('h3', content=content, attrs=attrs)

def h4(content, attrs=None):
    return Element('h4', content=content, attrs=attrs)

def h5(content, attrs=None):
    return Element('h5', content=content, attrs=attrs)

def h6(content, attrs=None):
    return Element('h6', content=content, attrs=attrs)


def title(content, attrs=None):
    return Element('title', content=content, attrs=attrs)

def div(content, attrs=None):
    return Element('span', content=content, attrs=attrs)

def stylelink(href):
    return Element("link", attrs={
        "rel":"stylesheet",
        "type":"text/css",
        "href":href})


def prefixEveryLine(prefix, s):
    extra = ""
    s = str(s)
    if s.endswith("\n"): extra = "\n"+prefix
    return prefix+("\n"+prefix).join(s.splitlines())+extra

if __name__ =='__main__':
    import doctest, html
    print "Performing doctest..."
    print doctest.testmod(html) 

# $Log$
# Revision 1.1  2003-01-29 18:28:37  sandro
# first version, passes doctests, [warning: excessive tool-building]
#
