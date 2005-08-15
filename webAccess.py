#!/usr/local/bin/python
"""Web Access

This module implements some basic bits of the web architecture:
dereferencing a URI to get a document, with content negotiation,
and deciding on the basis of the Internet Content Type what to do with it.

$Id$


Web access functionality building on urllib2

"""

import sys, os

#import urllib
import urllib2, urllib  # Python standard

import uripath # http://www.w3.org/2000/10/swap/uripath.py
import diag
from diag import progress
import notation3   # Parser    @@@ Registery of parsers vs content types woudl be better.

from OrderedSequence import indentString

HTTP_Content_Type = 'content-type' #@@ belongs elsewhere?

print_all_file_names = diag.print_all_file_names   # for listing test files

class SecurityError(RuntimeError):
    pass

def setting(self, val=None):
    if val is not None:
        self[0] = val
    return self[0]

sandBoxed = setting.__get__([False])

def cacheHack(addr):
    """ If on a plane, hack remote w3.org access to local access
    """
    real = "http://www.w3.org/"
    local = "/devel/WWW/"
    suffixes = [ "", ".rdf", ".n3" ]
    if addr.startswith(real):
	rest = local + addr[len(real):]
	for s in suffixes:
	    fn = rest + s
	    try:
		os.stat(fn)
		progress("Offline: Using local copy %s" % fn)
		return "file://" + fn
	    except OSError:
		continue
    return addr
		
def urlopenForRDF(addr, referer=None):
    """A version of urllib.urlopen() which asks for RDF by preference

    This is now uses urllib2.urlopen(), in order to get better error handling
    """

    if sandBoxed():
        if addr[:5] == 'file:':
            raise SecurityError('Nice try')
    addr = cacheHack(addr) # @@ hack
    if addr[:5] == 'data:':
        return urllib.urlopen(addr)
    z = urllib2.Request(addr)
    z.add_header('Accept', 'text/rdf+n3, application/rdf+xml')
    if referer: #consistently misspelt
        z.add_header('Referer', referer)
#    z.add_header('Accept', 'text/plain q=0.1')
    q =  urllib2.urlopen(z)
    if print_all_file_names:
        diag.file_list.append(addr)
    return q

def load(store, uri=None, openFormula=None, asIfFrom=None, contentType=None,
		flags="", referer=None, why=None):
    """Get and parse document.  Guesses format if necessary.

    uri:      if None, load from standard input.
    remember: if 1, store as metadata the relationship between this URI and this formula.
    
    Returns:  top-level formula of the parsed document.
    Raises:   IOError, SyntaxError, DocumentError
    
    This is an independent function, as it is fairly independent
    of the store. However, it is natural to call it as a method on the store.
    And a proliferation of APIs confuses.
    """
#    if referer is None:
#        raise RuntimeError("We are trying to force things to include a referer header")
    try:
	baseURI = uripath.base()
	if uri != None:
	    addr = uripath.join(baseURI, uri) # Make abs from relative
	    if diag.chatty_flag > 40: progress("Taking input from " + addr)
	    netStream = urlopenForRDF(addr, referer)
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
	    elif contentType.find('sparql') >= 0 or contentType.find('rq'):
                guess = "x-application/sparql"
	buffer = netStream.read()
	if guess == None:

	    # can't be XML if it starts with these...
	    if buffer[0:1] == "#" or buffer[0:7] == "@prefix":
		guess = 'text/rdf+n3'
	    elif buffer[0:6] == 'PREFIX' or buffer[0:4] == 'BASE':
                guess = "x-application/sparql"
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
    import os
    if guess == "x-application/sparql":
        if diag.chatty_flag > 49: progress("Parsing as SPARQL")
        from sparql import sparql_parser
        import sparql2cwm
        convertor = sparql2cwm.FromSparql(store, F, why=why)
        import StringIO
        p = sparql_parser.N3Parser(StringIO.StringIO(buffer), sparql_parser.branches, convertor)
        F = p.parse(sparql_parser.start).close()
    elif guess == 'application/rdf+xml':
	if diag.chatty_flag > 49: progress("Parsing as RDF")
#	import sax2rdf, xml.sax._exceptions
#	p = sax2rdf.RDFXMLParser(store, F,  thisDoc=asIfFrom, flags=flags)
        if flags == 'rdflib' or int(os.environ.get("CWM_RDFLIB", 0)):
            parser = 'rdflib'
            flags = ''
        else:
            parser = os.environ.get("CWM_RDF_PARSER", "sax2rdf")
        import rdfxml
        p = rdfxml.rdfxmlparser(store, F,  thisDoc=asIfFrom, flags=flags, parser=parser)
	p.feed(buffer)
	F = p.close()
    else:
	assert guess == 'text/rdf+n3'
	if diag.chatty_flag > 49: progress("Parsing as N3")
	if os.environ.get("CWM_N3_PARSER", 0) == 'n3p':
            import n3p_tm
            import triple_maker
            tm = triple_maker.TripleMaker(formula=F, store=store)
            p = n3p_tm.n3p_tm(asIfFrom, tm)
        else:
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
    

