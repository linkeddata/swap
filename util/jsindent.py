#!/usr/bin/python
#
#  Cheap and cheerful Javascript indenter.  
# Note block braces must be last or fisrt char on line if line ahs any quotes on it.
# This doesnot properly parse the file.  Just designed for pyjs conversions from python  to js
#
import sys
import string
import os
import re

version = "$Id$"[1:-1]

def convert(path):
#    print "// Start of info from", path
    input = open(path, "r")
    buf = input.read()  # Read the file
    eol = -1
    indent = 0
    while eol<len(buf):
        sol = eol +1
        eol = buf.find('\n', sol)
        if eol < 0: break;
        opens, closes =  0, 0
        quotes, suspect = 0, 0
        line = buf[sol:eol]
        while len(line) > 0 and line[0] in ' \t':
            line = line[1:]
        for i in range(len(line)):
            ch = line[i]
            if ch in "\"'":
                quotes = 1
            if ch == '{':
                if i != len(line) -1 and i != 0 and quotes:
                    suspect += 1
                else: 
                    opens += 1
            if ch == '}':
                if i != len(line) -1 and i != 0 and quotes:
                    suspect += 1
                else: 
                    closes += 1
            
        indent -= closes
        print " " * (4*indent) + line
#        if (suspect): print "// @@ check indent"
        indent += opens
        if indent < 0: indent = 0; 
        
    input.close()
    if (indent != 0) :
        print "// Ooops, final indent = ", indent
#    print "// End of info from", path
    


def do(path, explicit=1):
    """Indent-fix files
    
    """
    global doall
    global recursive
    global verbose

    if verbose: sys.stderr.write("fink2n3: converting " + path + "\n")
    convert(path)
        
######################################## Main program

recursive = 0
nochange = 1
verbose = 0
doall = 0
files = []

for arg in sys.argv[1:]:
    if arg[0:1] == "-":
        if arg == "-r": recursive = 1    # Recursive
	elif arg == "-a": doall=1
	elif arg == "-v": verbose=1
        elif arg == "-?" or arg == "-h" or arg == "--help":
	    print """Convert Fink .info format  to n3 format.

Syntax:    make2n3  [-r] <file>

    where <file> can be omitted and if so defaults to /sw/fink/dists .
    This program was http://www.w3.org/2000/10/swap/util/fink2p3.py
    $Id$
"""
        else:
            print """Bad option argument.""", arg, ". use -? for help."
            sys.exit(-1)
    else:
        files.append(arg)

if files == []: files = [ "/sw/fink/dists" ] # Default

for path in files:
    do(path)

# ends
