"""


"""
__version__ = "$Revision$"
# $Id$

import cStringIO
import LX
import LX.kb
import LX.logic

def quant(text, expr, nameTable, operators, prec, linePrefix):
    # could use gatherLeft
    left = expr.args[0].serializeWithOperators(nameTable, operators, 9999, linePrefix)
    right = expr.args[1].serializeWithOperators(nameTable, operators, 9999, linePrefix)
    return text+left+" ("+right+")"
    
operators = {
    LX.logic.FORALL:    [ 1000, quant, "all " ],
    LX.logic.EXISTS:    [ 1000, quant, "exists " ],
    LX.logic.IMPLIES:   [ 800, "xfx", " -> " ],
    LX.logic.MEANS:     [ 800, "xfx", " <-> " ],
    LX.logic.OR:        [ 790, "xfy", " | " ],
    LX.logic.AND:       [ 780, "xfy", " & " ],
    LX.logic.NOT:       [ 710, "fx", " -" ],
    }

def univar(count):
    try:
        return ["A", "B", "C", "D", "E", "F", "G", "H"][count]
    except IndexError:
        pass
    return "X"+str(count-8)

def exivar(count):
    try:
        return ["s", "t", "u"][count]
    except IndexError:
        pass
    return "s"+str(count-3)

# Obviously there should be some more general mechanism here, but
# in some ways (like using "_" for prefixing) this is otter specific....

ns = {
    "http://www.w3.org/1999/02/22-rdf-syntax-ns": "rdf",
    "http://www.w3.org/2000/01/rdf-schema":"rdfs",
    "http://www.w3.org/2000/10/swap/log": "log",
    "http://www.daml.org/2001/03/daml+oil": "daml",
    "http://www.w3.org/2002/03owlt/ontAx": "ontAx",
    }

# borrowed & modified from urllib.py
safe = ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        'abcdefghijklmnopqrstuvwxyz'
        '0123456789' '_')

def alnumEscape(s):
    res = list(s)
    for i in range(len(res)):
        c = res[i]
        if c not in safe:
            res[i] = '_%02X' % ord(c)
    return ''.join(res)

constCount = 0

def prename(f, names, counter):
    global ns
    global constCount
    if names.has_key(f): return
    if f.isAtomic():
        #print "What to do with:", f
        result = None
        if isinstance(f, LX.logic.Constant):
            s = str(f)
            try:
                (pre,post) = s.split("#")
                result = ns[pre]+"_"+post
            except KeyError:
                ns[pre] = "ns"+str(len(ns))
                ###print "# autoprefix %s %s" % (ns[pre], pre)    # @@@@@@
                result = ns[pre]+"_"+post
            except ValueError:
                # original...
                result = "'<"+str(f)+">'"
                # stricter, for mace
                #   result = "uri_"+alnumEscape(str(f))
                # still stricter, mace is a pain
                #result = "const"+str(constCount);
                #constCount += 1
        elif isinstance(f, LX.logic.UniVar):
            result = univar(counter["u"])
            counter["x"].append(result)
            counter["u"] += 1
        elif isinstance(f, LX.logic.ExiVar):
            result = exivar(+counter["e"])
            counter["e"] += 1
        names[f] = result
    else:
        for t in f.args:
            prename(t, names, counter)
        
class Serializer:

    def __init__(self, stream, flags=""):
        self.stream = stream
        # no flags right now... 

    def makeComment(self, comment):
        self.stream.write("% "+comment+"\n")
        
    def serializeKB(self, expr):
        names = {}
        counter = { "u":0, "e":0, "x":[] }
        if expr.exivars:
            formula = expr.asFormula()
        if isinstance(expr, LX.kb.KB):
            result = ""
            for f in expr:
                # Let's do separate namings for each formula, although
                # this is a bit questionable.  (ns stuff is global, still).
                names = {}
                counter = { "u":0, "e":0, "x":[] }
                prename(f, names, counter)
                if (counter["x"]):
                    result += "\nall "
                    for x in counter["x"]:
                        result += x+" "
                    result += "(\n   "
                result += f.serializeWithOperators(names, operators)
                if (counter["x"]):
                    result += "\n)"
                result += ".\n"
            result = result[:-1]
            self.stream.write(result)
            self.stream.write("\n")
        else:
            prename(formula, names, counter)
            self.stream.write(formula.serializeWithOperators(names, operators))

def serialize(kb):
    str = cStringIO.StringIO()
    s = Serializer(str)
    s.serializeKB(kb)
    return str.getvalue()

# $Log$
# Revision 1.6  2003-02-14 00:36:08  sandro
# added newline; changed for reorg elsewhere
#
# Revision 1.5  2003/01/29 20:59:33  sandro
# Moved otter language support back from engine/otter to language/otter
# Changed cwm.py to use this, and [ --engine=otter --think ] instead of
# --check.
#
# Revision 1.4  2003/01/29 06:09:18  sandro
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

 
