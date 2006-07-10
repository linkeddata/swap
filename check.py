"""Check a proof

This is a simple proof checker.  It hasn't itself been proved,
and there are probably lots of ways to fool it especially as a deliberate
malicious attack. That is because there are simple things I may have forgotten
to check.

Command line options for debug:
 -v50   Set verbosity to 50 (range is 0 -100)
 -c50   Set verbosity for inference done by cwm code to 50
 -p50   Set verobsity when parsing top 50    

@@for more command line options, see main() in source
"""
__version__ = '$Id$'[1:-1]

from swap.myStore import load, Namespace, formula
from swap.RDFSink import PRED, SUBJ, OBJ
from swap.set_importer import Set
from swap.term import List, Literal, CompoundTerm, BuiltIn, Function
from swap.llyn import Formula #@@ dependency should not be be necessary
from swap.diag import verbosity, setVerbosity, progress
from swap import diag
from swap.query import testIncludes

import swap.llyn # Chosen engine registers itself
import sys # to get exception info for diagnostics


reason = Namespace("http://www.w3.org/2000/10/swap/reason#")
log = Namespace("http://www.w3.org/2000/10/swap/log#")
rdf=Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
rei = Namespace("http://www.w3.org/2004/06/rei#")

chatty = 0
debugLevelForInference = 000
debugLevelForParsing = 0
nameBlankNodes = 0
proofSteps = 0

knownReasons = Set([reason.Premise, reason.Parsing,
                    reason.Inference, reason.Conjunction,
                    reason.Fact, reason.Extraction,
                    reason.CommandLine,
                    reason.Conclusion])


class Policy(object):
    """a proof-checking policy"""
    def documentOK(self, u):
        raise RuntimeError("subclass must implement")
    
    def assumes(self, f):
        """Check whether a formula is an axiom.

        Hmm... move checkBuiltin here?"""
        raise RuntimeError("subclass must implement")

class AllPremises(Policy):
    """A useful testing policy is to accept all premises and no sources.
    """
    def __init__(self):
        return Policy.__init__(self, True)

    def assumes(self, f):
        return True

    def documentOK(self, f):
        return False

class FormulaCache(object):
    def __init__(self):
        self._loaded = {}

    def get(self, uri):
        f = self._loaded.get(uri, None)
        if f == None:
            setVerbosity(debugLevelForParsing)
            f = load(uri, flags="B") # why B? -DWC
            setVerbosity(0)
            self._loaded[uri] = f
        return f

def topLevelLoad(uri=None, flags=''):
        graph = formula()
        graph.setClosureMode("e")    # Implement sameAs by smushing
        graph = load(uri, flags=flags, openFormula=graph)
        bindings = {}
        for s in graph.statementsMatching(pred=reason.representedBy):
            val, _, key = s.spo()
            bindings[key] = val
        return graph.substitution(bindings)


def n3Entails(f, g, skipIncludes=0, level=0):
    """Does f N3-entail g?
    
    First try indexed graph match algorithm, and if that fails,
    unification."""

    v = verbosity()
    setVerbosity(debugLevelForInference)
    try:
        if f is g:
            fyi("Yahooo! #########  ")
            return 1

        if not isinstance(f, Formula) or not isinstance(g, Formula):
            return 0
        #if len(g) != 4: return True #I hope not....
        f.resetRenames()
        try:
            if testIncludes(f,g):
                fyi(lambda : "Indexed query works looking in %s for %s" %(f,g), level)
                
                return 1
        finally:
            f.resetRenames(False)

        return False
        return bool(g.n3EntailedBy(f))
        fyi("Indexed query fails to find match, try unification", level)
        for s in g:
            context, pred, subj, obj = s.quad
            if skipIncludes and pred is context.store.includes:
                fyi("(log:includes found in antecedent, assumed good)", level) 
                continue
            if f.statementsMatching(pred=pred, subj=subj,
                    obj=obj) != []:
                fyi("Statement found in index: %s" % s, level)
                continue

            for t in f.statements:
                fyi("Trying unify  statement %s" %(`t`), level=level+1, thresh=70) 
                if (t[PRED].unify(pred) != [] and
                    t[SUBJ].unify(subj) != [] and 
                    t[OBJ].unify(obj) != []):
                    fyi("Statement unified: %s" % t, level) 
                    break
            else:
                setVerbosity(0)
                fyi("""n3Entailment failure.\nCan't find: %s=%s\nin formula: %s=%s\n""" %
                                (g, g.n3String(), f, f.n3String()), level, thresh=1)
                fyi("""The triple which failed to match was %s""" % s, thresh=-1)
                return 0
        
        return 1
    finally:
         setVerbosity(v)


