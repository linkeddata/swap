#!/usr/bin/env python

"""
     plwm (pronounced plume) is a plugable rewrite of cwm.  it should
     be a drop-in replacement, eventually renamed cwm.py.

     does --n3  mean the new default language is n3, or the new
     default parser is Notation3 ?   I think it's the language,
     which means (1) you need a parser which can handle it, and
     (2) you need to tell the parser that's the language.
     
"""

import sys
import ArgHandler
import hotswap

# Import ourself, so our classes are known as plwm.Foo, not
# just __main__.Foo.   This is important since hotswap 
# compares class names to determine interface conformance.
import plwm

class NotImplented(RuntimeError):
    pass

################################################################
##
##  The basic interfaces implemented by the hotswap modules
##  we load and use.
##

class Store:
    """
    A passive repository for structured data.   See KB.
    """
    pass

class Opener:
    """
    A general communications driver which can establish
    read and write connections to various external storage
    and processing facilities.
    """
    pass

class Engine:
    """
    A server (passive) object which works with a Store, potentially
    doing complex queries and inference.  See KB.
    """
    pass

class KB:
    """
    The combination of a Store and an Engine.  Sometimes it makes more
    sense to treat the pair as one unit; sometimes it makes to
    consider them separately.  
    """
    pass

class Parser:
    """
    An active (client) object which reads from a stream (produced
    by an Opener) and writes to a Store.
    """
    pass

class Serializer:
    """
    A passive (server) object which receives content like a Store but
    instead of keeping it, write it out to an output stream.
    """
    pass

class Pump:
    """
    An active (client) object which queries a KB and sends the results
    to a Receiver (Store or Serializer).
    """
    pass

class Receiver:
    """
    Something to which you can send structured information.
    """
    pass

################################################################

class MyArgHandler(ArgHandler.ArgHandler):

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
        parser = hotswap.get(plwm.Parser)
        ih = hotswap.get(plwm.Opener)
        store = hotswap.get(plwm.Store)
        stream = ih.open(arg)
        parser.parse(stream, store)

    def handleNoArgs(self):
        self.handleExtraArgument("-")

################################################################
    
if __name__ == "__main__":
    # should pass some extra help text...
    a = MyArgHandler(program="plwm",
                     version="$Id$",
                     uri="http://www.w3.org/2000/10/swap/doc/cwm")

    hotswap.append("sillyParser")
    try:
        a.run()
    except hotswap.NoMatchFound, e:
        print e
        print "Try  --help preplug  for more information\n"
        sys.exit(1)


# $Log$
# Revision 1.4  2003-04-03 05:14:55  sandro
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
