#!/usr/local/bin/python
"""
$Id$

Web access functionality building on urllib

"""

import sys

#import urllib
import urllib2
import uripath # http://www.w3.org/2000/10/swap/uripath.py
import diag
from diag import progress
import notation3   # Parser    @@@ Registery of parsers vs content types woudl be better.

from OrderedSequence import indentString

HTTP_Content_Type = 'content-type' #@@ belongs elsewhere?


def urlopenForRDF(addr):
    """A version of urllib.urlopen() which asks for RDF by preference

    This is now uses urllib2.urlopen(), in order to get better error handling
    """
    z = urllib2.Request(addr)
    z.add_header('Accept', 'text/rdf+n3, application/rdf+xml')
#    z.add_header('Accept', 'text/plain q=0.1')
    return urllib2.urlopen(z)

def load(store, uri=None, openFormula=None, asIfFrom=None, contentType=None,
		flags="", why=None):
    """Get and parse document.  Guesses format if necessary.

    uri:      if None, load from standard input.
    remember: if 1, store as metadata the relationship between this URI and this formula.
    
    Returns:  top-level formula of the parsed document.
    Raises:   IOError, SyntaxError, DocumentError
    
    This is an independent function, as it is fairly independent
    of the store. However, it is natural to call it as a method on the store.
    And a proliferation of APIs confuses.
    """
    try:
	baseURI = uripath.base()
	if uri != None:
	    addr = uripath.join(baseURI, uri) # Make abs from relative
	    if diag.chatty_flag > 40: progress("Taking input from " + addr)
	    netStream = urlopenForRDF(addr)
	    if diag.chatty_flag > 60:
		progress("   Headers for %s: %s\n" %(addr, netStream.headers.items()))
	    receivedContentType = netStream.headers.get(HTTP_Content_Type, None)
	else:
	    if diag.chatty_flag > 40: progress("Taking input from standard input")
	    addr = uripath.join(baseURI, "STDIN") # Make abs from relative
	    netStream = sys.stdin
	    receivedContentType = None

    #    if diag.chatty_flag > 19: progress("HTTP Headers:" +`netStream.headers`)
    #    @@How to get at all headers??
    #    @@ Get sensible net errors and produce dignostics

	guess = None
	if receivedContentType:
	    if diag.chatty_flag > 9:
		progress("Recieved Content-type: " + `receivedContentType` + " for "+addr)
	    if receivedContentType.find('xml') >= 0 or (
	             receivedContentType.find('rdf')>=0
		     and not (receivedContentType.find('n3')>=0)  ):
		guess = "application/rdf+xml"
	    elif receivedContentType.find('n3') >= 0:
		guess = "text/rdf+n3"
	if guess== None and contentType:
	    if diag.chatty_flag > 9:
		progress("Given Content-type: " + `contentType` + " for "+addr)
	    if contentType.find('xml') >= 0 or (
		    contentType.find('rdf') >= 0  and not (contentType.find('n3') >= 0 )):
		guess = "application/rdf+xml"
	    elif contentType.find('n3') >= 0:
		guess = "text/rdf+n3"
	buffer = netStream.read()
	if guess == None:

	    # can't be XML if it starts with these...
	    if buffer[0:1] == "#" or buffer[0:7] == "@prefix":
		guess = 'text/rdf+n3'
	    elif buffer.find('xmlns="') >=0 or buffer.find('xmlns:') >=0: #"
		guess = 'application/rdf+xml'
	    else:
		guess = 'text/rdf+n3'
	    if diag.chatty_flag > 9: progress("Guessed ContentType:" + guess)
    except (IOError, OSError):  
	raise DocumentAccessError(addr, sys.exc_info() )
	
    if asIfFrom == None:
	asIfFrom = addr
    if openFormula != None:
	F = openFormula
    else:
	F = store.newFormula()
    if guess == 'application/rdf+xml':
	if diag.chatty_flag > 49: progress("Parsing as RDF")
#	import sax2rdf, xml.sax._exceptions
#	p = sax2rdf.RDFXMLParser(store, F,  thisDoc=asIfFrom, flags=flags)
        import os
        if flags == 'rdflib' or int(os.environ.get("CWM_RDFLIB", 0)):
            parser = 'rdflib'
            flags = ''
        else:
            parser = 'sax2rdf'
        import rdfxml
        p = rdfxml.rdfxmlparser(store, F,  thisDoc=asIfFrom, flags=flags, parser=parser)
	p.feed(buffer)
	F = p.close()
    else:
	assert guess == 'text/rdf+n3'
	if diag.chatty_flag > 49: progress("Parsing as N3")
	p = notation3.SinkParser(store, F,  thisDoc=asIfFrom,flags=flags, why=why)
	p.startDoc()
	p.feed(buffer)
	p.endDoc()
    if not openFormula:
	F = F.close()
    return F 




def loadMany(store, uris, openFormula=None):
    """Get, parse and merge serveral documents, given a list of URIs. 
    
    Guesses format if necessary.
    Returns top-level formula which is the parse result.
    Raises IOError, SyntaxError
    """
    assert type(uris) is type([])
    if openFormula == None: F = store.newFormula()
    else:  F = openFormula
    f = F.uriref()
    for u in uris:
	F.reopen()  # should not be necessary
	store.load(u, openFormula=F, remember=0)
    return F.close()
    
    
#@@@@@@@@@@  Junk - just to keep track iof the interface to sandros stuff and rdflib
    
def getParser(format, inputURI, workingContext, flags):
    """Return something which can load from a URI in the given format, while
    writing to the given store.
    """
    r = BecauseOfCommandLine(sys.argv[0]) # @@ add user, host, pid, date time? Privacy!
    if format == "rdf" :
        touch(_store)
	if "l" in flags["rdf"]:
	    from rdflib2rdf import RDFXMLParser
	else:
	    rdfParserName = os.environ.get("CWM_RDF_PARSER", "sax2rdf")
	    if rdfParserName == "rdflib2rdf":
		from rdflib2rdf import RDFXMLParser
	    elif rdfParserName == "sax2rdf":
		from sax2rdf import RDFXMLParser
	    else:
		raise RuntimeError("Unknown RDF parser: " + rdfParserName)
	return RDFXMLParser(_store, workingContext, inputURI,
					flags=flags[format], why=r)
    elif format == "n3":
        touch(_store)
        return notation3.SinkParser(_store, openFormula=workingContext,
		    thisDoc=inputURI,  why=r)
    else:
        need(lxkb)
        touch(lxkb)
        return LX.language.getParser(language=format,
                                     sink=lxkb,
                                     flags=flags)

class DocumentAccessError(IOError):
    def __init__(self, uri, info):
        self._uri = uri
        self._info = info
        
    def __str__(self):
        # See C:\Python16\Doc\ref\try.html or URI to that effect
#        reason = `self._info[0]` + " with args: " + `self._info[1]`
        reason = indentString(self._info[1].__str__())
        return ("Unable to access document <%s>, because:\n%s" % ( self._uri, reason))
    

