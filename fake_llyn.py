#! /usr/bin/python
"""

$Id$



    
Copyright ()  2000-2004 World Wide Web Consortium, (Massachusetts Institute
of Technology, European Research Consortium for Informatics and Mathematics,
Keio University). All Rights Reserved. This work is distributed under the
W3C Software License [1] in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 FOR A PARTICULAR PURPOSE.
"""

# emacsbug="""emacs got confused by long string above@@"""

from __future__ import generators
# see http://www.amk.ca/python/2.2/index.html#SECTION000500000000000000000

import types
import string
import re
import StringIO
import sys
import time
from warnings import warn


import urllib # for log:content
import md5, binascii  # for building md5 URIs

import uripath
#import notation3    # N3 parsers and generators, and RDF generator
#from webAccess import urlopenForRDF   # http://www.w3.org/2000/10/swap/
# import sax2rdf      # RDF1.0 syntax parser to N3 RDF stream

import diag  # problems importing the tracking flag, and chatty_flag must be explicit it seems diag.tracking
from diag import progress, verbosity
from term import BuiltIn, LightBuiltIn, \
    HeavyBuiltIn, Function, ReverseFunction, \
    Literal, Symbol, Fragment, FragmentNil, Term,\
    CompoundTerm, List, EmptyList, NonEmptyList, AnonymousNode,  AnonymousExistential
from OrderedSequence import merge
from formula import Formula, StoredStatement
import reify

from query import think, applyRules, testIncludes
#import webAccess
#from webAccess import DocumentAccessError
from decimal import Decimal
#from llyn import RDFStore

from RDFSink import Logic_NS, RDFSink, forSomeSym, forAllSym
from RDFSink import CONTEXT, PRED, SUBJ, OBJ, PARTS, ALL4
from RDFSink import N3_nil, N3_first, N3_rest, OWL_NS, N3_Empty, N3_List, List_NS
from RDFSink import RDF_NS_URI

from RDFSink import FORMULA, LITERAL, ANONYMOUS, SYMBOL

from pretty import Serializer
from OrderedSequence import indentString

LITERAL_URI_prefix = "data:text/rdf+n3;"
Delta_NS = "http://www.w3.org/2004/delta#"
cvsRevision = "$Revision$"


# Magic resources we know about

from RDFSink import RDF_type_URI, DAML_sameAs_URI

from why import Because, BecauseBuiltIn, BecauseOfRule, \
    BecauseOfExperience, becauseSubexpression, BecauseMerge ,report

STRING_NS_URI = "http://www.w3.org/2000/10/swap/string#"
META_NS_URI = "http://www.w3.org/2000/10/swap/meta#"
INTEGER_DATATYPE = "http://www.w3.org/2001/XMLSchema#integer"
FLOAT_DATATYPE = "http://www.w3.org/2001/XMLSchema#double"
DECIMAL_DATATYPE = "http://www.w3.org/2001/XMLSchema#decimal"

#reason=Namespace("http://www.w3.org/2000/10/swap/reason#")

META_mergedWith = META_NS_URI + "mergedWith"
META_source = META_NS_URI + "source"
META_run = META_NS_URI + "run"

doMeta = 0  # wait until we have written the code! :-)
    

class DataObject:
    """The info about a term in the context of a specific formula
    It is created by being passed the formula and the term, and is
    then accessed like a python dictionary of sequences of values. Example:
    
    F = myWorkingFormula
    x = F.theObject(pred=rdfType obj=fooCar)
    for y in x[color][label]
    """
    def __init__(context, term):
	self.context = context
	self.term = term
	
    def __getItem__(pred):   #   Use . or [] ?
	values = context.objects(pred=pred, subj=self.term)
	for v in value:
	    yield DataObject(self.context, v)



