#!/usr/bin/python
"""

$Id$

Financial

"""

"""emacs got confused by long string above@@"""


import llyn

from diag import verbosity, setVerbosity, progress


import notation3    	# N3 parsers and generators
# import toXML 		#  RDF generator

from RDFSink import FORMULA, LITERAL, ANONYMOUS, Logic_NS
import uripath
import string
import sys
from uripath import join
from thing import  Namespace
from notation3 import RDF_NS_URI


qu = Namespace("http://www.w3.org/2000/10/swap/pim/qif#")
tax = Namespace("http://www.w3.org/2000/10/swap/pim/tax.n3#")
rdf = Namespace(RDF_NS_URI)
rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
cat_ns = Namespace("categories.n3#")

monthName= ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

import thing
import uripath

store = llyn.RDFStore()
thing.setStore(store)

rdf_type = rdf.type
cat = cat_ns


#################################################  Command line
    
def sym(uri):
    global store
    return store.intern((0, uri))

def printTransactionDetails(t):
    for st in kb.statementsMatching(subj=t):
	print "     %-15s "%`st.predicate()`, str(st.object())
    
def printCategories(cats, totals, count):
    trans = 0
    inc, out = 0,0
    global kb
    print "<table>"
    for c in cats:
	label = `c`
	tot = totals.get(c, 0)
	if tot != 0:
	    print "<tr><td>%s</td><td>" %(label),
	    for s in kb.each(subj=c, pred=rdfs.subClassOf):
		print " (%s)"% `s`,
	    print "</td><td class='amount'>%9.2f</td></tr>" %(tot),
	    print
	    if tot > 0: inc = inc + tot
	    else: out = out + tot
	trans = trans + count.get(c,0)

    print "</table>"
    print "<p>In %i transactions, Total income %9.2f,  outgoings %9.2f, balance %92f</p>" % (trans, inc, out, inc + out)



def tableRow(label, anchor, totals, value):
    str = ""
    for month in range(12):
	str = str + "<td class='amt'>%6.2f</td>" % value[month]
    if anchor:
	return "<tr><td><a href='%s'>%s</a></td><td class='total'>%7.2f</td>%s</tr>" %(
		"year-cat.html#" + anchor, label, totals, str)
    return "<tr><td>%s</td><td class='total'>%7.2f</td>%s</tr>" %(label, totals, str)

def internalCheck():
    global kb
    global cat
    transactions = kb.each(pred=rdf.type, obj=cat_ns.Internal)
    unbalanced = []
    while len(transactions) > 0:
	x = transactions.pop()
	date = str(kb.the(subj=x, pred=qu.date))
	amount = float(str(kb.the(subj=x, pred=qu.amount)))
	for y in transactions:
	    datey = str(kb.the(subj=y, pred=qu.date))
	    if date[0:10] == datey[0:10]:  # precision one day
		if abs(amount + float(str(kb.the(subj=y, pred=qu.amount)))) < 0.001 : # Floating point ~=
		    transactions.remove(y)
		    break
	else:
	    unbalanced.append(x)
    transaction = unbalanced
    unbalanced = []
    while len(transactions) > 0:
	x = transactions.pop()
	amount = float(str(kb.the(subj=x, pred=qu.amount)))
	for y in transactions:
	    if abs(amount + float(str(kb.the(subj=y, pred=qu.amount)))) < 0.001 : # Floating point ~=
		transactions.remove(y)
		break
	else:
	    unbalanced.append((date, x))

    unbalanced.sort()
    print "<h2>Unbalanced internal transactions</h2>"
    print "<table>"
    for da, x in unbalanced:
    	amount = float(str(kb.the(subj=x, pred=qu.amount)))
	payee = kb.any(subj=x, pred=qu.payee)
	toAccount = kb.the(subj=x, pred=qu.toAccount)
	print "<tr class='%s'><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" %(
	    toAccount, da, payee, toAccount, amount)
    print "</table>"
	
    return unbalanced

def doCommand():
        """Fin - financial summary
        
 <command> <options> <inputURIs>
 Totals transactions by classes to which they are known to belong 
 This is or was  http://www.w3.org/2000/10/swap/pim/fin.py
 
"""
        
        #import urllib
        import time
        import sys
        global sax2rdf
        import thing
	global store
	global kb
        #from thing import chatty
        #import sax2rdf

        option_need_rdf_sometime = 0  # If we don't need it, don't import it
                               # (to save errors where parsers don't exist)
        
        option_pipe = 0     # Don't store, just pipe though
        option_inputs = []
        option_test = 0     # Do simple self-test
        option_reify = 0    # Flag: reify on output  (process?)
        option_flat = 0    # Flag: reify on output  (process?)
	option_crypto = 0  # Flag: make cryptographic algorithms available
        option_outURI = None
        option_outputStyle = "-best"
        _gotInput = 0     #  Do we not need to take input from stdin?
        option_meta = 0
        option_quiet = 0


        
        # The base URI for this process - the Web equiv of cwd
	_baseURI = uripath.base()
	
        option_format = "n3"      # set the default format
        option_first_format = None
        
        _outURI = _baseURI
        option_baseURI = _baseURI     # To start with - then tracks running base
        for argnum in range(1,len(sys.argv)):  # Command line options after script name
            arg = sys.argv[argnum]
            if arg.startswith("--"): arg = arg[1:]   # Chop posix-style double dash to one
            _equals = string.find(arg, "=")
            _lhs = ""
            _rhs = ""
            if _equals >=0:
                _lhs = arg[:_equals]
                _rhs = arg[_equals+1:]
                _uri = join(option_baseURI, _rhs)
            elif arg[0] == "-": pass  # Other option
            else :
                option_inputs.append(join(option_baseURI, arg))
                _gotInput = _gotInput + 1  # input filename
            


        option_format = "n3"
        #  Fix the output sink
        if option_format == "rdf":
            _outSink = toXML.ToRDF(sys.stdout, _outURI, base=option_baseURI)
        else:
            _outSink = notation3.ToN3(sys.stdout.write, base=option_baseURI,
                                      quiet=option_quiet)

