"""


"""
__version__ = "$Revision$"
# $Id$


import LX
import LX.language.abstract

class Serializer(LX.language.abstract.Serializer):

    opTable = {
        # Parts of this table are in the otter user manual
        LX.IMPLIES:   [ 800, "xfx", " -> " ],
        LX.MEANS:     [ 800, "xfx", " <-> " ],
        LX.OR:        [ 790, "xfy", " | " ],
        LX.AND:       [ 780, "xfy", " & " ],
        LX.NOT:       [ 710, "fx", " -" ],
        }

    def serializeFormula(self, f, parentPrecedence=9999, linePrefix=""):
        # print "Otter SerializeFormula "+`f`
        if f[0] == LX.ALL:
            assert(len(f) == 3)
            vars, child = f.collectLeft(LX.ALL)
            val = ("all " +
                   " ".join([self.serializeTerm(x, 9999) for x in vars]) +
                   " (" + self.serializeFormula(child, 9999, linePrefix) + ")")
            if parentPrecedence < 1000: val = "("+val+")"
            return val
        if f[0] == LX.EXISTS:
            assert(len(f) == 3)
            return ("(exists " + self.serializeTerm(f[1], 9999) +
                    " (" + self.serializeFormula(f[2], 9999, linePrefix) + "))")
        return LX.language.abstract.Serializer.serializeFormula(self, f, parentPrecedence)
        

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
# Revision 1.1  2002-08-29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

 
