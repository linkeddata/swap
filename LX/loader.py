"""

oops.
Unpickling might shared (uri, data) Constants, etc.   :-/
(does it?     getstate/setstate -- make it?)
http://www.python.org/doc/current/lib/node68.html

 x >>> l=LX.loader.Loader(kb,
 "file:test/surnia-test-results-0013.rdf")
 
>>> import LX.kb
>>> import LX.loader
>>> kb=LX.kb.KB()
>>> l=LX.loader.Loader(kb, "file:test/1blank.rdf")
>>> l.run()
>>> print len(kb), len(kb.exivars)
2 1
>>> l2=LX.loader.Loader(kb, "file:test/1blank.rdf")
>>> l2.run()
>>> print len(kb), len(kb.exivars)
4 2
>>> import time
>>> t0=time.time()
>>> kb.load("http://www.w3.org/TR/2003/CR-owl-test-20030818/Manifest.rdf")
>>> print time.time() - t0
>>> print len(kb), len(kb.exivars)
xxx
>>> t0=time.time()
>>> kb.load("http://www.w3.org/TR/2003/CR-owl-test-20030818/Manifest.rdf")
>>> print time.time() - t0
>>> print len(kb), len(kb.exivars)
xxx
"""
__version__ = "$Revision$"
# $Id$

import time
import os.path
import os
import LX
import LX.kb
import sniff
import urllib
from cPickle import Pickler, Unpickler

defaultSuffixes=[("rdf",  "applicate/rdf+xml"),
                 ("xml",  "applicate/xml"),
                 ("html", "text/html"),
                 ("txt",  "text/plain"),
                 ]

class NotCached(RuntimeError): pass

class NotModified(RuntimeError): pass

class AlreadyLoaded(RuntimeError): pass

class Opener(urllib.FancyURLopener):

    def __init__(self, *args, **kwargs):
        urllib.FancyURLopener.__init__(self, *args, **kwargs)

    # http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.25
    def http_error_304(self, url, fp, errcode, errmsg, headers, data=None):
        """Error 304 -- Not Modified."""
        raise NotModified()

class Meta:

    def __init__(self, stream_info):

        self.lastModText = stream_info.getheader("Last-Modified")
        try:
            self.lastMod = time.mktime(stream_info.getdate("Last-Modified"))
        except TypeError, error:
            self.lastMod = None

        try:
            self.expires = time.mktime(stream_info.getdate("Expires"))
        except TypeError, error:
            # make up an expiration time...
            now=time.time()
            age = now-self.lastMod
            nextChange = age/100
            if nextChange > 300: nextChange = 300
            self.expires = now + nextChange
        
