#!/bin/python
"""Convert disk utiliyzation output to scalable graphic


dusvg > foo.svg
"""

import os
from os.path import join, getsize

#for root, dirs, files in os.walk('python/Lib/email'):
#    print root, "consumes",
#    print sum([getsize(join(root, name)) for name in files]),
#    print "bytes in", len(files), "non-directory files"
#    if 'CVS' in dirs:
#        dirs.remove('CVS')  # don't visit CVS directories

verbose = 1
ignorable = []

class File:
    def __init__(self, parent, name, level=0):
	self.parent = parent
	self.name = name
	self.size = None
	self.size = None
	self.level = level
	self.children = None

    def path(self):
	if self.parent == None: return self.name
	return join(self.parent.path(), self.name)

    def measure(self):
	if self.name in ignorable:
	    return 0
	path = self.path()
	try:
	    s = os.lstat(path)  # unix only
	except OSError:
	    if verbose >= 0: sys.stderr.write(" "*level + "Error checking %s\n" % path)
	    self.size = 0
	else:
	    if verbose: print " "*level, \
		"Checking", child, "mode=%6o" % s.st_mode, (s.st_mode & 0x4000)
	    self.size = s.st_size
	    if not (s.st_mode & 0x4000): # Directory .. symbol?
		if verbose: print " "*level, "...Non-dir Size", self.size
	    else:
		if verbose: print " "*level, "...Directory size", self.size
		contents = os.listdir(path)
		for fn in contents:
		    child = File(self, fn, self.level+1)
		    self.size += child.measure()
	return self.size
    



top = File(".", [".Trash"])
x = top.measure()
print "Total size", x

# ends
