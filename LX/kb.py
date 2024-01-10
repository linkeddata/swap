"""Provides the KB class.

Should be called KB.py, ... but we can't rename like that without
messing up windows CVS users.

KB() should perhaps be available just from "import LX", but I don't
know how to make that work without loop problems.

"""
__version__ = "$Revision$"
# $Id$

import re

import LX
import LX.rdf
from . import sniff
import urllib.request, urllib.parse, urllib.error
import LX.language
import pluggable
import LX.nodepath
import LX.loader
from LX.namespace import ns

from sys import stderr

class UnsupportedDatatype(RuntimeError):
    pass

defaultScope = {
    ("legal",): re.compile(r"^[a-zA-Z0-9_]+$"),
    ("hint",): re.compile(r"(?:\/|#)([a-zA-Z0-9_]*)/?$")
    }

nonNegIntPattern = re.compile("[0-9]+")
intPattern = re.compile("-?[0-9]+")
decimalPattern = re.compile("(-?[0-9]*)(\.([0-9])+)?")

class KB(list, pluggable.Store):
    """A Knowledge Base, a list of implicitely conjoined sentences.

    This is comparable to an RDF Graph if the Sentences here are all
    plain triples.

    Actually it's more complicated: we have a list of top level
    quantifications, too, so the elements can be open formulas iff
    their open variables are quantified by the kb. So the kb is a
    sentence of the form

       exists e1 e2 e3 ... (
          all x1 x2 x3 ... (
             formula1 & formula2 & formula3 ...
          )
       )

    (aka a sentence in "prenex" form.)

    Currently inherits from "list" but that's probably a mistake,
    since we'll be wanting to catch updates.   Don't try to modify
    except via add(), please...?

    """

    def __init__(self, namespaceCluster=LX.namespace.ns):
        self.ns = namespaceCluster
        self.exivars = []
        self.univars = []
        self.exIndex = 0
        self.__datatypeValuesChecked = { }
        self.nodes = { }
        self.nodesAreCurrent = 1
        self.nicknames = { }
        self.firstOrder = False
        self.reporter = LX.reporter.theNullReporter

    def clear(self):
        self.__init__()
        self[:] = []

    def __repr__(self):
        return "<KB instance at %x>" % id(self)
    
    def __str__(self):
        scope = defaultScope.copy()
        result = "\nKB Contents:"
        result+= "\n  exivars: "+", ".join(map(LX.expr.getNameInScope, self.exivars, [scope] * len(self.exivars)))
        result+= "\n  univars: "+", ".join(map(LX.expr.getNameInScope, self.univars, [scope] * len(self.univars)))
        result+= "\n  interpretation: "
