#!/usr/bin/python
#
import sys
import string

crs = 0
total = 0

buf = sys.stdin.read()  # Read the file
for c in buf:
    if c != "\r" :
	sys.stdout.write(c)
	total = total +1
    else:
	crs = crs + 1

sys.stderr.write("%i crs found, %i non-cr characters.\n"%(crs,total))



