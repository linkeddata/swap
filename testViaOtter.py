#  

#
# total bailing wire for now -- need to move peices into LX

import os
import sys

import rdf
import toShortNames

axlong=sys.argv[1]
axname = axlong.split(".")[0]
axclean = axname + "Cleaned.n3"
axrdf = axname + ".rdf"
axP = axname + ".P"
axOtter = axname + ".otter"

# include swap/util/rdfs-rules.n3
os.system("grep -v '#HIDELINE' < %s > %s" % (axlong, axclean))
os.system("cwm %s --flatten --rdf > %s" % (axclean, axrdf))

ax=rdf.read(axrdf)
#axclean=[]
#for t in ax:
#    skip = 0
#    for s in t:
#        if (s.getURI() == "http://www.w3.org/2000/10/swap/log#forAll" or
#            s.getURI() == "http://www.w3.org/2000/10/swap/log#forSome"):
#            skip = 1
#        print s.getURI()
#    if not skip: axclean.append(t)
    
p=rdf.asOtter(ax)
ps = toShortNames.trans(p)
f=open(axP, "w")
f.write(ps)
f.close()

f=open(axOtter, "w")
f.write("""set(auto).
formula_list(usable).
""")
f.close()

cmd = "xsb --quietload --noprompt --nobanner -e \"['%s'], ['../LX/recognizeLX.P'], writeKB, halt.\" >> %s" % (axP, axOtter)
#print "PY running:", cmd
os.system(cmd)


# don't actually call otter yet!

