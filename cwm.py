#! /usr/bin/python /devel/WWW/2000/10/swap/cwm.py
"""
$Id$

Closed World Machine

(also, in Wales, a valley)

This is an engine which knows a certian amount of stuff and can manipulate it.
It is a query engine, not an inference engine: that is, it will apply rules
but won't figure out which ones to apply to prove something.


http://www.w3.org/DesignIssues/Notation3
Date: 2000/07/17 21:46:13  

Agenda:
=======

 - filter out duplicate conclusions - BUG!
 - run hhtp daemon/client sending changes to database
 - act as client/server for distributed
 - Bultins - says, startsWith,
 - postgress underlying database?
 -    
 -    standard mappping of SQL database into the web in N3/RDF
 -    
 - logic API as requested DC 2000/12/10
 - sucking in the schema (http library?); to know about r1 see r2
 - schema validation - done partly but no "no schema for xx predicate".
 -   syntax for "all she wrote" - schema is complete and definitive
 - metaindexes - "to know more about x please see r" - described by
 - general python URI access with catalog!
 - equivalence handling inc. equivalence of equivalence?
 Shakedown:
 - Find all synonyms of synonym
 - Find closure for all synonyms
 - Find superclass closure?
 - Use unambiguous property to infer synomnyms
 - Validation:  validate domain and range constraints against closuer of classes and
   mutually disjoint classes.
- represent URIs bound to same equivalence closuse object?


- Translation;  Try to represent the space (or a context) using a subset of namespaces

- Other forms of context - explanation of derivation by rule or merging of contexts




Done
====
 - Separate the store hash table from the parser. - DONE
 - regeneration of genids on output. - DONE
 - repreentation of genids and foralls in model
- regression test - DONE (once!)
 Manipulation:
  { } as notation for bag of statements - DONE
  - filter -DONE
  - graph match -DONE
  - recursive dump of nested bags - DONE
 - semi-reification - reifying only subexpressions - DONE
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

N3_forSome_URI = Logic_NS + "forSome"
#N3_subExpression_URI = Logic_NS + "subExpression"
N3_forAll_URI = Logic_NS + "forAll"

META_NS_URI = "http://www.w3.org/2000/01/swap/meta.n3#"
META_mergedWith = META_NS_URI + "mergedWith"
META_source = META_NS_URI + "source"
META_run = META_NS_URI + "run"

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


chatty = 20   # verbosity debug flag
doMeta = 0  # wait until we have written the code! :-)

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

    # Use the URI to allow sorted listings - for cannonnicalization if nothing else
    #  Put a type declaration before anything else
    def __cmp__(self, other):
        if self is other: return 0
        _type = "<" + notation3.RDF_type_URI + ">"
        s = self.representation()
        if s == _type:
            return -1
        o = other.representation()
        if o == _type:
            return 1
        if s < o :
#            print s,  "LESS THAN", o
            return -1
        if s > o :
#            print s, "GREATER THAN", o
            return 1
        raise internalError # Strings should not match if not same object

    def representation(self, base=None):
        """ in N3 """
        return "<" + self.uriref(base) + ">"

    def generated(self):
        """  Is this thing a genid - is its name arbitrary? """
        return 0    # unless overridden

  
    def asPair(self):
        return (RESOURCE, self.uriref(None))
    
    def occurrences(self, p, context):
        """ Count the times a thing occurs in a statement in given context
        """
        lp = len(self.occursAs[p])
        lc = len(context.occursAs[CONTEXT])
        n = 0
        if lc < lp:
            for s in context.occursAs[CONTEXT]:
                if s.triple[p] is self:
                    n = n + 1
        else:
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

#   The order of statements is only for cannonical output
    def __cmp__(self, other):
        if self is other: return 0
        if self.triple[CONTEXT] is not other.triple[CONTEXT]:
            return self.triple[CONTEXT].__cmp__(other.triple[CONTEXT])
        for p in [CONTEXT, SUBJ, PRED, OBJ]: # Note NOT internal order
            if self.triple[p] is not other.triple[p]:
                return self.triple[p].__cmp__(other.triple[p])
        raise internalerror # SHould never have two identical distinct
        
class RDFStore(notation3.RDFSink) :
    """ Absorbs RDF stream and saves in triple store
    """

    def __init__(self, engine, genPrefix=None):
        notation3.RDFSink.__init__(self)
        self.engine = engine
        self.size = 0
        self._nextId = 0
        if genPrefix: self._genPrefix = genPrefix
        else: self._genPrefix = "#_gs"

        # Constants, as interned:
        self.forSome = engine.internURI(Logic_NS + "forSome")
#        self.subExpression = engine.internURI(Logic_NS + "subExpression")
        self.forAll  = engine.internURI(Logic_NS + "forAll")
        self.implies = engine.internURI(Logic_NS + "implies")
        self.asserts = engine.internURI(Logic_NS + "asserts")
        self.Truth = engine.internURI(Logic_NS + "Truth")
        self.type = engine.internURI(notation3.RDF_type_URI)
        self.Chaff = engine.internURI(Logic_NS + "Chaff")

# List stuff - beware of namespace changes! :-(

        self.first = engine.intern(notation3.N3_first)
        self.rest = engine.intern(notation3.N3_rest)
        self.nil = engine.intern(notation3.N3_nil)
        self.Empty = engine.intern(notation3.N3_Empty)
        self.List = engine.intern(notation3.N3_List)


# Input methods:

    def loadURI(self, uri):
        p = notation3.SinkParser(self,  uri)
        p.load(uri)
        del(p)


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

    def contains(self, q):
        """  Check whether this quad  exists in the store
	"""
        short = 1000000 #@@
	for p in ALL4:
            l = len(q[p].occursAs[p])
            if l < short:
                short = l
                p_short = p
        for t in q[p_short].occursAs[p_short]:
            if t.triple == q: return t
        return None

    def storeQuad(self, q):
        """ Effectively intern quads, in that dupliates are eliminated.
        """
        #  Check whether this quad already exists
	if self.contains(q): return 0  # Return no change in size of store

	s = StoredStatement(q)
        for p in ALL4: s.triple[p].occursAs[p].append(s)
        self.size = self.size+1
        return 1  # One statement has been added

    def startDoc(self):
        pass

    def endDoc(self):
        pass

    def selectDefaultPrefix(self, context):

        """ Resource whose fragments have the most occurrences.
        """
        best = 0
        mp = None
        for r in self.engine.resources.values() :
            total = 0
            for f in r.fragments.values():
                anon, inc, se = self._topology(f, context)
                if not anon:
                    total = total + (f.occurrences(PRED,context)+
                                     f.occurrences(SUBJ,context)+
                                     f.occurrences(OBJ,context))
            if total > best :
                best = total
                mp = r
        if mp is None: return
        
        if chatty > 20:
            progress("# Most popular Namesapce in %s is %s with %i" % (`context`, `mp`, best))
        mpPair = (RESOURCE, mp.uriref(None)+"#")
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
#   x is an existential if there is in the context C we are printing
# a statement  (c log:forSome x). If so the anonymous syntaxes follow.
# c is 1 if x is a subexpression of the current context else c=0
# r s and o are the number  times x occurs within context as p,s or o
# o excludes the statements making it an existential and maybe subexp.
#
#   c  p  s  o   Syntax
#   0  0  0  0   (won't occur.)
#   0  0  ?  1   y p [ ... ] .
#   0  0  y  0   [] p z, ....     or  [ p y,z ... ] .  or a combination
#   0  0  y  1   y q [ p y z ... ] .
#   0  1  ?  0   y  [ ... ] w .
#   ?  1  ?  1   can't be pred and obj.
#   y  0  y  0   { ... } p y z,... .
#   y  0  y  1   y q [ p y z ...; = { ... } ] .
#   ?  ?  ?  >1  can't without using revese <- p -< notation
#   ?  >1 ?  ?   can't UNLESS all occurrences for same subject
#   y  0  0  0   { ... } .     Does this have any meaning? Void meaning I think.
#   y  0  0  1   y q { ... } .
#   y  1  0  0   x  { .... }  y .   Illegal because statementlist and property disjoint????
#   y  1  y  0   x  [ ... ; ={ ...} ]  (illegal - same reason?)
# simplified rules:
#  If it occurs > once as a (predicate or object), forget it.
#  If it occurs as a predicate or object at all
#       Wait for it to turn up
#
#  If it is not as a subject but is as a context use {}
#  Else use [ ..] with optionally a = { ... } inside. 
#
#  Exception: when the subject, and when 
#  If it occurs both as predicate and object, forget it.
#  If it occurs as context and subject in the SAME STATEMENT, forget it.
#  Else
#      If it does not occur as a subject use { ... } form
#      Else use [ ... ] form optionally with  = { ... } if both
#  Exception:  if subject and not pred or obj then use  [] p z... form to cut down nesting?

# An intersting alternative is to use the reverse syntax to the max, which
# makes the DLG an undirected labelled graph. s and o above merge. The only think which
# then prevents us from dumping the graph without genids is the presence of cycles.

# Contexts
#
# These are in some way like literal strings, in that theyu are defined completely
# by their contents. They are sets of statements. (To say a statement occurs
# twice has no menaing).  Can they be given an id?  You can assert that any
# object is equivalent to (=) a given context. However, it is the contexts which
# define a context. If one could label it in one place then one would want to
# be able to label it in more than one.  I'm not sure whether this is wise.
# Let's try it with no IDs on contexts as in the N3 syntax.  There would be
# the question of in which context the assertion wa made that the URI was
# a label for the expression. You couldn't just treat it as part of the
# machinery as we do for URI of a regular thing.


    def _topology(self, x, context): 
        """ Can be output as an anonymous node in N3. Also counts incoming links.

        1. True iff can be represented as anonymous node in N3
        2. Number of incoming links: >0 means occurs as object or pred, 0 means as only as subject.
        3. Is this a literal context? forSome and exists as context.
            Literal contexts are represented wherever they occur by braces expression
        
        Returns  number of incoming links (1 or 2) including forSome link
        or zero if self can NOT be represented as an anonymous node.
        Paired with this is whether this is a subexpression.
        """
        # @@@@ This is NOT a proper test - we should test that the statment
        # is an assumed one.
        # @@@ what about nested contexts? @@@@@@@@@@@@@@@@@@@@@@@@@@
        _asPred = x.occurrences(PRED, context)
        
        _isSubExp = 0
        _asObj = 0       # Times occurs as object NOT counting the subExpression or ForSome
        _isExistential = 0  # Is there a forSome?
        for s in x.occursAs[OBJ]:  # Checking all statements about x
#            if string.find(`x`, "_gs") >0: print "  ----- ",quadToString(s.triple)
            if not isinstance(s,StoredStatement):print "s=",`s`
            con, pred, subj, obj = s.triple
            # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ HACK - error - check context is ancestor
            if subj is con and pred is self.forSome :
                _isExistential = 1
            else:
                if con is context:
                    _asObj = _asObj + 1  # Regular object

            # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ end hack
#            
#            if con is context:  # believing ones in this context
#                if subj is context and pred is self.forSome :
#                    _isExistential = 1
#                else:
#                    _asObj = _asObj + 1  # Regular object
#            elif con is x:   # Believing also for this purpose only those in context x
#                if pred is self.forSome :
#                    _isExistential = 1

        _op = _asObj + _asPred
        _anon = (_op < 2) and _isExistential
        _isSubExp = _isExistential and (x.occursAs[CONTEXT] != [] and x is not context) # subExpression removal

        if 0: print "Topology <%s in <%sanon=%i ob=%i,pr=%i se=%i exl=%i"%(
            `x`[-8:], `context`[-8:], _anon, _asObj, _asPred, _isSubExp, _isExistential)
        return ( _anon, _asObj+_asPred, _isSubExp)  

    def isList(self, x, context):
        """ Does this look like a list?
        This should check that this is a node which can be represented in N3
        without loss of information as a list.
        This does not check whether the node is anonymous - check that first.
        
        """
        if x == self.nil: return 1  # Yes, nil is the list ()

        empty = 0
        left = []
        right = []
        for s in x.occursAs[SUBJ]:
            con, pred, subj, obj = s.triple
            if con == context:
                #print "     ",quadToString(s.triple), `self.first`
                if pred is self.first: left.append(obj)
                elif pred is self.rest: right.append(obj)
                elif pred is self.type:
                    if obj is self.Empty: empty = 1
                    if obj is not self.List and obj is not self.Empty : return 0
                else:
                    #print "     Unacceptable: ",quadToString(s.triple), `self.rest`, `pred`
                    return 0  # Can't have anything else - wouldn't print.
        #print "# ", `x`[-8:], "left:", left, "right", right
        if left == [] and right == [] and empty: return 1
        if len(left) != 1 or len(right)!=1: return 0 # Invalid
        return self.isList(right[0], context)
    


    def dumpNested(self, context, sink):
        """ Iterates over all URIs ever seen looking for statements
        """
        self.selectDefaultPrefix(context)        
        sink.startDoc()
        for c in self.prefixes.items() :   #  bind in same way as input did FYI
            sink.bind(c[1], c[0])
        self.dumpNestedStatements(context, sink)
        sink.endDoc()

    def dumpNestedStatements(self, context, sink, sorting=1):
        """ Iterates over statements in 
        """
        if sorting: context.occursAs[CONTEXT].sort()
        currentSubject = None
        statements = []
        for s in context.occursAs[CONTEXT]:
            con, pred, subj, obj =  s.triple
            if not currentSubject: currentSubject = subj
            if subj != currentSubject:
                self._dumpSubject(currentSubject, context, sink, sorting, statements)
                statements = []
                currentSubject = subj
            statements.append(s)
        if currentSubject:
            self._dumpSubject(currentSubject, context, sink, sorting, statements)

    def dumpNestedStatements_old(self, context, sink, sorting=1):
        """ Iterates over all URIs ever seen looking for statements
        """
        rs = self.engine.resources.values()[:]
        if sorting: rs.sort()
        for r in rs :  # First the bare resource
            #print "# sorted?" ,`r`
            self._dumpSubject(r, context, sink, sorting)
            fs = r.fragments.values()[:]
            if sorting: fs.sort() 
            for f in fs :  # then anything in its namespace
                self._dumpSubject(f, context, sink, sorting)


    def _dumpSubject(self, subj, context, sink, sorting=1, statements=[]):
        """ Take care of top level anonymous nodes
        """
        if 0: print "...%s occurs %i as context, %i as pred, %i as subj, %i as obj" % (
            `subj`, len(subj.occurrsAs[CONTEXT, None]),
            subj.occurrences(PRED,context), subj.occurrences(SUBJ,context),
            subj.occurrences(OBJ, context))
        _anon, _incoming, _se = self._topology(subj, context)    # Is anonymous?
#        _isSubject = subj.occurrences(SUBJ,context) # Has properties in this context?
#        if not _isSubject and not _se: return       # Waste no more time
#        if not _isSubject: return       # Waste no more time
        
        if 0: sink.makeComment("...%s incoming=%i, se=%i, asSubj=%i" % (
            `subj`[-8:], _incoming, _se, _isSubject))
        if _anon and  _incoming == 1: return           # Forget it - will be dealt with in recursion
    
        if _anon and _incoming == 0:    # Will be root anonymous node - {} or []
#            print " #@@@@@@ Subject", `subj`[-10:], " se=",_se
            if _se > 0:  # Is subexpression of this context
                sink.startBagSubject(subj.asPair())
                self.dumpNestedStatements(subj, sink)  # dump contents of anonymous bag
                sink.endBagSubject(subj.asPair())       # Subject is now set up
                # continue to do arcs

            else:     #  Could have alternative syntax here

                for s in statements:  # Find at least one we will print
                    context, pre, sub, obj = s.triple
                    if sub is obj: break  # Ok, we will do it
                    _anon, _incoming, _se = self._topology(obj, context)
                    if not((pre is self.forSome) and sub is context and _anon):
                        break # We will print it
                else: return # Nothing to print - so avoid printing [].

                sink.startAnonymousNode(subj.asPair())
                if sorting: statements.sort()    # Order only for output
                for s in statements:
                    self.dumpStatement(sink, s)
#                if _se > 0:  # Is subexpression of this context  @@@@@@ MISSING "="
#                    sink.startBagSubject(subj.asPair())
#                    self.dumpNestedStatements(subj, sink)  # dump contents of anonymous bag
#                    sink.endBagSubject(subj.asPair())
                sink.endAnonymousNode()
                return  # arcs as subject done

        if not _anon and subj.occursAs[CONTEXT] != [] and subj is not context:
            sink.startBagNamed(subj.asPair())
            self.dumpNestedStatements(subj, sink)  # dump contents of anonymous bag
            sink.endBagNamed(subj.asPair())       # Subject is now set up

        if sorting: statements.sort()
        for s in statements:
            self.dumpStatement(sink, s)


                
    def dumpStatement(self, sink, s, sorting=0):
        triple = s.triple
        context, pre, sub, obj = triple
        if sub is obj:
            self._outputStatement(sink, s) # Do 1-loops simply
            return
        _anon, _incoming, _se = self._topology(obj, context)
        if 0: sink.makeComment("...%s anon=%i, incoming=%i, se=%i" % (
            `obj`[-8:], _anon, _incoming, _se))
        
        if ((pre is self.forSome) and sub is context and _anon):
#            print "# @@@@ implicit ", quadToString(s.triple)  
            return # implicit forSome - may leave [] empty :-(

        if _anon and _incoming == 1:  # Embedded anonymous node in N3
            _isSubject = obj.occurrences(SUBJ,context) # Has properties in this context?

#            if _isContext > 0 and _isSubject > 0: raise CantDoThat # Syntax problem!@@@
            
            if _isSubject > 0 or not _se :   #   Do [ ] if nothing else as placeholder.
                li = _anon and self.isList(obj,context)
                sink.startAnonymous(self.extern(triple), li)
                if sorting: obj.occursAs[SUBJ].sort()
                for t in obj.occursAs[SUBJ]:
                    if t.triple[CONTEXT] is context:
                        self.dumpStatement(sink, t)
                if _se > 0:
                    sink.startBagNamed(obj.asPair()) # @@@@@@@@@  missing "="
                    self.dumpNestedStatements(obj, sink)  # dump contents of anonymous bag
                    sink.endBagObject(pre.asPair(), sub.asPair())
                    
                sink.endAnonymous(sub.asPair(), pre.asPair()) # Restore parse state
            else:  # _isSubject == 0 and _se
                sink.startBagObject(self.extern(triple))
                self.dumpNestedStatements(obj, sink)  # dump contents of anonymous bag
                sink.endBagObject(pre.asPair(), sub.asPair())
            return # Arc is done

        if _se:
            sink.startBagObject(self.extern(triple))
            self.dumpNestedStatements(obj, sink)  # dump contents of anonymous bag
            sink.endBagObject(pre.asPair(), sub.asPair())
            return

        self._outputStatement(sink, s)
                


########1#########################  Manipulation methods:

    def moveContext(self, old, new):
        for s in old.occursAs[CONTEXT][:] :   # Copy list!
            con, pred, subj, obj = s.triple
            for p in CONTEXT, PRED, SUBJ, OBJ:
                x = s.triple[p]
                if x is old:
                    s.triple = s.triple[:p] + (new,) + s.triple[p+1:]
                    old.occursAs[p].remove(s)
                    new.occursAs[p].append(s)
                
#  Clean up intermediate results:
#
# Statements in the given context that a term is a Chaff cause
# any mentions of that term to be removed from the context.

    def purge(self, context, boringClass=None):
        if not boringClass:
            boringClass = self.Chaff
        for s in boringClass.occursAs[OBJ][:]:
            con, pred, subj, obj = s.triple
            if con is context and  pred is self.type:
                total = 0
                for p in (PRED, SUBJ, OBJ):
                    for t in subj.occursAs[p][:]:  # Take copy as list changes
                        if t.triple[CONTEXT] is context:
#                            print "     ", quadToString(t.triple)
                            self.removeStatement(t)
                            total = total + 1

                progress("Purged %i statements with...%s" % (total,`subj`[-20:]))


    def removeStatement(self, s):
        for p in ALL4:
            i=0
            l=s.triple[p].occursAs[p]
            while l[i] is not s:
                i = i + 1
            l[i:i+1] = []  # Remove one element
            # s.triple[p].occursAs[p].remove(s)  # uses slow __cmp__
        self.size = self.size-1
        del s

#  Apply rules from one context to another
                
    def applyRules(self, workingContext,    # Data we assume 
                   filterContext = None,    # Where to find the rules
                   targetContext = None,    # Where to put the conclusions
                   universals = []):        # Inherited from higher contexts
        """ Apply rules in one context to the same or another
        """

# A rule here is defined by logic:implies, which associates the template (premise, precondidtion,
# antecedent) to the conclusion (postcondition).
#
# This is just a database search, very SQL-like.
#
# To verify that for all x, f(s) one can either find that asserted explicitly,
# or find an example for some specific value of x.  Here, we deliberately
# chose only to do the first.
        
        if targetContext is None: targetContext = workingContext # return new data to store
        if filterContext is None: filterContext = workingContext # apply own rules

        # Execute a filter:
        
        _variables = universals[:] # Rule-wide or wider universals
        _total = 0
        for s in filterContext.occursAs[CONTEXT]:
            t = s.triple
            if t[PRED] is self.forAll and t[SUBJ] is filterContext:
                _variables.append(t[OBJ])
#        print "\n\n# APPLY RULES TO %s, (%i vars)" % (filterContext, len(_variables),), _variables
        
        for s in filterContext.occursAs[CONTEXT]:
            t = s.triple
    #                print "Filter quad:", t
            if t[PRED] is self.implies:
                tries = 0
                found = self.tryRule(s, workingContext, filterContext, targetContext, _variables)
                if (chatty >40) or (chatty > 5 and tries > 1):
                    progress( "Found %i new stmts for rule %s" % (subtotal, tries, quadToString(t)))
                sys.stderr.write( "# Found %i new stmts for rule %s\n" % (found, quadToString(t)))
                _total = _total+found
            else:
                c = None
                if t[PRED] is self.asserts and t[SUBJ] is filterContext: c=t[OBJ]
                elif t[PRED] is self.type and t[OBJ] is self.Truth: c=t[SUBJ]
# We could shorten the rule format if forAll(x,y) asserted truth of y too, but this messes up
# { x foo y } forAll x,y; log:implies {...}. where truth is NOT asserted. This line would do it:
#                elif t[PRED] is self.forAll and t[SUBJ] is self.Truth: c=t[SUBJ]  # DanC suggestion
                if c:
                    _vs = _variables[:]
                    for s in filterContext.occursAs[CONTEXT]: # find forAlls pointing downward
                        if s.triple[PRED] is self.forAll and s.triple[SUBJ] is c:
                            _vs.append(s.triple[OBJ])
                    _total = _total + self.applyRules(workingContext, c, targetContext, _vs)  # Nested rules


        progress("Total %i new statements from rules in %s" % ( _total, filterContext))
        return _total


    def tryRule(self, s, workingContext, filterContext, targetContext, _variables):
        t = s.triple
        template = t[SUBJ]
        conclusion = t[OBJ]

        if chatty >30: print"\n\n=================== IMPLIES ============\n"

        # When the template refers to itself, the thing we are
        # are looking for will refer to the context we are searching
        # Similarly, refernces to the working context have to be moved into the
        # target context when the conclusion is drawn.

        unmatched, _templateVariables = self.nestedContexts(template)
        _substitute([( template, workingContext)], unmatched)
        if chatty >20:
            print "# IMPLIES Template", setToString(unmatched)
            for v in _variables: print "    %s" % `v`[-8:]
        conclusions, _outputVariables = self.nestedContexts(conclusion)
        _substitute([( conclusion, targetContext)], conclusions)                

        if chatty > 20:
            print "# IMPLIES rule, %i terms in template %s (%i t,%i e) => %s (%i t, %i e)" % (
                len(template.occursAs[CONTEXT]),
                `template`[-8:], len(unmatched), len(_templateVariables),
                `conclusion`[-8:], len(conclusions), len(_outputVariables))
        if chatty > 80:
            for v in _variables:
                print "    Variable: ", `v`[-8:]

        return match(unmatched, _variables, _templateVariables,
                      conclude, ( self, conclusions, targetContext, _outputVariables))
 
    def genid(self,context):        
        self._nextId = self._nextId + 1
        return self.engine.internURI(self._genPrefix+`self._nextId`)

    def nestedContexts(self, con):
        """ Return a list of statements and variables of either type
        found within the nested subcontexts
        """
        statements = []
        variables = []
        existentials = []
#        print "# NESTING in ", `self`, " using ", `subExpression`
        for arc in con.occursAs[CONTEXT]:
#            print"#    NESTED ",arc.triple
            context, pred, subj, obj = arc.triple
            statements.append(arc.triple)
#            print "%%%%%%", quadToString(arc.triple)
            if subj is context and (pred is self.forSome or pred is self.forAll): # @@@@
                variables.append(obj)   # Collect list of existentials
            if subj is context and pred is self.forSome: # @@@@
                existentials.append(obj)   # Collect list of existentials

        for arc in con.occursAs[CONTEXT]:
#           if pred is self.subExpression and subj is con:
            for p in [ SUBJ, PRED, OBJ]:  # @ can remove PRED if contexts and predicates distinct
                x = arc.triple[p]
                if x.occursAs[CONTEXT] != [] and x in existentials:  # Nested context                    
                    for a2 in con.occursAs[CONTEXT]:  # Rescan for variables
                        c2, p2, s2, o2 = a2.triple
                        if  s2 is x and (pred is self.forSome or pred is self.forAll):
                            variables.append(o2)   # Collect list of existentials
                    s, v = self.nestedContexts(x)
                    statements = statements + s
                    variables = variables + v
        return statements, variables
    


def bindingsToString(bindings):
    str = ""
    for x, y in bindings:
        str = str + " %s --> %s," % ( `x`[-10:], `y`[-10:])
    return str + "\n"

def setToString(set):
    str = ""
    for q in set:
        str = str+ "        " + quadToString(q) + "\n"
    return str

def quadToString(q):
    return "<%s> ::  <%s <%s <%s ." %(
        `q[CONTEXT]`[-10:], `q[SUBJ]`[-10:], `q[PRED]`[-10:], `q[OBJ]`[-10:])

def conclude(bindings, param):  # Returns number of statements added to store
    store, conclusions, targetContext, oes = param
    if chatty >60: print "\n#Concluding tenttatively...", bindingsToString(bindings)

    myConclusions = conclusions[:]
    _substitute(bindings, myConclusions)
    # Does this conclusion exist already in the database?
    found = match(myConclusions[:], [], oes[:], justOne=1)  # Find first occurrence
    if found:
        if chatty>60: print "    .... forget it, conclusion already in store."
        return 0
    
    # Regenerate a new form with its own existential variables
    # because we can't reuse the subexpression identifiers.
    bindings2 = []
    for i in oes:
        g = store.genid(targetContext)
        bindings2.append((i,g))
    total = 0
    for q in myConclusions:
        q2 = _lookupQuad(bindings2, q)
        total = total + store.storeQuad(q2)
        if chatty>75: print "# *** Conclude: ", quadToString(q2)
    return total

def _substitute(bindings, list):
    for i in range(len(list)):
        q = list[i]
        list[i] = _lookupQuad(bindings, q)
                            
def _lookupQuad(bindings, q):
	context, pred, subj, obj = q
	return (
            _lookup(bindings, context),  # target context not workingContext
            _lookup(bindings, pred),
            _lookup(bindings, subj),
            _lookup(bindings, obj) )

def _lookup(bindings, value):
    for pair in bindings:
        if pair[0] == value: return pair[1]
    return value



############################################################## Query engine

# Template matching in a graph

    
def doNothing(bindings, param):
    if chatty>99: print "Success! found it!"
    return 1                    # Return count of calls only

INFINITY = 1000000000           # @@ larger than any number occurences

def match (unmatched,           # Tuple of interned quads we are trying to match CORRUPTED
           variables,           # List of variables to match and return
	   existentials,        # List of variables to match to anything
                                # Existentials or any kind of variable in subexpression
           action = doNothing,  # Action routine retiurn subtotal of actions
           param = None,        # a tuple, see the call itself and conclude()
           bindings = [],       # Bindings discovered so far
           newBindings = [],    # Bindings JUST discovered - not followed though on
           justOne = 0):        # Flag: Stop when you find the first one

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
    
    if chatty > 50:
        print "\n## match: called %i terms, %i bindings:" % (len(unmatched),len(bindings))
        print bindingsToString(newBindings)
        if chatty > 90: print setToString(unmatched)
    
    for pair in newBindings:   # Take care of business left over from recursive call
        if pair[0] in variables:
            variables.remove(pair[0])  
            bindings.append(pair)  # Record for posterity
        else:
            existentials.remove(pair[0]) # Can't match anything anymore, need exact match
    _substitute(newBindings, unmatched)     # Replace variables with values

    if len(unmatched) == 0:
        if chatty>50: print "# Match found with bindings: ", bindingsToString(bindings)
        return action(bindings, param)  # No terms left .. success!

    
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
                    # Actually, it could be a valid problem -but pathalogical.

    quad = shortest_t
    unmatched.remove(quad)  # We will resolve this one now if possible

    consts = []   # Parts of speech to test for match
    vars = []   # Parts of speech which are variables
    for p in ALL4 :
        if quad[p] in variables + existentials:
            vars.append(p)
        elif p != shortest_p :
            consts.append(p)

    if chatty > 36:
        print "# Searching %i with %s in slot %i." %(shortest, `quad[shortest_p]`[-8:],shortest_p)
        print "#    for ", quadToString(quad)
        if chatty > 75:
            print "#    where variables are"
            for i in variables + existentials:
                print "#         ", `i`[-8:] 

    for s in quad[shortest_p].occursAs[shortest_p]:
        for p in consts:
            if s.triple[p] is not quad[p]:
                if chatty>78: print "   Rejecting ", quadToString(s.triple), "\n      for ", quadToString(quad)
                break
        else:  # found match
            nb = []
            for p in vars:
                nb.append(( quad[p], s.triple[p]))
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
 
 -pipe      Don't store, just pipe out *

 -rdf       Input & Output ** in RDF M&S 1.0 insead of n3 from now on
 -n3        Input & Output in N3 from now on
 -ugly      Store input and regurgitate *
 -bySubject Store inpyt and regurgitate in subject order *
 -no        No output *
            (default is to store and pretty print with anonymous nodes) *
 -apply=foo Read rules from foo, apply to store, adding conclusions to store
 -filter=foo Read rules from foo, apply to store, REPLACING store with conclusions
 -rules     Apply rules in store to store, adding conclusions to store
 -think     as -rules but continue until no more rule matches (or forever!)
 -reify     Replace the statements in the store with statements describing them.
 -flat      Reify only nested subexpressions (not top level) so that no {} remain.
 -help      print this message
 -chatty    Verbose output of questionable use
 

            * mutually exclusive
            ** doesn't work for complex cases :-/
Examples:
  cwm -rdf foo.rdf -n3 -pipe        Convert from rdf to n3
  cwm foo.n3 bar.n3 -think          Combine data and find all deductions

"""
        
        import urllib
        import time
        option_ugly = 0     # Store and regurgitate with genids *
        option_pipe = 0     # Don't store, just pipe though
        option_bySubject= 0 # Store and regurgitate in subject order *
        option_inputs = []
        option_reify = 0    # Flag: reify on output  (process?)
        option_outURI = None
        _doneOutput = 0
        _gotInput = 0     #  Do we not need to take input from stdin?
        option_meta = 0

        _step = 0           # Step number used for metadata

        hostname = "localhost" # @@@@@@@@@@@ Get real one
        
        # The base URI for this process - the Web equiv of cwd
