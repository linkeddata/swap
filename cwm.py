#! /usr/bin/python
"""
$Id$

Closed World Machine

(also, in Wales, a valley)

This is an engine which knows a certian amount of stuff and can manipulate it.


http://www.w3.org/DesignIssues/Notation3
Date: 2000/07/17 21:46:13  



---- hmmmm ... not expandable - a bit of a trap.

DWC:
idea: migrate toward CSS notation?

idea: use notation3 for wiki record keeping.

TBL: more cool things:
 - sucking in the schema (http library?) - to know about r see r
 - metaindexes - "to know more about x please see r" - described by
 - equivalence handling inc. equivalence of equivalence
 - regeneration of genids on output. - DONE
 - repreentation of genids and foralls in model
- regression test - DONE (once!)
 Shakedown:
 - Find all synonyms of synonym
 - Find closure for all synonyms
 - Find superclass closure?
 - Use unambiguous property to infer synomnyms

 - Separate the store hash table from the parser. - DONE
 
 Manipulation:
  { } as notation for bag of statements
  - filter 
  - graph match
  - recursive dump of nested bags
Validation:  validate domain and range constraints against closuer of classes and
   mutually disjoint classes.

- represent URIs bound to same equivalence closuse object?

Translation;  Try to represent the space (or a context) using a subset of namespaces

- Other forms of context - explanation of derivation by rule or merging of contexts
1
"""



import string
import urlparse
import re
import StringIO

import notation3    # N3 parsers and generators, and RDF generator
import xml2rdf      # RDF1.0 syntax parser to N3 RDF stream

# Magic resources we know about

RDF_type_URI = notation3.RDF_type_URI # "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
DAML_equivalentTo_URI = notation3.DAML_equivalentTo_URI


Logic_NS = notation3.Logic_NS


# The statement is stored as a quad - affectionately known as a triple ;-)

CONTEXT = notation3.CONTEXT
PRED = notation3.PRED  # offsets when a statement is stored as a Python tuple (p, s, o, c)
SUBJ = notation3.SUBJ
OBJ = notation3.OBJ

PARTS =  PRED, SUBJ, OBJ
ALL4 = CONTEXT, PRED, SUBJ, OBJ

# The parser outputs quads where each item is a pair   type, value

RESOURCE = notation3.RESOURCE        # which or may not have a fragment
LITERAL = notation3.LITERAL         # string etc - maps to data:
ANONYMOUS = notation3.ANONYMOUS       # existentially qualified unlabelled resource
VARIABLE = notation3.VARIABLE


chatty = 0   # verbosity flag



########################################  Storage URI Handling
#
#  In general an RDf resource - here a Thing, has a uriRef rather
# than just a URI.  It has subclasses of Resource and Fragment.
# (libwww equivalent HTParentAnchor and HTChildAnchor IIRC)
#
# Every resource has a symbol table of fragments.
# A resource may (later) have a connection to a bunch of parsed stuff.
#
# We are nesting symbols two deep let's make a symbol table for each resource
#
#  The statement store lists are to reduce the search time
# for triples in some cases. Of course, indexes would be faster.
# but we can figure out what to optimize later.  The target for now
# is being able to find synonyms and so translate documents.

        
class Thing:
    def __init__(self):
      self.occursAs = [], [], [], []  #  List of statements in store by part of speech       
            
    def __repr__(self):   # only used for debugging I think
        return self.representation()

    def representation(self, base=None):
        """ in N3 """
        return "<" + self.uriref(base) + ">"

    def generated(self):
        """  Is this thing a genid - is its name arbitrary? """
        return 0    # unless overridden

    def n3_anonymous(self, context): 
        """ Can be output as an anonymous node in N3
        Returns number of incoming links (1 or 2) including forSome link
        or zero if self can NOT be represented as an anonymous node.
        """
        incoming = self.occurrences(OBJ,context)
        if incoming > 2:
#            print "## Anon: %s has %i incoming nodes" % (`self`, incoming)
            return 0  # Not an anonymous node

        if self.occurrences(PRED, context) >0:
#            print "## Anon: %s has %i pred occurrences" % (`self`, self.occurrences(PRED, context))
            return 0 # Occurs as a predicate => needs a name in N3
        
        for s in self.occursAs[OBJ]:
            con, pred, subj, obj = s.triple
            if con is context and subj is context:
#                print "## Anon - what about", `pred`
                if pred.uriref(None)==Logic_NS + "forSome":
#                    print "## Anon: %s has %i incoming and passes" % (`self`, incoming)
                    return incoming
            
#        print "## Anon: %s has no existential" % (`self`,)
        return 0  # No existential found
    
    def asPair(self):
        return (RESOURCE, self.uriref(None))
    
    def occurrences(self, p, context):
        """ Count the times a thing occurs in a statement in given context
        """
        if context == None:   # meaning any
            return len(self.occursAs[p])
        else:
            n = 0
            for s in self.occursAs[p]:
                if s.triple[CONTEXT] is context:
                    n = n+1
            return n

