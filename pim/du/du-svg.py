#!/bin/python
"""Convert disk utiliyzation output to scalable graphic


dusvg > foo.svg
"""

import os, sys
from os.path import join, getsize

#for root, dirs, files in os.walk('python/Lib/email'):
#    print root, "consumes",
#    print sum([getsize(join(root, name)) for name in files]),
#    print "bytes in", len(files), "non-directory files"
#    if 'CVS' in dirs:
#        dirs.remove('CVS')  # don't visit CVS directories

verbose = 1
ignorable = []
threshold = 1 # Bytes: ignore below this size
chunking = 120	# Number of perpendicular things we like in a region
#	strokeColor  fillColor
style =  [
	("#FDD",		"#400"),  	# red
	("#FED",		"#420"),	# Orange
	("#FFD",		"#440"),
	("#DFD",		"#040"),
	("#DFF",		"#044"),
	("#DDF",		"#004"),
	("#FFF",		"#002"),
	("#FDD",		"#400"),
	("#FFF",		"none")
	]
	
svg = sys.stdout.write
deb = sys.stderr.write

class File:
    def __init__(self,  name, parent=None, level=0):
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
	    if verbose >= 0: deb(" "*level + "Error checking %s\n" % path)
	    self.size = 0
	else:
	    if verbose: deb( " "*self.level + "Checking %s, mode=%6o, size=%i\n" %(path, s.st_mode, s.st_size))
	    self.size = s.st_size
	    if (s.st_mode & 0x4000): # Directory .. symbol?
		self.children = []
		contents = os.listdir(path)
		for fn in contents:
		    child = File(fn, self, self.level+1)
		    self.size += child.measure()
		    self.children.append(child)
		if verbose: deb( " "*self.level + "...Dir %s total size %i\n" %(self.name,self.size))
	return self.size
    
    def layout(self, x, y, width, height, flipped=0):
	if verbose: deb( " "*self.level + "Layout for %s (%f,%f)-(%f,%f) %i\n" %(
			    self.path(), x, y, x+width, y+height, flipped))
	if height > width: return self.layout(y, x, height, width, flipped=1-flipped)
	if self.children == None:
	    self.rectangle(x, y, width, height, flipped)
	    self.label(x, y, width, height, flipped)
	    return # Plain file

	# First the details then overlay this one
	yy = []
	for child in self.children:
	    if child.size > threshold:
		yy.append((child.size, child))
	yy.sort()
	yy.reverse()  # Now in reverse order of size, biggest first
	cursor = 0
	for siz, child in yy:
	    if siz * chunking > self.size:
		dx = width * siz/float(self.size)
		child.layout(x + cursor, y, dx, height, flipped)
		cursor += dx
	    remaining = width - cursor

	self.rectangle(x, y, width, height, flipped, opacity=0.2)
	if self.level > 0:
	    self.label(x, y, width, height, flipped, opacity=0.2)

    def rectangle(self, x, y, dx, dy, flipped=0, opacity=1.0):
	if flipped: return self.rectangle(y, x, dy, dx, flipped=0, opacity=opacity) #  flip
	fillColor, strokeColor = style[self.level]
	if opacity < 0.9: fillColor = "none"  #  Don't bother
	strokeWidth = (dx + dy) /400.0
	svg("""<rect x="%f" y="%f" width="%f" height="%f" opacity="%1.1f"
        fill="%s" stroke="%s" stroke-width="%f"/>\n""" %(x, y, dx, dy, opacity, fillColor, strokeColor, strokeWidth))

    def label(self, x, y, dx, dy, flipped, opacity=1.0):
	fillColor, strokeColor = style[self.level]
	if flipped:
	    em1 = (dy/len(self.name))
	    em2 = (dx/2)
	else:
	    em1 = (dx/len(self.name))
	    em2 = (dy/2)
	em = min(em1, em2)
	strokeWidth = em/200
	if flipped:
	    svg("""<g transform="translate(%f,%f)">
	<text transform="rotate(-90deg)" x="0" y="0" opacity="%1.1f" 
	    fill="%s" stroke="%s" font-size="%f" stroke-width="%f">%s</text></g>\n""" #"
		%(y+(dy/2)+ (0.3*em), x+dy-em, opacity,  strokeColor, strokeColor, em,  strokeWidth, self.name))
	else:
	    svg("""<text x="%f" y="%f" opacity="%1.1f" fill="%s" stroke="%s" font-size="%f" stroke-width="%f">%s</text>\n""" 
		%(x+(em/2), y+(dy/2)+ (0.3*em),  opacity, strokeColor, strokeColor, em,  strokeWidth, self.name))
	
    def discreteLabel(self, x, y, dx, dy, flipped):
	fillColor, strokeColor = style[self.level]
	if flipped:
	    em1 = (dy/len(self.name))
	    em2 = (dx/4)
	else:
	    em1 = (dx/len(self.name))
	    em2 = (dy/4)
	em = min(em1, em2)
	strokeWidth = em/200
	if flipped:
	    svg("""<g transform="rotate(-90deg)"><text transform="translate(%f,%f)" x="0" y="0" opacity="0.2" fill="%s" stroke="%s" font-size="%f" stroke-width="%f">%s</text></g>\n""" #"
		%(y+dy-em, x+em,  strokeColor, strokeColor, em,  strokeWidth, self.name))
	else:
	    svg("""<text x="%f" y="%f" opacity="0.2" fill="%s" stroke="%s" font-size="%f" stroke-width="%f">%s</text>\n""" #"
		%(x+em, y+dy-em,  strokeColor, strokeColor, em,  strokeWidth, self.name))
	

try: start = sys.argv[1]
except IndexError: start = "."

svg("<svg>\n")
top = File(start)
x = top.measure()
print "Total size", x
top.layout(0, 0, 600, 800)
svg("</svg>\n")

# ends
