"""


"""
__version__ = "$Revision$"
# $Id$


import LX
from string import split

class Serializer:

    # Must have an opTable defined, like:

    # this is the classic prolog way to do operators, as in
    #    http://www.forestro.com/kiev/kiev-187_4.html
    #    http://cs.wwc.edu/~aabyan/Logic/Prolog.html
    #    http://www.trinc-prolog.com/doc/pl_lang2.htm
    #
    # The first number is the "precedence" or "priority", but I think of
    # of it as "looseness", since higher numbered operators bind more
    # loosely to their arguments.
    #
    ##opTable = {
    ##    LX.IMPLIES:   [ 800, "xfx", "->" ],
    ##    LX.OR:        [ 790, "xfy", "|" ],
    ##    LX.AND:       [ 780, "xfy", "&" ],
    ##}

    # TODO: handling indentation - when should we start a new line?

    def __init__(self):
        self.abbrev = { }
        
    def serialize(self, arg):
        if isinstance(arg, LX.Formula): return self.serializeFormula(arg)
        if isinstance(arg, list): return self.serializeKB(arg)
        raise RuntimeError, "Don't know how to serialize \""+`arg`+"\""

    def serializeKB(self, kb):
        kb = LX.KB.prep(kb)
        result = ""
        for f in kb:
            result = result + self.serializeFormula(f) + ".\n"
        result = result[0:-1]
        return result

    def serializeFormula(self, f, parentPrecedence=9999, linePrefix=""):
        #print "Abstract SerializeFormula "+`f`

        if f[0] == LX.ATOMIC_SENTENCE:
            result = "rdf("
            for term in f[1:]:
                result = result + self.serializeTerm(term, 9999) + ", "
                #result = result + "[[" +`term`+"]]   "
            result = result[0:-2] + ")"
            return result
        
        op = self.opTable[f[0]]
        prec = op[0]
        form = op[1]
        text = op[2]
        prefix = ""; suffix = ""
        # first pass, not thinking about the difference between "x" and "y",
        # so we'll get some extra parens
        if prec >= parentPrecedence:
            prefix = "("; suffix = ")"
        if form == "xfx" or form == "xfy" or form == "yfx":
            assert(len(f) == 3)
            left = self.serializeFormula(f[1], prec, linePrefix)
            right = self.serializeFormula(f[2], prec, linePrefix)
            if 1 or (len(left) + len(right) < 50):
                result = prefix + left + text + right + suffix
            else:
                linePrefix = "  " + linePrefix
                left = self.serializeFormula(f[1], prec, linePrefix)
                right = self.serializeFormula(f[2], prec, linePrefix)
                result = (prefix + "\n" + linePrefix + left + text +
                          "\n" + linePrefix + right + suffix)
        elif form == "fxy":
            assert(len(f) == 3)
            result = (prefix + text + self.serializeFormula(f[1], prec, linePrefix)
                      + " " + self.serializeFormula(f[2], prec, linePrefix) + suffix)
        elif form == "fx" or form == "fy":
            assert(len(f) == 2)
            result = prefix + text + self.serializeFormula(f[1], prec, linePrefix)
        else:
            raise RuntimeError, "unknown form in opTable"
        return result

    def addAbbreviation(self, short, long):
        self.abbrev[short] = long
        self.abbrev[long] = short

    def serializeTerm(self, t, parentPrecedence):
        # print "SerializeTerm "+`t`+", "+t.racine
        if isinstance(t, LX.URIRef):
            try:
                return self.abbrev[t.racine]+t.fragment
            except:
                # should we do auto-abbreviation???
                return "'<"+t.value+">'"
        raise RuntimeError, "No serialization for term: "+`t`

    
# $Log$
# Revision 1.3  2002-10-02 22:56:35  sandro
# Switched cwm main-loop to keeping state in llyn AND/OR an LX.formula,
# as needed by each command-line option.  Also factored out common
# language code in main loop, so cwm can handle more than just "rdf" and
# "n3".  New functionality is not thoroughly tested, but old functionality
# is and should be fine.  Also did a few changes to LX variable
# handling.
#
# Revision 1.2  2002/08/29 17:10:38  sandro
# fixed description bug; flatten runs and may even be correct
#
# Revision 1.1  2002/08/29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