#	_baseURI = "file://" + hostname + os.getcwd() + "/"
	_baseURI = "file:" + fixslash(os.getcwd()) + "/"
	
        option_rdf = 0      # Use RDF rather than XML
        _outURI = _baseURI
        option_baseURI = _baseURI     # To start with - then tracks running base
        for arg in sys.argv[1:]:  # Command line options after script name
            _equals = string.find(arg, "=")
            _lhs = ""
            _rhs = ""
            if _equals >=0:
                _lhs = arg[:_equals]
                _rhs = arg[_equals+1:]
                _uri = urlparse.urljoin(option_baseURI, _rhs) # Make abs from relative
            if arg == "-test":
                option_test = 1
                _gotInput = 1
            elif arg == "-ugly": _doneOutput = 1
            elif _lhs == "-base": option_baseURI = _uri
            elif arg == "-rdf": option_rdf = 1
            elif arg == "-n3": option_rdf = 0
            elif arg == "-pipe": option_pipe = 1
            elif arg == "-bySubject": _doneOutput = 1
            elif _lhs == "-outURI": option_outURI = _uri
            elif arg == "-chatty": chatty = 1
            elif arg[:7] == "-apply=": pass
            elif arg == "-reify": option_reify = 1
            elif arg == "-help":
                print doCommand.__doc__
                return
            elif arg[0] == "-": pass  # Other option
            else :
                option_inputs.append(urlparse.urljoin(option_baseURI,arg))
                _gotInput = _gotInput + 1  # input filename
            

