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
    from sets import ifilterfalse, BaseSet, ImmutableSet as notImmutableEnoughSet
    class ImmutableSet(notImmutableEnoughSet):
        def copy(self):
            return self.__class__(self)

        def union(self, other):
            ret = self._data.copy()
            if isinstance(other, BaseSet): 
                ret.update(other._data)
                return self.__class__(ret)

            value = True

            if type(other) in (list, tuple, xrange):
                # Optimized: we know that __iter__() and next() can't
                # raise TypeError, so we can move 'try:' out of the loop.
                it = iter(other)
                while True:
                    try:
                        for element in it:
                            ret[element] = value
                        return self.__class__(ret)
                    except TypeError:
                        transform = getattr(element, "__as_immutable__", None)
                        if transform is None:
                            raise # re-raise the TypeError exception we caught
                        ret[transform()] = value
            else:
                # Safe: only catch TypeError where intended
                for element in iterable:
                    try:
                        ret[element] = value
                    except TypeError:
                        transform = getattr(element, "__as_immutable__", None)
                        if transform is None:
                            raise # re-raise the TypeError exception we caught
                        ret[transform()] = value
            return self.__class__(ret)

        
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
