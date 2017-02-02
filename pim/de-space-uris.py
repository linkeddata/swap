#!/usr/bin/python
#
#   Look for and remove spaces from tel: URIs in turtle files
#
import sys
import string
import os


def preExtension(str):
    dot = str.find('.')
    if dot < 0: return str
    return str[0: dot]

def extension(str):
    dot = str.find('.')
    if dot < 0: return None
    return str[dot + 1:]


def do(path):
    global doall
    global URIsFixed
    global filesDeleted
    sys.stdout.write("Scanning " + path + '\n')
    if os.path.isdir(path):
        names = os.listdir(path)
        for name in names:
            thisPath = path + '/' + name
            if os.path.isdir(thisPath):
                do(thisPath)
    else: # Not directory
        if (path.endswith('.ttl')):
            print "Looking at " + path
            buf = file.open(path, 'r').read()
            lines = bug.split('\n')
            for i in range(len(lines)):
                line = lines[i]
                result = line
                start = line.find('<tel:')
                if start >= 0:
                    end = line.indexOf('>', start)
                    result = line[0:start+5] + line[start+5:end].replace(' ', '') + line[end:]
                    print "    fixed to: " + result
                    URIsFixed += 1
                    line[i] = result
            buf2 = lines.join('\n')


######################################## Main program

recursive = 0
nochange = 1
verbose = 0
doall = 0
files = []
nulls = 0
totals = 0
URIsFixed = 0
filesDeleted = 0

for arg in sys.argv[1:]:
    if arg[0:1] == "-":
        if arg == "-f": nochange = 0   # Modify the file

        elif arg == "-v": verbose = 1   # Tell me even about files which were ok
        else:
            print """Bad option argument.
            -f  fix files instead of just looking: remove redundant files

This program rmeoves (with -f) or counts (without -f)
files where one starts with the name of trhe other, and they are music files,
like     song.mp3 and "song 1.mp3"

Runs recusively through the directories.
Command line argument is a directory (or more than one).
"""
            sys.exit(-1)
    else:
        files.append(arg)

if files == []: files = [ "." ] # Default to this directory

for path in files:
    do(path)
if nochange:
    adjective = "redundant"
else:
    adjective = "deleted"
sys.stdout.write("Files %s: %i" % (adjective, filesDeleted) + '\n')
sys.stdout.write("Bytes %s: %i" % (adjective, URIsFixed) + '\n')