#  Base defauts

        if option_baseURI == _baseURI:
            if _gotInput == 1:
                _baseURI = option_inputs[0]

#  Metadata context - storing information about what we are doing

	_metaURI = urlparse.urljoin(option_baseURI, "META/")  # Reserrved URI @@
	_runURI = _metaURI+`time.time()`
	history = None

# Between passes, prepare for processing

        _outURI = _baseURI
        if option_baseURI == _baseURI: # If base not specified
            if _gotInput == 1:          # and only one input then relative to that
                _outURI = option_inputs[0]
        if option_outURI: _outURI = urlparse.urljoin(_outURI, option_outURI)
        
	if option_rdf:
            _outSink = notation3.ToRDF(sys.stdout, _outURI)
        else:
            _outSink = notation3.ToN3(sys.stdout.write, _outURI)
        version = "$Id$"
	_outSink.makeComment("Processed by " + version[1:-1]) # Strip $ to disarm
	_outSink.makeComment("    using base " + _baseURI)


        if option_pipe:
            _store = _outSink
            if option_reify: _store = notation3.Reifier(_store, _outURI)
        else:
            myEngine = Engine()
            _store = RDFStore(myEngine, _outURI+"#_gs")
            workingContext = myEngine.internURI(_outURI)
            _meta = myEngine.internURI(_metaURI)

        if not _gotInput: #@@@@@@@@@@ default input
            _inputURI = _baseURI # Make abs from relative
            p = notation3.SinkParser(_store,  _inputURI)
            p.load("")
            del(p)
            if not option_pipe:
                inputContext = myEngine.internURI(_inputURI)
                history = inputContext
                if inputContext is not workingContext:
                    _store.moveContext(inputContext,workingContext)  # Move input data to output context


