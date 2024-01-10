# Python2 had a `cmp` function 
# Python3 removed it and replaced it with `__lt__`, `__eq__`, `__gt__`

# for sorting, key functions are used instread of compaison functions in p3.
# but sometimes it useful to have a comparison function.

def compareStrings(self, other):
    if self < other: return -1
    if self > other: return 1
    return 0    

def compareNumbers(self, other):
    if self < other: return -1
    if self > other: return 1
    return 0    