###################################### Forumula
#
class fakeFormula(Formula):
    """A fake formula
    """
    def __init__(self, store, uri=None):
        AnonymousNode.__init__(self, store, uri)
        self.canonical = None # Set to self if this has been canonicalized
	self.statements = []
	self._existentialVariables = []
	self._universalVariables = []

    def existentials(self):
        """Return a list of existential variables with this formula as scope.
	
	Implementation:
	we may move to an internal storage rather than these pseudo-statements"""
        return []


    def universals(self):
        """Return a list of variables universally quantified with this formula as scope.

	Implementation:
	We may move to an internal storage rather than these statements."""
	return []
    
    def variables(self):
        """Return a list of all variables quantified within this scope."""
        return self.existentials() + self.universals()
	
    def size(self):
        """Return the number statements.
	Obsolete: use len(F)."""
        return len(self.statements)

    def __len__(self):
        """ How many statements? """
        return len(self.statements)

    def newSymbol(self, uri):
	"""Create or reuse the internal representation of the RDF node whose uri is given
	
	The symbol is created in the same store as the formula."""
	return self.store.newSymbol(uri)

    def newList(self, list):
	return self.store.nil.newList(list)

    def newLiteral(self, str, dt=None, lang=None):
	"""Create or reuse the internal representation of the RDF literal whose string is given
	
	The literal is created in the same store as the formula."""
	return self.store.newLiteral(str, dt, lang)

    def intern(self, value):
	return self.store.intern(value)
	
    def newBlankNode(self, uri=None, why=None):
	"""Create a new unnamed node with this formula as context.
	
	The URI is typically omitted, and the system will make up an internal idnetifier.
        If given is used as the (arbitrary) internal identifier of the node."""
	x = AnonymousExistential(self, uri)
	self._existentialVariables.append(x)
	return x

    
    def declareUniversal(self, v):
	if verbosity() > 90: progress("Declare universal:", v)
	if v not in self._universalVariables:
	    self._universalVariables.append(v)
	
    def declareExistential(self, v):
	if verbosity() > 90: progress("Declare existential:", v)
	if v not in self._existentialVariables:  # Takes time
	    self._existentialVariables.append(v)