# Load the data:

	if _gotInput:
	    kb=store.load(option_inputs[0])
	else:
	    kb=store.load()  # STDIN
	
	print "Size of kb: ", len(kb)
	
	meta = store.loadMany(["categories.n3", "classify.n3"])  # Category names etc
	print "Size of meta", len(meta)
	
	qu_date = qu.date
	qu_amount = qu.amount
	qu_payee = qu.payee
	qu_Classified = qu.Classified
	qu_Unclassified = qu.Unclassified

####### Analyse the data:
	monthTotals = [0] * 12 
	incomeByMonth = [0] * 12 
	income, outgoings = 0,0
	outgoingsByMonth = [0] * 12 

	quCategories = kb.each(pred=rdf_type, obj=qu.Cat)
	
	totals = {}  # Total by all classes of transaction
	count = {}  # Number of transactions
	byMonth = {}
	satis = tax.Category, qu.Cat  # Satisfactory classes
	classified =  kb.each(pred=rdf_type, obj=qu_Classified)
	unclassified = kb.each(pred=rdf_type, obj=qu_Unclassified)
	for t in classified: assert t not in unclassified, "Can't be classified and unclassified!"+`t`
	for s in classified + unclassified:
	    t_ok, c_ok = 0, 0
	    date = kb.any(subj=s, pred=qu_date).__str__()
	    year = int(date[0:4])
	    if  year != 2002: continue
	    month = int(date[5:7]) -1
	    
	    payees = kb.each(subj=s, pred=qu_payee)
	    if str(payees[0]) == "Check" and len(payees) >1: payee = payees[1]
	    else: payee = payees[0]
	    
	    amount = float(kb.the(subj=s, pred=qu_amount).__str__())
#	    print "%s  %40s  %10s month %i" %(date, payee, `amount`, month)

	    monthTotals[month] = monthTotals[month] + amount
	    cats = kb.each(subj=s, pred=rdf_type)
	    if cat_ns.Internal not in cats:
		if amount > 0:
		    incomeByMonth[month] = incomeByMonth[month] + amount
		    income = income + amount
		else:
		    outgoingsByMonth[month] = outgoingsByMonth[month] + amount
		    outgoings = outgoings + amount

	    for cat in kb.each(subj=s, pred=rdf_type):
		totals[cat] = totals.get(cat, 0) + amount
		byMonth[cat] = byMonth.get(cat, [0] * 12)
		count[cat] = count.get(cat, 0) + 1
		byMonth[cat][month] = byMonth[cat][month] + amount
#		if `cat` == "Internal" and month == 8:
#		    print "@@@@@ INTERNAL", "%s  %40s  %10s month %i" %(date, payee, `amount`, month)
    

	print '<html xmlsns="http://www.w3.org/@@@@xhtml">'
	print """<head>
	    <title>Annual Summary by month</title>
	    <link rel="Stylesheet" href="report.css">
	</head>
	<body>
	"""
	
        version = "$Id$"
	if not option_quiet:
            _outSink.makeComment("<address>Processed by " + version[1:-1]+"</address>") # Strip $ to disarm


#   TABLE OF CATEGORY BY MONTH

		
	print "<h2>Personal categories and month</h2><table class='wide'><tr><th></th><th>Year</th>"
	for month in range(12):
	    print "<th><a href='year-chron.html#m%s'>%s</a></th>" %(("0"+`month+1`)[-2:], monthName[month]),
	print "</tr>"
	for cat in quCategories + [ qu.UnclassifiedIncome, qu.UnclassifiedOutgoing]:
	    try:
		print tableRow(`cat`, `cat`, totals[cat], byMonth.get(cat, [0] * 12))
	    except KeyError:
		continue

	print "<tr><td colspan='14'></td></tr>"
	print tableRow("Income", None,  income, incomeByMonth)
	print tableRow("Outgoings", None, outgoings, outgoingsByMonth)
	print tableRow("Balance", None, income + outgoings, monthTotals)

	print "</table>"

	
