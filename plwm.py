#!/usr/bin/env python

"""
     plwm (pronounced plume) is a plugable rewrite of cwm.  it should
     be a drop-in replacement, eventually renamed cwm.py.

"""

from ArgHandler import ArgHandler;
from PluginManager import PluginManager;

class NotImplented(RuntimeError):
    pass

################################################################

plugger = PluginManager()

class MyArgHandler(ArgHandler):

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
        """prepend this location to the list of plugins
        """
        plugger.prepend(location)

    def handle__postplug(self, location):
        """append this location to the list of plugins
        """
        plugger.append(location)

    def handle__unplug(self, location):
        """remove this location from the list of plugins
        """
        plugger.remove(location)

################################################################
    
if __name__ == "__main__":
    a = MyArgHandler(program="plwm",
                     version="$Id$",
                     uri="http://www.w3.org/2000/10/swap/doc/cwm")
    a.run()
else:
    raise RuntimeError, "this is not a module"

# $Log$
# Revision 1.1  2003-04-02 20:43:22  sandro
# first draft
#
