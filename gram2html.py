"""
gram2html -- convert Yapps grammar to HTML

Share and Enjoy. Open Source license:
Copyright (c) 2001 W3C (MIT, INRIA, Keio)
http://www.w3.org/Consortium/Legal/copyright-software-19980720
$Id$
see log at end

REFERENCES
  Yapps: Yet Another Python Parser System
  http://theory.stanford.edu/~amitp/Yapps/
  Sat, 18 Aug 2001 16:54:32 GMT
  Last modified 13:21 Sun 26 Nov 2000 , Amit Patel 

$Id$
"""

from string import find
import yapps2, yappsrt


def toHTML(self, xwr):
    self.calculate()
    xwr.startElement('dl')
    for r in self.goals:
        xwr.startElement('dt')
        xwr.startElement('a', [('name', r), ('id', r)])
        xwr.data(r)
        xwr.endElement()

        argsToHTML(self.params[r], xwr)
        xwr.endElement()

        exp = self.rules[r]
        xwr.startElement('dd')
        expToHTML(exp, xwr)
        xwr.endElement()

    xwr.endElement()

from yapps2 import Eval, Terminal, NonTerminal, \
     Sequence, Choice, Option, Plus, Star

def expToHTML(sym, xwr, toplevel=1):
    if isinstance(sym, Eval):
        pass

    elif isinstance(sym, Terminal):
        xwr.startElement('tt')
        xwr.data(sym.token)
        xwr.endElement()
        xwr.data(" ")

    elif isinstance(sym, NonTerminal):
        xwr.startElement('a', [('href', "#%s" % (sym.name,))])
        xwr.data(sym.name)
        xwr.endElement()
        argsToHTML(sym.args, xwr)
        xwr.data(" ")

    elif isinstance(sym, Sequence):
        if not toplevel: xwr.data('( ')
        for s in sym.children:
            expToHTML(s, xwr, 0)
        if not toplevel: xwr.data(' ) ')

    elif isinstance(sym, Choice):
        if not toplevel: xwr.data('( ')
        for s in sym.children[:-1]:
            expToHTML(s, xwr, 0)
            xwr.emptyElement('br', [('class', "")])
            xwr.data(' | ')
        expToHTML(sym.children[-1], xwr, 0)
        if not toplevel: xwr.data(' ) ')
    elif isinstance(sym, Option):
        xwr.data('[ ')
        expToHTML(sym.child, xwr )
        xwr.data(' ] ')
    elif isinstance(sym, Star):
        expToHTML(sym.child, xwr, 0)
        xwr.data('* ')
    elif isinstance(sym, Plus):
        expToHTML(sym.child, xwr, 0)
        xwr.data('+ ')
    else:
        xwr.startElement('b')
        xwr.data('@@%s@@' % sym.name)
        xwr.endElement()
        xwr.data(" ")
        
def argsToHTML(args, xwr):
    xwr.startElement('sub')
    xwr.data(args)
    xwr.endElement()
    
def generate(title, inputfilename, outputfilename=''):
    """Generate an HTML version of the grammar,
    given a title, an input filename (X.g)
    and an output filename (defaulting to X.py)."""

    import sys, codecs
    from toXML import XMLWriter
    dummy, dummy, dummy, encWriter = codecs.lookup('utf-8')

    if not outputfilename:
	if inputfilename[-2:]=='.g': outputfilename = inputfilename[:-2]+'.html'
	else: raise "Invalid Filename", outputfilename
        
    DIVIDER = '\n%%\n' # This pattern separates the pre/post parsers
    preparser, postparser = None, None # Code before and after the parser desc

    # Read the entire file
    s = open(inputfilename,'r').read()

    # See if there's a separation between the pre-parser and parser
    f = find(s, DIVIDER)
    if f >= 0: preparser, s = s[:f]+'\n\n', s[f+len(DIVIDER):]

    # See if there's a separation between the parser and post-parser
    f = find(s, DIVIDER)
    if f >= 0: s, postparser = s[:f], '\n\n'+s[f+len(DIVIDER):]

    # Create the parser and scanner
    p = yapps2.ParserDescription(yapps2.ParserDescriptionScanner(s))
    if not p: return
    
    # Now parse the file
    t = yappsrt.wrap_error_reporter(p, 'Parser')
    if not t: return # Error

    # Generate the output
    xwr = XMLWriter(encWriter(sys.stdout))
    xwr.startElement('html') #@@ xmlns
    xwr.startElement('head')
    xwr.startElement('title')
    xwr.data(title)
    xwr.endElement()
    xwr.endElement()
    xwr.startElement('body')
    xwr.startElement('h1')
    xwr.data(title)
    xwr.endElement() # h1
    xwr.startElement('address')
    xwr.data('source: ')
    xwr.startElement('a', [('href', inputfilename)])
    xwr.data(inputfilename)
    xwr.endElement() #a
    xwr.data(', a ')
    xwr.startElement('a', [('href', 'http://theory.stanford.edu/~amitp/Yapps/')])
    xwr.data('YAPPS')
    xwr.endElement() #a
    xwr.data(' grammar')
    xwr.endElement() #address
    
    toHTML(t, xwr)
    xwr.endElement() # body
    xwr.endElement() # html


def main(argv):
    generate(argv[2], argv[1])

if __name__ == '__main__':
    import sys
    main(sys.argv)

# $Log$
# Revision 1.3  2002-08-15 23:24:17  connolly
# updated grammar, cited YAPPS
#
# Revision 1.2  2002/07/17 19:33:48  connolly
# published HTML version of relaxNG grammar
#
# Revision 1.1  2001/09/01 05:31:17  connolly
# - gram2html.py generates HTML version of grammar from rdfn3.g
# - make use of [] in rdfn3.g
# - more inline terminals
# - jargon change: scopes rather than contexts
# - term rule split into name, expr; got rid of shorthand
#