class InvalidProof(Exception):
    def __init__(self, s, level=0):
        self._s = s
        if True or chatty > 0:
            progress(" "*(level*4), "Proof failed: ", s)

    def __str__(self):
        return self._s

class PolicyViolation(InvalidProof):
    pass

class LogicalFallacy(InvalidProof):
    pass



class Checker(FormulaCache):
    def __init__(self, proof):
        """proof   is the formula which contains the proof
        """
    
        FormulaCache.__init__(self)

        self._checked = {}
        self._pf = proof
        

    def conjecture(self):
        """return the formula that is claimed to be proved and
        the main justification step.
        """
        s = self._pf.the(pred=rdf.type, obj=reason.Proof)
        if not s: raise InvalidProof("no main :Proof step")
        f = self._pf.the(subj=s, pred=reason.gives)
        if not f: raise InvalidProof("main Proof step has no :gives")
        return f, s
        
    def result(self, r, policy, level=0):
        """Get the result of a proof step.

        r       is the step to be checked; in the case of the root reason,
                proof.the(pred=rdf.type, obj=reason.Proof),
                as from `proofStep()`

        level   is just the nesting level for diagnostic output

        Returns the formula proved
        raises InvalidProof (perhaps IOError, others)
        """

        fyi("Starting valid on %s" % r, level=level, thresh=1000)

        f = self._checked.get(r, None)
        if f is not None:
            fyi("Cache hit: already checked reason for %s is %s."%(f, r), level, 80)
            return f

        global proofSteps
        proofSteps += 1

        proof = self._pf
        
        f = proof.any(r, reason.gives)
        if f != None:
            assert isinstance(f, Formula), \
                            "%s gives: %s which should be Formula" % (`r`, f)
            fs = " proof of %s" % f
        else:
            fs = ""
    #    fyi("Validating: Reason for %s is %s."%(f, r), level, 60)

        if r == None:
            if f is None: txt = 'None'
            else: txt = f.n3String()
            raise InvalidProof("No reason for "+`f` + " :\n\n"+ txt +"\n\n", level=level)
        classesOfReason = knownReasons.intersection(proof.each(subj=r, pred=rdf.type))
        if len(classesOfReason) < 1:
            raise InvalidProof("%s does not have the type of any reason" % r)
        if len(classesOfReason) > 1:
            raise InvalidProof("%s has too many reasons, being %s" % (r, classesOfReason))
        t = classesOfReason.pop()
        fyi("%s %s %s"%(t,r,fs), level=level, thresh=10)
        level = level + 1

        if t is reason.Parsing:
            return self.checkParsing(r, f, policy)
        elif t is reason.Inference:
            g = checkGMP(r, f, self, policy, level)
        elif t is reason.Conjunction:
            g = checkConjunction(r, f, self, policy, level)
        elif t is reason.Fact:
            return checkBuiltin(r, f, self, policy, level)
        elif t is reason.Conclusion:
            return checkSupports(r, f, self, policy, level)
        elif t is reason.Extraction:
            return checkExtraction(r, f, self, policy, level)
        elif t is reason.CommandLine:
            raise RuntimeError("shouldn't get here: command line a not a proof step")
        elif t is reason.Premise:
            g = proof.the(r, reason.gives)
            if g is None: raise InvalidProof("No given input for %s" % r)
            fyi(lambda : "Premise is: %s" % g.n3String(), level, thresh=25)
            if not policy.assumes(g):
                raise PolicyViolation("I cannot assume %s" % g)

        # this is crying out for a unit test -DWC
        if g.occurringIn(g.existentials()) != g.existentials(): # Check integrity
            raise RuntimeError(g.debugString())

    ##    setVerbosity(1000)
        fyi("About to check if proved %s matches given %s" % (g, f), level=level, thresh=100)
        if f is not None and f.unify(g) == []:
            diag.chatty_flag=1000
            f.unify(g)
            setVerbosity(0)
            raise LogicalFallacy("%s: Calculated formula: %s\ndoes not match given: %s" %
                    (t, g.debugString(), f.debugString()))
    ##    setVerbosity(0)
        self._checked[r] = g
        fyi(lambda : "\n\nRESULT of %s %s is:\n%s\n\n" %(t,r,g.n3String()), level, thresh=100)
        return g


    def checkParsing(self, r, f, policy):
        proof = self._pf
        res = proof.any(subj=r, pred=reason.source)
        if res == None: raise InvalidProof("No source given to parse", level=level)
        u = res.uriref()
        if not policy.documentOK(u):
            raise PolicyViolation("I cannot trust that source: %s" % u)
        v = verbosity()
        setVerbosity(debugLevelForParsing)
        try:
            g = self.get(u)
        except IOError:
            raise InvalidProof("Can't retreive/parse <%s> because:\n  %s." 
                                %(u, sys.exc_info()[1].__str__()), 0)
        setVerbosity(v)
        if f != None:  # Additional intermediate check not essential
            #@@ this code is untested, no? -DWC
            if f.unify(g) == []:
                raise InvalidProof("""Parsed data does not match that given.\n
                Parsed: <%s>\n\n
                Given: %s\n\n""" % (g,f) , level=level)
        self._checked[r] = g
        return g


    #
    # some of the check* routines below should probably be
    # methods on Checker too.
    #