class Resource(Thing):
    """   A Thing which has no fragment
    """
    
    def __init__(self, uri):
        Thing.__init__(self)
        self.uri = uri
        self.fragments = {}

    def uriref(self, base):
        if base is self :  # @@@@@@@ Really should generate relative URI!
            return ""
        else:
            return self.uri

    def internFrag(r,fragid):
            f = r.fragments.get(fragid, None)
            if f: return f
            f = Fragment(r, fragid)
            r.fragments[fragid] = f
            return f
                
    def internAnonymous(r, fragid):
            f = r.fragments.get(fragid, None)
            if f: return f
            f = Anonymous(r, fragid)
            r.fragments[fragid] = f
            return f
                
                
    
class Fragment(Thing):
    """    A Thing which DOES have a fragment id in its URI
    """
    def __init__(self, resource, fragid):
        Thing.__init__(self)

        self.resource = resource
        self.fragid = fragid

    def uriref(self, base):
        return self.resource.uriref(base) + "#" + self.fragid

    def representation(self,  base=None):
        """ Optimize output if prefixes available
        """
        return  "<" + self.uriref(base) + ">"

    def generated(self):
         """ A generated identifier?
         This arises when a document is parsed and a arbitrary
         name is made up to represent a node with no known URI.
         It is useful to know that its ID has no use outside that
         context.
         """
         return self.fragid[0] == "_"  # Convention for now @@@@@
                                # parser should use seperate class?


class Anonymous(Fragment):
    def __init__(self, resource, fragid):
        Fragment.__init__(self, resource, fragid)

    def generated(self):
        return 1

    def asPair(self):
        return (ANONYMOUS, self.uriref(None))
        
        
class Literal(Thing):
    """ A Literal is a data resource to make it clean

    really, data:application/n3;%22hello%22 == "hello" but who
    wants to store it that way?  Maybe we do... at least in theory and maybe
    practice but, for now, we keep them in separate subclases of Thing.
    """
    Literal_URI_Prefix = "data:application/n3;"

    def __init__(self, string):
        Thing.__init__(self)
        self.string = string    #  n3 notation EXcluding the "  "

    def __repr__(self):
        return self.string

    def asPair(self):
        return (LITERAL, self.string)

    def representation(self, base=None):
        return '"' + self.string + '"'   # @@@ encode quotes; @@@@ strings containing \n

    def uriref(self, base=None):      # Unused at present but interesting! 2000/10/14
        return  Literal_URI_Prefix + uri_encode(self.representation())

def uri_encode(str):
        """ untested - this must be in a standard library somewhere
        """
        result = ""
        i=0
        while i<len(str) :
            if string.find('"\'><"', str[i]) <0 :   # @@@ etc
                result.append("%%%2x" % (atoi(str[i])))
            else:
                result.append(str[i])
        return result

####################################### Engine
    
class Engine:
    """ The root of the references in the system -a set of things and stores
    """

    def __init__(self):
        self.resources = {}    # Hash table of URIs for interning things
        

    def internURI(self, str):
        return self.intern((RESOURCE,str))
    
    def intern(self, pair):
        """  Returns either a Fragment or a Resource as appropriate

    This is the way they are actually made.
    """
        type, uriref = pair
        if type == LITERAL:
            return Literal(uriref)  # No interning for literals (?@@?)

#        print " ... interning <%s>" % `uriref`
        hash = len(uriref)-1
        while (hash >= 0) and not (uriref[hash] == "#"):
            hash = hash-1
        if hash < 0 :     # This is a resource with no fragment
            r = self.resources.get(uriref, None)
            if r: return r
            r = Resource(uriref)
            self.resources[uriref] = r
            return r
        
        else :      # This has a fragment and a resource
            r = self.internURI(uriref[:hash])
            if type == RESOURCE:  return r.internFrag(uriref[hash+1:])



######################################################## Storage
# The store uses an index in the interned resource objects.
#
#   store.occurs[context, thing][partofspeech]   dict, list, ???


class StoredStatement:

    def __init__(self, q):
        self.triple = q
        
class RDFStore(notation3.RDFSink) :
    """ Absorbs RDF stream and saves in triple store
    """

    def __init__(self, engine):
        notation3.RDFSink.__init__(self)
        self.engine = engine
        self.size = 0
        self.forSome = engine.internURI(Logic_NS + "forSome")
        self.forAll  = engine.internURI(Logic_NS + "forAll")
        self.implies = engine.internURI(Logic_NS + "implies")
        self.asserts = engine.internURI(Logic_NS + "asserts")


