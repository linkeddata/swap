import popen2, time, select, signal, os, string
import tempfile
import sys
import LX.fol
import LX.language.otter

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

def kill(pid):
    #print "kill -TERM ", pid
    os.kill(pid, signal.SIGTERM)
    time.sleep(0.10)
    #print "kill -KILL ", pid, child.pid
    os.kill(pid, signal.SIGKILL)
    os.kill(child.pid, signal.SIGKILL)
    time.sleep(0.10)

def think(kb=None):
    print("\n\n# Running Otter...")
    try:
        proof = LX.engine.otter.run(kb)
        print("# Contradiction found.")
        print("# for details try:  cat ,lx.engine.otter.fromOtter")
    except LX.engine.otter.SOSEmpty:
        print("# Consistency proven.")
        print("# for details try:  cat ,lx.engine.otter.fromOtter")
        print("# Done running Otter [ Inferences NOT incorporated back into cwm ]")

def run(string, fileBase=",lx.engine.otter", includes=None, maxSeconds=1,
        inputFileName=None, outputFileName=None):
    """Run otter on this formula/kb and see what it does.

    >>> from LX.engine.otter import *
    >>> run("a & -a.")
    ['maxproofs']
    """
    if not isinstance(string, str):
        string = LX.language.otter.serialize(string)
    if inputFileName:
        filename = inputFileName
    else:
        filename = fileBase+".toOtter"
    if outputFileName:
        out = outputFileName
    else:
        out = fileBase+".fromOtter"
    f=open(filename, "w")
    f.write("set(auto).\n")
    #f.write("set(prolog_style_variables).\n")

    #  this is needed for completeness, but slows things down a lot
    f.write("clear(control_memory).\n")
    # undocumented (as yet) otter feature to let SIGINT just kill it
    f.write("clear(sigint_interact).\n")

    if includes:
        for i in includes:
            f.write("include('%s').\n" % i)
    
    f.write("formula_list(usable).\n")
    f.write(string)
    # if not string.endswith("."): f.write(".")
    f.write("\nend_of_list.")
    f.close()
    return runOtter(filename, out, maxSeconds=maxSeconds)

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
                    kill(pid)
                except OSError as e:   # should only pass "No such process"
                    if (str(e) == "[Errno 3] No such process"):
                        pass
                    else:
                        raise e
            line = child.fromchild.readline()
            if not line:
                break
            
            outputLog.write(line)
            if line.startswith('The command was "otter".  The process ID is '):
                pid = string.atoi(line[44:-2])
                #print "Line: ",line
                #print "Got pid:", pid
            if line == "Search stopped by max_proofs option.\n":
                result.append('maxproofs')
            if line == "Search stopped because sos empty.\n":
                sosEmpty = 1
        outputLog.close()
    except KeyboardInterrupt as k:
        print()
        print("Caught Interrupt; killing sub-reasoner process")
        try:
            kill(pid)
        except OSError:
            pass
        raise KeyboardInterrupt(k)

    message = "During:\n   otter < %s > %s" % (toOtterFilename, fromOtterFilename)
    if result == []:
        if timeout:
            raise TimeoutBeforeAnyProof(message)
        if sosEmpty:
            raise SOSEmpty(message)
        raise AbnormalRun(message)
    #os.unlink(fromOtterFilename)     # or maybe sometimes you want it left around?
    #print "leaving", fromOtterFilename
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

