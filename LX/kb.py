"""


"""
__version__ = "$Revision$"
# $Id$

import LX

class KB(list):
    """A Knowledge Base, a list of implicitely conjoined sentences.

    This is comparable to an RDF Graph if the Sentences here are all
    triples.

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
    """

    def __init__(self):
        self.exivars = []
        self.univars = []
        self.exIndex = 0

    def clear(self):
        self.__init__()
        self[:] = []
        
    def prep(kb):
        """return a KB if possible, perhaps just the argument; throw
        an error we can't make a KB out of this thing"""
        if isinstance(kb, KB): return kb
        if isinstance(kb, list): return KB(kb)
        # nothing else for now
        raise RuntimeError, "Not convertable to a KB"
    prep = staticmethod(prep)

    def add(self, formula):
        assert(isinstance(formula, LX.Formula))
        self.append(formula)

    def addFrom(self, kb):
        for formula in kb:
            self.add(formula)
        self.exivars.extend(kb.exivars)
        self.univars.extend(kb.univars)
        self.exIndex = self.exIndex + kb.exIndex

    def newExistential(self, name=None):
        if name is None:
            name = "g" + str(self.exIndex)
            self.exIndex = self.exIndex + 1
        # @@@ check to make sure name not used!
        v = LX.ExiVar(name)
        self.exivars.append(v)
        return v

    
    def reifyAsTrue(self):
        flat = KB()
        LX.rdf.flatten(self, flat, indirect=1)
        self.clear()
        self.addFrom(flat)

    def reifyAsTrueNonRDF(self):
        flat = KB()
        LX.rdf.flatten(self, flat, indirect=0)
        self.clear()
        self.addFrom(flat)

    def load(self, uri, allowedLanguages=["*"]):
        """Add the formal meaning of identified document.

        In the simplest case, this might mean opening a local file,
        which we know to contain n3, read the contents, and parse them
        directly to the kb.

        In a more complex case, we do an HTTP GET to obtain the
        document, using allowedLanguages to help guide our content
        negotiation, get some content, figure out what language is
        actually used, [recursively] load that language's definition,
        use that definition to build a parser for the original content,
        and parse it.

        We end up with a logical formula which might or might not be
        RDF (depending on how the language definition is written), but
        we can convert it, of course.  If we want to load from an
        untrusted source, load to a temporary kb first, reify it to
        the main KB, then apply your trust rules.

        See Blindfold.

        Does something like:

           1.  Identify the language
                 from content-type, other headers, embedded emacs magic strings,
                 suffixes, 
                 and perhaps a pre-arranged list of allowed languages.
           2.  Look up its definition
                 from an allowed set of language definitions, and/or the web
           3.  Parse it, collecting the semantics
                 perhaps by compiling a parser for it
           4.  return the logic sentence it claims
                 with some latitude as to form; the sentence only guarantees
                 to be inconsistent (T=F) or to entail only the intended
                 expression's meaning and separable metadata. 

        """
        
        
# $Log$
# Revision 1.3  2002-10-02 23:32:20  sandro
# not sure
#
# Revision 1.2  2002/08/29 16:39:55  sandro
# fixed various early typos and ommissions; working on logic bug which is manifesting in description loops
#
# Revision 1.1  2002/08/29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

  
