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
   *   <head><title>Test Document</title></head>
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
   *   <head><title>Test Document</title></head>
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
       """

       cleverly put plain text into a div.   what else to do with it???
       """
       if isinstance(content, Element):
           self.body.append(content)
       else:
           self.body.append(div(content))
       return self

   def __lshift__(self, content):
       """Convenience syntax for append, with no parens to balance."""
       return self.append(content)

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
                if key.endswith("_"):
                    # to allow the "class" attr to be given as "class_"
                    # (in standard python style) to avoid conflict with
                    # the python keyword.
                    s.write(key[0:-1])
                else:
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
        return self  # allows chaining    x.append(y).append(z)

    def __lshift__(self, content):
       """Convenience syntax for append, with no parens to balance."""
       return self.append(content)


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

class Flow:
    """
    >>> import html
    >>> h = html.Flow()
    >>> print prefixEveryLine("* ",
    ...                       h.span("Spanned Text", class_="authorName"))
    * 
    * <span class="authorName">Spanned Text</span>
    * 
    """
    def __getattr__(self, name):
        def func(content="", **kw):
            return Element(name, content, attrs=kw)
        return func

class Inline:
    """
    >>> import html
    >>> h = html.Inline()
    >>> print h.span("Spanned Text", class_="authorName")
    <span class="authorName">Spanned Text</span>
    """
    def __getattr__(self, name):
        def func(content="", **kw):
            return Element(name, content, attrs=kw, inline=1)
        return func

"""Foo"""

def createStdElements():
    import html

    flow = Flow()
    inline = Inline()

    # These element names come from
    # http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd
    #
    # I added the "+" myself (a flag for non-inline element); it's
    # just about the style in which the HTML is generated and doesnt
    # HAVE to match inline/flow in HTML's own syntax.

    elements = """a abbr acronym address area b base bdo big
    blockquote+ body+ br+ button caption cite code col colgroup dd del
    dfn div+ dl dt em fieldset form+ h1+ h2+ h3+ h4+ h5+ h6+ head+ hr+ html+ i
    img input+ ins kbd label legend li link map meta noscript object ol+
    optgroup option p+ param pre q samp script+ select+ small span strong
    style sub sup table+ tbody+ td textarea+ tfoot th thead title tr+ tt
    ul+ var"""

    for x in elements.split(" "):
        tag = x.strip()
        if tag:
            if tag.endswith("+"):
                tag = tag[0:-1]
                html.__dict__[tag] = getattr(flow, tag)
            else:
                html.__dict__[tag] = getattr(inline, tag)
            

createStdElements()

if __name__ =='__main__':
    import doctest, html
    print "Performing doctest..."
    print doctest.testmod(html) 

# $Log$
# Revision 1.4  2003-04-29 04:46:57  sandro
# added clever << operator (now where have I seen that before?)
#
# Revision 1.3  2003/02/18 17:02:05  sandro
# added auto-generation of element-creation functions, based on XHTML DTD
#
# Revision 1.2  2003/02/14 00:44:24  sandro
# added some more functions: htable, tr, td, a
#
# Revision 1.1  2003/01/29 18:28:37  sandro
# first version, passes doctests, [warning: excessive tool-building]
#
