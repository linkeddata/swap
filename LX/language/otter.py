"""


"""
__version__ = "$Revision$"
# $Id$


import LX
import LX.language.abstract

class Serializer(LX.language.abstract.Serializer):

    def __init__(self):
        LX.language.abstract.Serializer.__init__(self)
        self.overrideTerms = {}
        self.recursing = 0
        
    opTable = {
        # Parts of this table are in the otter user manual
        LX.IMPLIES:   [ 800, "xfx", " -> " ],
        LX.MEANS:     [ 800, "xfx", " <-> " ],
        LX.OR:        [ 790, "xfy", " | " ],
        LX.AND:       [ 780, "xfy", " & " ],
        LX.NOT:       [ 710, "fx", " -" ],
        }

    quantOpName = { LX.ALL: "all",
                    LX.EXISTS: "exists" }
        

    def serializeFormula(self, f, parentPrecedence=9999, linePrefix=""):
        if f[0] in (LX.ALL, LX.EXISTS):
            val = (self.quantOpName[f.operator] + " " +
                   " ".join([self.serializeTerm(x, 9999) for x in f.openVars()]) +
                   " (" + self.serializeFormula(child, 9999, linePrefix) + ")")

            if parentPrecedence < 1000: val = "("+val+")"
            return val
        return LX.language.abstract.Serializer.serializeFormula(self, f, parentPrecedence)

    def serializeTerm(self, t, parentPrecedence):
        try:
            return self.overrideTerms[t]
        except KeyError:
            return LX.language.abstract.Serializer.serializeTerm(self, t, parentPrecedence)

        


defaultSerializer = Serializer()
defaultSerializer.addAbbreviation("rdf_", "http://www.w3.org/1999/02/22-rdf-syntax-ns")
defaultSerializer.addAbbreviation("daml_", "http://www.daml.org/2001/03/daml+oil")

def serialize(x):
    return defaultSerializer.serialize(x)

def test():
    t1 = LX.AtomicFormula(LX.URIRef("a"))
    t2 = LX.AtomicFormula(LX.URIRef("b"))
    t3 = LX.AtomicFormula(LX.URIRef("c"))
    t4 = LX.AtomicFormula(LX.URIRef("d"))
    s = Serializer()
    print s.serialize((t1 & t2) | t3)
    print s.serialize(t1 & (t2 | t3))
    print s.serialize(t1 & (t2 | t3) | t4)
    print s.serialize(t1 & (t2 | t3 | t4))
    print s.serialize([(t1 & t2) | t3, t1 & (t2 | t3)])
    
if __name__ =='__main__':
    test()

# $Log$
# Revision 1.4  2003-01-29 06:09:18  sandro
# Major shift in style of LX towards using expr.py.  Added some access
# to otter, via --check.  Works as described in
# http://lists.w3.org/Archives/Public/www-archive/2003Jan/0024
# I don't like this UI; I imagine something more like --engine=otter
# --think, and --language=otter (instead of --otterDump).
# No tests for any of this.
#
# Revision 1.3  2002/10/03 16:13:03  sandro
# some minor changes to LX-formula stuff, but it's still broken in ways
# that don't show up on the regression test.
#
# mostly: moved llyn-LX conversion stuff out of llyn.py, into
# LX.engine.llynInterface.py
#
# Revision 1.2  2002/10/02 22:56:35  sandro
# Switched cwm main-loop to keeping state in llyn AND/OR an LX.formula,
# as needed by each command-line option.  Also factored out common
# language code in main loop, so cwm can handle more than just "rdf" and
# "n3".  New functionality is not thoroughly tested, but old functionality
# is and should be fine.  Also did a few changes to LX variable
# handling.
#
# Revision 1.1  2002/08/29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

 