# Input methods:

    def bind(self, prefix, nsPair):
        if prefix:   #  Ignore binding to empty prefix
            return notation3.RDFSink.bind(self, prefix, nsPair) # Otherwise, do as usual.
    
    def makeStatement(self, tuple):
        q = ( self.engine.intern(tuple[CONTEXT]),
              self.engine.intern(tuple[PRED]),
              self.engine.intern(tuple[SUBJ]),
              self.engine.intern(tuple[OBJ]) )
	self.storeQuad(q)
                    
    def makeComment(self, str):
        pass        # Can't store comments

    def storeQuad(self, q):
        """ Effectively intern quads, in that dupliates are eliminated.
        """
        #  Check whether this quad already exists
	short = 1000000 #@@
	for p in ALL4:
            l = len(q[p].occursAs[p])
            if l < short:
                short = l
                p_short = p
        for t in q[p_short].occursAs[p_short]:
            if t.triple == q: return 0

	s = StoredStatement(q)
        for p in ALL4: s.triple[p].occursAs[p].append(s)
        self.size = self.size+1
        return 1

    def startDoc(self):
        pass

    def endDoc(self):
        pass

    def selectDefaultPrefix(self, context):

        """ Resource whose fragments have the most occurrences
        """
        best = 0
        mp = None
        for r in self.engine.resources.values() :
            total = 0
            for f in r.fragments.values():
                total = total + (f.occurrences(PRED,context)+
                                 f.occurrences(SUBJ,context)+
                                 f.occurrences(OBJ,context))
            if total > best :
                best = total
                mp = r
        if mp == None: return
        
        if chatty: print "# Most popular Namesapce in %s is %s" % (`context`, `mp`)
        mpPair = mp.asPair()
        defns = self.namespaces.get("", None)
        if defns :
            del self.namespaces[""]
            del self.prefixes[defns]
        if self.prefixes.has_key(mpPair) :
            oldp = self.prefixes[mpPair]
            del self.prefixes[mpPair]
            del self.namespaces[oldp]
        self.prefixes[mpPair] = ""
        self.namespaces[""] = mpPair
        
# Output methods:

    def dumpChronological(self, context, sink):
        sink.startDoc()
        for c in self.prefixes.items():   #  bind in same way as input did FYI
            sink.bind(c[1], c[0])
#        print "# There are %i statements in %s" % (len(context.occursAs[CONTEXT]), `context` )
        for s in context.occursAs[CONTEXT]:
            self._outputStatement(sink, s)
        sink.endDoc()

    def _outputStatement(self, sink, s):
        t = s.triple
        sink.makeStatement(self.extern(t))

    def extern(self, t):
        return(t[CONTEXT].asPair(),
                            t[PRED].asPair(),
                            t[SUBJ].asPair(),
                            t[OBJ].asPair(),
                            )

    def dumpBySubject(self, context, sink):

        self.selectDefaultPrefix(context)        
        sink.startDoc()
        for c in self.prefixes.items() :   #  bind in same way as input did FYI
            sink.bind(c[1], c[0])

        for r in self.engine.resources.values() :  # First the bare resource
            for s in r.occursAs[SUBJ] :
                if context is s.triple[CONTEXT]:
                    self._outputStatement(sink, s)
            for f in r.fragments.values() :  # then anything in its namespace
                for s in f.occursAs[SUBJ] :
#                    print "...dumping %s in context %s" % (`s.triple[CONTEXT]`, `context`)
                    if s.triple[CONTEXT] is context:
                        self._outputStatement(sink, s)
        sink.endDoc()
#
#  Pretty printing
#
    def dumpNested(self, context, sink):
        """ Iterates over all URIs ever seen looking for statements
        """
        self.selectDefaultPrefix(context)        
        sink.startDoc()
        for c in self.prefixes.items() :   #  bind in same way as input did FYI
            sink.bind(c[1], c[0])
        self.dumpNestedStatements(context, sink)

    def dumpNestedStatements(self, context, sink):
        """ Iterates over all URIs ever seen looking for statements
        """
        for r in self.engine.resources.values() :  # First the bare resource
            self._dumpSubject(r, context, sink)
            for f in r.fragments.values() :  # then anything in its namespace
                self._dumpSubject(f, context, sink)
        sink.endDoc()


    def _dumpSubject(self, subj, context, sink):
        """ Take care of top level anonymous nodes
        """
        if 0: print "%s occurs %i as context, %i as pred, %i as subj, %i as obj" % (
            `subj`, subj.occurrences(CONTEXT, None),
            subj.occurrences(PRED,context), subj.occurrences(SUBJ,context),
            subj.occurrences(OBJ, context))
        _incoming = subj.n3_anonymous(context)    # Is anonymous?
        _isContext = len(subj.occursAs[CONTEXT])  # Is a bag?  @@@@ check is subcontext @@@!!
        _isSubject = subj.occurrences(SUBJ,context) # Has properties in this context?
        if _incoming == 2: return           # Forget it - will be dealt with in recursion
        
        if _incoming == 1:    # Can be root anonymous node
            if _isContext > 0:  # @@@ How represent the empty bag in the model?
                sink.startBagSubject(subj.asPair())
