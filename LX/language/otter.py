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
    LX.logic.EQUALS:    [ 600, "xfx", " = " ],
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
verysafe = ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        'abcdefghijklmnopqrstuvwxyz'
        '0123456789')

mostchars = ('ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        'abcdefghijklmnopqrstuvwxyz'
        '0123456789' ' ()[]:{}"<>/.,%')

def escapeUnlessSafe(s, safe=verysafe):
    """Encode one string in another, hex-escaping all unsafe chars.   We
    use _xx instead of %xx because we want to even fit inside a C-identifier.

    If your safechars has "_" in it, this is not reversable.
    """
    res = list(s)
    for i in range(len(res)):
        c = res[i]
        if c not in safe:
            res[i] = '_%02X' % ord(c)
    return ''.join(res)


class Serializer:

    def __init__(self, stream=None, flags=""):
        self.stream = stream
        self.mace = flags.count("m")
        # print "Flags:", self.mace, flags
        self.constCount = 0
        self.nsused = { }

    def makeComment(self, comment):
        self.stream.write("% "+comment.replace("\n","\\n")+"\n")
        
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
                self.prename(f, names, counter)
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

            nspres = self.nsused.keys()
            nspres.sort()
            for pre in nspres:
                self.makeComment(" prefix %s_ <%s#>" % (pre, self.nsused[pre]))

            self.stream.write(result)
            self.stream.write("\n")
        else:
            self.prename(formula, names, counter)
            self.stream.write(formula.serializeWithOperators(names, operators))

    def prename(self, f, names, counter):
        global ns
        if names.has_key(f): return
        if operators.has_key(f): return
        if f.isAtomic():
            #print "What to do with:", f
            result = None
            if (isinstance(f, LX.logic.Constant) or
                isinstance(f, LX.logic.Predicate) or 
                isinstance(f, LX.logic.Function)):
                s = str(f)
                try:
                    (pre,post) = s.split("#")
                    result = ns[pre]+"_"+post
                    self.nsused[ns[pre]] = pre
                except KeyError:
                    ns[pre] = "ns"+str(len(ns))
                    self.nsused[ns[pre]] = pre
                    # self.makeComment("autoprefix %s %s" % (ns[pre], pre))
                    result = ns[pre]+"_"+post
                except ValueError:
                    ee = escapeUnlessSafe(s)
                    if s == ee:
                        result = s
                    elif self.mace == 0:
                        result = "'"+escapeUnlessSafe(s,safe=mostchars)+"'"
                    elif self.mace == 1:
                        result = "uri_"+escapeUnlessSafe(s)
                        self.makeComment(result+" is "+s)
                    else:    # mace mace
                        result = "const"+str(self.constCount);
                        self.constCount += 1
                        self.makeComment(result+" is "+s)
            elif isinstance(f, LX.logic.UniVar):
                result = univar(counter["u"])
                counter["x"].append(result)
                counter["u"] += 1
            elif isinstance(f, LX.logic.ExiVar):
                result = exivar(+counter["e"])
                counter["e"] += 1
            else:
                raise RuntimeError, ("Can't serialize term %s of class %s" %
                                     (str(f), f.__class__))
            #print "names %s is %s" % (f, result)
            names[f] = result
        else:
            for t in f.all:
                self.prename(t, names, counter)


def serialize(kb):
    str = cStringIO.StringIO()
    s = Serializer(str)
    s.serializeKB(kb)
    return str.getvalue()

# $Log$
# Revision 1.8  2003-02-14 19:40:32  sandro
# working lbase -> otter translation, with regression test
#
# Revision 1.7  2003/02/14 17:21:59  sandro
# Switched to import-as-needed for LX languages and engines
#
# Revision 1.6  2003/02/14 00:36:08  sandro
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

 
