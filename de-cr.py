#!/usr/bin/python
#
import sys
import string
import os


def strip(path):
    global nochange
    global verbose
    crs = 0
    total = 0

    input = open(path, "r")
    if not nochange:
        temporary = path + ".decr-temp"
        output = open(temporary, "w")
    buf = input.read()  # Read the file
    for c in buf:
        if c != "\r" :
            if not nochange: output.write(c)
            total = total + 1
        else:
            crs = crs + 1
    input.close()
    if not nochange:
        output.close()
        os.rename(temporary, path)
        
    if crs > 0 or verbose:
        sys.stderr.write("de-cr: %i crs found, %i non-cr characters in %s.\n"%(crs,total, path))


def do(path):
    if verbose: sys.stderr.write("Doing " + path + "\n")
    if os.path.isdir(path):
        if recursive:
            for name in os.listdir(path):
                do(path + "/" + name)
    else:
        if path[-3:] == ".n3" or path[-4:] == ".rdf" or path[-3:] == ".py":
            strip(path) 
        
######################################## Main program

recursive = 0
nochange = 1
verbose = 0
files = []

for arg in sys.argv[1:]:
    if arg[0:1] == "-":
        if arg == "-r": recursive = 1    # Recursive
        elif arg == "-f": nochange = 0   # Fix
        elif arg == "-v": verbose = 1   # Tell me even about files which were ok
        else:
            print """Bad option argument.
            -r  recursive
            -f  fix files instead of just looking

"""
            sys.exit(-1)
    else:
        files.append(arg)

if files == []: files = [ "." ] # Default to this directory

for path in files:
    do(path)
