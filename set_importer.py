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
    from sets import ImmutableSet