#        for (key,valueList) in self.__interpretation.iteritems():
#            result+="\n     %s -->  %s"%(key.getNameInScope(scope), ", ".join(map(str, valueList)))
        result+= "\n  formulas: "
        result+= "\n     "
        result+= "\n     ".join(map(LX.expr.getNameInScope, self, [scope] * len(self)))
        result+= "\n"
        #result+= "\n  asFormulaString: "+self.asFormulaString()+"\n"
        #result+= "\n  asFormula:       "+str(self.asFormula())+"\n"
        return result
    
    def asFormulaString(self):
        scope = defaultScope.copy()
        result = ""
        if self.exivars: result += "exists "+" ".join(map(LX.expr.getNameInScope, self.exivars, [scope] * len(self.exivars)))
        if self.univars: result += "all "   +" ".join(map(LX.expr.getNameInScope, self.univars, [scope] * len(self.univars)))
        result += " (" + " &\n    ".join(map(LX.expr.getNameInScope, self, [scope] * len(self))) + ")"
        return result

    def asFormula(self):
        result = self[0]
        for s in self[1:]:
            result = LX.logic.AND(result, s)
        for v in self.univars:
            result = LX.logic.FORALL(v, result)
        for v in self.exivars:
            result = LX.logic.EXISTS(v, result)
        return result
       
    def prep(kb):
        """return a KB if possible, perhaps just the argument; throw
        an error we can't make a KB out of this thing"""
        if isinstance(kb, KB): return kb
        if isinstance(kb, list): return KB(kb)
        # nothing else for now
        raise RuntimeError("Not convertable to a KB")
    prep = staticmethod(prep)

    def addSupportingTheory(self, term):
        """
        If the term, or elements of the term (as an Expr) are datatype
        value constants (as in LX.logic.ConstantForDatatypeValue),
        then we should make sure this KB has a datatype theory to
        support it.
        """
        if not term.isAtomic():
            for e in term.args:   # don't bother with function???! @@@
                # print 
                #assert(e != term)
                self.addSupportingTheory(e)
            return

        # hack in rdf:_(n) here  -- if it's mentioned, makes sure
        # we know it's a ContainerMembershipProperty
        try:
            uri = term.uri
        except AttributeError:
            pass
        else:
            if uri.startswith("http://www.w3.org/1999/02/22-rdf-syntax-ns#_"):
                if uri in self.__datatypeValuesChecked: return
                self.append(LX.logic.RDF(term, ns.rdf.type,
                                         ns.rdfs.ContainerMembershipProperty))
                self.__datatypeValuesChecked[uri] = 1
            return
        

        try:
            lexrep = term.lexrep
            dturi = term.datatype
        except AttributeError:
            return

        pair = (lexrep, dturi)

        if pair in self.__datatypeValuesChecked: return

        #print "DTURI", dturi

        if dturi == ns.xsd.nonNegativeInteger:
            m = nonNegIntPattern.match(lexrep)
            if m is None:
                return  # it's not real...   Report this somehow?
            val = int(lexrep)
            assert(val != 0)   # would have been handled in LX.logic
            assert(val > 0)
            if val > 50:
                raise UnsupportedDatatype("Int %s too big" % val)
            for n in range(1, val+1):
                # print "Describing",n,"via:", n-1, "succ", n
                lesser = LX.logic.ConstantForDatatypeValue(str(n-1), dturi)
                succ = LX.logic.ConstantForURI('foo:succ')
                greater = LX.logic.ConstantForDatatypeValue(str(n), dturi)
                self.append(LX.logic.RDF(lesser,succ,greater))
                self.__datatypeValuesChecked[pair] = 1
            return

        if dturi == ns.xsd.int or dturi == ns.xsd.integer:
            m = intPattern.match(lexrep)
            if m is None:
                return  # it's not real...   Report this somehow?
            val = int(lexrep)
            if val == 0:
                raise RuntimeError("Int 0 not caught in LX.logic? "+repr(lexrep)+", "+repr(dturi))
            if val > 50:
                raise UnsupportedDatatype("Int %s too big" % val)
            if val < 0:
                raise UnsupportedDatatype("Int %s too small" % val)
            for n in range(1, val+1):
                # print "Describing",n,"via:", n-1, "succ", n
                lesser = LX.logic.ConstantForDatatypeValue(str(n-1), dturi)
                succ = LX.logic.ConstantForURI('foo:succ')
                greater = LX.logic.ConstantForDatatypeValue(str(n), dturi)
                self.append(LX.logic.RDF(lesser,succ,greater))
                self.__datatypeValuesChecked[pair] = 1
            return


        if dturi == ns.xsd.decimal:
            m = decimalPattern.match(lexrep)
            if m is None:
                return  # it's not real...   Report this somehow?
            if m.group(3) is not None and int(m.group(3)) != 0:
                raise UnsupportedDatatype("Decimal really a decimal!" % val)
            val = int(m.group(1))
            if val == 0:
                raise RuntimeError("Int 0 not caught in LX.logic? "+repr(lexrep)+", "+repr(dturi))
            if val > 50:
                raise UnsupportedDatatype("Int %s too big" % val)
            if val < 0:
                raise UnsupportedDatatype("Int %s too small" % val)
            for n in range(1, val+1):
                # print "Describing",n,"via:", n-1, "succ", n
                lesser = LX.logic.ConstantForDatatypeValue(str(n-1), dturi)
                succ = LX.logic.ConstantForURI('foo:succ')
                greater = LX.logic.ConstantForDatatypeValue(str(n), dturi)
                self.append(LX.logic.RDF(lesser,succ,greater))
                self.__datatypeValuesChecked[pair] = 1
            return

        if dturi is None:
            self.append(LX.logic.URIConstant("foo:plainLit")(term))
            self.__datatypeValuesChecked[pair] = 1
            return

        if dturi == ns.xsd.string:
            self.__datatypeValuesChecked[pair] = 1
            return
        
        if dturi == ns.rdf.XMLLiteral:
            self.append(LX.logic.URIConstant("foo:xmlLit")(term))
            self.__datatypeValuesChecked[pair] = 1
            return

        raise UnsupportedDatatype("unsupported datatype: "+str(lexrep)+ ", type "+str(dturi))
        
        
    def add(self, formula, p=None, o=None):
        """
        Possibility: call Constant, ConstantForURI, ConstantForDTV,
        if you don't pass in constants...?  Nah.
        """
        self.nodesAreCurrent = 0
        if (p is not None):
            s = formula
            if self.firstOrder:
                self.append(LX.logic.RDF(s,p,o))
                #print >>stderr, "Doing FO"
            else:
                self.append(p(s,o))
                #print >>stderr, "Doing HO"
            self.addSupportingTheory(s)
            self.addSupportingTheory(p)
            self.addSupportingTheory(o)
            return

        #print "KB adding: ",
        #formula.dump()
        #print
        
        ##assert(isinstance(formula, LX.Formula))
        ##assert(LX.fol.isFirstOrderFormula(formula))
        # could check that all its openVars are in are vars

        if (self.firstOrder and
            formula.function != LX.logic.RDF and
            len(formula) == 3):
            #print >>stderr, "FO-ind during formula add"
            formula = LX.logic.RDF(formula[1], formula[0], formula[2])
        
        self.append(formula)
        #print >>stderr, "Doing Formula"
        self.addSupportingTheory(formula)

    def addFrom(self, kb):
        for formula in kb:
            self.add(formula)
        self.exivars.extend(kb.exivars)
        self.univars.extend(kb.univars)
        self.exIndex = self.exIndex + kb.exIndex

    def newExistential(self, name=None):
        if name is None: name = "g"
        v = LX.logic.ExiVar(name)
        self.exivars.append(v)
        return v

    def reifyAsTrue(self):
        flat = KB()
        LX.rdf.flatten(self, flat, indirect=1)
        self.clear()
        self.addFrom(flat)

    def dereifyTrue(self):
        LX.rdf.dereify(self)

    def reifyAsTrueNonRDF(self):
        flat = KB()
        LX.rdf.flatten(self, flat, indirect=0)
        self.clear()
        self.addFrom(flat)

    def serializeWithOperators(self, scope, ops):
        result = ""
        for f in self:
            result = result + f.serializeWithOperators(scope, ops) + ".\n"
        result = result[0:-1]
        return result

        
    def isSelfConsistent(self):
        # should also try mace, icgns, etc...
        try:
            proof = LX.engine.otter.run(self)
            return 0
        except LX.engine.otter.SOSEmpty:
            return 1
        # ... just let other exceptions bubble up, for now

    def gather(self, prefixMap={}):
        """Fetch more knowledge associated with each term in the KB.

        Basically do a web retrieval on each URI term and incorporate
        the result.   This can be repeated if you want a broader
        inclusion.

        The prefixMap is used to override certain URI terms and point
        them somewhere else, such as when the published content for
        OWL doesn't contain the OWL axioms, you might use
          { 'http://www.w3.org/2002/07/owl#':
            'file:web-override/owl/' }

        Mapping to None means no gathering should be done on that prefix.
            
        The actual retrieval and parsing is done by .load(...)
        """
        uris = { }
        for formula in self:
            LX.logic.gatherURIs(formula, uris)
            #print "Did Formula", "Got", uris
        loadable = { }
        for uri in list(uris.keys()):
            #print "Do with: ", uri
            for (key, value) in prefixMap.items():
                if uri.startswith(key):
                    if value is None:
                        uri = None
                        #print " ... Dropped"
                    else:
                        uri = value + uri[len(key):]
                        #print " ... prefix", value
                    break
            if uri is None: continue
            try:
                uri=uri[0:uri.index("#")]
                #print "  ... chopped"
            except ValueError:
                pass
            loadable[uri] = 1
            #print "  ... done, as ", uri
        for uri in list(loadable.keys()):
            self.load(uri)
            
    def load(self, uri):
        loader=LX.loader.Loader(self, uri, reporter=self.reporter)
        loader.run()
    
    def __getattr__(self, name):
        """
        >>> import LX.kb
        >>> kb=LX.kb.KB()
        >>> kb.rdf_type.fromTerm
        LX.logic.URIConstant("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
        """

        # is it a namespace-underscore-name name?
        try:
            (pre, post) = name.split("_", 2)
        except ValueError:
            raise AttributeError("KB has no %s attribute" % name)
        ns = getattr(self.ns, pre)
        term = getattr(ns, post)
        # if this is always true, we could just maintain an inverse map...
        if name != self.nickname(term):
            raise RuntimeError("NAME: %s, TERM: %s , NICK: %s" % (name, term, self.nickname(term)))
        return self.getNode(term)

    def getNode(self, term):
        """Return a Node, which is a lot like a logic.Term, except that
        it's attached to a particular KB.  

        Talking about the nodes properties is like talking about the
        properties of the thing symbolized by that Term, according to
        the attached KB.

        The getattr override allow you to use kb.rdf_type as a
        shorthand for kb.getNode(LX.logic.ConstantForURI("http:.....#type"))
        """
        self.fillNodes()
        return self.nodes.setdefault(term, LX.nodepath.Node(self, term))

    def fillNodes(self):
        """In this implementation, the node API is all
        forward-chained; you call kb.fillNodes() and it
        fills out all the nodes.   You can still refer
        to nodes and paths not in the KB, as needed for adding stuff,
        but we've filled in the __dict__s for the stuff in the KB.

        This wins for being simple, and fast in the common case of the
        KB being loaded then node-queried a lot.

        It's unclear whether I should hide this, in slightly-lazy-eval
        way, or not....
        """
        if self.nodesAreCurrent: return
        self.nodesAreCurrent = 1

        for f in self:
            if f.function == LX.logic.RDF:
                (subj, pred, obj) = f.args
            else:
                try:
                    (pred, subj, obj) = f.all
                except ValueError:
                    pass  
                    # was:  raise RuntimeError, "Not pure-RDF KB!"
                    # but the foo:plainLit terms mess that up.

            #print "PreFill-SPO", subj, pred, obj

            try:
                k = self.nickname(pred)
            except LX.namespace.NoShortNameDeclared:
                # we *could* make one up, but the user wouldn't
                # know what it was anyway, so what's the point?
                # ... don't bother to record this.
                continue
            
            subjNode = self.nodes.setdefault(subj, LX.nodepath.Node(self, subj))
            objNode = self.nodes.setdefault(obj, LX.nodepath.Node(self, obj))

            subjNode.preFill(k, objNode, pred, 0)
            objNode.preFill("is_"+k, subjNode, pred, 1)

        #print self.nodes

    def nickname(self, term):
        try:
            return self.nicknames[term]
        except KeyError:
            pass
        try:
            nick = "_".join(self.ns.inverseLookup(term))
        except KeyError as e:
            raise KeyError(term)
        self.nicknames[term] = nick
        return nick
        


        
