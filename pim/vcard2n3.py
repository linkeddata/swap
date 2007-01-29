#!/usr/bin/python
#
# 
# Open source. W3C licence.
#
"""
See http://www.w3.org/2002/12/cal/vcard-notes

See Namespace <http://www.w3.org/2006/vcard/ns>
and python iCalendar (vcard?) implementtions

<http://www.schooltool.org/products/schooltool-calendar>

<http://www.w3.org/2002/12/cal/icslex.py>

<http://www.ietf.org/rfc/rfc2425.txt>
    dc:title <A MIME Content-Type for Directory Information>;
    s:comment "Defines text/directory . the line-folding
     and basic record type structure".
<http://www.ietf.org/rfc/rfc2426.txt>
    dc:title "vCard MIME Directory Profile".

<http://www.w3.org/TR/vcard-rdf> dc:title "Representing vCard Objects in RDF/XML".

<http://lesscode.org/projects/kid/> an project used by 
<http://www.w3.org/2002/12/cal/vcardin.py> written by danc
"""

import sys, string, re, os
import icslex # from http://www.w3.org/2002/12/cal/icslex.py

# From http://www.ietf.org/rfc/rfc2426.txt  adr-type
typeFields = {
    'adr':   [ "dom" , "intl" , "postal" , "parcel" , "home"
                , "work" , "pref" ], # , iana-type / x-name

    'bday': [ 'date' ],
    
    'tel': ["home" , "work", "pref", "voice", "fax", "msg",
                "cell", "pager",  "bbs", "modem", "car", "isdn",
                "video", "pcs" 
		, 'main'      # @@ Added for AB
		],
    'email': [ "internet", "x400"
		    ,'home', 'work'    # @@ Added as they turn up in AB
		],
    'x-aim': ['home', 'work'    # @@ Added as they turn up in AB
		],
    'url':  [ 'home', 'work', 'foaf'] #unofficial
	    }

fieldProperties = {   # @@@ These are rather long localnames IMHO
    'n': [ 'family-name', 'given-name', 'additional-name', 'prefix', 'suffix' ],

    'adr': [ 'post-office-box', 'extended-address', 'street-address',
	    'locality', 'region', 'postal-code', 'country-name' ],
    'org': [ 'organization-name', 'organization-unit']
	    }
	    
def stripOut(str, characters):
    str2 = ""
    for i in range(len(str)):
        if str[i] not in characters:
            str2 = str2 + str[i]
    return str2

def zapOut(str, allowed):
    """Only allow the characters give. Strings of consecutive
    unallowed characters are replaced with a single underscore character"""
    str2 = ""
    for i in range(len(str)):
        if str[i] in allowed:
            str2 = str2 + str[i]
        else:
            if str2[-1:] != "_": str2 = str2 + "_"
    return str2

