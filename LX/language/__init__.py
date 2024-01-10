"""


"""
__version__ = "$Revision$"
# $Id$

__all__ = ["otter", "abstract", "htables", "lbase"]

import LX

serializers = {
    "otter":  { "module": "LX.language.otter",
              },
#    "lbase":  { "module": "LX.language.lbase",
#              },
    }

parsers = {
    "n3x":    { "module": "LX.language.n3",
              },
    "lbase":  { "module": "LX.language.lbase",
              },
    "kifax":  { "module": "LX.language.kifax",
              },
    "rdflib":  { "module": "LX.language.rdflib_rdfxml",
              },
    "nt":     { "module": "LX.language.rdflib_nt",
              },
    "otter":  { "module": "LX.language.otter",
              },
    }

def getSerializer(language=None, stream=None, flags=""):
    if language in serializers:
        ser = serializers[language]
        moduleName = ser["module"]
        __import__(moduleName)
        return eval(moduleName+".Serializer(stream=stream, flags=flags)")
    else:
        have = ", ".join(list(serializers.keys()))
        raise RuntimeError("No such serializer: \"%s\"\nWe have: %s" %
                             (language, have))

def getParser(language=None, sink=None, flags=""):
    if language in parsers:
        ser = parsers[language]
        moduleName = ser["module"]
        __import__(moduleName)
        if sink is None and flags == "":
            return eval(moduleName+".Parser()")
        # obsolete interface?
        return eval(moduleName+".Parser(sink=sink, flags=flags)")
    else:
        raise RuntimeError("No such parser: \"%s\"\nWe have: %s" % (language, ", ".join(list(parsers.keys()))))
    
# $Log$
# Revision 1.9  2003-11-07 06:53:05  sandro
# support for running RDF Core tests
#
# Revision 1.8  2003/09/17 16:12:41  sandro
# removed n3x; it never materialized
#
# Revision 1.7  2003/08/22 20:49:41  sandro
# midway on getting load() and parser abstraction to work better
#
# Revision 1.6  2003/07/31 18:26:02  sandro
# unknown older stuff
#
# Revision 1.5  2003/07/18 04:37:18  sandro
# added kifax parser
#
# Revision 1.4  2003/02/14 17:21:59  sandro
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