if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])
 
# $Log$
# Revision 1.25  2003-11-07 06:53:05  sandro
# support for running RDF Core tests
#
# Revision 1.24  2003/09/17 17:55:57  sandro
# moved load() code over to loader.py; changed to accomodate changes in logic.py
#
# Revision 1.23  2003/09/10 20:12:56  sandro
# store in either RDF(s,p,o) or p(s,o)
#
# Revision 1.22  2003/09/08 17:31:07  sandro
# handle case where no namespace-prefix is declared
#
# Revision 1.21  2003/09/06 04:49:24  sandro
# just in debugging comments
#
# Revision 1.20  2003/09/04 15:23:18  sandro
# make load() able to look at the URI, and grok more mime types
#
# Revision 1.19  2003/09/04 07:14:12  sandro
# fixed plain literal handling
#
# Revision 1.18  2003/09/04 03:15:20  sandro
# removed a leftover reference to __interpretation; diddled with nick exceptions
#
# Revision 1.17  2003/08/25 21:10:01  sandro
# general nodepath support
#
# Revision 1.16  2003/08/25 16:10:41  sandro
# removed all the leftover 'interpretation' stuff
#
# Revision 1.15  2003/08/22 20:49:41  sandro
# midway on getting load() and parser abstraction to work better
#
# Revision 1.14  2003/08/20 11:50:58  sandro
# --dereify implemented (linear time algorithm)
#
# Revision 1.13  2003/08/20 09:26:48  sandro
# update --flatten code path to work again, using newer URI strategy
#
# Revision 1.12  2003/08/01 15:27:21  sandro
# kind of vaguely working datatype support (for xsd unsigned ints)
#
# Revision 1.11  2003/07/31 18:25:15  sandro
# some unknown earlier changes...
# PLUS increasing support for datatype values
#
# Revision 1.10  2003/02/14 17:21:59  sandro
# Switched to import-as-needed for LX languages and engines
#
# Revision 1.9  2003/02/14 00:36:37  sandro
# added constantFor() method
#
# Revision 1.8  2003/02/13 19:48:31  sandro
# a little more thinking/comment about interpretations
#
# Revision 1.7  2003/02/01 05:58:10  sandro
# intermediate lbase support; getting there but buggy; commented out
# some fol checks 
#
# Revision 1.6  2003/01/29 20:59:34  sandro
# Moved otter language support back from engine/otter to language/otter
# Changed cwm.py to use this, and [ --engine=otter --think ] instead of
# --check.
#
# Revision 1.5  2003/01/29 06:09:18  sandro
# Major shift in style of LX towards using expr.py.  Added some access
# to otter, via --check.  Works as described in
# http://lists.w3.org/Archives/Public/www-archive/2003Jan/0024
# I don't like this UI; I imagine something more like --engine=otter
# --think, and --language=otter (instead of --otterDump).
# No tests for any of this.
#
# Revision 1.4  2002/10/03 16:13:02  sandro
# some minor changes to LX-formula stuff, but it's still broken in ways
# that don't show up on the regression test.
#
# mostly: moved llyn-LX conversion stuff out of llyn.py, into
# LX.engine.llynInterface.py
#
# Revision 1.3  2002/10/02 23:32:20  sandro
# not sure
#
# Revision 1.2  2002/08/29 16:39:55  sandro
# fixed various early typos and ommissions; working on logic bug which
# is manifesting in description loops  
#
# Revision 1.1  2002/08/29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

  