#	else:
#	    raise RuntimeError("Redeclared %s in %s -- trying to erase that" %(v, self)) 
	
    def newExistential(self, uri=None, why=None):
	"""Create a named variable existentially qualified within this formula
	
	If the URI is not given, an arbitrary identifier is generated.
	See also: existentials()."""
	if uri == None:
	    raise RuntimeError("Please use newBlankNode with no URI")
	    return self.newBlankNode()  # Please ask for a bnode next time
	return self.store.newExistential(self, uri, why=why)
    
    def newUniversal(self, uri=None, why=None):
	"""Create a named variable universally qualified within this formula
	
	If the URI is not given, an arbitrary identifier is generated.
	See also: universals()"""
	x = AnonymousUniversal(self, uri)
	self._universalVariables.append(x)
	return x

    def newFormula(self, uri=None):
	"""Create a new open, empty, formula in the same store as this one.
	
	The URI is typically omitted, and the system will make up an internal idnetifier.
        If given is used as the (arbitrary) internal identifier of the formula."""
	return self.store.newFormula(uri)

    def statementsMatching(self, pred=None, subj=None, obj=None):
        """Return a READ-ONLY list of StoredStatement objects matching the parts given
	
	For example:
	for s in f.statementsMatching(pred=pantoneColor):
	    print "We've got one which is ", `s[OBJ]`
	    
	If none, returns []
	"""
        raise RuntimeError

    def contains(self, pred=None, subj=None, obj=None):
        """Return boolean true iff formula contains statement(s) matching the parts given
	
	For example:
	if f.contains(pred=pantoneColor):
	    print "We've got one statement about something being some color"
	"""
        raise RuntimeError


    def any(self, subj=None, pred=None, obj=None):
        """Return None or the value filing the blank in the called parameters.
	
	Specifiy exactly two of the arguments.
	color = f.any(pred=pantoneColor, subj=myCar)
	somethingRed = f.any(pred=pantoneColor, obj=red)
	
	Note difference from the old store.any!!
	Note SPO order not PSO.
	To aboid confusion, use named parameters.
	"""
        raise RuntimeError


    def the(self, subj=None, pred=None, obj=None):
        """Return None or the value filing the blank in the called parameters
	
	This is just like any() except it checks that there is only
	one answer in the store. It wise to use this when you expect only one.
	
	color = f.the(pred=pantoneColor, subj=myCar)
	redCar = f.the(pred=pantoneColor, obj=red)
	"""
	raise RuntimeError

    def each(self, subj=None, pred=None, obj=None):
        """Return a list of values value filing the blank in the called parameters
	
	Examples:
	colors = f.each(pred=pantoneColor, subj=myCar)
	
	for redthing in f.each(pred=pantoneColor, obj=red): ...
	
	"""
        raise RuntimeError

    def searchable(self, subj=None, pred=None, obj=None):
	"""A pair of the difficulty of searching and a statement iterator of found statements
	
	The difficulty is a store-portable measure of how long the store
	thinks (in arbitrary units) it will take to search.
	This will only be used for choisng which part of the query to search first.
	If it is 0 there is no solution to the query, we know now.
	
	In this implementation, we use the length of the sequence to be searched."""
	raise RuntimeError


    def substitution(self, bindings, why=None):
	"Return this or a version of me with subsitution made"
	raise RuntimeError
    
    def loadFormulaWithSubsitution(self, old, bindings={}, why=None):
	"""Load information from another formula, subsituting as we go
	returns number of statements added (roughly)"""
        raise RuntimeError
                
    def substituteEquals(self, bindings, newBindings):
	"""Return this or a version of me with subsitution made
	
	Subsitution of = for = does NOT happen inside a formula,
	as the formula is a form of quotation."""
	return self

    def occurringIn(self, vars):
	"Which variables in the list occur in this?"
	raise RuntimeError

    def unify(self, other, vars, existentials, bindings):
	"""See Term.unify()
	"""
        raise RuntimeError
	
		    

    def bind(self, prefix, uri):
	"""Give a prefix and associated URI as a hint for output
	
	The store does not use prefixes internally, but keeping track
	of those usedd in the input data makes for more human-readable output.
	"""
	return self.store.bind(prefix, uri)

    def add(self, subj, pred, obj, why=None):
	"""Add a triple to the formula.
	
	The formula must be open.
	subj, pred and obj must be objects as for example generated by Formula.newSymbol() and newLiteral(), or else literal values which can be interned.
	why 	may be a reason for use when a proof will be required.
	"""
        if self.canonical != None:
            raise RuntimeError("Attempt to add statement to canonical formula "+`self`)

        raise RuntimeError('Not overloading this function  makes very little sense')
    
    def removeStatement(self, s):
	"""Removes a statement The formula must be open.
	
	This implementation is alas slow, as removal of items from tha hash is slow.
	"""
        raise RuntimeError
    
    def close(self):
        """No more to add. Please return interned value.
	NOTE You must now use the interned one, not the original!"""
        return self.canonicalize()

    def canonicalize(F):
        """If this formula already exists, return the master version.
        If not, record this one and return it.
        Call this when the formula is in its final form, with all its statements.
        Make sure no one else has a copy of the pointer to the smushed one.
	 
	LIMITATION: The basic Formula class does NOT canonicalize. So
	it won't spot idenical formulae. The IndexedFormula will.
        """
	store = F.store
	if F.canonical != None:
            if verbosity() > 70:
                progress("Canonicalize -- @@ already canonical:"+`F`)
            return F.canonical
	# @@@@@@@@ no canonicalization @@ warning
	F.canonical = F
	return F


    def n3String(self, base=None, flags=""):
        "Dump the formula to an absolute string in N3"
        buffer=StringIO.StringIO()
        _outSink = notation3.ToN3(buffer.write,
                                      quiet=1, base=base, flags=flags)
        self.store.dumpNested(self, _outSink)
        return buffer.getvalue()

    def rdfString(self, base=None, flags=""):
        "Dump the formula to an absolute string in RDF/XML"
        buffer=StringIO.StringIO()
        _outSink = ToRDF(buffer, _outURI, base=base, flags=flags)
        self.store.dumpNested(self, _outSink)
        return buffer.getvalue()

    def outputStrings(self, channel=None, relation=None):
        """Fetch output strings from store, sort and output

        To output a string, associate (using the given relation) with a key
        such that the order of the keys is the order in which you want the corresponding
        strings output.
        """
        if channel == None:
            channel = sys.stdout
        if relation == None:
            relation = self.store.intern((SYMBOL, Logic_NS + "outputString"))
        list = self.statementsMatching(pred=relation)  # List of things of (subj, obj) pairs
        pairs = []
        for s in list:
            pairs.append((s[SUBJ], s[OBJ]))
        pairs.sort(comparePair)
        for key, str in pairs:
            channel.write(str.string.encode('utf-8'))

    def reopen(self):
	"""Make a formula which was once closed oopen for input again.
	
	NOT Recommended.  Dangers: this formula will be, because of interning,
	the same objet as a formula used elsewhere which happens to have the same content.
	You mess with this one, you mess with that one.
	Much better to keep teh formula open until you don't needed it open any more.
	The trouble is, the parsers close it at the moment automatically. To be fixed."""
        return self.store.reopen(self)


    def includes(f, g, _variables=[],  bindings=[]):
	"""Does this formula include the information in the other?
	
	bindings is for use within a query.
	"""
	return  f.store.testIncludes(f, g, _variables=_variables,  bindings=bindings)

    def generated(self):
	"""Yes, any identifier you see for this is arbitrary."""
        return 1

    def asPair(self):
	"""Return an old representation. Obsolete"""
        return (FORMULA, self.uriref())

    def subjects(self, pred=None, obj=None):
        """Obsolete - use each(pred=..., obj=...)"""
	raise RuntimeError

    def predicates(self, subj=None, obj=None):
        """Obsolete - use each(subj=..., obj=...)"""
	raise RuntimeError

    def objects(self, pred=None, subj=None):
        """Obsolete - use each(subj=..., pred=...)"""
	raise RuntimeError

    def reification(self, sink, bnodeMap={}, why=None):
	"""Describe myself in RDF to the given context
	
	
	"""
	raise RuntimeError

    def flatten(self, sink, why=None):
        return self.reification(sink, {}, why=why)

    def doesNodeAppear(self, symbol):
        """Does that particular node appear anywhere in this formula

        This function is necessarily recursive, and is useful for the pretty printer
        It will also be useful for the flattener, when we write it.
        """
        raise RuntimeError


