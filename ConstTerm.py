"""Intern Semantic Web logical constants

We divide RDF/SWeLL terms into the following hierarchy:

Term
  Constant
    Symbol (i.e. URI, with or without #fragment)
    StringLiteral (i.e. unicode character sequence)
    IntegerLiteral (not in RDF '98)
    XMLLiteral (@@TODO: not implemented)
  BNode (i.e. existentially quantified variable)
    (also used for things like lists)
  Formula (i.e. nested formula; not in RDF '98)

This constant module covers only the constants, i.e.
the objects that can be shared accross stores/formulas/etc.

They are interned, meanwhile:

  >>> x=Symbol("http://example/")
  >>> y=Symbol("http://example/")
  >>> x is y
  1

  >>> l=StringLiteral("abc")
  >>> m=StringLiteral("abc")
  >>> l is m
  1

String literals are disjoint from symbols:

  >>> n=StringLiteral("http://example/")
  >>> x is n
  0
"""

__version__ = '$Id$'


class Symbol(str):
    """A symbol, or logical name, in the Semantic Web.

    Don't try to use a relative URI reference as a symbol:

      >>> bug=Symbol("../foo")
      Traceback (most recent call last):
        File "<string>", line 1, in ?
        File "ConstTerm.py", line 51, in __new__
          assert ':' in name, "must be absolute: %s" % name
      AssertionError: must be absolute: ../foo

    For now, at least, stick to US-ASCII characters in symbols:

      >>> bug=Symbol(u"http://example/#D\u00fcrst")
      Traceback (most recent call last):
        File "<string>", line 1, in ?
        File "ConstTerm.py", line 63, in __new__
          sym = str.__new__(Symbol, name)
      UnicodeError: ASCII encoding error: ordinal not in range(128)

    """
    
    _seen = {}
    
    def __new__(cls, name):
        seen = Symbol._seen
        try:
            return seen[name]
        except KeyError:
            assert ':' in name, "must be absolute: %s" % name
            sym = str.__new__(cls, name)
            seen[name] = sym
            return sym


class Namespace(object):
    """A collection of symbols with a common prefix

      >>> RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
      >>> RDF['type']
      'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
      >>> RDF['type'] is RDF['type']
      1

    """
    
    def __init__(self, name):
        assert ':' in name, "must be absolute: %s" % name
        self._name = name
        self._seen = {}

    def name(self):
        return self._name
    
    def __getitem__(self, lname):
        """get the lname Symbol in this namespace.

        lname -- an XML name (limited to URI characters)

        Hmm... we keep another hash table of just the names
        in this namespace... is this worthwhile?
        """
        
        seen = self._seen
        try:
            return seen[lname]
        except KeyError:
            sym = Symbol(self._name + lname)
            seen[lname] = sym
            return sym

        
class StringLiteral(unicode):
    _seen = {}
    
    def __new__(cls, chars):
        seen = StringLiteral._seen
        try:
            return seen[chars]
        except KeyError:
            lit = unicode.__new__(cls, chars)
            seen[chars] = lit
            return lit


def _test():
    import doctest, ConstTerm
    return doctest.testmod(ConstTerm)

if __name__ == "__main__":
    _test()