_TestCEstep = """
@prefix soc: <http://example/socrates#>.
@prefix : <http://www.w3.org/2000/10/swap/reason#>.
@prefix n3: <http://www.w3.org/2004/06/rei#>.

<#p1> a :Premise;
  :gives {soc:socrates     a soc:Man . soc:socrates a soc:Mortal }.
  
<#step1> a :Extraction;
 :because <#p1>;
 :gives { soc:socrates     a soc:Man }.
"""

def checkExtraction(r, f, checker, policy, level=0):
    r"""check an Extraction step.

    >>> soc = Namespace("http://example/socrates#")
    >>> pf = _s2f(_TestCEstep, "http://example/socrates")
    >>> checkExtraction(soc.step1,
    ...                 pf.the(subj=soc.step1, pred=reason.gives),
    ...                 Checker(pf), AllPremises())
    {soc:socrates type soc:Man}
    """
    # """ emacs python mode needs help

    proof = checker._pf
    r2 = proof.the(r, reason.because)
    if r2 == None:
        raise InvalidProof("Extraction: no source formula given for %s." % (`r`), level)
    f2 = checker.result(r2, policy, level)
    if not isinstance(f2, Formula):
        raise InvalidProof("Extraction of %s gave something odd, %s" % (r2, f2), level)

    if not n3Entails(f2, f):
        raise LogicalFallacy("""Extraction %s=%s not included in formula  %s=%s."""
                    #    """ 
                %(f, f.n3String(), f2, f2.n3String()), level=level)
    checker._checked[r] = f # hmm... why different between Extraction and GMP?
    return f


def checkConjunction(r, f, checker, policy, level):
    proof = checker._pf
    components = proof.each(subj=r, pred=reason.component)
    fyi("Conjunction:  %i components" % len(components), thresh=20)
    g = r.store.newFormula()
    for e in components:
        g1 = checker.result(e, policy, level)
        before = len(g)
        g.loadFormulaWithSubstitution(g1)
        fyi(lambda : "Conjunction: adding %i statements, was %i, total %i\nAdded: %s" %
                    (len(g1), before, len(g), g1.n3String()), level, thresh=80) 
    #@@ hmm... don't we check f against g? -DWC
    return g.close()


_TestGMPStep = """
@prefix soc: <http://example/socrates#>.
@prefix : <http://www.w3.org/2000/10/swap/reason#>.
@prefix n3: <http://www.w3.org/2004/06/rei#>.

<#p1> a :Premise;
  :gives {soc:socrates     a soc:Man . }.
<#p2>  a :Premise;
  :gives { @forAll soc:who .
     { soc:who     a soc:Man . } => {soc:who     a soc:Mortal }
  }.
  
<#step1> a :Inference;
 :evidence  ( <#p1> );
 :rule  <#p2>;
 :binding  [
   :variable [ n3:uri "http://example/socrates#who" ];
   :boundTo [  n3:uri "http://example/socrates#socrates" ];
   ].
"""

# """ emacs python mode needs help