def comparePair(self, other):
    "Used only in outputString"
    for i in 0,1:
        x = self[i].compareAnyTerm(other[i])
        if x != 0:
            return x





###############################################################################################
#
#                       C W M - S P E C I A L   B U I L T - I N s
#
###########################################################################
    
# Equivalence relations


################################################################################################

class fakeRDFStore(RDFSink):
    """ Absorbs RDF stream and saves in triple store
    """

    def clear(self):
        "Remove all formulas from the store     @@@ DOESN'T ACTUALLY DO IT/BROKEN"
        self.resources = {}    # Hash table of URIs for interning things
#        self.formulae = []     # List of all formulae        
        self._experience = None   #  A formula of all the things program run knows from direct experience
        self._formulaeOfLength = {} # A dictionary of all the constant formuale in the store, lookup by length key.
        self.size = 0

    def __init__(self, genPrefix=None, metaURI=None, argv=None, crypto=0):
        RDFSink.__init__(self, genPrefix=genPrefix)
        self.clear()
        self.argv = argv     # List of command line arguments for N3 scripts

	run = uripath.join(uripath.base(), ".RUN/") + `time.time()`  # Reserrved URI @@

        if metaURI != None: meta = metaURI
	else: meta = run + "meta#formula"
	self.reset(meta)


        # Constants, as interned:
        
        self.forSome = self.symbol(forSomeSym)
	self.integer = self.symbol(INTEGER_DATATYPE)
	self.float  = self.symbol(FLOAT_DATATYPE)
	self.decimal = self.symbol(DECIMAL_DATATYPE)
        self.forAll  = self.symbol(forAllSym)
        self.implies = self.symbol(Logic_NS + "implies")
        self.insertion = self.symbol(Delta_NS + "insertion")
        self.deletion  = self.symbol(Delta_NS + "deletion")
        self.means = self.symbol(Logic_NS + "means")
        self.asserts = self.symbol(Logic_NS + "asserts")
        
