#!/bin/python
"""Visualize disk usage as scalable graphic

A rectangular area is divided up according to directories and subdirectories,
to scale so you can see where all you disk space has gone.

du-svg ~/Documents > foo.svg

Author timbl@w3.org 2004/9/19
Licence: W3C open source. Enjoy
"""

import os, sys
from os.path import join, getsize

verbose = 0
ignorable = []
threshold = 1 # Bytes: ignore below this size
chunking = 120	# Number of perpendicular things we like in a region
#	 fillColor	strokeColor
style =  [
	("none",		"black"),
	("#FDD",		"#400"),  	# red
#	("#FED",		"#420"),	# Orange
	("#FFD",		"#440"),	# Yellow
	("#DFD",		"#040"),
	("#DFF",		"#044"),
	("#DDF",		"#004"),
	("#FFF",		"#002"),
	("#FDF",		"#404"),
	("none",		"black")
	]
	
svg = sys.stdout.write
deb = sys.stderr.write

def styleFor(level):
    return style[level % len(style)]

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
	    if verbose >= 0: deb(" "*self.level + "Error checking %s\n" % path)
	    self.size = 0
	else:
	    if verbose: deb( " "*self.level + "Checking %s, mode=%6o, size=%i\n" %(path, s.st_mode, s.st_size))
	    self.size = s.st_size
	    if (s.st_mode & 0x4000): # Directory .. symbol?
		self.children = []
		try:
		    contents = os.listdir(path)
		except OSError:
		    if verbose >= 0:
			deb(" "*self.level +  "Error listing %s, assumed empty\n" % path)
		    contents = []
		for fn in contents:
		    child = File(fn, self, self.level+1)
		    self.size += child.measure()
		    self.children.append(child)
		if verbose: deb( " "*self.level + "...Dir %s total size %i\n" %(self.name,self.size))
	return self.size
    
    def layout(self, x, y, width, height, flipped=0, inheritedPath = ""):
	if verbose: deb( " "*self.level + "Layout for %s (%f,%f)-(%f,%f) %i\n" %(
			    self.path(), x, y, x+width, y+height, flipped))
	if height > width: return self.layout(y, x, height, width, flipped=1-flipped, inheritedPath= inheritedPath)
	lab = inheritedPath + self.name
	if self.children == None:
	    self.rectangle(x, y, width, height, flipped)
	    self.label(lab, x, y, width, height, flipped)
	    return # Plain file

	# First the details then overlay this one
	yy = []
	for child in self.children:
	    if (child.size > threshold):  #  and (child.size * chunking > self.size):
		yy.append((child.size, child))
	yy.sort()
	yy.reverse()  # Now in reverse order of size, biggest first
	cursor = 0
	singleton = (len(yy) == 1) and (self.size - yy[0][0]) < threshold
	if singleton: ip = lab + "/"
	else: ip = ""
	for siz, child in yy:
	    dx = width * siz/float(self.size)
	    child.layout(x + cursor, y, dx, height, flipped, ip)
	    cursor += dx
#	remaining = width - cursor

	self.rectangle(x, y, width, height, flipped, opacity=0.2)
	if self.level > 0 and not singleton:
	    if len(yy) == 0: opacity = 1.0
	    else: opacity = 0.2
	    self.label(lab, x, y, width, height, flipped, opacity=opacity)

    def rectangle(self, x, y, dx, dy, flipped=0, opacity=1.0):
	if flipped: return self.rectangle(y, x, dy, dx, flipped=0, opacity=opacity) #  flip
	fillColor, strokeColor = styleFor(self.level)
	if opacity < 0.9: fillColor = "none"  #  Don't bother
	strokeWidth = (dx + dy) /400.0
	svg("""<rect x="%f" y="%f" width="%f" height="%f" opacity="%1.1f"
        fill="%s" stroke="%s" stroke-width="%f"/>\n""" %(x, y, dx, dy, opacity, fillColor, strokeColor, strokeWidth))

    def label(self, lab, x, y, dx, dy, flipped, opacity=1.0):
	fillColor, strokeColor = styleFor(self.level)
	# Figure out max font size will fit in
#	if flipped:
	if 0:
	    em1 = (dy/(len(lab)+2)) * 1.6
	    em2 = (dx/2)
	else:
	    em1 = (dx/(len(lab)+2)) * 1.6
	    em2 = (dy/2)
	em = min(em1, em2)
	stagger = (self.level-2) * em /2.0
	y1 = y+(dy/2)+ (0.3*em) + stagger
	strokeWidth = em/200
	if flipped:
	    svg("""<g transform="translate(%f,%f)">
	<text transform="rotate(-90deg)" x="0" y="0" opacity="%1.1f" 
	    fill="%s" stroke="%s" font-size="%f" stroke-width="%f">%s</text></g>\n""" #"
		%(y1, x+dx-em, opacity,  strokeColor, strokeColor, em,  strokeWidth, escape(lab)))
	else:
	    svg("""<text x="%f" y="%f" opacity="%1.1f" fill="%s" stroke="%s" font-size="%f" stroke-width="%f">%s</text>\n""" 
		%(x+(em/2), y1,  opacity, strokeColor, strokeColor, em,  strokeWidth, escape(lab)))
	
def escape(s):
    "Escape text for XML"
    res = ""
    for ch in s:
	if ch == "&": ch = "&amp;"
	elif ch == "<": ch = "&lt;"
	elif ch == ">": ch = "&gt;"
	res += ch
    return res

try: start = sys.argv[1]
except IndexError: start = "."

svg("<svg xmlns=\"http://www.w3.org/2000/svg\">\n")
top = File(start)
x = top.measure()
threshold = x/1000.0  # say ... try that
deb("Total size %f; ignoring things less than %f\n" %(x, threshold))
top.layout(0, 0, 550, 700)
svg("</svg>\n")

# ends
