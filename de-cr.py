#!/usr/bin/python
#
import sys
import string
import os


def strip(path):
    """Check the file and replace it with a version with no CRs.
    If the file does not contain a CR, don't touch it"""
    global nochange
    global verbose
    crs = 0
    total = 0

    input = open(path, "r")
    buf = input.read()  # Read the file
    input.close()
    if buf.find("\r") >=0:
        if not nochange:
            temporary = path + ".decr-temp"
            output = open(temporary, "w")
        for c in buf:
            if c != "\r" :
                if not nochange: output.write(c)
                total = total + 1
            else:
                crs = crs + 1
        if not nochange:
            output.close()
            os.rename(temporary, path)
        
    if crs > 0 or verbose:
        if nochange:
            sys.stderr.write("de-cr: %i crs found, %i non-cr characters in %s.\n"%(crs,total, path))
        else:
            sys.stderr.write("de-cr: %i crs removed, %i non-cr characters left in %s.\n"%(crs,total, path))


def do(path):
    global doall
    if verbose: sys.stderr.write("de-cr: considering " + path + "\n")
    if os.path.isdir(path):
        if recursive:
            for name in os.listdir(path):
                do(path + "/" + name)
    else:
        if doall or path[-3:] == ".n3" or path[-4:] == ".rdf" or path[-3:] == ".py":
            strip(path)
        else:
            sys.stderr.write("de-cr: skipping "+path+"\n")
        
######################################## Main program

recursive = 0
nochange = 1
verbose = 0
doall = 0
files = []

for arg in sys.argv[1:]:
    if arg[0:1] == "-":
        if arg == "-r": recursive = 1    # Recursive
        elif arg == "-a": doall = 1   # Fix
        elif arg == "-f": nochange = 0   # Fix
        elif arg == "-v": verbose = 1   # Tell me even about files which were ok
        else:
            print """Bad option argument.
            -r  recursive
            -a  do all files, not just .n3 .py and .rdf
            -f  fix files instead of just looking

"""
            sys.exit(-1)
    else:
        files.append(arg)

if files == []: files = [ "." ] # Default to this directory

for path in files:
    do(path)
