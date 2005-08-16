#! /usr/bin/python
"""
Synchronize a set of files which (may) have changed with respect to
a last known common file.

--from=uri    	-f uri     The last known common file.
--to=uri      	-t uri     File whcih may have changed (typically two)
--meta=uri      -m uri     file with metadata to be assumed (in addition to schemas)
--help    	-h         print this help message
--verbose 	-v         verbose mode (two for extra)
--granularity=  -g 0       g=0 - lots of little diffs.
			   g=1, fewer diffs (default)

Uris are relative to present working directory.

For motivation and explanation, see  <http://www.w3.org/DesignIssues/Diff>

$Id$
http://www.w3.org/2000/10/swap/diff.py
"""



import string, getopt
from sets import Set    # Python2.3 and on
import string
import sys




# http://www.w3.org/2000/10/swap/
try:
    from swap import llyn, diag
    from swap.myStore import loadMany
    from swap.diag import verbosity, setVerbosity, progress
    from swap import notation3    	# N3 parsers and generators


    from swap.RDFSink import FORMULA, LITERAL, ANONYMOUS, Logic_NS
    from swap import uripath
    from swap.uripath import base
    from swap.myStore import  Namespace
    from swap import myStore
    from swap.notation3 import RDF_NS_URI
    from swap.llyn import Formula, CONTEXT, PRED, SUBJ, OBJ
    from swap.update import patch

except ImportError:
    import llyn, diag
    from myStore import loadMany
    from diag import verbosity, setVerbosity, progress
    import notation3    	# N3 parsers and generators


    from RDFSink import FORMULA, LITERAL, ANONYMOUS, Logic_NS
    import uripath
    from uripath import base
    from myStore import  Namespace
    import myStore
    from notation3 import RDF_NS_URI
    from llyn import Formula, CONTEXT, PRED, SUBJ, OBJ
    from update import patch


def loadFiles(files):
    graph = myStore.formula()
    graph.setClosureMode("e")    # Implement sameAs by smushing
    graph = myStore.loadMany(files, openFormula=graph)
    if verbose: progress("Loaded", graph, graph.__class__)
    return graph

def usage():
    sys.stderr.write(__doc__)
    
def main():
    oldFiles = []
    changedFiles = []
    commonFiles = []
    assumptions = Set()
    global ploughOn # even if error
    ploughOn = 0
    global verbose
    global lumped
    verbose = 0
    lumped = 1
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:t:c:m:vg",
	    ["help", "from=", "to=", "common=", "meta=", "verbose", "granularity="])
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)
    output = None
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-v", "--verbose"):
	    verbose += 1
        if o in ("-l", "--granularity"):
	    lumped = int(a)
	if o in ("-f", "--from"):
	    oldFiles.append(a)
	if o in ("-t", "--to"):
	    changedFiles.append(a)
	if o in ("-m", "--meta"):
	    assumptions.add(a)
	if o in ("-o", "--out"):
	    output = a

    

    version = "$Id$"[1:-1]
    if len(oldFiles) != 1 or len(changedFiles) < 1:
	usage()
	sys.exit(2)
    G = loadFiles(oldFiles)
    commonFile = oldFiles[0]
    
    deltas = []
    changedFormulas = []
    biggest = None
    for i in range(len(changedFiles)):
	changedFile = changedFiles[i]
	progress("Diffing %s against %s" %(changedFile, commonFile))
	F = loadFiles([changedFile])
	D = differences(F, G, assumptions):
	deltas.append(D)
	if len(D) == 0:
	    progress("Great, no change in %s." % (changedFile))
	else:
	    if biggest == None or len(D) > len(biggest)):
		biggest_i = i
		biggest = F

    if biggest == None:
	progress("No changes in any inputs.")
	if outputFile != None:
	    sys.exit(0)
	    #  exit without overwriting
    else:
	progress("Most changed is %s" %(changedFiles[biggest_i]))
	G = biggest    			# (drop the original common formula)
	for i in range(len(changedFiles)):
	    progress("Applying changes from %s" %(changedFiles[i]))
	    G = patch(G, delta[i])

    if outputFile:
	out = open(outputFile, "w")
	out.write(G.asN3String())
	close(out)
    else:
	print G.asN3String() 
    sys.exit(0)   # didn't crash
    
	
		
if __name__ == "__main__":
    main()


	