# Register Light Builtins:

        log = self.symbol(Logic_NS[:-1])   # The resource without the hash

# Functions:        

        self.Literal =  log.internFrag("Literal", Fragment) # syntactic type possible value - a class
        self.List =     log.internFrag("List", Fragment) # syntactic type possible value - a class
        self.Formula =  log.internFrag("Formula", Fragment) # syntactic type possible value - a class
        self.Other =    log.internFrag("Other", Fragment) # syntactic type possible value - a class
        
	self.sameAs = self.symbol(OWL_NS + "sameAs")

# Remote service flag in metadata:

	self.definitiveService = log.internFrag("definitiveService", Fragment)
	self.definitiveDocument = log.internFrag("definitiveDocument", Fragment)
	self.pointsAt = log.internFrag("pointsAt", Fragment)  # This was EricP's

# Constants:

        self.Truth = self.symbol(Logic_NS + "Truth")
        self.Falsehood = self.symbol(Logic_NS + "Falsehood")
        self.type = self.symbol(RDF_type_URI)
        self.Chaff = self.symbol(Logic_NS + "Chaff")
	self.docRules = self.symbol("http://www.w3.org/2000/10/swap/pim/doc#rules")
	self.imports = self.symbol("http://www.w3.org/2002/07/owl#imports")

# List stuff - beware of namespace changes! :-(

	from cwm_list import BI_first, BI_rest
        rdf = self.symbol(List_NS[:-1])
	self.first = rdf.internFrag("first", BI_first)
        self.rest = rdf.internFrag("rest", BI_rest)
        self.nil = self.intern(N3_nil, FragmentNil)
        self.Empty = self.intern(N3_Empty)
        self.List = self.intern(N3_List)

        import cwm_string  # String builtins
        import cwm_os      # OS builtins
        import cwm_time    # time and date builtins
        import cwm_math    # Mathematics
        import cwm_trigo   # Trignometry
        import cwm_times    # time and date builtins
        import cwm_maths   # Mathematics, perl/string style
	import cwm_list	   # List handling operations
        cwm_string.register(self)
        cwm_math.register(self)
        cwm_trigo.register(self)
        cwm_maths.register(self)
        cwm_os.register(self)
        cwm_time.register(self)
        cwm_times.register(self)
	cwm_list.register(self)
        if crypto:
	    import cwm_crypto  # Cryptography
	    cwm_crypto.register(self)  # would like to anyway to catch bug if used but not available


    def newLiteral(self, str, dt=None, lang=None):
	"In a fake RDFStore we don't intern things"
	return Literal(self, str, dt, lang)
	
    def newFormula(self, uri=None):
	return fakeFormula(self, uri)



