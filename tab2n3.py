#! /usr/bin/python
"""  Convert tab-separated text to n3 notation
#  This has been hacked to work with the "Tab separated (Windows)" outputt from
# MS Outlook export of contaxt files.
#
    -comma    Use comma as delimited instead of tab
    -schema   Generate a little RDF schema
"""
import sys
import string

inFp = sys.stdin

def readTabs(delim):
    result = []

    l = inFp.readline()
    if len(l) == 0 : return result #EOF
    while l != "" and l[-1:] in "\015\012" :
        l=l[:-1]  # Strip CR and/or LF
#    print "# Line: ", l

    while 1: # Next field
        if l == "": return result  

        if l[0] == '"':  # Is this a quoted string?
            l = l[1:]  # Chop leading quote
            result.append("")
            while 1:
                j = string.find(l, '"')  # Is it terminated on this line?
                if j >= 0:   # Yes!
                    if l[j+1:j+2] == '"': # Two doublequotes means embedded doublequote
                        result[-1] =  result[-1] + l[:j] + '\\"'
                        l = l[j+2:]
                        continue
                    result[-1] = result[-1] + l[:j]
                    l = l[j+1:]
                    if l == "":  # End of values
                        return result
                    else:
                        if l[0] ==  delim:
                            l = l[1:]  # redundancy: tab follows quote
                        else:
                            print "# @@@@@@@@@@@@@@@@@@@@ No tab after close quote: "+l
                    break
                else:  # Notterminated on this line
                    result[-1] = result[-1] + l + "\n" # wot no loop?
                    l = inFp.readline()
                    if len(l) == 0 : return result #EOF
                    while l != "" and l[-1:] in "\015\012" :
                        l=l[:-1]  # Strip CR and/or LF
#                   print "# Line: ", l

        else:  # No leading quote: Must be tab or newline delim
            i=string.find(l, delim)
            if i>=0:
                result.append(l[:i])
                l = l[i+1:]
            else:
                result.append(l)
                return result           # end of values
     
import sys

def convert():
    if "-comma" in sys.argv[1:]:
        delim = ','
    else:
        delim = '\t'
    headings = [ "" ];

    while len(headings) <2: # Hack for fidelity files which have pre-heading items
        headings = readTabs(delim)
        print "# headings found: ", len(headings), headings

    records = 0
    labels = []
    for i in range(0,len(headings)):
        h = headings[i]
        labels.append(h) # raw heading field
        for j in range(0,len(h)):
            if h[j] not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_":
                headings[i] = headings[i][:j] + "_" + headings[i] [j+1:]
        headings[i] = headings[i][:1].lower() + headings[i][1:] # Predicates initial lower case 
                
    if "-schema" in sys.argv[1:]:
        print "# Schema"
        # print "@prefix : <> ."
        print "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> ."
        for i in range(0,len(headings)):
            print "  :%s  a rdfs:Property; rdfs:label \"%s\"." % \
                    ( headings[i], labels[i]  )
        print
 
    while 1:
        values = readTabs(delim)
#       print "Values: ", values
        if values == []: break
        if len(values) < 2: continue;
        records = records + 1
        if len(values) != len(headings):
            print "#  %i headings but %i values" % (len(headings), len(values))


        print "["
        i=0
        while i < len(values):
            v = values[i]
            while v[:1] == ' ': v = v[1:]   # Strip spaces
            while v[-1:] == ' ': v = v[:-1]
            
            if (len(v) and v!="0/0/00"
                and v!="\n")  :  # Kludge to remove void Exchange dates & notes
                if string.find(v, "\n") >= 0:
                    print '    :%s """%s""";' % (headings[i], v) # Not n3 spec (yet?)
                else:
                    print '    :%s "%s";' % (headings[i], v)
            i = i+1
        print " ] .\n"

    print "# Total number of records:", records

convert() 
















