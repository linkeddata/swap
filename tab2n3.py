#! /usr/bin/python
#  Convert tab-separated text to n3 notation
#  This has been hacked to work with the "Tab separated (Windows)" outputt from
# MS Outlook export of contaxt files.
#

import sys
import string

inFp = sys.stdin

def readTabs():
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
		    result[-1] = result[-1] + l[:j]
		    l = l[j+1:]
		    if l == "":  # End of values
			return result
		    else:
			if l[0] ==  "\t":
			    l = l[1:]  # redundancy: tab follows quote
		        else:
			    print "# @@@@@@@@@@@@@@@@@@@@ NO TAB AFTER CLOASE QUOTE"
		    break
	        else:  # Notterminated on this line
		    result[-1] = result[-1] + l + "\n"
	            l = inFp.readline()
                    if len(l) == 0 : return result #EOF
	            while l != "" and l[-1:] in "\015\012" :
		        l=l[:-1]  # Strip CR and/or LF
#    	            print "# Line: ", l

	else:  # No leading quote: Must be tab or newline delim
            i=string.find(l,"\t")
	    if i>=0:
	        result.append(l[:i])
	        l = l[i+1:]
	    else:
	        result.append(l)
	        return result		# end of values
     
import sys

def convert():
    headings = readTabs()
#    print "# headings found: ", len(headings), headings

    records = 0
    for i in range(0,len(headings)-1):
	h = headings[i]
        for j in range(0,len(h)-1):
	    if h[j] not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_":
		headings[i] = headings[i][:j] + "_" + headings[i] [j+1:]

    if "-schema" in sys.argv[1:]:
	print "# Schema"
	print "bind : <> ."
	print "bind rdfs: <http://www.w3.org/2000/01/rdf-schema>"
	for h in headings:
	    print "  :%s  a rdfs:Property ." % ( h )
	print
 
    while 1:
	values = readTabs()
#	print "Values: ", values
	if values == []: break
        records = records + 1
	if len(values) != len(headings):
	    print "#  %i headings but %i values" % (len(headings), len(values))


        print "["
	i=0
	while i < len(values):
	    v = values[i]
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
















