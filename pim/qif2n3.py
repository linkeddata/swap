#!/usr/bin/python
#
# See google QIF interchange format
#
#  It is hoped that the kludges in this program only echo the kludges in the
# QIF specification. :-)
## Open source. W3C licence.
#

import sys
import string
import os


def stripOut(str, characters):
    str2 = ""
    for i in range(len(str)):
        if str[i] not in characters:
            str2.append(str[i])
    return str2

def dealWithNumber(str):
    """The number field can be used for other things, which map to class membership."""
    if str == "ATM": return "a qu:ATMTrans;"
    if str == "DEP": return "a qu:depositTrans;"
    return "qu:number " + str

def convertAmount(str):
    return stripOut(str, ",")

def convertDate(qdate):
    """ convert from QIF time format to ISO date string

    QIF is like   "7/ 9/98"  "9/ 7/99"  or   "10/10/99"  or "10/10'01" for y2k
    ISO is like   YYYY-MM-DD  I think @@check
    """
    if qdate[1] == "/":
        qdate = "0" + qdate   # Extend month to 2 digits
    for i in range(len(qdate)):
        if qdate[i] == " ":
            qdate = qdate[:i] + "0" + qdate[i+1:]
    if qdate[5] == "'": C="20"
    else: C="19"
    return C + qdate[6:8] + "-" + qdate[3:5] + "-" + qdate[0:2]
    
def extract(path):
    global nochange
    global verbose
    crs = 0
    total = 0
    ignorables = [ "Clear:AutoSwitch", "Option:AutoSwitch" ]   # Without leading "!"
    
    # The properties for any non-investment account:
    nonInvestmentProperties = { "C": None, "D": "date", "E": "splitMemo", "L": "category", "P": "payee",
                   "M": "memo", "N": "number", "S": "splitCategory", "T": "amount", "U": None, "$": "splitAmount"}

    # For each type of account, a conversion from QIF poerty letter to rdf property name:
    properties = {
        # The line below was "Oth L"  for a mortguage type which looks corrupted!
         "Mort": nonInvestmentProperties,
         "Account": {"D": "description", "L": "limit", "N": "name", "T":  "type"},
         "Bank": nonInvestmentProperties,
         "Bill": nonInvestmentProperties,
         "Cat":   {"B": None, "D": "description", "I": None, "N": "name", "T": None},   # Category
         "CCard": nonInvestmentProperties,
         "Class": {"D": "description", "N": "name"},
         "Invst": { "D": "date", "L": "link", "P": "payee", "M": "memo",
                    "N": "number", "T": "amount", "U": "amount2" },
         "Oth_A": nonInvestmentProperties,
         "Oth_L": nonInvestmentProperties,
         }
    
    print "# n3  Personal and confidential. Not for distrbution."
    print "# From Quicken data in ", path
    print "# Extracted by $Id$ "
    print
    print """
    @prefix : <#>.
    @prefix d: <#>.
    @prefix qu: <qif#>.
    
    """

    input = open(path, "r")
    inRecord = 0
    inList = 0
    split = 0
    what = ""

    while 1:
        line = input.readline()
        if line=="": break # EOF
        if line [-1:] == "\n": line = line[:-1] # Strip triling LF
        while line [-1:] == "\r": line = line[:-1] # Strip triling CRs
        attr = line[0]
        value = line[1:]
        if attr == "!":
            if inRecord:
                print "]",
                inRecord = 0
            while value[-1:]==" ":value=value[:-1] # strip trailing blanks(!)
            for i in range(len(value)):
                if value[i]==" ":
                    value=value[:i]+"_"+value[i+1:]
            if inList and what == "Account" and value[0:5]=="Type:":   #  @@@ sic
                print "\n# List of transactions follows:\n    is qu:toAccount of [\n"
                inList = 1
                inRecord = 1
                what = value[5:]
                continue

            if inList:
                print ".",
                inList = 0
            print
            if value in ignorables:
                print "# Ignoring ", line
            elif value[0:5] == "Type:":
                was = what
                what = value[5:]
                print "\n# List of %s\n:theSnapshot qu:%s [\n    " % (what,what),
                inList = 1
                inRecord = 1
            elif value == "Account":
                what = "Account"
                print "\n# List of Accounts OR define account\n:theSnapshot qu:account [\n" 
                inList = 1
                inRecord = 1
            else:
                print "#@@@@@@ Unknown ", line
        elif attr == "^":
            if split:
                print "]",
                split = 0
            print "]",
            inRecord = 0
        else:
            dictionary = properties.get(what, None)
            if dictionary == None:
                print dictionary
                raise RuntimeError("@@ No propertylist for <%s>" % what)
            property = dictionary.get(attr, "quicken_"+what+"_"+attr)
            if not inList : raise oops
            val = ""
            for c in value:
                if c == '"': val = val+'\\"'
                else: val = val + c
            if property != None:
                if not inRecord:
                    print ",\n    [",
                    inRecord = 1
                if split and property=="splitCategory":  # @ special!  Starts new part of split
                    print "],\n            [",
                if not split and property[0:5]=="split":  # @ convention!
                    print "qu:split\n            ["
                    split =1
                if property.find("date") >= 0: val = convertDate(val)
                elif property.find("amount") >=0: val = convertAmount(val)
                elif property == "number":
                    print dealWithNumber(val),  # includess the property name
                    continue
                print 'qu:%s "%s"; '%(property, val),
    if inRecord: print "]",
    if inList: print "."
    print "\n\n#ends\n"
            
    input.close()


def do(path):
    if verbose: sys.stderr.write("Doing " + path + "\n")
#    if os.path.isdir(path):
#        if recursive:
#            for name in os.listdir(path):
#                do(path + "/" + name)
    else:
        if path[-4:] == ".QIF" or path[-4:] == ".rqif":
            extract(path) 
        
######################################## Main program

recursive = 0
nochange = 1
verbose = 0
files = []

for arg in sys.argv[1:]:
    if arg[0:1] == "-":
        if arg == "-r": recursive = 1    # Recursive
        elif arg == "-f": nochange = 0   # Fix
        elif arg == "-v": verbose = 1   # Tell me even about files which were ok
        else:
            print """Bad option argument.
            -r  recursive
            -f  fix files instead of just looking

"""
            sys.exit(-1)
    else:
        files.append(arg)

if files == []: files = [ "." ] # Default to this directory

for path in files:
    do(path)