class Loader:
    """

        cachePolicy has the following values & meanings (in order of
        remoteness):

        local == use the local (saved) copy if there is one,
                 fatal error if not.  (never looks at the net)
        saved == use the local (saved) copy if there is one,
                 otherwise try the network.   Good when you know
                 the page hasn't changed, you care about speed, and the
                 server gives a short or absent expireation time.
        auto == if there is a saved copy and it's not expired, then
                use it.  If it's expired, then check the
	        network for a more recent one.   This is
                what network proxies should do; browsers usually do
                this, unless you've configured them to only check once
                per session.  Mozilla calls it "FOR_EACH_PAGE"
        check == check for a remote one being more recent, even
                if we're not expired.  This is what pressing "reload"
                usually does.   Mozilla FORCE_VALIDATE
        remote == use the remote copy (updating the local one),
                even if it's not more recent.  Never looks at
	        what's saved.  This is what pressing shift-reload
                usually does.   Mozilla FORCE_RELOAD
        Moz per: http://www.geocrawler.com/archives/3/141/2001/3/50/5351741/

        WHY do we do our own cache management, you ask?!?!   Because
        we're trying to save on PARSE TIME as much as NETWORK LATENCY.
        For instance, the OWL test manfest parses on my system in 1
        second from a file, but can unPickle in about 0.1 second.


                ======== old stuff from here on... =======

        Add the formal meaning of identified document.

        ONLY BARELY IMPLEMENTED.   Intended to work in a
        blindfold-like manner; just works for hard coded languages
        right now.

        @@@   languageOverrides={}
           a mapping from string->string, overriding self-identificat.

        In the simplest case, this might mean opening a local file,
        which we know to contain n3, read the contents, and parse them
        directly to the kb.

        In a more complex case, we do an HTTP GET to obtain the
        document, using allowedLanguages to help guide our content
        negotiation, get some content, figure out what language is
        actually used, [recursively] load that language's definition,
        use that definition to build a parser for the original content,
        and parse it.

        We end up with a logical formula which might or might not be
        RDF (depending on how the language definition is written), but
        we can convert it, of course.  If we want to load from an
        untrusted source, load to a temporary kb first, reify it to
        the main KB, then apply your trust rules.

        See Blindfold.

        Does something like:

           1.  Identify the language
                 from content-type, other headers, embedded emacs magic strings,
                 suffixes, 
                 and perhaps a pre-arranged list of allowed languages.
           2.  Look up its definition
                 from an allowed set of language definitions, and/or the web
           3.  Parse it, collecting the semantics
                 perhaps by compiling a parser for it
           4.  return the logic sentence it claims
                 with some latitude as to form; the sentence only guarantees
                 to be inconsistent (T=F) or to entail only the intended
                 expression's meaning and separable metadata. 


    """

    def __init__(self, kb=None, uri=None):
        self.kb=kb
        self.uri=uri
        self.cachePolicy="auto"
        self.suffixes=defaultSuffixes[:]
        self.typeFromSuffix=None

    def run(self):

        try:
            self.openStream()
        except AlreadyLoaded, error:
            return
        
        self.typeFromSniff=sniff.sniffLanguage(self.stream)
        language=self.typeFromSniff
        #print "LANGUAGE",language

        # generalize this!   first one which can handle this lang!
        
        if language=="http://www.w3.org/1999/02/22-rdf-syntax-ns#RDF":
            language="rdflib"
        if language=="application/rdf":
            language="rdflib"
        if language=="application/rdf+xml":
            language="rdflib"
        
        parser=LX.language.getParser(language=language)

        # the need for a tempKB is a little... annoying, but otherwise
        # we can't cache just the stuff we learned here.  If addFrom
        # is done right, it can probably be quite cheap.  I think...
        tempKB = LX.kb.KB()
        parser.parse(self.stream, tempKB)
        self.saveInCache(Meta(self.stream.info()), tempKB)
        self.kb.addFrom(tempKB)

    
    def openStream(self):

        """Open self.stream for fetching the content available at
        self.uri, or raise AlreadyLoaded if we've already got it.

        Also tries adding self.prefixes as needed to try to find
        something (for file: uris, or if the server doesn't do ConNeg
        like w3.org).   Fills in self.typeFromSuffix.

        This would be just
           self.stream=urllib.urlopen(self.uri)
        if we didn't do any caching.   But we do.  :-)
        """

        #          0        1       2        3        4
        mode = (["local", "saved", "auto", "check", "remote"]
                .index(self.cachePolicy))

        if mode <= 1:
            try:
                self.loadLocal()
            except NotCached, error:
                if mode == 0:
                    raise error
                # fall through to trying the network
            else:
                raise AlreadyLoaded()

        meta = None
        if mode >= 2 and mode <=3:
            # (mode < 2 would be okay, but we know there's nothing stored)
            try:
                meta = self.savedMeta()
            except NotCached:
                pass
            else:
                if mode <= 2 and meta.expires <= time.time():
                    # should not fail, since metadata was there...
                    self.loadLocal()
                    raise AlreadyLoaded()
            
        opener = Opener()

        if mode <= 4:
            if not meta:
                try:
                    meta = self.savedMeta()
                except NotCached:
                    pass
            if meta and meta.lastModText:
                opener.addheader("If-Modified-Since", lastModText)
                # http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.25

        firstError=None
        for (suffix, contenttype) in [("",None)]+self.suffixes:
            try:
                self.stream = opener.open(self.uri+suffix)
            except NotImplemented, error:
                if firstError is None: firstError = error
                continue
            except NotModified:
                self.loadLocal()
                raise AlreadyLoaded()
            else:
                self.stream.info().uri = self.uri+suffix
                self.typeFromSuffix = contenttype
                return
        raise firstError

    def guessLanguageFromContent(self):
        """ use sniff, or something like it """
        pass

    def filename(self):
        q=urllib.quote(self.uri, safe='')
        return os.path.expanduser(os.path.expandvars("~/.LX-save/"+q))
    
    def loadLocal(self):
        """Add to the KB the formulas associated with the given uri,
        or raise NotCached."""
        f=file(self.filename()+",kb", "r")
        p=Unpickler(f)
        (exivars, univars, formulas) = p.load()
        for f in formulas:
            self.kb.add(f)
        self.kb.exivars.extend(exivars)
        self.kb.univars.extend(univars)

    def savedMeta(self):
        """Return a metadata (info) object associated with the given
        uri, or raise NotCached.    Class Meta."""
        
        try:
            f=file(self.filename()+",meta", "r")
        except IOError, error:
            raise NotCached()
        p=Unpickler(f)
        return p.load()
        
    def saveInCache(self, meta, kb):
        """Save these things associated with the uri

        """

        try:
            os.makedirs(os.path.dirname(self.filename()))
        except OSError, error:
            if error.strerror != "File exists": raise error

        f=file(self.filename()+",meta", "w")
        p=Pickler(f, -1)
        p.dump(meta)

        f=file(self.filename()+",kb", "w")
        p=Pickler(f, 0)
        p.dump((kb.exivars, kb.univars, kb[:]))

if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])

# $Log$
# Revision 1.1  2003-09-11 06:16:11  sandro
# new caching kb.load replacement (not yet working)
#
        
