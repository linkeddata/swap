"""

"""
__version__ = "$Revision$"
# $Id$

import re
import io
import xml.sax

ianaBase = "http://www.isi.edu/in-notes/iana/assignments/media-types/"
ianaBase = ""

# Consider text/html as quite possibly XML; if it turns out to not
# be well-formed XML, we'll just leave it as text/html.
xmlPattern = re.compile(re.escape(ianaBase)+
                        r"(((text|application)/(\w+\+)?xml)|text/html)$")

plainPattern = re.compile(re.escape(ianaBase)+r"text/plain")

def sniffLanguage(stream, baseURI=ianaBase):
    """

    Return a URI which identifies the stream's formal language,
    following some experimental rules.

    May replace stream's internals with a seekable version of the same
    data.

    >>> import sniff
    >>> import urllib
    >>> f=urllib.urlopen("http://www.w3.org/Icons/w3c_main")
    >>> sniff.sniffLanguage(f)
    'image/png'

    Now let's try it with XML content.  Right now at least this is
    served as text/html, but we'll sniff out the namespace:
    
    >>> f=urllib.urlopen("http://www.w3.org")
    >>> sniff.sniffLanguage(f)
    'http://www.w3.org/1999/xhtml#html'

    Note the first line still appears next...
    
    >>> f.readline().strip()
    '<?xml version="1.0" encoding="utf-8"?>'
    
    Now try a few sniffs of text/plain documents.   This one has no
    override:
    
    >>> f=urllib.urlopen("file:test/sniff-1.plain")
    >>> sniff.sniffLanguage(f)
    'text/plain'

    But this one does:
    
    >>> f=urllib.urlopen("file:test/sniff-2.plain")
    >>> sniff.sniffLanguage(f)
    'application/octet-stream'

    #>>> f=urllib.urlopen("file:/home/sandro/WWW/2000/10/swap/test/crypto/acc.n3")
    #>>> sniff.sniffLanguage(f)
    #'application/vnd.w3c.n3'

    @@ still needs a way to handle suffixes: n3, nt, etc.
    http://archive.ncsa.uiuc.edu/SDG/Software/Mosaic/Docs/extension-map.html
    http://web.pydoc.org/2.2/mimetypes.html
    use .mime.types if still text/plain
    maybe special case n3?

    @@ needs preferences to handle content-negotation, both
    with file: (knowing suffixes) and http: .

    (open   foo   when foo.html exists.)
    
    """

    lang = stream.info().type
    
    if lang.find(":") == -1:
        lang = baseURI + lang

    if xmlPattern.match(lang):
        sniffer = sniffXML
    elif plainPattern.match(lang):
        sniffer = sniffPlain
    else:
        return lang
        
    try:
        stream.fp.seek(0)
    except IOError:
        makeSeekable(stream)
    except AttributeError:
        makeSeekable(stream)
        

    lang = sniffer(stream, lang)
    stream.fp.seek(0)

    if lang.find(":") == -1:
        lang = baseURI + lang

    # fall back to suffix!
    if lang == baseURI+"text/plain":
        try:
            uri=stream.info().uri
        except AttributeError:
            pass
        else:
            try:
                suffix = uri[uri.rindex(".")+1:]
                return baseURI+"application/"+suffix
            except ValueError:
                # no period in it?!?!
                pass

    return lang

def makeSeekable(stream):
    """

    Assume stream is like urllib[2].urlopen returns; replace its
    internal file reference with a string reader that has the same
    data.

    """

    tmp = stream.read()
    s = io.StringIO(tmp)
    stream.fp = s
    stream.read = stream.fp.read
    stream.readline = stream.fp.readline
    stream.readlines = stream.fp.readlines

varPattern = re.compile(r'.*\-\*\-.*Content\-Type\:\ *\"([^"]*)\".*\-\*\-.*')
def sniffPlain(stream, lang):
    """

    Use emacs embedded-variables syntax.

    """
    while 1:
        line = stream.readline()
        if not line: return lang
        match = varPattern.match(line)
        if match:
            return match.group(1)

def sniffXML(stream, lang):
    """

    Make a URI out of the root element namespace and the root element
    name, of the form rootns#rootelement.  If the rootns ends in a
    hash, don't add another one.

    Should we treat HTML as XHTML?

    """
    handler = sniffXMLHandler()
    parser = xml.sax.make_parser()
    parser.setContentHandler(handler)
    parser.setFeature(xml.sax.handler.feature_namespaces, 1)
    try:
        parser.parse(stream)
    except EnoughHasBeenRead as j:
        if j.nsname.endswith("#"):
            return j.nsname+j.elname
        else:
            return j.nsname+"#"+j.elname

    return lang

class EnoughHasBeenRead:
    def __init__(self, nsname, elname):
        self.nsname = nsname.encode()
        self.elname = elname.encode()

class sniffXMLHandler(xml.sax.handler.ContentHandler):

    def startElementNS(self, name, qname, attrs):
        raise EnoughHasBeenRead(name)


    
    


    

# $Log$
# Revision 1.6  2003-09-17 18:01:04  sandro
# updated doctests to reflect removal of iana prefix
# made more tollerant of not having a URI
#
# Revision 1.5  2003/09/17 16:09:08  sandro
# handle a change to python 2.3 silently
#
# Revision 1.4  2003/08/22 20:49:41  sandro
# midway on getting load() and parser abstraction to work better
#
# Revision 1.3  2003/01/29 06:09:18  sandro
# Major shift in style of LX towards using expr.py.  Added some access
# to otter, via --check.  Works as described in
# http://lists.w3.org/Archives/Public/www-archive/2003Jan/0024
# I don't like this UI; I imagine something more like --engine=otter
# --think, and --language=otter (instead of --otterDump).
# No tests for any of this.
#
# Revision 1.2  2003/01/10 21:59:39  sandro
# added notes about n3, a little more doctest
#
# Revision 1.1  2003/01/10 21:33:18  sandro
# first version, trying to put down in code something that's been
# bouncing around in my head (and various notes) for quite some time.
#
