
class GivenReasonNotUsed(KeyError):
    pass

class FormulaNotFound(KeyError):
    pass

class Store:
    """

    A set, with reasons why things are in it, and watchers.

    When you add, you supply a reason

    When you remove, you say which reason is no longer valid.  When
    all reasons for an element are gone, the element goes away.
    
    At this level we don't actually *look* at the formula or reason at
    all!   The examples just use strings.   I imagine this will be
    used with LX.expr's as the formula (element).  I'm not yet sure
    what structure the reasons/justifications might take.
    
    >>> import LX.store.basic
    >>> s=LX.store.basic.Store()

    * ADD STUFF
    
    >>> s.add("Rain is Wet", "dictionary.com")
    >>> s.add("Rain is Wet", "dictionary.com")
    >>> s.add("Rain is Wet", "I felt it")
    >>> s.formulas
    ['Rain is Wet']
    >>> s.add("Rain is Cold", "I felt it")
    >>> s.add("Rain is Cold", "I felt it")
    >>> s.formulas
    ['Rain is Wet', 'Rain is Cold']

    * ITERATE
    
    >>> for f in s:
    ...    print f
    Rain is Wet
    Rain is Cold

    * EXAMINE

    >>> s.why("Rain is Cold")
    ['I felt it']

    >>> "Rain is Cold" in s
    True

    >>> "Rain is GREEN" in s
    False
    
    * REMOVE STUFF
    
    >>> s.remove("Rain is FUNNY", "I felt it")
    Traceback (most recent call last):
    ...
    FormulaNotFound
    >>> s.remove("Rain is Cold", "Some other reason")
    Traceback (most recent call last):
    ...
    GivenReasonNotUsed
    >>> s.remove("Rain is Cold", "I felt it")
    >>> s.formulas
    ['Rain is Wet']
    >>> s.remove("Rain is Wet", "I felt it")
    >>> s.formulas
    ['Rain is Wet']
    >>> s.why('Rain is Wet')
    ['dictionary.com']

    * WATCHERS -- USED FOR PRINTING CHANGES
    
    >>> s.addTo(Print())
    (PRINT) Add 'Rain is Wet', because 'dictionary.com', formulaAdded=None
    >>> s.watchers.append(Print())
    >>> s.add("I love spring", "just a feeling")
    (PRINT) Add 'I love spring', because 'just a feeling', formulaAdded=True
    >>> s.add("I love spring", "just a feeling")
    (PRINT) Add 'I love spring', because 'just a feeling', formulaAdded=False
    >>> s.add("I love spring", "just a feeling 2")
    (PRINT) Add 'I love spring', because 'just a feeling 2', formulaAdded=False
    >>> s.formulas
    ['Rain is Wet', 'I love spring']
    >>> s.remove("I love spring", "not a feeling")
    Traceback (most recent call last):
    ...
    GivenReasonNotUsed
    >>> s.remove("I love spring", "just a feeling")
    (PRINT) Remove 'I love spring', because 'just a feeling', formulaRemoved=False
    >>> s.remove("I love spring", "just a feeling 2")
    (PRINT) Remove 'I love spring', because 'just a feeling 2', formulaRemoved=True

    * WATCHERS -- USED FOR MIRRORING...

    (I want this for Node-centric form to be kept in sync, not
    to mention all sorts of .... other stuff.)
    
    
    """

    def __init__(self):
        self._formulas = []
        self._why = { }
        self.watchers = []

    def add(self, formula, why, formulaAdded=None):
        """Make sure this formula is in the store, and add this reason
           to the set of reasons why it's there.  
        """
        try:
            # make sure this reason is listed
            self._why[formula].setdefault(why, 1)
            assert(formulaAdded is None or not formulaAdded)
            formulaAdded = False
        except KeyError:
            self._why[formula] = { why: 1 }
            self._formulas.append(formula)
            assert(formulaAdded is None or formulaAdded)
            formulaAdded = True
        for w in self.watchers:
            w.add(formula, why, formulaAdded)

    def remove(self, formula, why, formulaRemoved=None):
        """Remove this reason for the formula being in the store; if
        there are no reasons left, remove the formula.  Note that we
        don't keep count of the number of times a given reason is
        used; if that reason is no longer valid, it doesnt matter how
        many times it was used earlier.

        If formulaRemoved= is True, then you're supposed to end up actually
        removing the formula; if it's False then you're not.  This is
        mostly meant as a hint for lazy stores which don't want to
        keep a list of _why, and trust they'll be called right
        (because, for instance, they are watchers).
        """
        try:
            reasons = self._why[formula]
        except KeyError, e:
            raise FormulaNotFound
        try:
            del reasons[why]
        except KeyError, e:
            raise GivenReasonNotUsed()
        if len(reasons) == 0:
            self._formulas.remove(formula)
            assert(formulaRemoved is None or formulaRemoved)
            formulaRemoved=True
        else:
            assert(formulaRemoved is None or not formulaRemoved)
            formulaRemoved=False
        for w in self.watchers:
            w.remove(formula, why, formulaRemoved)

    def __iter__(self):
        return self._formulas.__iter__()
        
    def why(self, formula):
        return self._why[formula].keys()

    def __in__(self, formula):
        return formula in self._why.keys()

    def getFormulas(self):
        return self._formulas

    formulas = property(getFormulas)

    def addTo(self, other):
        for f in self._formulas:
            for w in self.why(f):
                other.add(f, w)

    def removeFrom(self, other):
        for f in self._formulas:
            for w in self.why(f):
                try:
                    other.remove(f, w)
                except GivenReasonNotUsed: pass
                except FormulaNotFound: pass

class Print:

    def add(self, formula, why, formulaAdded=None):
        print "(PRINT) Add '%s', because '%s', formulaAdded=%s" % (
            formula, why, formulaAdded)
        
    def remove(self, formula, why, formulaRemoved=None):
        print "(PRINT) Remove '%s', because '%s', formulaRemoved=%s" % (formula, why, formulaRemoved)
    

if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])
 
# $Log$
# Revision 1.1  2003-09-30 05:04:42  sandro
# first draft
#
