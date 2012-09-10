#! /usr/bin/python
"""  Convert tab-separated text to n3 notation
  This has been hacked in 2000 to work with the "Tab separated (Windows)" output from
 MS Outlook export of contact files.
 Runtime options:

    -comma          Use comma as delimited instead of tab
    -id             Generate sequential URIs for the items described by each row
    -idfield        Use column 'id' to form the URI for each item
    -type           Declare each thing as of a type <#Item>.
    -namespace xxx  Properties are in namespace <xxx#> note added hash
    -schema         Generate a little RDF schema
    -nostrip        Do not strip empty cells
    -help           Display this message and exit.
    
This is or was http://www.w3.org/2000/10/swap/tab2n3.py
It is open source under the W3C software license.
http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231
"""
import sys
import string
from sys import argv

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

# Column headings can have newlines embedded
def sanitize(s):
    return s.replace('\n', ' ')
            
def sanitizeID(s):
    res = ""
    for ch in s:
        if ch in string.ascii_letters or ch in string.digits:
            res += ch
        else:
            res += '_'
    return res
            
def convert():
    
    namespace = None;
    for i in range(len(argv)-2):
        if argv[i+1] == '-namespace': namespace = argv[i+2] + '#'
            
    if "-help" in sys.argv[1:]:
        print __doc__
        return
        
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
                
    if namespace: print "@prefix : <%s>." % namespace
    if "-schema" in sys.argv[1:]:
        print "# Schema"
        # print "@prefix : <> ."
        print "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>."
        print "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>."
        for i in range(0,len(headings)):
            print "  :%s  a rdf:Property; rdfs:label \"%s\"." % \
                    ( headings[i], sanitize(labels[i])  )
        print
 
    while 1:
        values = readTabs(delim)
        if values == []: break
        if len(values) < 2: continue;
        records = records + 1
        if len(values) != len(headings):
            print "#  Warning: %i headings but %i values" % (len(headings), len(values))
        open = False  # Open means the predicate object syntax needs to be closed
        str = ""
        this_id = None
        if "-type" in sys.argv[1:]:
            str += " a <#Item> "
            open = True
        for i in range(len(values)):
            v = values[i].strip()
            if ((len(v) and v!="0/0/00"
                and v!="\n") or  ("-nostrip" in sys.argv[1:]))  :  # Kludge to remove void Exchange dates & notes
                if i < len(headings) : pred = headings[i]
                else: pred = 'column%i' % (i)
                if ('-idfield' in sys.argv[1:]) and headings[i] == 'id':
                    this_id = sanitizeID(v)
                else:
                    if open:  str+= "; "
                    if string.find(v, "\n") >= 0:
                        str += '\n    :%s """%s"""' % (pred, v)
                    else:
                        str += '\n    :%s "%s"' % (pred, v)
                    open = True
        if open: str += "."
        open = False
        if str != "":
            if "-id" in sys.argv[1:]: print "<#n%i>" % records + str
            elif  "-idfield" in sys.argv[1:]: print "<#n%s>" % this_id + str
            else: print "[]" + str

    print "# Total number of records:", records

convert() 
