def checkGMP(r, f, checker, policy, level=0):
    r"""check a generalized modus ponens step.

    >>> soc = Namespace("http://example/socrates#")
    >>> pf = _s2f(_TestGMPStep, "http://example/socrates")
    >>> f = checkGMP(soc.step1, None, Checker(pf), AllPremises())
    >>> f.n3String().strip()
    u'@prefix : <http://example/socrates#> .\n    \n    :socrates     a :Mortal .'
    """

    # """ emacs python mode needs help

    proof = checker._pf
    evidence = proof.the(subj=r, pred=reason.evidence)
    existentials = Set()
    bindings = {}
    for b in proof.each(subj=r, pred=reason.binding):
        var_rei  = proof.the(subj=b, pred=reason.variable)
        var = getSymbol(proof, var_rei)
        val_rei  = proof.the(subj=b, pred=reason.boundTo)
        # @@@ Check that they really are variables in the rule!
        val = getTerm(proof, val_rei)
        bindings[var] = val
        if proof.contains(subj=val_rei, pred=proof.store.type, obj=reason.Existential):
##        if val_rei in proof.existentials():
            existentials.add(val)

    rule = proof.the(subj=r, pred=reason.rule)

    proofFormula = checker.result(rule, policy, level)
    
    for s in proofFormula.statements:  #@@@@@@ why look here?
        if s[PRED] is log.implies:
            ruleStatement = s
            break
    else: raise InvalidProof("Rule has %s instead of log:implies as predicate.",
        level)

    for v in proofFormula.variables():
        var = proof.newSymbol(v.uriref())
        if var in bindings:
            val = bindings[var]
            del bindings[var]
            bindings[v] = val
            

    # Check the evidence is itself proved
    evidenceFormula = proof.newFormula()
    for e in evidence:
        f2 = checker.result(e, policy, level)
        f2.store.copyFormula(f2, evidenceFormula)
    evidenceFormula = evidenceFormula.close()

    # Check: Every antecedent statement must be included as evidence
    antecedent = proof.newFormula()
    for k in bindings.values():
        if k in existentials: #k in evidenceFormula.existentials() or 
            antecedent.declareExistential(k)
    antecedent.loadFormulaWithSubstitution(ruleStatement[SUBJ], bindings)
    antecedent = antecedent.close()

    #antecedent = ruleStatement[SUBJ].substitution(bindings)
    fyi(lambda : "Bindings: %s\nAntecedent after subst: %s" % (
        bindings, antecedent.debugString()),
        level, 195)
    fyi("about to test if n3Entails(%s, %s)" % (evidenceFormula, antecedent), level, 1)
    fyi(lambda : "about to test if n3Entails(%s, %s)" % (evidenceFormula.n3String(), antecedent.n3String()), level, 80)
    if not n3Entails(evidenceFormula, antecedent,
                    skipIncludes=1, level=level+1):
        raise LogicalFallacy("Can't find %s in evidence for\n"
                    "Antecedent of rule: %s\n"
                    "Evidence:%s\n"
                    "Bindings:%s"
                    %((s[SUBJ], s[PRED],  s[OBJ]), antecedent.n3String(),
                      evidenceFormula.n3String(), bindings),
                    level=level)

    fyi("Rule %s conditions met" % ruleStatement, level=level)

    retVal = proof.newFormula()
    for k in ruleStatement[OBJ].occurringIn(Set(bindings)):
        v = bindings[k]
        if v in existentials: #k in evidenceFormula.existentials() or
            retVal.declareExistential(v)
    retVal.loadFormulaWithSubstitution(ruleStatement[OBJ], bindings)
    retVal = retVal.close()

    return retVal

###    return ruleStatement[OBJ].substitution(bindings)

def getSymbol(proof, x):
    "De-reify a symbol: get the informatuion identifying it from the proof"

    y = proof.the(subj=x, pred=rei.uri)
    if y != None: return proof.newSymbol(y.string)
    
    y = proof.the(subj=x, pred=rei.nodeId)
    if y != None:
        fyi("Warning: variable is identified by nodeId: <%s>" %
                    y.string, level=0, thresh=20)
        return proof.newSymbol(y.string)
    raise RuntimeError("Can't de-reify %s" % x)
	

def getTerm(proof, x):
    "De-reify a term: get the informatuion about it from the proof"
    if isinstance(x, (Literal, CompoundTerm)):
        return x

    val = proof.the(subj=x, pred=rei.value)
    if val != None:  return proof.newLiteral(val.string,
                            val_value.datatype, val.lang)
    return getSymbol(proof, x)