#                raise theRoof
                self.dumpNestedStatements(subj, sink)  # dump contents of anonymous bag
                sink.endBagSubject(subj.asPair())                     # Subject is now set up

            elif _isSubject > 0 :   # Ignore if actually no statements for this thing
                sink.startAnonymousNode(subj.asPair())
                for s in subj.occursAs[SUBJ]:
                    if s.triple[CONTEXT] is context:
                        self.coolMakeStatement(sink, s)
                sink.endAnonymousNode()
                return   # Done [ ... ]

        for s in subj.occursAs[SUBJ]:
            con, pred, subj, obj = s.triple
            if con is context:
                    self.coolMakeStatement(sink, s)


    def implicitExistential(self, s):
        con, pred, subj, obj = s.triple
        x = (pred is self.forSome and
                subj is con and
                obj.n3_anonymous(con))   # Involved extra search -could simplify
        return x
                
    def coolMakeStatement(self, sink, s):
        """ Filter then recursively dump
        """
        con, pred, subj, obj = s.triple
        if not self.implicitExistential(s): # weed out existential links to anonymous nodes
            if subj is obj:
                self._outputStatement(sink, s) # Do loops anyway
            else:
 #               if not subj.n3_anonymous(con) != 1 :  # Don't repeat
                    self.coolMakeStatement2(sink, s)
                
    def coolMakeStatement2(self, sink, s):
        triple = s.triple
        context, pre, sub, obj = triple
        if obj.n3_anonymous(context) == 2:  # Embedded anonymous node in N3
            _isContext = len(obj.occursAs[CONTEXT])  # Is a bag?  @@@@ check is subcontext @@@!!
            _isSubject = obj.occurrences(SUBJ,context) # Has properties in this context?

            if _isContext > 0 and _isSubject > 0: raise CantDoThat # Syntax problem!@@@

            if _isContext > 0:  # @@@ How represent the empty bag in the model?
                sink.startBagObject(self.extern(triple))
                self.dumpNestedStatements(obj, sink)  # dump contents of anonymous bag
                sink.endBagObject(pre.asPair(), sub.asPair())
                return # Arc has been made

            
            if _isSubject > 0 :   #   statements for this thing
                sink.startAnonymous(self.extern(triple))
                for t in obj.occursAs[SUBJ]:
                    if t.triple[CONTEXT] is context:
                        self.coolMakeStatement2(sink, t)
                sink.endAnonymous(sub.asPair(), pre.asPair()) # Restore parse state
                return   # Arc has been made

        if self.implicitExistential(s):
            print "### implicit existential", `triple`
            return # Existential will be implicit.
        self._outputStatement(sink, s)
                


#################################  Manipulation methods:

    def moveContext(self, old, new):
        for s in old.occursAs[CONTEXT][:] :   # Copy list!
#            print  "Old, new:",`old`, `new`, "Quad:", `s.triple`
            con, pred, subj, obj = s.triple
#            if pred is self.forAll or pred is self.forSome:
#                if subj is old: subj = new # Move quantifier pointers too
            if pred is old: pred = new # Move references (even pred?)
            if subj is old: subj = new # Move
            if obj is old: obj  = new # Move

            s.triple = new, pred, subj, obj
#            print "Quantifiers: ", `self.forAll`, `self.forSome`
 
            old.occursAs[CONTEXT].remove(s)
            new.occursAs[CONTEXT].append(s)
            
            
    def copyContext(self, old, new):
        for s in old.occursAs[CONTEXT][:] :  # Copy list!
                self.makeStatement((new, s.triple[PRED], s.triple[SUBJ], s.triple[OBJ]))
            
#  Apply rules from one context to another
                
    def applyRules(self, workingContext, filterContext=None, targetContext=None):
        """ Apply rules in one context to the same or another
        """
        chatty = 0

# A rule here is defined by logic:implies, which associates the template (premise, precondidtion,
# antecedent) to the conclusion (postcondition).
#
# This is just a database search, very SQL-like.
#
# To verify that for all x, f(s) one can either find that asserted explicitly,
# or find an example for some specific value of x.  Here, we deliberately
# chose only to do the first.
        
        if targetContext == None: targetContext = workingContext # return new data to store
        if filterContext == None: filterContext = workingContext # apply own rules

        # Execute a filter:
        
        _variables = []
        _total = 0
        for s in filterContext.occursAs[CONTEXT]:
            t = s.triple
            if t[PRED] is self.forAll and t[SUBJ] is filterContext:
                _variables.append(t[OBJ])
        if chatty: print "# We have %i variables" % (len(_variables),), _variables
        
        for s in filterContext.occursAs[CONTEXT]:
            t = s.triple
    #                print "Filter quad:", t
            if t[PRED] is self.implies:
                template = t[SUBJ]
                conclusion = t[OBJ]
                unmatched = []
                print "\n\n# IMPLIES rule, %i terms in template %s => %s" % (len(template.occursAs[CONTEXT]),
                                                                             `template`[-8:], `conclusion`[-8:])


                _existentials = [] # Things existentially quantified in the template
                for arc in template.occursAs[CONTEXT]:   #@@@ and sub contexts!!

                    context, pred, subj, obj = arc.triple
                    if subj is template and pred is self.forSome:
                        _existentials.append(obj)
                    if context is template: context = workingContext # where we will look for it
                    unmatched.append((context, pred, subj, obj))
                
                found = match(unmatched, _variables, _existentials,
                              conclude, ( self, conclusion, targetContext))
                _total = _total + found
                print "# Found %i matches for %s => %s" % (found, `template`[:-8], `conclusion`[:-8])
        
            elif t[PRED] is self.asserts and t[SUBJ] is filterContext:
                self.applyRules(t[OBJ], workingContext, targetContext)  # Nested rules
        print "#  Total matches in filter", _total, "\n"
                
