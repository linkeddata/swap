#
# total bailing wire for now -- need to move peices into LX

# PYTHONPATH=/home/sandro/2/05/positive-triples/lib/python

import os
import sys

axlong=sys.argv[1]
axname = axlong.split(".")[0]
axrdf = axname + ".rdf"
axP = axname + ".P"

# include swap/util/rdfs-rules.n3
os.system("cwm %s --flatten --rdf > %s" % (axlong, axrdf))

import rdf
ax=rdf.read(axrdf)
p=rdf.asProlog(ax)
import toShortNames
ps = toShortNames.trans(p)
f=open(axP, "w")
f.write(ps)

os.system("xsb -e \"['%s'], ['../LX/recognizeLX.P'], writeKB.  halt.\"" % axP)

# don't actually call otter yet!

