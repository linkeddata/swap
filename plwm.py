#!/usr/bin/env python

"""
     plwm (pronounced plume) is a plugable rewrite of cwm.  it should
     be a drop-in replacement, eventually renamed cwm.py.  Or maybe
     staying plwm, as "plugable web machine".

     does --n3  mean the new default language is n3, or the new
     default parser is Notation3 ?   I think it's the language,
     which means (1) you need a parser which can handle it, and
     (2) you need to tell the parser that's the language.
     
"""
revision = '$Id$'

import sys
import ArgHandler
import hotswap
import pluggable
import urllib

class NotImplented(RuntimeError):
    pass


class Host:
    """The host is the central point of control and resource
    management, dispatching to the parsers, stores, query engines,
    etc, as needed.

    The host passes itself (or a different host) to the components it
    calls to allow for a flexible callback/dialog mechanism.  This
    allows the components access to virtual system state: they can
    look at option flags, produce debugging output, read and write
    files, etc, ... all managed through one interface.   In fact, they
    are expected to run in a restricted execution environment where
    they can ONLY do these things through this interface.

    If you don't want to some component to be able to do something,
    pass it a different host which disallows those things.

    We do all the handling of hotswap here.  Components (eg parsers)
    should not need to know about that.  If they need a Store to pass
    to, we'll hand them one.  If they need a particular KIND of store,
    .... um ... um ....     Maybe they should use hotswap.

    """

    def __init__(self):
        # we don't need to keep track of a current Store, current Parser,
        # or any of that, because hotswap does it for us, while letting them
        # be swapped.
        pass
    
    def trace(self, message, subsystem=None):
        # look at who caller is, too
        raise NotImplemented

    def open(self, url, readwrite="read"):
        # readwrite part not implemented
        stream = urllib.urlopen(url)
        stream.info().uri = url     # @@ absoluteize?  sanitize?
        return stream

    def output(self):
        raise NotImplemented

    def explain(self, result, step):       # is this about right?!?!
        raise NotImplemented

    def load(self, source):
        " or is load() an option on a store/kb?    Hrmph. "
        parser = hotswap.get(pluggable.Parser)
        store = hotswap.get(pluggable.Store)
        parser.setSink(store)
        stream = self.open(source)
        parser.parse(stream, host=self)
        

################################################################

class MyArgHandler(ArgHandler.ArgHandler):

    def __init__(self, host=None, *args, **kwargs):
        #apply(super(MyArgHandler, self).__init__, args, kwargs)
        apply(ArgHandler.ArgHandler.__init__, [self]+list(args), kwargs)
        self.host = host

    def handle__pipe(self):
        """Don't store, just pipe out
        """
        raise NotImplemented

    def handle__rdf(self):
        """Input & Output ** in RDF M&S 1.0 insead of n3 from now on
        """
        raise NotImplemented
    def handle__n3(self):
        """Input & Output in N3 from now on
        """
        raise NotImplemented
    def handle__rdfEQ(self, flags):
        """Input & Output ** in RDF and set given RDF flags
        """
        raise NotImplemented
    def handle__n3EQ(self, flags):
        """Input & Output in N3 and set N3 flags
        """
        raise NotImplemented
    
    def handle__ntriples(self):
        """Input & Output in NTriples (equiv --n3=spart -bySubject -quiet)
        """
        raise NotImplemented
    
    def handle__ugly (self):
        """Store input and regurgitate *
        """
        raise NotImplemented
    
    def handle__bySubject(self):
        """Store input and regurgitate in subject order *
        """
        raise NotImplemented
    
    def handle__no(self):
        """No output *

        (default is to store and pretty print with anonymous nodes) *
        """
        raise NotImplemented
    
    def handle__strings(self):
        """Dump :s to stdout ordered by :k whereever { :k log:outputString :s }
        """
        raise NotImplemented
    
    def handle__applyEQ(self, rulesource):
        """Read rules from foo, apply to store, adding conclusions to store
        """
        raise NotImplemented
    
    def handle__filterEQ(self, rulesource):
        """Read rules from foo, apply to store,
        REPLACING store with conclusions
        """
        raise NotImplemented
    
    def handle__rules(self):
        """Apply rules in store to store, adding conclusions to store
        """
        raise NotImplemented
    
    def handle__think(self):
        """as -rules but continue until no more rule matches (or forever!)
        """
        raise NotImplemented
    
    def handle__why(self):
        """Replace the store with an explanation of its contents
        """
        raise NotImplemented
    
    def handle__modeEQ(self, flags):
        """Set modus operandi for inference (see below)
        """
        raise NotImplemented
    
    def handle__thinkEQ(self):
        """as -apply=foo but continue until no more rule matches (or forever!)
        """
        raise NotImplemented

    def handle__purge(self):
        """Remove from store any triple involving anything in class log:Chaff
        """
        raise NotImplemented

    def handle__purge_rules(self):
        """Remove from store any triple involving log:implies
        """
        raise NotImplemented

    def handle__crypto(self):
        """Enable processing of crypto builtin functions.
        Requires python crypto.
        """
        raise NotImplemented

    def handle__chattyEQ(self, level):
        """Verbose output of questionable use, range 0-99
        """
        raise NotImplemented

    def handle__with(self):
        """Pass any further arguments to the N3 store as os:argv values
        """
        raise NotImplemented

    def handle__flatten(self):
        """turn formulas into triples using LX vocabulary
        """
        raise NotImplemented

    def handle__unflatten(self):
        """turn described-as-true LX sentences into formulas
        """
        raise NotImplemented

    def handle__reify(self):
        """reify using the LX vocabulary
        """
        raise NotImplemented

    def handle__unreify(self):
        """unreify using the LX vocabulary
        """
        raise NotImplemented

    def handle__preplug(self, location):
        """prepend this location to the list of hotswap modules
        """
        hotswap.prepend(location)

    def handle__postplug(self, location):
        """append this location to the list of hotswap modules
        """
        hotswap.append(location)

    def handle__unplug(self, location):
        """remove this location from the list of hotswap modules
        """
        hotswap.remove(location)

    def handleExtraArgument(self, arg):
        self.host.load(arg)

    def handleNoArgs(self):
        self.handleExtraArgument("-")

################################################################
    
if __name__ == "__main__":


    host=Host()
    # should pass some extra help text...
    a = MyArgHandler(host=host,
                     program="plwm",
                     version="$Id$",
                     uri="http://www.w3.org/2000/10/swap/doc/cwm")

    hotswap.prepend("wrap_n3")
    hotswap.prepend("wrap_llyn")
    try:
        a.run()
    except hotswap.NoMatchFound, e:
        print e
        print "Try  --help preplug  for more information\n"
        sys.exit(1)

    # who should do this, really?
    store = hotswap.get(pluggable.Store)
    ser = hotswap.get(pluggable.Serializer, initargs=[sys.stdout, ""])
    pump = hotswap.get(pluggable.Pump)
    # which pump?   let that be up to hotswap of course
    pump.pump(store, ser)
    
# $Log$
# Revision 1.5  2003-04-25 19:55:53  sandro
# moved interface class defns out of plwm into pluggable
# implemented wrappers around llyn and notation3
# implemented simple Host class to handle jailing
# works on simple read/store/write an n3 file
#
# Revision 1.4  2003/04/03 05:14:55  sandro
# passes two simple tests
#
# Revision 1.3  2003/04/03 04:51:49  sandro
# fairly stable in skeletal state
#
# Revision 1.2  2003/04/02 20:53:13  sandro
# Added skeletal plugin manager
#
# Revision 1.1  2003/04/02 20:43:22  sandro
# first draft
#
