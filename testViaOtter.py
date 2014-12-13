
import os
import sys
import getopt

import LX.old.rdf
import LX.old.toShortNames
import LX.engine.otter

def otterFormulaFromN3Files(files, base=",n32o"):

    # this is a nutty way to do this; there should be a much shorter
    # path through other LX code, not even involving reification.

    inputs = []
    for f in files:
        clean = base + "-cleaned-" + str(len(inputs))
        os.system("grep -v '#HIDELINE' < %s > %s" % (f, clean))
        inputs.append(clean)

    axrdf = base + ".rdf"
    axP = base + ".P"

    os.system("cwm %s --flatten --rdf > %s" % (" ".join(inputs), axrdf))
    ax=LX.old.rdf.read(axrdf)
    
    p=LX.old.rdf.asOtter(ax)
    ps = LX.old.toShortNames.trans(p)
    f=open(axP, "w")
    f.write(ps)
    f.close()

    recfile = LX.__file__[:-13] + "/support/recognizeLX.P"
    cmd = "xsb --quietload --noprompt --nobanner -e \"['%s'], ['%s'], writeKB, halt.  halt\"" % (axP, recfile)
    fromXSB = os.popen(cmd, "r")
    result = fromXSB.read()
    return result


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "hk:g:",
                                   ["help", "keep=", "goal="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    base = ",testViaOtter"
    keepBase = 0
    goal = 0
    
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-t", "--basefile"):
            base = a
            keepBase = 1
        if o in ("-g", "--goal"):
            print "Got a goal:", a
            goal = otterFormulaFromN3Files([a], base+"-goal")

    if len(args) == 0: usage()

    prem = otterFormulaFromN3Files(args, base)

    #if maceFindsModel(prem):
    #    print "Mace found a model (premises are consistent)"

    try:
        proof = LX.engine.otter.run(prem, base+".prem")
        print "Otter found an inconsistency in the premises"
    except LX.engine.otter.SOSEmpty:
        print "Otter says: system is consistent (hyperres terminated)"

    if goal:
        while goal.endswith("\n") or goal.endswith(" ") or goal.endswith("."):
            goal = goal[:-1]
        kb = prem + "\n" + "-(" + goal + ").\n"
        proof = LX.engine.otter.run(kb, base+".all")
        print "Otter found a proof!"
    

def usage():
    print """
usage:  testViaOtter [opts] premise...

 opts:  --keep basename       Set the tempfile prefix, and leave temp
                              files around after completion.
        --goal goalfile       Set a goal; system will look for a proof
                              of the goal from the premises.

Always checks for satisfiability of the combined premises.
   
"""
    sys.exit(1)
    
if __name__ == "__main__":
    main()
