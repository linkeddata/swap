"""

xxx
"""
__version__ = "$Revision$"
# $Id$

import time
import os.path
import os
from reporter import theNullReporter
from sys import stderr
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
                 http1.1: only-if-cached

        saved == use the local (saved) copy if there is one,
                 otherwise try the network.   Good when you know
                 the page hasn't changed, you care about speed, and the
                 server gives a short or absent expireation time.
                 max-stale=inf in http1.1

        auto == if there is a saved copy and it's not expired, then
                use it.  If it's expired, then check the
	        network for a more recent one.   This is
                what network proxies should do; browsers usually do
                this, unless you've configured them to only check once
                per session.  Mozilla calls it "FOR_EACH_PAGE"

        check == check for a remote one being more recent, even
                if we're not expired.  This is what pressing "reload"
                usually does.   Mozilla FORCE_VALIDATE, http1.1
                must-revalidate.

        remote == use the remote copy (updating the local one),
                even if it's not more recent.  Never looks at
	        what's saved.  This is what pressing shift-reload
                usually does.   Mozilla FORCE_RELOAD, http no-cache.
                
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

    def __init__(self, kb=None, uri=None, reporter=theNullReporter):
        self.kb=kb
        self.uri=uri
        self.cachePolicy="auto"
        self.suffixes=defaultSuffixes[:]
        self.typeFromSuffix=None
        self.cacheDirectory="~/.LX/cache/"
        self.reporter = reporter

    def run(self):

        self.reporter.begin("loading "+self.uri)
        
        try:
            self.openStream()
            self.cacheAction = "fetched"
        except AlreadyLoaded, error:
            #print >>stderr, "Used cached version"
            self.cacheAction = "used cache"
            self.reporter.end("used cache")
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
        self.reporter.end()

    
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

        #print >>stderr, "MODE", mode

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
                print >>stderr, "No cache (meta) data"
                pass
            else:
                if mode <= 2:
                    if meta.expires > time.time():
                        # should not fail, since metadata was there...
                        self.loadLocal()
                        raise AlreadyLoaded()
                    else:
                        self.reporter.msg("cached version expired %f days ago"%
                                          ((time.time() - meta.expires)/86400))
                else:
                    print >>stderr, "Assuming cache has expired"
            
        opener = Opener()

        if mode <= 3:
            if not meta:
                try:
                    meta = self.savedMeta()
                except NotCached:
                    pass
            if meta and meta.lastModText:
                # can we get this to work with File URLs?
                #print >>stderr, "If-Modified-Since:", meta.lastModText
                opener.addheader("If-Modified-Since", meta.lastModText)
                self.reporter.msg("using If-Modified-Since conditional GET")
                # http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.25

        firstError=None
        for (suffix, contenttype) in [("",None)]+self.suffixes:
            try:
                self.stream = opener.open(self.uri+suffix)
            except NotImplemented, error:
                if firstError is None: firstError = error
                continue
            except NotModified:
                self.reporter.msg("server says \"304 Not Modified\"; using cached version")
                #  @@ reset expiration information
                self.loadLocal()
                raise AlreadyLoaded()
            else:
                self.stream.info().uri = self.uri+suffix
                self.typeFromSuffix = contenttype
                self.reporter.begin("receiving data")
                return
        raise firstError

    def guessLanguageFromContent(self):
        """ use sniff, or something like it """
        pass

    def filename(self):
        q=urllib.quote(self.uri, safe='')
        return os.path.expanduser(os.path.expandvars(self.cacheDirectory+q))
    
    def loadLocal(self):
        """Add to the KB the formulas associated with the given uri,
        or raise NotCached."""
        try:
            f=file(self.filename()+",kb", "r")
        except IOError, error:
            self.reporter.msg("not found in internal cache")
            raise NotCached()
        self.reporter.msg( "found in internal cache")
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
        #f=kb[0]
        #print >>stderr, f
        #t=f.function
        #print >>stderr, t
        #p.dump(t)
        p.dump((kb.exivars, kb.univars, kb[:]))

if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])

def __test1():

    tdir = "./test-tmp-dir/"
    #try:
    #    os.removedirs(tdir)
    #except OSError, error:
    #    if error.strerror.startswith("No such file or dir"):
    #        pass
    #    else:
    #        raise error

    from LX.kb import KB
    kb=KB()
    l=Loader(kb, "file:test/1blank.rdf")
    l.cacheDirectory = tdir
    l.cachePolicy="remote"

    l.run()
    #print kb
    #print "LIT BEFORE", `kb[1].args[1]`

    kb2=KB()

    l=Loader(kb2, "file:test/1blank.rdf")
    l.cacheDirectory = tdir
    l.cachePolicy="saved"

    l.run()
    #print kb2
    #print "LIT AFTER", `kb2[1].args[1]`

    l=Loader(kb2, "file:test/1blank.rdf")
    l.cacheDirectory = tdir
    l.cachePolicy="saved"

    l.run()
    #print kb2
    #print `kb2[1].args[1]`
    #print `kb2[3].args[1]`

    #type(q, PassingRun)
    #label(q, lit)
    #type(q2, PassingRun)
    #label(q2, lit)

    if kb2[1].args[1] is not kb2[3].args[1]:
        raise RuntimeError()
    if kb2[0].args[1] is not kb2[2].args[1]:
        raise RuntimeError()
    if kb2[1].args[0] is kb2[3].args[0]:
        raise RuntimeError()
    

    kb = KB()
    l=Loader(kb2, "http://www.w3.org/TR/2003/CR-owl-test-20030818/Manifest.rdf")
    l.cacheDirectory = tdir
    l.cachePolicy="remote"
    print "Get Manifest"
    t0 = time.time()
    l.run()
    assert(l.cacheAction=="fetched")
    print "%fs" % (time.time() - t0)
    print "Get Manifest"
    l.cachePolicy="auto"
    t0 = time.time()
    l.run()
    print "%fs" % (time.time() - t0)
    assert(l.cacheAction=="used cache")
    
    

    
# $Log$
# Revision 1.2  2003-09-16 17:05:59  sandro
# improved docs
# added a little proper testing
# change output to use reporter
# made cacheDirectory variable
# fixed a mode branch
#
# Revision 1.1  2003/09/11 06:16:11  sandro
# new caching kb.load replacement (not yet working)
#
        
