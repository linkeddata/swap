"""A package of various inference engines (reasoner), or at least of proxies
for them.

Basic use, simple style

    x>>> import LX.engine
    x>>> e = LX.engine.any()          # just picks one
    x>>> e.setStore(st)
    x>>> e.findInconsistencies()
                NotImplemented
                Timeout, ...
                SearchComplete
    x>>> e.proveConsistent()
                NotImplemented
                Timeout, ...
                SearchComplete

         e.query(Query(retval, formula))

         e.forwardChain(extraRules, intoStore=maybeSelf)



engine.any()
    see what it can import and instantiate, and does one.
    maybe give it the store
    * Given a list of classes (not modules)

WHAT about having this hidden inside the store?   Or as MixIn?


    x>>> import LX.engine.external_otter
    x>>> e = LX.engine.external_otter
    e = 
An engine is something which can look at a the contents of a
store and tell you if it's consistent and what you can 


OLD ToDoPerhaps:
   allow module name and engine name to be different
   give some metadata
   know which modules will work on this platform

"""
__version__ = "$Revision$"
# $Id$

__all__ = ["otter",
           "llynInterface",
           ]
import LX

def any(prefs=__all__, store=None):
    """ other ways of picking one?
    http://c2.com/cgi/wiki?YouArentGonnaNeedIt
    """
    engine = None
    for engine in prefs:
        try:
            mod = __import__("LX.engine."+engine).engine
        except ImportError:
            continue
        try:
            engine = mod.Engine(store=store)
        except NotAvailable, e:
            continue
    if engine is None:
        return NotAvailable()
    return engine

def think(engine=None, kb=None):
    try:
        mod = __import__("LX.engine."+engine).engine
    except ImportError:
        raise RuntimeError, ("No such engine, \"%s\".  Try one of: llyn, %s" %
                             (engine, ", ".join(__all__)))
                            
    mod = getattr(mod, engine)
    mod.think(kb=kb)

# $Log$
# Revision 1.3  2003-11-07 06:53:05  sandro
# support for running RDF Core tests
#
# Revision 1.2  2003/02/14 17:21:59  sandro
# Switched to import-as-needed for LX languages and engines
#
# Revision 1.3  2003/01/29 20:59:33  sandro
# Moved otter language support back from engine/otter to language/otter
# Changed cwm.py to use this, and [ --engine=otter --think ] instead of
# --check.
#
# Revision 1.2  2002/08/29 16:39:55  sandro
# fixed various early typos and ommissions; working on logic bug which is manifesting in description loops
#
# Revision 1.1  2002/08/29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#