_TestBuiltinStep = """
@keywords is, of, a.
@prefix math: <http://www.w3.org/2000/10/swap/math#>.
@prefix str: <http://www.w3.org/2000/10/swap/string#>.
@prefix : <http://www.w3.org/2000/10/swap/reason#>.

<#step1> a :Fact, :Proof;
  :gives { %s }.
"""

def checkBuiltin(r, f, checker, policy, level=0):
    """Check a built-in step.
    @@hmm... integrate with Policy more?
    
    >>> soc = Namespace("http://example/socrates#")
    >>> pf = _s2f(_TestBuiltinStep % '"abc" str:startsWith "a"',
    ...           "http://example/socrates")
    >>> f = checkBuiltin(soc.step1,
    ...                 pf.the(subj=soc.step1, pred=reason.gives),
    ...                 Checker(pf), AllPremises())
    >>> len(f)
    1


    >>> pf = _s2f(_TestBuiltinStep % '"abc" str:startsWith "b"',
    ...           "http://example/socrates")
    >>> f = checkBuiltin(soc.step1,
    ...                 pf.the(subj=soc.step1, pred=reason.gives),
    ...                 Checker(pf), AllPremises())
    Traceback (most recent call last):
        ...
    LogicalFallacy: Built-in fact does not give correct results: predicate: abc subject: str:startsWith object: b result: None

    """
    # """ help emacs
    
    proof = checker._pf
    pred, subj, obj = atomicFormulaTerms(f)
    fyi("Built-in: testing fact {%s %s %s}" % (subj, pred, obj), level=level)
    if pred is log.includes:
        #log:includes is very special. Huh? Why? -DWC
        if n3Entails(subj, obj):
            checker._checked[r] = f
            return f
        else:
            raise LogicalFallacy("Include test failed.\n"
                        "It seems {%s} log:includes {%s} is false""" %
                        (subj.n3String(), obj.n3String()))
    if not isinstance(pred, BuiltIn):
        raise PolicyViolation("Claimed as fact, but predicate is %s not builtin" % pred, level)
    if  pred.eval(subj, obj, None, None, None, None):
        checker._checked[r] = f
        return f

    if isinstance(pred, Function) and isinstance(obj, Formula):
        result =  pred.evalObj(subj, None, None, None, None)
        fyi("Re-checking builtin %s  result %s against quoted %s"
            %(pred, result, obj))
        if n3Entails(obj, result):
            fyi("Ok for n3Entails(obj, result), checking reverse.")
            if n3Entails(result, obj):
                fyi("Re-checked OK builtin %s  result %s against quoted %s"
                %(pred, result, obj))
                checker._checked[r] = f
                return f
            else:
                fyi("Failed reverse n3Entails!\n\n\n")
        else:
            global debugLevelForInference
            fyi("Failed forward n3Entails!\n\n\n")
            debugLevelForInference = 1000
            n3Entails(obj, result)
            debugLevelForInference = 0
    else:
        result = None

    s, o, r = subj, obj, result
    if isinstance(subj, Formula): s = subj.n3String()
    if isinstance(obj, Formula): o = obj.n3String()
    if isinstance(result, Formula): r = obj.n3String()

##	if n3Entails(result, obj) and not n3Entails(obj, result): a = 0
##	elif n3Entails(obj, result) and not n3Entails(result, obj): a = 1
##	else: a = 2
    raise LogicalFallacy("Built-in fact does not give correct results: "
                         "predicate: %s "
                         "subject: %s "
                         "object: %s "
                         "result: %s" % (s, pred, o, r), level)


def atomicFormulaTerms(f):
    """Check that a formula is atomic and return the p, s, o terms.

    >>> atomicFormulaTerms(_s2f("<#sky> <#color> <#blue>.",
    ...                         "http://example/stuff"))
    (color, sky, blue)
    """
    # """ help emacs
    if len(f) <> 1:
        raise ValueError("expected atomic formula; got: %s." %
                         f.statements)

    #warn("DanC wants to get rid of the StoredStatement interface.")
    c, p, s, o = f.statements[0].quad
    return p, s, o


