import popen2, time, select, signal, os, string
import tempfile
import sys
import LX.fol

class Error(RuntimeError):
    pass

class AbnormalRun(Error):
    pass

class Interrupted(Exception):
    pass

class NoProofFound(Exception):
    pass

class TimeoutBeforeAnyProof(NoProofFound):
    pass

class SOSEmpty(NoProofFound):
    """The Set-of-Support was empty; there's no where else to search
    for a proof"""
    pass

def quant(text, expr, nameTable, operators, prec, linePrefix):
    # could use gatherLeft
    left = expr.args[0].serializeWithOperators(nameTable, operators, 9999, linePrefix)
    right = expr.args[1].serializeWithOperators(nameTable, operators, 9999, linePrefix)
    return text+left+" ("+right+")"
    
operators = {
    LX.fol.FORALL:    [ 1000, quant, "all " ],
    LX.fol.EXISTS:    [ 1000, quant, "exists " ],
    LX.fol.IMPLIES:   [ 800, "xfx", " -> " ],
    LX.fol.MEANS:     [ 800, "xfx", " <-> " ],
    LX.fol.OR:        [ 790, "xfy", " | " ],
    LX.fol.AND:       [ 780, "xfy", " & " ],
    LX.fol.NOT:       [ 710, "fx", " -" ],
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
        if isinstance(f, LX.fol.Constant):
            s = str(f)
            try:
                (pre,post) = s.split("#")
                result = ns[pre]+"_"+post
            except KeyError:
                ns[pre] = "ns"+str(len(ns))
                print "# autoprefix %s %s" % (ns[pre], pre)
                result = ns[pre]+"_"+post
            except ValueError:
                # original...
                result = "'<"+str(f)+">'"
                # stricter, for mace
                #   result = "uri_"+alnumEscape(str(f))
                # still stricter, mace is a pain
                #result = "const"+str(constCount);
                #constCount += 1
        elif isinstance(f, LX.fol.UniVar):
            result = univar(counter["u"])
            counter["x"].append(result)
            counter["u"] += 1
        elif isinstance(f, LX.fol.ExiVar):
            result = exivar(+counter["e"])
            counter["e"] += 1
        names[f] = result
    else:
        for t in f.args:
            prename(t, names, counter)
        
def serialize(expr):
    #  "asFormula()" used until we have    asIfInwarded  or something
    #print expr
    #print "---------------"
    names = {}
    counter = { "u":0, "e":0, "x":[] }
    if expr.exivars:
        formula = expr.asFormula()
    if isinstance(expr, LX.KB):
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
        return result
    else:
        prename(formula, names, counter)
        return(formula.serializeWithOperators(names, operators))

def run(string, fileBase=",lx.engine.otter"):
    """Run otter on this formula/kb and see what it does.

    >>> from LX.engine.otter import *
    >>> run("a & -a.")
    leaving ,lx.engine.otter.fromOtter
    ['maxproofs']
    """
    if not isinstance(string, str):
        string = serialize(string)
    filename = fileBase+".toOtter"
    out = fileBase+".fromOtter"
    f=open(filename, "w")
    f.write("set(auto).\n")
    f.write("set(prolog_style_variables).\n")
    f.write("clear(control_memory).\n")
    f.write("formula_list(usable).\n")
    f.write(string)
    if not string.endswith("."): f.write(".")
    f.write("\nend_list.")
    f.close()
    return runOtter(filename, out)

def runOtter(toOtterFilename, fromOtterFilename=None, maxSeconds=1):
    """
    Run OTTER for up to maxSeconds, with the given file as input
    text.  Output will be placed in fromOtterFilename (defaults to
    toOtterFilename+".postOtter").

    Returns a sequence of zero of more proofs, or raises an exception.

    I'm torn about input & output being to strings vs files.  Aside
    from the deadlock problems (which we could address with something
    like http://www.python.org/ftp/python/contrib/expect.README), it's
    nice to have the record (so we can eg run otter by hand), and look
    in more detail....

    ToDo: parse the proof output
    ToDo: how to signal timeout AND return results?
    ToDo: maxproofs
    ToDo: caching of serialization...?
    """
    outputLog = None
    child = None
    result = []
    sosEmpty = 0
    timeout = 0
    try:
        # docs: http://www.python.org/doc/current/lib/module-popen2.html
        child = popen2.Popen4("otter < "+toOtterFilename)
        pid = child.pid   # probably the shell, but okay for now
        if not fromOtterFilename:
            fromOtterFilename = toOtterFilename+".postOtter"
        #print "Logging to", fromOtterFilename
        outputLog = open(fromOtterFilename, "w")
        endTime = time.time() + maxSeconds
        while 1:
            timeRemaining = endTime - time.time()
            if timeRemaining > 0.001:
                select.select([child.fromchild], [], [], timeRemaining)
            else:
                timeout = 1
                try:
                    #print "kill -TERM ", pid
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(0.10)
                    #print "kill -KILL ", pid, child.pid
                    os.kill(pid, signal.SIGKILL)
                    os.kill(child.pid, signal.SIGKILL)
                    time.sleep(0.10)
                except OSError, e:   # should only pass "No such process"
                    if (str(e) == "[Errno 3] No such process"):
                        pass
                    else:
                        raise e
            line = child.fromchild.readline()
            if not line:
                break
            
            outputLog.write(line)
            if line.startswith('The command was "otter".  The process ID is '):
                #print "Got pid:", line[-7:-2]
                pid = string.atoi(line[-7:-2])
            if line == "Search stopped by max_proofs option.\n":
                result.append('maxproofs')
            if line == "Search stopped because sos empty.\n":
                sosEmpty = 1
        outputLog.close()
    except KeyboardInterrupt:
        print "Caught Interrupt, now what?"
    message = "During:\n   otter < %s > %s" % (toOtterFilename, fromOtterFilename)
    if result == []:
        if timeout:
            raise TimeoutBeforeAnyProof, message
        if sosEmpty:
            raise SOSEmpty, message
        raise AbnormalRun, message
    #os.unlink(fromOtterFilename)     # or maybe sometimes you want it left around?
    print "leaving", fromOtterFilename
    return result

template = """
include('%(axioms)s').
formula_list(usable).

%(kb)s

-(%(expr)s ).

end_of_list.
"""

#  def prove(kbtext, goaltext, maxSeconds=1, axiomFile="axioms.otter"):
#      """Prove the asserted reification of the kbtext, plus out axioms,
#      implies the goaltext (which may well be the kbtext)
#  
#      Would make more sense as:
#          otter.findContradiction(Conjunction(assertedReification(parse(kbtext)),
#                                              axioms, Negation(parse(goaltext))))
#  
#      """
#      # pass in kb and goal in any form, cache conversions, ...?
#      # check to make sure malformed() is not proved?
#      parseTree = [parse.parse("formula", kbtext+".")]
#      kb = []
#      fsym = describe.describeContentsOfKB(parseTree, lambda t: kb.append(t))
#      kbstr = toShortNames.trans(rdf.asProlog(kb))
#      filename = tempfile.mktemp('.otter')
#      f = open(filename, "w")
#      f.write(template % {"axioms":axiomFile, "kb":kbstr, "expr":goaltext} )
#      f.close()
#      proofs = runOtter(filename, maxSeconds=maxSeconds)
#      os.unlink(filename)
#      return proofs
#  
#  

