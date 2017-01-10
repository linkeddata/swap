#!/usr/bin/python
#
#   Look for and remove duplicate iTunes songs
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

activeExtensions = [ 'mp3', 'm4a']

def do(path):
    global doall
    global bytesDeleted
    global filesDeleted
    sys.stdout.write("Scanning " + path + '\n')
    if os.path.isdir(path):
        names = os.listdir(path)
        for name in names:
          if extension(name) in activeExtensions:
              thisPath = path + '/' + name
              start = preExtension(name)
              for other in names:
                  otherPath = path + '/' +  other
                  if len(other) > len(name) and other.startswith(start) and extension(other) == extension(name):
                      # sys.stdout.write( "Contender: \"" + otherPath + "\" as duplicate of \"" + name + "\"\n")
                      with open(thisPath, 'r') as thisFile:
                          x = thisFile.read()
                      with open(otherPath, 'r') as otherFile:
                          y = otherFile.read()
                      if x == y:
                          sys.stdout.write( "    Content of \"" + otherPath + "\"  exactly matches \"" + name + "\"\n")
                          size = os.stat(otherPath).st_size
                          bytesDeleted += size
                          filesDeleted += 1
                          if not nochange:
                              os.remove(otherPath)
                              "      rm " + otherPath
                      else:

                          sys.stdout.write( "    Different content: \"" + otherPath + "\" and  \"" + name + "\"\n")



        for name in names:
            thisPath = path + '/' + name
            if os.path.isdir(thisPath):
                do(thisPath)
    else:
        sys.stderr.write("SHOULD BE A DIRECTORY" + path+"\n")

######################################## Main program

recursive = 0
nochange = 1
verbose = 0
doall = 0
files = []
nulls = 0
totals = 0
bytesDeleted = 0
filesDeleted = 0

for arg in sys.argv[1:]:
    if arg[0:1] == "-":
        # if arg == "-r": recursive = 1    # Recursive
        # elif arg == "-a": doall = 1   # not just .n3 .rdf .py
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
sys.stdout.write("Bytes %s: %i" % (adjective, bytesDeleted) + '\n')