#  Take commands from command line: Second Pass on command line:

        option_rdf = 0      # Use RDF rather than XML
        _outURI = _baseURI
        option_baseURI = _baseURI     # To start with
        for arg in sys.argv[1:]:  # Command line options after script name
            _equals = string.find(arg, "=")
            _lhs = ""
            _rhs = ""
            if _equals >=0:
                _lhs = arg[:_equals]
                _rhs = arg[_equals+1:]
                _uri = urlparse.urljoin(option_baseURI, _rhs) # Make abs from relative
                
            if arg[0] != "-":
                _inputURI = urlparse.urljoin(option_baseURI, arg) # Make abs from relative
                if option_rdf: p = xml2rdf.RDFXMLParser(_store,  _inputURI)
                else: p = notation3.SinkParser(_store,  _inputURI)
                p.load(_inputURI)
                del(p)
                if not option_pipe:
                    inputContext = myEngine.internURI(_inputURI)
                    _store.moveContext(inputContext,workingContext)  # Move input data to output context
                    _step  = _step + 1
                    s = _metaURI + `_step`  #@@ leading 0s to make them sort?
                    if doMeta and history:
                        _store.storeQuad((_meta, META_mergedWith, s, history))
                        _store.storeQuad((_meta, META_source, s, inputContext))
                        _store.storeQuad((_meta, META_run, s, run))
                        history = s
                    else:
                        history = inputContext
                _gotInput = 1

            elif arg == "-help":
                print doCommand.__doc__

            elif arg == "-test": test()
            elif _lhs == "-base":
                option_baseURI = _uri
                progress("Base now "+option_baseURI)

            elif arg == "-ugly":
                _store.dumpChronological(workingContext, _outSink)
                _doneOutput = 1            

            elif arg == "-pipe": pass
            elif _lhs == "-outURI": option_outURI = _uri

            elif arg == "-rdf": option_rdf = 1
            elif arg == "-n3": option_rdf = 0
            
            elif arg == "-chatty": cwm.chatty = 1

            elif arg == "-reify":
                if not option_pipe:
                    _playURI = urlparse.urljoin(_baseURI, "PLAY")  # Intermediate
                    _playContext = myEngine.internURI(_playURI)
                    _store.moveContext(workingContext, _playContext)

                    _store.dumpBySubject(_playContext,
                                         notation3.Reifier(_store, _outURI))                                

            elif arg == "-flat":  # reify only nested expressions, not top level
                if not option_pipe:
                    _playURI = urlparse.urljoin(_baseURI, "PLAY")  # Intermediate
                    _playContext = myEngine.internURI(_playURI)
                    _store.moveContext(workingContext, _playContext)

                    _store.dumpBySubject(_playContext,
                                         notation3.Reifier(_store, _outURI, 1)) #flat                                

            elif option_pipe: ############## End of pipable options
                print "# Command line error: %s illegal option with -pipe", arg
                break

            elif arg == "-bySubject":
                _store.dumpBySubject(workingContext, _outSink)
                _doneOutput = 1            

            elif arg[:7] == "-apply=":
                filterContext = (myEngine.internURI(_uri))
                print "# Input rules to apply from ", _uri
                _store.loadURI(_uri)
                _store.applyRules(workingContext, filterContext);

            elif _lhs == "-filter":
                filterContext = myEngine.internURI(_uri)
                _playURI = urlparse.urljoin(_baseURI, "PLAY")  # Intermediate
                _playContext = myEngine.internURI(_playURI)
                _store.moveContext(workingContext, _playContext)