def conclude(bindings, param):
    store, conclusion, targetContext = param
    for s in conclusion.occursAs[CONTEXT]:
        print "# *** Conclude: ", s.triple
	context, pred, subj, obj = s.triple
        store.storeQuad((targetContext,
                             _lookup(bindings, pred),
                             _lookup(bindings, subj),
                             _lookup(bindings, obj) ))
                            
def _lookup(bindings, value):
    for pair in bindings:
        if pair[0] == value: return pair[1]
    return value



############################################################## Query engine

# Template matching in a graph

    

INFINITY = 1000000000           # @@ larger than any number occurences

def match (unmatched,       # Tuple of interned quads we are trying to match
           variables,       # List of variables to match and return
	   existentials,    # List of variables to match to anything
           action,
           param,
           bindings = [],    # Bindings discovered so far
           newBindings = [] ):  # Bindings JUST discovered - not followed though on

    """ Apply action(bindings, param) to succussful matches
bindings      collected matches alreday found
newBindings  matches found and not yet applied - used in recursion
    """
# Scan terms to see what sort of a problem we have:
#
# We prefer terms with a single variable to those with two.
# (Those with none we immediately check and therafter ignore)
# Secondarily, we prefer short searches to long ones.

    total = 0           # Number of matches found (recursively)
    fewest = 5          # Variables to find
    shortest = INFINITY # List to search for one of the variables
    shortest_t = None
    chatty = 0
    
    if chatty: print "\n## match: called %i terms, %i bindings, terms & new bindings:" % (len(unmatched),len(bindings)), `bindings`,`newBindings`

    for pair in newBindings:
        variables.remove(pair[0])
        bindings.append(pair)  # Record for posterity
    for i in range(len(unmatched)):     # Replace variables with values
        q = unmatched[i]
        unmatched[i] = ( _lookup(newBindings, q[0]),
              _lookup(newBindings, q[1]),
              _lookup(newBindings, q[2]),
              _lookup(newBindings, q[3]))

    if chatty:
        for q in unmatched:
            print "        %s     %s  %s  %s ."  % (`q[0]`[-8:],`q[1]`[-8:],`q[2]`[-8:],`q[3]`[-8:])

    if len(unmatched) == 0:
        if chatty: print "# Match found with bindings: ", bindings
        action(bindings, param)  # No terms left .. success!
        return 1

    
    for quad in unmatched:
        found = 0       # Count where variables are
        short_p = -1
        short = INFINITY
        for p in ALL4:
            r = quad[p]
            if r in variables + existentials:
                found = found + 1
            else:
                length = len(r.occursAs[p])
                if length < short:
                    short_p = p
                    short = length


        if chatty: print "# One term has %i vars, shortest list %i" % (found, short)
        
        if (found < fewest or
            found == fewest and short < shortest) : # We find better.
                fewest = found
                shortest = short
                shortest_p = short_p
                shortest_t = quad
    
    # Now we have identified the  list to search

    if fewest == 4:
        raise notimp
        return 0    # Can't handle something with no constants at all.
                    # Not a closed world problem - and this is a cwm!

    quad = shortest_t
    unmatched.remove(quad)  # We will resolve this one now if possible

    consts = []   # Parts of speech to test for match
    vars = []   # Parts of speech which are variables
    for p in ALL4 :
        if quad[p] in variables + existentials:
            vars.append(p)
        elif p != shortest_p :
            consts.append(p)

    if chatty: print "# Searching through %i for %s in slot %i." %(shortest, `quad[shortest_p]`,shortest_p)    

    for s in quad[shortest_p].occursAs[shortest_p]:
        for p in consts:
            if s.triple[p] is not quad[p]: break
        else:  # found match
            nb = []
            for p in vars: nb.append(( quad[p], s.triple[p]))
            total = total + match(unmatched[:], variables[:], existentials[:], action, param,
                                  bindings[:], nb)
    return total
     
                            


######################################################### Tests
  