def checkSupports(r, f, checker, policy, level):
    proof = checker._pf
    pred, subj, obj = atomicFormulaTerms(f)
    fyi("Built-in: testing log:supports {%s %s %s}" % (subj, pred, obj), level=level)
    if pred is not log.supports:
        raise InvalidProof('Supports step is not a log:supports')
        #log:includes is very special
    r2 = proof.the(r, reason.because)
    if r2 is None:
        raise InvalidProof("Extraction: no source formula given for %s." % (`r`), level)
    fyi("Starting nested conclusion", level=level)
    f2 = checker.result(r2, Assumption(subj), level)
    if not isinstance(f2, Formula):
        raise InvalidProof("Extraction of %s gave something odd, %s" % (r2, f2), level)
    fyi("... ended nested conclusion. success!", level=level)
    if not n3Entails(f2, obj):
        raise LogicalFallacy("""Extraction %s not included in formula  %s."""
                %(obj.debugString(), f2.debugString()), level=level)
    checker._checked[r] = f
    return f

class Assumption(Policy):
    def __init__(self, premise):
        self.premise = premise

    def documentOK(self, u):
        return False
    
    def assumes(self, f):
        return n3Entails(self.premise, f)



# Main program 

def usage():
    sys.stderr.write(__doc__)
    
class ParsingOK(Policy):
    """When run from the command-line, the policy is that
    all Parsing's are OK.

    Hmm... shouldn't it be only those that are mentioned
    in the CommandLine step?
    """
    def documentOK(self, u):
        return True
    
    def assumes(self, f):
        return False


def main(argv):
    global chatty
    global debugLevelForInference
    global debugLevelForParsing
    global nameBlankNodes
    setVerbosity(0)
    

    policy=ParsingOK()

    try:
        opts, args = getopt.getopt(argv[1:], "hv:c:p:B:a",
	    [ "help", "verbose=", "chatty=", "parsing=", "nameBlankNodes",
              "allPremises"])
    except getopt.GetoptError:
	sys.stderr.write("check.py:  Command line syntax error.\n\n")
        usage()
        sys.exit(2)
    output = None
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-v", "--verbose"):
	    chatty = int(a)
        if o in ("-p", "--verboseParsing"):
	    debugLevelForParsing = int(a)
        if o in ("-c", "--chatty"):
	    debugLevelForInference = int(a)
        if o in ("-B", "--nameBlankNodes"):
	    nameBlankNodes = 1
        if o in ("-a", "--allPremises"):
	    policy = AllPremises()
    if nameBlankNodes: flags="B"
    else: flags=""
    
    if args:
        fyi("Reading proof from "+args[0])
        proof = topLevelLoad(args[0], flags=flags)
    else:
	fyi("Reading proof from standard input.", thresh=5)
	proof = topLevelLoad(flags=flags)

    # setVerbosity(60)
    fyi("Length of proof formula: "+`len(proof)`, thresh=5)

    try:
        c = Checker(proof)
        proved = c.result(proof.the(pred=rdf.type, obj=reason.Proof),
                          policy=policy)

	fyi("Proof looks OK.   %i Steps" % proofSteps, thresh=5)
	setVerbosity(0)
	print proved.n3String().encode('utf-8')
    except InvalidProof, e:
        progress("Proof invalid:", e)
        sys.exit(-1)


################################
# test harness and diagnostics

def fyi(str, level=0, thresh=50):
    if chatty >= thresh:
        if isinstance(str, (lambda : True).__class__):
            str = str()
	progress(" "*(level*4),  str)
    return None



def _test():
    import doctest
    chatty = 20 #@@
    doctest.testmod()
    

def _s2f(s, base):
    """make a formula from a string.

    Cribbed from llyn.BI_parsedAsN3
    should be part of the myStore API, no?

    >>> _s2f("<#sky> <#color> <#blue>.", "http://example/socrates")
    {sky color blue}

    ^ that test output depends on the way formulas print themselves.
    """
    # """ emacs python mode needs help

    import notation3
    graph = formula()
    graph.setClosureMode("e")    # Implement sameAs by smushing
    p = notation3.SinkParser(graph.store, openFormula=graph, baseURI=base)
    p.startDoc()
    p.feed(s)
    f = p.endDoc()
    f.close()
    bindings = {}
    for s in f.statementsMatching(pred=reason.representedBy):
        val, _, key = s.spo()
        bindings[key] = val
    return f.substitution(bindings)


########

if __name__ == "__main__": # we're running as a script, not imported...
    import sys, getopt

    if '--test' in sys.argv:
        _test()
    else:
        main(sys.argv)


#ends