###################

    def reset(self, metaURI): # Set the metaURI
        self._experience = self.newFormula(metaURI + "_formula")
	assert isinstance(self._experience, Formula)

    def load(store, uri=None, openFormula=None, asIfFrom=None, contentType=None, remember=1,
		    flags="", referer=None, why=None):
	"""Get and parse document.  Guesses format if necessary.

	uri:      if None, load from standard input.
	remember: if 1, store as metadata the relationship between this URI and this formula.
	
	Returns:  top-level formula of the parsed document.
	Raises:   IOError, SyntaxError, DocumentError
	
	This was and could be an independent function, as it is fairly independent
	of the store. However, it is natural to call it as a method on the store.
	And a proliferation of APIs confuses.
	"""
	raise RuntimeError
    



    def loadMany(self, uris, openFormula=None, referer=None):
	"""Get, parse and merge serveral documents, given a list of URIs. 
	
	Guesses format if necessary.
	Returns top-level formula which is the parse result.
	Raises IOError, SyntaxError
	"""
	raise RuntimeError

    def genId(self):
	"""Generate a new identifier
	
	This uses the inherited class, but also checks that we haven't for some pathalogical reason
	ended up generating the same one as for example in another run of the same system. 
	"""
	while 1:
	    uriRefString = RDFSink.genId(self)
            hash = string.rfind(uriRefString, "#")
            if hash < 0 :     # This is a resource with no fragment
		return uriRefString # ?!
	    resid = uriRefString[:hash]
	    r = self.resources.get(resid, None)
	    if r == None: return uriRefString
	    fragid = uriRefString[hash+1:]
	    f = r.fragments.get(fragid, None)
	    if f == None: return uriRefString
	    if diag.chatty_flag > 70:
		progress("llyn.genid Rejecting Id already used: "+uriRefString)
		
    def checkNewId(self, urirefString):
	"""Raise an exception if the id is not in fact new.
	
	This is useful because it is usfeul
	to generate IDs with useful diagnostic ways but this lays them
	open to possibly clashing in pathalogical cases."""
	hash = string.rfind(urirefString, "#")
	if hash < 0 :     # This is a resource with no fragment
	    result = self.resources.get(urirefString, None)
	    if result == None: return
	else:
	    r = self.resources.get(urirefString[:hash], None)
	    if r == None: return
            f = r.fragments.get(urirefString[hash+1:], None)
            if f == None: return
	raise ValueError("Ooops! Attempt to create new identifier hits on one already used: %s"%(urirefString))
	return


    def internURI(self, str, why=None):
        warn("use symbol()", DeprecationWarning, stacklevel=3)
        return self.intern((SYMBOL,str), why)

    def symbol(self, str, why=None):
	"""Intern a URI for a symvol, returning a symbol object"""
        return self.intern((SYMBOL,str), why)

    
    def _fromPython(self, x, queue=None):
	"""Takem a python string, seq etc and represent as a llyn object"""
        if isinstance(x, tuple(types.StringTypes)):
            return self.newLiteral(x)
        elif type(x) is types.LongType or type(x) is types.IntType:
            return self.newLiteral(str(x), self.integer)
        elif isinstance(x, Decimal):
            return self.newLiteral(str(x), self.decimal)
        elif type(x) is types.FloatType:
	    if `x`.lower() == "nan":  # We can get these form eg 2.math:asin
		return None
            return self.newLiteral(`x`, self.float)
        elif isinstance(x, Term):
            return x
        elif hasattr(x,'__getitem__'): #type(x) == type([]):
	    return self.newList([self._fromPython(y) for y in x])
        return x

    def intern(self, what, dt=None, lang=None, why=None, ):
        """find-or-create a Fragment or a Symbol or Literal or list as appropriate

        returns URISyntaxError if, for example, the URIref has
        two #'s.
        
        This is the way they are actually made.
        """

	if isinstance(what, Term): return what # Already interned.  @@Could mask bugs
	if type(what) is not types.TupleType:
	    if isinstance(what, tuple(types.StringTypes)):
		return self.newLiteral(what, dt, lang)