def test():
    import sys
    testString = []
    
    t0 = """bind x: <http://example.org/x-ns/> .
	    bind dc: <http://purl.org/dc/elements/1.1/> ."""

    t1="""[ >- x:firstname -> "Ora" ] >- dc:wrote ->
    [ >- dc:title -> "Moby Dick" ] .
     bind default <http://example.org/default>.
     <uriPath> :localProp defaultedName .
     
"""
    t2="""
[ >- x:type -> x:Receipt;
  >- x:number -> "5382183";
  >- x:for -> [ >- x:USD -> "2690" ];
  >- x:instrument -> [ >- x:type -> x:visa ] ]

>- x:inReplyTo ->

[ >- x:type -> x:jobOrder;
  >- x:number -> "025709";
 >- x:from ->

 [
  >- x:homePage -> <http://www.topnotchheatingandair.com/>;
  >- x:est -> "1974";
  >- x:address -> [ >- x:street -> "23754 W. 82nd Terr.";
      >- x:city -> "Lenexa";
      >- x:state -> "KS";
      >- x:zip -> "66227"];
  >- x:phoneMain -> <tel:+1-913-441-8900>;
  >- x:fax -> <tel:+1-913-441-8118>;
  >- x:mailbox -> <mailto:info@topnotchheatingandair.com> ]
].    

<http://www.davelennox.com/residential/furnaces/re_furnaces_content_body_elite90gas.asp>
 >- x:describes -> [ >- x:type -> x:furnace;
 >- x:brand -> "Lennox";
 >- x:model -> "G26Q3-75"
 ].
"""
    t3="""
bind pp: <http://example.org/payPalStuff?>.
bind default <http://example.org/payPalStuff?>.

<> a pp:Check; pp:payee :tim; pp:amount "$10.00";
  dc:author :dan; dc:date "2000/10/7" ;
  is pp:part of [ a pp:Transaction; = :t1 ] .
"""

# Janet's chart:
    t4="""
bind q: <http://example.org/>.
bind m: <>.
bind n: <http://example.org/base/>.
bind : <http://void-prefix.example.org/>.
bind w3c: <http://www.w3.org/2000/10/org>.

<#QA> :includes 
 [  = w3c:internal ; :includes <#TAB> , <#interoperability> ,
     <#validation> , w3c:wai , <#i18n> , <#translation> ,
     <#readability_elegance>, w3c:feedback_accountability ],
 [ = <#conformance>;
     :includes <#products>, <#content>, <#services> ],
 [ = <#support>; :includes
     <#tools>, <#tutorials>, <#workshops>, <#books_materails>,
     <#certification> ] .

<#internal> q:supports <#conformance> .  
<#support> q:supports <#conformance> .

"""

    t5 = """

bind u: <http://www.example.org/utilities>
bind default <>

:assumption = { :fred u:knows :john .
                :john u:knows :mary .} .

:conclusion = { :fred u:knows :mary . } .

"""
    thisURI = "file:notation3.py"

    testString.append(  t0 + t1 + t2 + t3 + t4 )
#    testString.append(  t5 )

#    p=notation3.SinkParser(RDFSink(),'http://example.org/base/', 'file:notation3.py',
#		     'data:#')

    r=notation3.SinkParser(notation3.ToN3(sys.stdout.write, 'file:output'),
                  thisURI,'http://example.org/base/',)
    r.startDoc()
    
    print "=== test stringing: ===== STARTS\n ", t0, "\n========= ENDS\n"
    r.feed(t0)

    print "=== test stringing: ===== STARTS\n ", t1, "\n========= ENDS\n"
    r.feed(t1)

    print "=== test stringing: ===== STARTS\n ", t2, "\n========= ENDS\n"
    r.feed(t2)

    print "=== test stringing: ===== STARTS\n ", t3, "\n========= ENDS\n"
    r.feed(t3)

    r.endDoc()

    print "----------------------- Test store:"

    testEngine = Engine()
    thisDoc = testEngine.internURI(thisURI)    # Store used interned forms of URIs

    store = RDFStore(testEngine)
    # (sink,  thisDoc,  baseURI, bindings)
    p = notation3.SinkParser(store,  thisURI, 'http://example.org/base/')
    p.startDoc()
    p.feed(testString[0])
    p.endDoc()

    print "\n\n------------------ dumping chronologically:"

    store.dumpChronological(thisDoc, notation3.ToN3(sys.stdout.write, thisURI))

    print "\n\n---------------- dumping in subject order:"

    store.dumpBySubject(thisDoc, notation3.ToN3(sys.stdout.write, thisURI))

    print "\n\n---------------- dumping nested:"

    store.dumpNested(thisDoc, notation3.ToN3(sys.stdout.write, thisURI))

    print "Regression test **********************************************"

    
    testString.append(reformat(testString[-1], thisDoc))

    if testString[-1] == testString[-2]:
        print "\nRegression Test succeeded FIRST TIME- WEIRD!!!!??!!!!!\n"
        return
    
    testString.append(reformat(testString[-1], thisDoc))

    if testString[-1] == testString[-2]:
        print "\nRegression Test succeeded SECOND time!!!!!!!!!\n"
    else:
        print "Regression Test Failure: ===================== LEVEL 1:"
        print testString[1]
        print "Regression Test Failure: ===================== LEVEL 2:"
        print testString[2]
        print "\n============================================= END"

    testString.append(reformat(testString[-1], thisDoc))
    if testString[-1] == testString[-2]:
        print "\nRegression Test succeeded THIRD TIME. This is not exciting.\n"

    
                
