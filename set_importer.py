"""
A hack to import sets and frozensets, internally if possible

"""

try:
    Set = set
except NameError:
    from sets import Set


try:
    ImmutableSet = frozenset
except NameError:
    from sets import ifilterfalse, ImmutableSet as notImmutableEnoughSet
    class ImmutableSet(notImmutableEnoughSet):
        def copy(self):
            return self.__class__(self)
        
        def symmetric_difference(self, other):
            """Return the symmetric difference of two sets as a new set.

            (I.e. all elements that are in exactly one of the sets.)
            """
            data = {}
            value = True
            selfdata = self._data
            try:
                otherdata = other._data
            except AttributeError:
                otherdata = Set(other)._data
            for elt in ifilterfalse(otherdata.has_key, selfdata):
                data[elt] = value
            for elt in ifilterfalse(selfdata.has_key, otherdata):
                data[elt] = value
            return self.__class__(data)

        def difference(self, other):
            """Return the difference of two sets as a new Set.

            (I.e. all elements that are in this set and not in the other.)
            """
            
            data = {}
            try:
                otherdata = other._data
            except AttributeError:
                otherdata = Set(other)._data
            value = True
            for elt in ifilterfalse(otherdata.has_key, self):
                data[elt] = value
            return self.__class__(data)