#	    progress("llyn1450 @@@ interning non-string", `what`)
	    if type(what) is types.LongType:
		return self.newLiteral(str(what),  self.integer)
	    if type(what) is types.IntType:
		return self.newLiteral(`what`,  self.integer)
	    if type(what) is types.FloatType:
		return self.newLiteral(`what`,  self.float)
	    if isinstance(what,Decimal):
                return self.newLiteral(str(what), self.decimal)
	    if type(what) is types.ListType: #types.SequenceType:
		return self.newList(what)
	    raise RuntimeError("Eh?  can't intern "+`what`+" of type: "+`type(what)`)

        typ, urirefString = what

        if typ == LITERAL:
	    return self.newLiteral(urirefString, dt, lang)
        else:
            assert ':' in urirefString, "must be absolute: %s" % urirefString

            hash = string.rfind(urirefString, "#")
            if hash < 0 :     # This is a resource with no fragment
		assert typ == SYMBOL, "If URI <%s>has no hash, must be symbol" % urirefString
                result = Symbol(urirefString, self)           
            else :      # This has a fragment and a resource
                resid = urirefString[:hash]
                if string.find(resid, "#") >= 0:
                    raise URISyntaxError("Hash in document ID - can be from parsing XML as N3! -"+resid)
                r = self.symbol(resid)
                if typ == SYMBOL:
                    if urirefString == N3_nil[1]:  # Hack - easier if we have a different classs
                        result = r.internFrag(urirefString[hash+1:], FragmentNil)
                    else:
                        result = r.internFrag(urirefString[hash+1:], Fragment)
                elif typ == ANONYMOUS:
		    result = r.internFrag(urirefString[hash+1:], AnonymousNode)
                elif typ == FORMULA:
		    raise RuntimeError("obsolete")
		    result = r.internFrag(urirefString[hash+1:], fakeFormula)
                else: raise RuntimeError, "did not expect other type:"+`typ`
        return result

    def newList(self, value, context=None):
	raise RuntimeError("You'll want to override this function too")

#    def deleteFormula(self,F):
#        if diag.chatty_flag > 30: progress("Deleting formula %s %ic" %
#                                            ( `F`, len(F.statements)))
#        for s in F.statements[:]:   # Take copy
#            self.removeStatement(s)


    def reopen(self, F):
        if F.canonical == None:
            if diag.chatty_flag > 50:
                progress("reopen formula -- @@ already open: "+`F`)
            return F # was open
        if diag.chatty_flag > 00:
            progress("warning - reopen formula:"+`F`)
	key = len(F.statements), len(F.universals()), len(F.existentials()) 
        self._formulaeOfLength[key].remove(F)  # Formulae of same length
        F.canonical = None
        return F

                    
    def makeComment(self, str):
        raise RuntimeError("You'll want to override this")

    def any(self, q):
        """Query the store for the first match.
	
	Quad contains one None as wildcard. Returns first value
        matching in that position.
	"""
        list = q[CONTEXT].statementsMatching(q[PRED], q[SUBJ], q[OBJ])
        if list == []: return None
        for p in ALL4:
            if q[p] == None:
                return list[0].quad[p]

    def bind(self, prefix, uri):
        raise RuntimeError("you want to do something here")
        if prefix != "":   #  Ignore binding to empty prefix
            return RDFSink.bind(self, prefix, uri) # Otherwise, do as usual.

    def makeStatement(self, tuple, why=None):
	"""Add a quad to the store, each part of the quad being in pair form."""
        q = ( self.intern(tuple[CONTEXT]),
              self.intern(tuple[PRED]),
              self.intern(tuple[SUBJ]),
              self.intern(tuple[OBJ]) )
        if q[PRED] is self.forSome and isinstance(q[OBJ], Formula):
            if diag.chatty_flag > 97:  progress("Makestatement suppressed")
            return  # This is implicit, and the same formula can be used un >1 place
        self.storeQuad(q, why)

    def storeQuad(self, q, why=None):
        """ intern quads, in that dupliates are eliminated.

	subject, predicate and object are terms - or atomic values to be interned.
        Builds the indexes and does stuff for lists.
	Deprocated: use Formula.add()         
        """
        context, pred, subj, obj = q
	assert isinstance(context, fakeFormula), "Should be a Formula: "+`context`
	
	return context.add(subj=subj, pred=pred, obj=obj, why=why)
	
    def newBlankNode(self, context, uri=None, why=None):
        return context.newBlankNode(uri, why)

    def startDoc(self):
        raise RuntimeError("You'll want to override this function too")

    def endDoc(self, rootFormulaPair):
        raise RuntimeError("You'll want to override this function too")