def reformat(str, thisDoc):
    if 0:
        print "Regression Test: ===================== INPUT:"
        print str
        print "================= ENDs"
    buffer=StringIO.StringIO()
    r=notation3.SinkParser(notation3.ToN3(buffer.write, `thisDoc`),
                  'file:notation3.py')
    r.startDoc()
    r.feed(str)
    r.endDoc()

    return buffer.getvalue()    # Do we need to explicitly close it or will it be GCd?
    


              
            
        
############################################################## Web service

import random
import time
import cgi
import sys
import StringIO

def serveRequest(env):
    import random #for message identifiers. Hmm... should seed from request

    #sys.stderr = open("/tmp/connolly-notation3-log", "w")

    form = cgi.FieldStorage()

    if form.has_key('data'):
	try:
	    convert(form, env)
	except BadSyntax, e:
	    print "Status: 500 syntax error in input data"
	    print "Content-type: text/plain"
	    print
	    print e
	    

	except:
	    import traceback

	    print "Status: 500 error in python script. traceback follows"
	    print "Content-type: text/plain"
	    print
	    traceback.print_exc(sys.stdout)
	    
    else:
	showForm()

def convert(form, env):
    """ raises KeyError if the form data is missing required fields."""

    serviceDomain = 'w3.org' #@@ should compute this from env['SCRIPT_NAME']
         # or whatever; cf. CGI spec
    thisMessage = 'mid:t%s-r%f@%s' % (time.time(), random.random(), serviceDomain)

    data = form['data'].value

    if form.has_key('genspace'):
	genspace = form['genspace'].value
    else: genspace = thisMessage + '#_'

    if form.has_key('baseURI'):	baseURI = form['baseURI'].value
    elif env.has_key('HTTP_REFERER'): baseURI = env['HTTP_REFERER']
    else: baseURI = None

    # output is buffered so that we only send
    # 200 OK if all went well
    buf = StringIO.StringIO()

    xlate = notation3.ToRDFParser(buf, baseURI, thisMessage, genspace)
    xlate.startDoc()
    xlate.feed(data)
    xlate.endDoc()

    print "Content-Type: text/xml"
    #hmm... other headers? last-modified?
    # handle if-modified-since? i.e. handle input by reference?
    print # end of HTTP response headers
    print buf.getvalue()

def showForm():
    print """Content-Type: text/html

<html>
<title>A Wiki RDF Service</title>
<body>

<form method="GET">
<textarea name="data" rows="4" cols="40">
bind dc: &lt;http://purl.org/dc/elements/1.1/&gt;
</textarea>
<input type="submit"/>
</form>

<div>
<h2>References</h2>
<ul>
<li><a href="http://www.w3.org/DesignIssues/Notation3">Notation 3</a></li>
<li><a href="http://www.python.org/doc/">python documentation</a></li>
<li><a href="http://www.w3.org/2000/01/sw/">Semantic Web Development</a></li>
</ul>
</div>

<address>
<a href="http://www.w3.org/People/Connolly/">Dan Connolly</a>
</address>

</body>
</html>
"""
#################################################  Command line
    
def doCommand():
        """Command line RDF/N3 tool
        
 <command> <options> <inputURIs>
 
 -rdf1out   Output in RDF M&S 1.0 insead of n3 (only works with -pipe at the moment)
 -pipe      Don't store, just pipe out *
 -ugly      Store input and regurgitate *
 -bySubject Store inpyt and regurgitate in subject order *
            (default is to store and pretty print with anonymous nodes) *

 -apply=foo Read rules from foo, apply to store, adding conclusions to store
 -reify     Replace the statements in the store with statements describing them.
 -help      print this message
 -chatty    Verbose output of questionable use
 

            * mutually exclusive
 
"""
        
        import urllib
        option_ugly = 0     # Store and regurgitate with genids *
        option_pipe = 0     # Don't store, just pipe though
        option_rdf = 0      # Use RDF rather than XML
        option_rdf1out = 0  # Output in RDF M&S 1.0 instead of N3
        option_bySubject= 0 # Store and regurgitate in subject order *
        option_inputs = []
        option_reify = 0    # Flag: reify on output  (process?)
        _doneOutput = 0
        _gotInput = 0     #  Do we not need to take input from stdin? 
        chatty = 0          # not too verbose please
        hostname = "localhost" # @@@@@@@@@@@ Get real one
        
        for arg in sys.argv[1:]:  # Command line options after script name
            if arg == "-test":
                option_test = 1
                _gotInput = 1
            elif arg == "-ugly": _doneOutput = 1
            elif arg == "-pipe": option_pipe = 1
            elif arg == "-bySubject": _doneOutput = 1
            elif arg == "-rdf1out": option_rdf1out = 1
            elif arg == "-chatty": chatty = 1
            elif arg[:7] == "-apply=": pass
            elif arg == "-reify": pass
            elif arg == "-help":
                print doCommand.__doc__
                return
            elif arg[0] == "-": pass  # Other option
            else : _gotInput=1  # input filename
            

        # The base URI for this process - the Web equiv of cwd