#                print "# Input filter ", _uri
                _store.loadURI(_uri)
                _store.applyRules(_playContext, filterContext, workingContext)

                if doMeta:
                    _step  = _step + 1
                    s = _metaURI + `_step`  #@@ leading 0s to make them sort?
                    _store.storeQuad(_meta, META_basis, s, history)
                    _store.storeQuad(_meta, META_filter, s, inputContext)
                    _store.storeQuad(_meta, META_run, s, run)
                    history = s

            elif arg == "-purge":
                _store.purge(workingContext)

            elif arg == "-rules":
                _store.applyRules(workingContext, workingContext)

            elif arg == "-think":
                grandtotal = 0
                iterations = 0
                while 1:
                    iterations = iterations + 1
                    step = _store.applyRules(workingContext, workingContext)
                    if step == 0: break
                    grandtotal= grandtotal + step
                progress("Grand total of %i new statements in %i iterations." %
                         (grandtotal, iterations))

            elif arg == "-size":
                progress("Size of store: %i statements." %(_store.size,))

            elif arg == "-no":  # suppress output
                _doneOutput = 1
                
            elif arg[:8] == "-outURI=": pass
            else: print "Unknown option", arg



# Squirt it out if no output done
        if not option_pipe and not _doneOutput:
            progress("Begining output.")
            _store.dumpNested(workingContext, _outSink)

def progress(str):
    sys.stderr.write("#   " + str + "\n")
    
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