#  Chart of income stacked up against expenses
	print "<a href='chart.svg'><p>Chart of income vs expense</p><img src='chart.svg'></a>"

	chart = open("chart.svg", "w")
	chart.write("""<?xml version="1.0" encoding="iso-8859-1"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:l="http://www.w3.org/1999/xlink">
""")
#"
	lineheight = 15 # for text
	upperBound = abs(income)
	if abs(outgoings) > upperBound: upperBound = abs(outgoings)
	
	dh = 600
	scale = (dh - 30) / abs(upperBound)   # Pixels/dollar
	
	y = 0
	while y < dh:   # grid
	    chart.write("""    <rect stroke="#ddffdd" fill="none" y="%ipx" x="50px" width="600px"
	    height="0px"/>
""" %(dh-y))
#"
	    y = y + 10000 * scale

	vc = []
	for c in quCategories + [ qu.UnclassifiedIncome, qu.UnclassifiedOutgoing]:
	    if totals.get(c, 0) == 0: continue
	    
	    label = meta.the(subj=c, pred=rdfs.label)
	    if label == None:
		label = `c`
		sys.stderr.write("@@ No label for "+`c` +"\n")
	    else:
		label = str(label)
	    
	    volatility = meta.the(subj=c, pred=qu.volatility)
	    if volatility == None:
		volatility = 50
		sys.stderr.write("No volatility for "+ cat.uriref() +"\n")
	    else:
		volatility = int(str(volatility))
	    vc.append((volatility, label, c))
	vc.sort()
	
	# for offset, cats, color in [ (100, incomeCategories, "#eeffee" ),
	#			    (400, spendingCategories, "#ffeeee") ]:

	total = [0,0]  # in, out
	offset = [100,400]
	color = ["#eeffee", "#ffeeee"]
	for volatility, label, c in vc:
	    tot = totals.get(c,0)
	    if tot == 0: continue
	    if tot < 0 : out = 1
	    else: out = 0
	    change = abs(tot)
	    bottom = total[out]
	    total[out] = total[out] + change
	    top = total[out]
	    height = round((top-bottom)*scale)

	    chart.write("""    <a l:href="year-cat.html#%s">
        <rect stroke="black" fill="none" y="%ipx" x="%ipx" width="200px"
	    height="%ipx" style="stroke: black; fill: %s"/></a>
""" %(`c`, dh-round(top*scale), offset[out], height, color[out]))
#"
	    if  height > lineheight:
		text = label
		text2 = " \n%7i" % round(abs(tot))
		
		middle = dh-round((bottom+top)*scale/2 - lineheight/2)
		if height > (3*lineheight):
		    chart.write("""    <text  y="%ipx" x="%ipx" width="160px"
	    height="%ipx" style="background: #eeeeff">%s</text>
""" %(middle - (lineheight/2), offset[out]+20, height-40, text)) 
#"	
		    chart.write("""    <text  y="%ipx" x="%ipx" width="160px"
	    height="%ipx" style="text-anchor:finish; background: #eeeeff">%s</text>
""" %(middle + (lineheight/2), offset[out]+20, height-40, text2)) 
#"
		else:
		    if len(text) < 15: text = text + " " + text2
		    chart.write("""    <text  y="%ipx" x="%ipx" width="160px"
	    height="%ipx" style="background: #eeeeff">%s</text>
""" %(middle, offset[out]+20, height-40, text)) 
#"	
	
	chart.write("""</svg>\n""")
	chart.close()


	# Output totals
	
	ko = store.intern(thing.formula())		# New formula  @@@ - yuk API!
	for c in quCategories + [ qu.UnclassifiedIncome, qu.UnclassifiedOutgoing]:
	    ko.add(subj=c, pred=qu.total, obj=store.intern(thing.literal("%7.2f" % totals.get(c,0))))
	ko.close()
	
	fo = open("totals.n3", "w")
	fo.write(ko.n3String())
	fo.close
	
	internalCheck()

	
	print "<h2>Tax Categories</h2>"
	taxCategories = kb.each(pred=rdf_type, obj=tax.Category)
	printCategories(taxCategories + [ qu.Unclassified], totals, count)
    
	print "<h2>Tax stuff</h2>"
	print "<table>"
	print "<tr><th>-<th>Form line</th><th>amount</th></tr>"
	print "</table>"
	    
#	print "<h2>Personal Categories</h2>"
#	printCategories(quCategories + [ qu.Unclassified], totals, count)

	print

	print "Note totals for tax and personal breakdowns must match."
	dates = kb.statementsMatching(pred=qu.date)
	print "There should be a total of %i transactions in each." % len(dates)

	

	if 0:
	    print "<pre>(consistency check)"
	    problems = 0
	    for s in dates:
		tra = s.subject()
		types = kb.each(subj=tra, pred=rdf_type)
		for typ in types:
		    if typ is qu.Unclassified or typ is qu.Classified:
			break # ok
		else:
		    print "@@@@ problem transcation with no classified or unclassified, with types", types
		    printTransactionDetails(tra)
		    problems = problems + 1
	    print problems, "problems.</pre>"
	
	print "</body></html>"

    
        
############################################################ Main program
    
if __name__ == '__main__':
    doCommand()