#	_baseURI = "file://" + hostname + os.getcwd() + "/"
	_baseURI = "file://" + fixslash(os.getcwd()) + "/"
	print "# Base URI of process is" , _baseURI
	
        _outURI = urlparse.urljoin(_baseURI, "STDOUT")
	if option_rdf1out:
            _outSink = notation3.ToRDF(sys.stdout, _outURI)
        else:
            _outSink = notation3.ToN3(sys.stdout.write, _outURI)

        if option_pipe:
            _store = _outSink
        else:
            myEngine = Engine()
            _store = RDFStore(myEngine)
            workingContext = myEngine.internURI(_outURI)

        if not _gotInput: #@@@@@@@@@@ default input
            _inputURI = urlparse.urljoin( _baseURI, "STDIN") # Make abs from relative
            p = notation3.SinkParser(_store,  _inputURI)
            p.load("")
            del(p)
            _store.moveContext(inputContext,workingContext)  # Move input data to output context


#  Take commands from command line:

        for arg in sys.argv[1:]:  # Command line options after script name
            _equals = string.find(arg, "=")
            _lhs = ""
            _rhs = ""
            if _equals >=0:
                _lhs = arg[:_equals]
                _rhs = arg[_equals+1:]
                _uri = urlparse.urljoin(_baseURI, _rhs) # Make abs from relative
                
            if arg == "-test": test()
            elif arg == "-ugly":
                _store.dumpChronological(workingContext, _outSink)
                _doneOutput = 1            

            elif arg == "-pipe": option_pipe = 1
            elif arg == "-bySubject":
                _store.dumpBySubject(workingContext, _outSink)
                _doneOutput = 1            

            elif arg == "-rdf1out": option_rdf1out = 1

            elif arg == "-rdf": option_rdf = 1
            elif arg == "n3": option_rdf = 0
            
            elif arg == "-chatty": chatty = 1

            elif arg[:7] == "-apply=":
                filterContext = (myEngine.internURI(_uri))
                print "# Input rules to apply from ", _uri
                p = notation3.SinkParser(_store,  _uri)
                p.load(_uri)
                del(p)
                _store.applyRules(workingContext, filterContext);

            elif _lhs == "-filter":
                filterContext = myEngine.internURI(_uri)
                _playURI = urlparse.urljoin(_baseURI, "PLAY")  # Intermediate
                _playContext = myEngine.internURI(_playURI)
                _store.moveContext(workingContext, _playContext)
                print "# Input filter ", _uri
                p = notation3.SinkParser(_store,  _uri)
                p.load(_uri)
                del(p)
                _store.applyRules(_playContext, filterContext, workingContext);

            elif arg == "-rules":
                _store.applyRules(workingContext, workingContext);

            elif arg == "-reify":
                _playURI = urlparse.urljoin(_baseURI, "PLAY")  # Intermediate
                _playContext = myEngine.internURI(_playURI)
                _store.moveContext(workingContext, _playContext)

                _store.dumpBySubject(_playContext,
                                     notation3.Reifier(_store, _outURI))                
                
            elif arg == "-help":
                print doCommand.__doc__

            elif arg == "-size":
                print "# Size of store: %i statements." %(_store.size,)

            elif arg[0] == "-": print "Unknown option", arg
            else :   # Input the data
                _inputURI = urlparse.urljoin(_baseURI, arg) # Make abs from relative
                if option_rdf: p = xml2rdf.RDFXMLParser(_store,  _inputURI)
                else: p = notation3.SinkParser(_store,  _inputURI)
                p.load(_inputURI)
                del(p)
                inputContext = myEngine.internURI(_inputURI)
                _store.moveContext(inputContext,workingContext)  # Move input data to output context
                _gotInput = 1


# Squirt it out if no output done
        if not _doneOutput:
            _store.dumpNested(workingContext, _outSink)


def fixslash(str):
    """ Fix windowslike filename to unixlike
    """
    s = str
    for i in range(len(s)):
        if s[i] == "\\": s = s[:i] + "/" + s[i+1:]
    if s[0] != "/" and s[1] == ":": s = s[2:]  # @@@ Hack when drive letter
    return s
        
############################################################ Main program
    
if __name__ == '__main__':
    import os
    import urlparse
    if os.environ.has_key('SCRIPT_NAME'):
        serveRequest(os.environ)
    else:
        doCommand()

