#! /usr/bin/python
"""
$Id$

Process-global store

Global variables are often a bad idea. However, the majority of cwm applications
involve just one RDF store. One store can contain many formulae.
The main thing which these formulae of the same store share is the index with which names 
and strings are interned.  Within a store, you can compare things by comparing
memory addresses rather than the whole tring, uri or list.

Therefore, it is normal to just use one store.
When you do this, the store paremeter to most methods beceomes unnecessary, and you get a simpler API.
That is what this module does. If you import it, you will get
a global store. This will not stop you using other stores.

You also get the Namespace() class which allows you to generate symbols easily

History:
    Spilt of from  thing.py 2003-08-19
"""

# Allow a strore provdier to register:

store = None
storeClass = None

def setStoreClass(c):
    """Set the process-global class to be used to generate a new store if needed"""
    global storeClass
    storeClass = c

def setStore(s):
    """Set the process-global default store to be used when an explicit store is not"""
    global store
    store = s

def _checkStore(s=None):
    """Check that an explict or implicit stroe exists"""
    global store, storeClass
    if s != None: return s
    if store != None: return store
    if storeClass == None:
	import llyn   # default 
    assert storeClass!= None, "Some storage module must register with myStore.py before you can use it"
    store = storeClass() # Make new one
    return store


def symbol(uri):
    """Create or reuse, in the default store, an interned version of the given symbol
    and return it for future use"""
    return _checkStore().newSymbol(uri)
    
def literal(str, dt=None, lang=None):
    """Create or reuse, in the default store, an interned version of the given literal string
    and return it for future use"""
    return _checkStore().newLiteral(str, dt, lang)

def formula():
    """Create or reuse, in the default store, a new empty formula (triple people think: triple store)
    and return it for future use"""
    return _checkStore().newFormula()

def bNode(str, context):
    """Create or reuse, in the default store, a new unnamed node within the given
    formula as context, and return it for future use"""
    return _checkStore().newBlankNode(context)

def existential(str, context, uri):
    """Create or reuse, in the default store, a new named variable
    existentially qualified within the given
    formula as context, and return it for future use"""
    return _checkStore().newExistential(context, uri)

def universal(str, context, uri):
    """Create or reuse, in the default store, a named variable
    universally qualified within the given
    formula as context, and return it for future use"""
    return _checkStore().newUniversal(context, uri)

def load(uri=None, contentType=None, formulaURI=None, remember=1):
    """Get and parse document.  Guesses format if necessary.

    uri:      if None, load from standard input.
    remember: if 1, store as metadata the relationship between this URI and this formula.
    
    Returns:  top-level formula of the parsed document.
    Raises:   IOError, SyntaxError, DocumentError
    """
    return _checkStore().load(uri, contentType, formulaURI, remember)

def loadMany(uris):
    """Load a number of resources into the same formula
    
    Returns:  top-level formula of the parsed information.
    Raises:   IOError, SyntaxError, DocumentError
    """
    return _checkStore().loadMany(uris)

class Namespace(object):
    """A shortcut for getting a symbols as interned by the default store

      >>> RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
      >>> RDF.type
      'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
      >>> RDF.type is RDF.type
      1

    """
    
    def __init__(self, name, store=None):
        if ':' not in name:    #, "must be absolute: %s" % name
	    base = uripath.base()
	    name = uripath.join(base, name)
        self._name = name
	self.store = store
        self._seen = {}
    
    def __getattr__(self, lname):
        """get the lname Symbol in this namespace.

        lname -- an XML name (limited to URI characters)
	I hope this is only called *after* the ones defines above have been checked
        """
        return _checkStore(self.store).symbol(self._name+lname)

    def sym(self, lname):
	"""For getting a symbol for an expression, rather than a constant.
	For, and from, pim/toIcal.py"""
	return  _checkStore(self.store).intern((SYMBOL, self._name + lname))


