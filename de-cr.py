#!/usr/bin/python
#
#   Sanitize a source file, data file etc
#
#  Unix uses LF by itself and no CR for lines.
#  Null characters are  a bad idea as it makes e,g, hg treat a file as binary file.
#  You can get the by pasing junk from say a pdf file into a HTML input field.
#
import sys
import string
import os


def strip(path):
    """Check the file and replace it with a version with no CRs.
    If the file does not contain a CR, don't touch it"""
    global nochange
    global verbose
    global ascii
    global allowZeroes
    global nulls
    global lineNumbers
    crs = 0
    total = 0
    newlines = 0
    lines = 0

    input = open(path, "r")
    buf = input.read()  # Read the file
    if not ascii:
	buf = buf.decode('utf8')
    input.close()
    if buf.find("\r") >=0 or buf.find("\0") >=0:
        if not nochange:
            temporary = path + ".decr-temp"
            output = open(temporary, "w")
    n = len(buf)
    for i in range(n):
        c = buf[i]
        if c == "\r" :
            crs = crs + 1
            if lineNumbers:
                print "CR at ", lines
            if i < n-1 and buf[i+1] != "\n":
                newlines += 1
                if not nochange: output.write("\n")
        else:
            if c == "\0" and not allowZeroes:
                nulls += 1
                continue
            if not nochange:
                output.write(c.encode('utf8'))
            total = total + 1
            if c == "\n":
                lines += 1

        if not nochange:
            output.close()
            os.rename(temporary, path)

    if crs > 0 or nulls > 0 or verbose:
        if nochange:
            sys.stderr.write("de-cr: %i CRs found, %i needed LFs, %i nulls, %i non-cr non-null characters in %s.\n"%(
			crs, newlines, nulls, total, path))
        else:
            sys.stderr.write("de-cr: %i CRs removed, %i LFs inserted, %i nulls, %i non-CR non-null characters left in %s.\n"%(
			crs, newlines, nulls, total, path))


def do(path):
    global doall
    if verbose: sys.stderr.write("de-cr: considering " + path + "\n")
    if os.path.isdir(path):
        if recursive:
            for name in os.listdir(path):
                do(path + "/" + name)
    else:
        if doall or path.endswith(".n3") or  path[-3:] == ".js" or path[-4:] == ".rdf" or path[-3:] == ".py":
            strip(path)
        else:
            sys.stderr.write("de-cr: skipping "+path+"\n")

######################################## Main program

recursive = 0
nochange = 1
verbose = 0
ascii = 0
allowZeroes = 0
doall = 0
files = []
nulls = 0
lineNumbers = 0

for arg in sys.argv[1:]:
    if arg[0:1] == "-":
        if arg == "-r": recursive = 1    # Recursive
        elif arg == "-a": doall = 1   # not just .n3 .rdf .py
        elif arg == "-n": lineNumbers = 1 # Print lf line numbers where CRs are
        elif arg == "-f": nochange = 0   # Modify the file
        elif arg == "-ascii": ascii = 1   # don't use UTF8 just ascii
        elif arg == "-0": allowZeroes = 1   # allow nulls in output

        elif arg == "-v": verbose = 1   # Tell me even about files which were ok
        else:
            print """Bad option argument.
            -r  recursive
            -a  do all files, not just .n3 .py and .rdf
            -f  fix files instead of just looking
	    -ascii use ascii not UTF8
	    -0  allow null characters

This program restores a file to standard unix LF conventions
for line end.  It removes CR characters, inserting a new LF to
replace them if they are not followed by a LF in the original file.
It will not change any files unless -f is given.
"""
            sys.exit(-1)
    else:
        files.append(arg)

if files == []: files = [ "." ] # Default to this directory

for path in files:
    do(path)