def munge(str):
    return zapOut(str, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")

wr = sys.stdout.write
	
def extract(path):
    global nochange
    global verbose
    total = 0
    
    print "# n3  http://www.w3.org/DesignIssues/Notation3."
    print "# From vCard data in ", path
    print "# Extracted by $Id$ "
    print
    print """
    @prefix : <#>.
    @prefix loc: <#loc_>.
    @prefix s: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix log: <http://www.w3.org/2000/10/swap/log#>.
    @prefix v:  <http://www.w3.org/2006/vcard/ns#>.
    @prefix abl:  <http://www.w3.org/2006/vcard/abl#>.
    @prefix user: <#>.
    """

    input = open(path, "r")
    inRecord = 0

    group_line = re.compile(r'^([a-zA-Z0-9]+)\.(.*)')
    field_value = re.compile(r'^([A-Za-z0-9_-]*):(.*)')
    group = None    # 
    
    cardData = ""
    groupData = {}
    groupPred = {}

    def readBareLine(input):
	line = input.readline()
        if line [-1:] == "\n": line = line[:-1] # Strip triling LF
        while line [-1:] == "\r": line = line[:-1] # Strip triling CRs
	return line
	
    def startGroup(g):
#	print "# Start group  <%s>" % `g`
	groupData[g] = []   # Pairs of p and o
	groupPred[g] = "loc:%s" % munge(g)  # Unless overwritten 


    def endGroup(g):
#        print "# End group <%s>" % `g`
	return " %s [ # %s\n%s]\n" % (groupPred[g], g, groupData[g])
	
    def orderedFields(value, map):
    	    cardData = "["
	    beg = 0
	    for i in range(len(map)):
		end = beg
	        while 1:
		    end = value.find(";", end)
		    if end>0 and value[end-1] == "\\":
			end += 1
			continue
		    break
		if end < 0:
		    end = len(value)
		st = value[beg:end].replace(',', ' ')
		if st: cardData += ' v:%s "%s";' % (map[i], st)
		beg=end+1
		if beg > len(value):
		    break
	    cardData += "]\n"
	    return cardData

    def predicateObject(n, props, value):
	"Return a pair of the predicate and object as N3 strings"
	modifiers = ""
	datatype = None
	for prop, val in props:
	    if prop == 'type':
		val = val.lower()
		if val == 'internet' and n == 'email':
		    pass
		elif val == 'pref':   # Preferred @@ - how represent?
		    pass
		elif val in typeFields.get(n, []):
		    if modifiers: print "# @@ multiple modifiers in: "+line
		    modifiers = val + '-' + modifiers
		else:
		    raise ValueError("Unhandled type %s in: %s" %(val, line))
	    elif prop == 'value':  # This means datatype
		datatype = val
		if val == 'date':
		    pass # Date-tiems from AB certainly look like w3c not iCal dates
		elif val == 'uri':
		    pass
		else:
		    raise ValueError ('Unimplemented data type:'+val)
	    elif prop == 'base64' or (prop == 'encoding' and val.lower() == 'b'):
		value = value.replace(' ','')
		res = ""
		while value:
		    res += value[:76] + "\n"
		    value = value[76:]
		return 'v:'+n, '[ v:base64 """%s"""];\n' % (res)  # Special case
				
	    else: raise ValueError('Unknown property %s with value %s' & (prop, val))

	map = fieldProperties.get(n,None)
	if map:
	     return 'v:%s%s' % (modifiers, n), orderedFields(value, map)
	if n == 'version':
	    assert value == "3.0", "value found: "+`value`
	    return "", ""
	if n == 'tel':
	    if value[0] != '+':
		print "# @@ Warning: not international form tel: "+value
	    return 'v:%s%s' % (modifiers, n),  '<tel:%s>;\n' % (value.replace(' ','-'))
	if n == 'url':
	    return 'v:%s%s' % (modifiers, n),  '<%s>;\n' % (value)
	if n == 'x.ablabel':
	    return "", "" # used elsewhere
	if n == 'email':
	    return 'v:%s%s' %(modifiers, n),  '<mailto:%s>;\n' % (value)
	if n == 'categories':   # Really should relate these to classes, but this roundtrips
	    value = ", ".join(['"'+x+'"' for x in value.split(',')])
	    return 'v:%s%s' % (modifiers, n),  '%s;\n' % (value) 
	if n in [ 'fn',  'title', 'bday', 'description',
	    'x-abuid','x-abadr', 'x-aim', 'x-abrelatednames', 'x-abshowas' ]:  # Single text
	    return 'v:%s%s' % (modifiers, n), '"%s";\n' % (value) # de-escape \:

	raise ValueError('Unknown tag:'+n)
    

    nextLine = readBareLine(input)
    while 1:

        line = nextLine;
	while 1:
	    nextLine = readBareLine(input)
	    if not nextLine or nextLine[0] != ' ': break
	    line += nextLine[1:]

        if line=="": break # EOF
	print "# line:", line[:100]
	m = group_line.match(line)
	if m:
	    g = m.group(1)
	    line = m.group(2)
	    if group != g:
		if group is not None: cardData += endGroup(group)
		if g is not None: startGroup(g)
	    group = g
	    
	    n, props, value = icslex.parseLine(line)
	    for prop, val in props:
		if prop == 'type':
		    val = val.lower()
		    if group .startswith("item"): # AB hack
			groupPred[group] = "loc:"+val
			
	    if n == 'x-ablabel':
		if value[:4] == "_$!<" and value[-4:] == ">!$_": # [sic]
		    groupPred[group] = "abl:"+value[4:-4]
		else:  # User generated
		    groupPred[group] = "user:"+munge(value)
	    else:
		p, o = predicateObject(n, props, value)
		groupData[group].append((p, o))

	else:
	    if group is not None:  # End group
		cardData += endGroup(group);
		group = None
	    n, props, value = icslex.parseLine(line)	
	    if n == 'begin':
		cardData = ""
		cardID = "[]"
	    elif n == "uid":
		cardID = "<uid:%s>" % value
	    elif n == 'end':
		wr("%s %s." % (cardID, cardData))
	    else:
		p, o = predicateObject(n, props, value)
		cardData+= "    %s %s" %(p, o)
	    
    wr("\n\n#ends\n")            
    input.close()


def do(path):
    if verbose: sys.stderr.write("Doing " + path + "\n")
#    if os.path.isdir(path):
#        if recursive:
#            for name in os.listdir(path):
#                do(path + "/" + name)
#    else:
#	if path[-4:].lower() == ".vcr" or path[-6:] == ".vcard":
    extract(path) 
        
######################################## Main program

recursive = 0
nochange = 1
verbose = 0
files = []

for arg in sys.argv[1:]:
    if arg[0:1] == "-":
#        if arg == "-r": recursive = 1    # Recursive
#        elif arg == "-f": nochange = 0   # Fix
        if arg == "-v": verbose = 1   # Tell me even about files which were ok
        else:
            print """Bad option argument.
            -v  verbose
            -f  fix files instead of just looking

"""
            sys.exit(-1)
    else:
        files.append(arg)

if files == []: files = [ "." ] # Default to this directory

for path in files:
    do(path)