##########################################################################
#
# Output methods:
#
    def dumpChronological(self, context, sink):
	"Fast as possible. Only dumps data. No formulae or universals."
	raise RuntimeError
	
    def dumpBySubject(self, context, sink, sorting=1):
        """ Dump by order of subject except forSome's first for n3=a mode"""
	raise RuntimeError
	

    def dumpNested(self, context, sink):
        """ Iterates over all URIs ever seen looking for statements
        """
	raise RuntimeError



##################################  Manipulation methods:
#
#  Note when we move things, then the store may shrink as they may
# move on top of existing entries and we don't allow duplicates.
#
#   @@@@ Should automatically here rewrite any variable name clashes
#  for variable names which occur in the other but not as the saem sort of variable
# Must be done by caller.

    def copyFormula(self, old, new, why=None):
	bindings = {old: new}
	for v in old.universals():
	    new.declareUniversal(bindings.get(v,v))
	for v in old.existentials():
	    new.declareExistential(bindings.get(v,v))
        for s in old.statements[:] :   # Copy list!
            q = s.quad
            for p in CONTEXT, PRED, SUBJ, OBJ:
                x = q[p]
                if x is old:
                    q = q[:p] + (new,) + q[p+1:]
            self.storeQuad(q, why)
                

    def purge(self, context, boringClass=None):
        """Clean up intermediate results

    Statements in the given context that a term is a Chaff cause
    any mentions of that term to be removed from the context.
    """
        if boringClass == None:
            boringClass = self.Chaff
        for subj in context.subjects(pred=self.type, obj=boringClass):
	    self.purgeSymbol(context, subj)

    def purgeSymbol(self, context, subj):
	"""Purge all triples in which a symbol occurs.
	"""
	total = 0
	for t in context.statementsMatching(subj=subj)[:]:
		    context.removeStatement(t)    # SLOW
		    total = total + 1
	for t in context.statementsMatching(pred=subj)[:]:
		    context.removeStatement(t)    # SLOW
		    total = total + 1
	for t in context.statementsMatching(obj=subj)[:]:
		    context.removeStatement(t)    # SLOW
		    total = total + 1
	if diag.chatty_flag > 30:
	    progress("Purged %i statements with %s" % (total,`subj`))
	return total


#    def removeStatement(self, s):
#        "Remove statement from store"
# 	return s[CONTEXT].removeStatement(s)

    def purgeExceptData(self, context):
	"""Remove anything which can't be expressed in plain RDF"""
	uu = context.universals()
	for s in context.statements[:]:
	    for p in PRED, SUBJ, OBJ:
		x = s[p]
		if x in uu or isinstance(x, Formula):
		    context.removeStatement(s)
		    break
	context._universalVariables =[]  # Cheat! @ use API



class URISyntaxError(ValueError):
    """A parameter is passed to a routine that requires a URI reference"""
    pass



def isString(x):
    # in 2.2, evidently we can test for isinstance(types.StringTypes)
    #    --- but on some releases, we need to say tuple(types.StringTypes)
    return type(x) is type('') or type(x) is type(u'')


#ends

