"""A package of various inference engines, or at least of consistent
interfaces to them.

ToDoPerhaps:
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

def think(engine=None, kb=None):
    try:
        mod = __import__("LX.engine."+engine).engine
    except ImportError:
        raise RuntimeError, ("No such engine, \"%s\".  Try one of: llyn, %s" %
                             (engine, ", ".join(__all__)))
                            
    mod = getattr(mod, engine)
    mod.think(kb=kb)

# $Log$
# Revision 1.2  2003-02-14 17:21:59  sandro
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
