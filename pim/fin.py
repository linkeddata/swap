#!/usr/bin/python
"""Summarize and chart one year's (or other period) finances
    
usage, eg:
    fin -y 2003
        Results for the year 2003-01 through 2003-12
    fin -y 2003-07
        Results for the year 2003-07 through 2004-06
    fin --start 2010-01 --end 2010-06
        Results for the half year upto NOT including June 2010
        
    -t foo.n3   --totals=foo.n3  Please output totals in this file   
    
    --report=rep.html     Make links to this file for details  
    
    The period must be given explicitly.
    Transactions outside that period will be ignored.

This is an RDF application.

$Id$
"""
from swap import llyn, diag, notation3, RDFSink, uripath, myStore

from swap.diag import verbosity, setVerbosity, progress
# from swap.uripath import join
from swap.notation3 import RDF_NS_URI
from swap.myStore import store, load, loadMany,  Namespace
import swap.llyn

#import uripath

global yearInQuestion, startDate, endDate

import string
import sys

qu = Namespace("http://www.w3.org/2000/10/swap/pim/qif#")
tax = Namespace("http://www.w3.org/2000/10/swap/pim/tax.n3#")
rdf = Namespace(RDF_NS_URI)
rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
trip = Namespace("http://www.w3.org/ns/pim/trip#")
cat_ns = Namespace("../../../Financial/Data/categories.n3#")
owl = Namespace("http://www.w3.org/2002/07/owl#")

monthName= ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul",
                            "Aug", "Sep", "Oct", "Nov", "Dec"]


rdf_type = rdf.type
# cat = cat_ns
kb = None;


def printTransactionDetails(t):
    for st in kb.statementsMatching(subj=t):
        print "     %-15s "%`st.predicate()`, str(st.object())
    
def printCategoryTotalsOnly(cats, totals, count):
    trans = 0
    inc, out = 0,0
    global kb
    print "<table class='wide' style='border-collapse:collapse; border: 0.01em solid #aaa; text-align: '.' ><col style='text-align: left'>"
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
    print """<p>In %i transactions, Total income %9.2f, 
    outgoings %9.2f, balance %92f</p>""" % (trans, inc, out, inc + out)



def monthGridRow(label, anchor, totals, value, nm, indent = 0):
    global reportLink
    str = ""
    style = ""
    if indent > 0: style = "style='padding-left: %iem'" % indent;
    for month in range(nm):
        str = str + "<td class='amt'>%6.0f</td>" % value[month]
    if anchor:
        return "<tr><td class='rowLabel' %s><a href='%s'>%s</a></td><td class='total'>%7.0f</td>%s</tr>" %(
                style, reportLink + "#" + anchor, label, totals, str)  # @@ add year in filename
    return "<tr><td class='rowLabel' %s>%s</td><td class='total'>%7.0f</td>%s</tr>" %(style, label, totals, str)

def transactionTable(list):
    st = "<table>\n"
    list2 = []
    for x in list: list2.append((str(kb.the(subj=x, pred=qu.date))[:10], x));
    list2.sort();
    for date, x in list2: st += transactionRow(x);
    return st + "</table>\n"

def transactionRow(x):
    date = str(kb.the(subj=x, pred=qu.date))[:10]
    amount = float(str(kb.the(subj=x, pred=qu.in_USD)))
    payee = kb.any(subj=x, pred=qu.payee)
    toAccount = kb.the(subj=x, pred=qu.toAccount)
    accLabel = kb.any(subj = toAccount, pred = rdfs.label)
    if not accLabel: accLabel = `toAccount`[-4:]
    return " <tr><td><a href='%s'>%s</a></td><td>%s</td><td>%s</td><td class='amt'>%7.2f</td></tr>\n" % (baseRel(x.uriref()), date, payee, accLabel, amount)
    
def reimbursablesCheck():
    global kb
    global cat
    st = ""
    transactions = kb.each(pred=rdf.type, obj=cat_ns.Reimbursables)
    
    st = "<h2>Reimbusables with no trip</h2>\n"
    
#    st += "<table>\n";
    needed = [];
    while len(transactions) > 0:
        x = transactions.pop()
        month = monthNumber(x)
        if month < 0 : continue
        if kb.any(subj = x, pred = trip.trip): continue
        needed.append(x);
#       st += transactionRow(x)
    return st + transactionTable(needed);
        
def internalCheck():
    global kb
    global cat
    transactions = kb.each(pred=rdf.type, obj=cat_ns.Internal)
    unbalanced = []
    while len(transactions) > 0:
        x = transactions.pop()
        month = monthNumber(x)
        if month < 0 : continue

        date = str(kb.the(subj=x, pred=qu.date))
        if len(kb.each(subj=x, pred=qu.in_USD)) != 1:
            progress("Ignoring !=1 amount transaction %s" % x)
            continue
        amount = float(str(kb.the(subj=x, pred=qu.in_USD)))
        for y in transactions:
            datey = str(kb.the(subj=y, pred=qu.date))
            if 1: #  date[0:10] == datey[0:10]:  # precision one day
                usds = kb.each(subj=y, pred=qu.in_USD)
                if len(usds) == 0:continue  # No amount => must be not in this period.
                if len(usds) != 1:
                    progress("Error: Ignoring: %i != 1 USD amounts for Internal transaction %s" % (len(usds), `y`+': '+ `usds`))
                    transactions.remove(y)
                    continue
                if abs(amount +
                        float(str(kb.the(subj=y, pred=qu.in_USD)))) < 0.001:
                    transactions.remove(y)
                    break
        else:
            unbalanced.append(x)

    print "<h2>Unbalanced internal transactions</h2>"
    print transactionTable(unbalanced);
    return


def writeChart(filename, categories, totals, income, outgoings, shortTerm=0):
    """Chart income vs outgoing
    
    Scaled chart
    """
    chart = open(filename, "w")
    chart.write("""<?xml version="1.0" encoding="iso-8859-1"?>
<svg xmlns="http://www.w3.org/2000/svg"
    xmlns:l="http://www.w3.org/1999/xlink">
""")
#"
    vc = []

    for c in categories:
        if totals.get(c, 0) == 0: continue
        
        label = kb.the(subj=c, pred=rdfs.label)
        if label == None:
            label = `c`
            sys.stderr.write("Warning: No label for category"+`c` +"\n")
        else:
            label = str(label)
        
        if shortTerm and kb.contains(subj=c, pred=rdf.type, obj=qu.LongTerm):
            continue  # ignore in budget diagram
        volatility = kb.the(subj=c, pred=qu.volatility)
        if volatility == None:
            volatility = 50
            sys.stderr.write("Warning: No volatility for "+ c.uriref() +"\n")
        else:
            volatility = int(str(volatility))
        vc.append((volatility, label, c))
    vc.sort()
    
    total = [0,0]  # in, out
    for volatility, label, c in vc:
        tot = totals.get(c,0)
        if tot == 0: continue
        if tot < 0 : out = 1
        else: out = 0
        change = abs(tot)
        total[out] = total[out] + change
    if total[0] > total[1]: largest = total[0]
    else: largest = total[1]


    lineheight = 15 # for text
    upperBound = abs(income)
    if abs(outgoings) > upperBound: upperBound = abs(outgoings)
    
    dh = 600  # document hight in pixels
    scale = (dh - 30) / abs(largest)   # Pixels/dollar


    chart.write("""    <text  y="%ipx" x="5px" width="60px"
        height="20px">%s up to but excluding %s</text>
""" %(20, startDate, endDate))

    
    y = 0
    while y < dh:   # grid
        chart.write("""    <rect stroke="#777777" fill="none" y="%ipx" x="50px" width="600px"
        height="0px"/>
""" %(dh-y))
#"
        chart.write("""    <text  y="%ipx" x="320px" width="60px"
        height="20px">%ik</text>
""" %(dh-y, round((y/scale)/1000))) 
#"      
        y = y + 10000 * scale

    # for offset, cats, color in [ (100, incomeCategories, "#eeffee" ),
    #                       (400, spendingCategories, "#ffeeee") ]:

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
""" %(c.fragid, dh-round(top*scale), offset[out], height, color[out]))
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
    return

def isBottomClass(c):
    subs = kb.each(pred=rdfs.subClassOf, obj=c);
    return len(subs) == 0

def allClasses(some):
    cats = []
    agenda = some[:]
    while len(agenda) > 0:
        c = agenda.pop()
        if c not in cats: cats.append(c);
        supers = kb.each(subj=c, pred=rdfs.subClassOf);
        for sup in supers:
            if sup not in agenda and sup not in cats: agenda.append(sup)
    return cats

def monthOfDate(date):
    return int(date[0:4]) * 12 + int(date[5:7])

def monthNumber(s):
    global qu
    date = kb.any(subj=s, pred=qu.date).__str__()
    if date == "None":
        # progress("@@@ No date for transaction %s -- ignoring!" % s.uriref())
        return  -1
    m = monthOfDate(date)
    startMonth = monthOfDate(startDate)
    endMonth = monthOfDate(endDate)
    if m >= endMonth: return -1
    return m - startMonth

def baseRel(uri):
    return uripath.refTo(uripath.base(), uri)
    
def doCommand(startDate, endDate, inputURIs=["/dev/stdin"],totalsFilename=None):
    """Fin - financial summary
        
 <command> <options> <inputURIs>
 Totals transactions by classes to which they are known to belong 
 This is or was  http://www.w3.org/2000/10/swap/pim/fin.py
 
"""
        
    #import urllib
    #import time
    import sys
    # global sax2rdf
    global kb, tax
    
    def noteError(e):
        if not errors.get(s, None): errors[s] = [];
        errors[s].append(e)
    
    # The base URI for this process - the Web equiv of cwd
    _baseURI = uripath.base()
    
    _outURI = _baseURI
    option_baseURI = _baseURI   # To start with - then tracks running base


# Load the data:

    kb = loadMany(inputURIs)
            
    qu_date = qu.date
    qu_in_USD = qu.in_USD
    qu_amount = qu.amount
    qu_payee = qu.payee
    qu_Classified = qu.Classified
    qu_Unclassified = qu.Unclassified
    taxCategories = kb.each(pred=rdf_type, obj=tax.Category)
    if verbose:
        progress("Tax categories" + `taxCategories`)
    specialCategories = taxCategories + [qu.Classified, qu.Unclassified, qu.Transaction]

####### Analyse the data:
    numberOfMonths = monthOfDate(endDate) - monthOfDate(startDate)
    monthTotals = [0] * numberOfMonths
    incomeByMonth = [0] * numberOfMonths
    income, outgoings = 0,0
    outgoingsByMonth = [0] * numberOfMonths

    quCategories = kb.each(pred=rdf_type, obj=qu.Cat)
    bottomCategories = [];
    for c in quCategories:
        if isBottomClass(c): bottomCategories.append(c);
    
    totals = {}  # Total by all classes of transaction
    count = {}  # Number of transactions
    byMonth = {}

    sts = kb.statementsMatching(pred=qu.amount)  # Ideally one per transaction
    errors = {}
    for st in sts:
        s = st.subject()
        uri = s.uriref()
#        classified =  kb.each(pred=rdf_type, obj=qu_Classified)
#        unclassified = kb.each(pred=rdf_type, obj=qu_Unclassified)
#        for t in classified: assert t not in unclassified, "Can't be classified and unclassified!"+`t`
#        for s in classified + unclassified:
#           progress( "Transaction ", `s`)
        t_ok, c_ok = 0, 0
        cats = allClasses(kb.each(subj=s, pred=rdf.type))
        # progress( "Categories: "+`cats`)
        
        month = monthNumber(s)
        if month not in range(numberOfMonths) : continue
                    
        payees = kb.each(subj=s, pred=qu_payee)
        if str(payees[0]) == "Check" and len(payees) >1: payee = payees[1]
        else: payee = payees[0]
        
        amounts = kb.each(subj=s, pred=qu_in_USD)
        if len(amounts) == 0:
            amounts = kb.each(subj=s, pred=qu_amount)
            if len(amounts) == 0:
                progress("@@@ Error: No amount for "+`uri`)
            else:
                progress("Warning: No USD amount for "+`uri`+", assuming USD")
        if len(amounts) >1:
            if (cat_ns.Internal not in cats or
                len(amounts) != 2 ):
            
                progress(
        "Error: More than one amount %s for transaction %s -- ignoring!\n"
                        % (`amounts`,uri))
            else:
                sum = float(amounts[0]) + float(amounts[1])
                if sum != 0:
                    progress("2 amounts %s for internal transaction %s.\n"
                        % (amounts,uri))
            continue

        if len(amounts) != 1:
            progress("@@@ Error: No amount for "+`uri`);
            ss = kb.statementsMatching(subj=s)
            progress(`ss`+'; KB='+`kb.n3String()`)
            continue
        amount = float(amounts[0].__str__())
#           print "%s  %40s  %10s month %i" %(date, payee, `amount`, month)

        monthTotals[month] = monthTotals[month] + amount
        if cat_ns.Internal not in cats:
            if amount > 0:
                incomeByMonth[month] = incomeByMonth[month] + amount
                income = income + amount
            else:
                outgoingsByMonth[month] = outgoingsByMonth[month] + amount
                outgoings = outgoings + amount

        normalCats = []  # For this item
        for c in cats:
            totals[c] = totals.get(c, 0) + amount
            byMonth[c] = byMonth.get(c, [0] * numberOfMonths)
            count[c] = count.get(c, 0) + 1
            byMonth[c][month] = byMonth[c][month] + amount
            if c not in specialCategories:
                normalCats.append(c)
        bottomCats = normalCats[:] # Copy
        for b in normalCats:
            sups = kb.each(subj=b, pred=rdfs.subClassOf)
            for sup in sups:
                if sup in bottomCats:
                    bottomCats.remove(sup)
        if len(bottomCats) == 0:
           noteError("No categoriy: %s  for <%s>"  # all cats: %s, raw cats:%s"
                        %(`bottomCats`, `s`))  #  ,`cats`, `kb.each(subj=s, pred=rdf.type)`)
        elif bottomCats[0] not in bottomCategories:
           noteError("Be more specifc: %s for <%s>"  %(`bottomCats[0]`, `s`)) # Won't get shown e.g. in year-cat.html
        if len(bottomCats) > 1:
           noteError("Inconsistent categories: %s"  # all cats: %s, raw cats:%s"
                        %(`bottomCats`))  #  ,`cats`, `kb.each(subj=s, pred=rdf.type)`)

    
    print '<html xmlns="http://www.w3.org/1999/xhtml">'
    print """<head>
        <meta charset='UTF-8'>
        <title>Annual Summary by month</title>
        <link rel="Stylesheet" href="report.css">
    </head>
    <body>
    """
#           <img src="sand-dollar.gif" alt="dollar" align="right"/>
    


    version = "$Id$"
#       if not option_quiet:
#       _outSink.makeComment("<address>Processed by " + version[1:-1]+"</address>") # Strip $ to disarm


#  SUMMARY  TABLE OF CATEGORY BY MONTH

    print "<h2>Personal categories and months %s - %s</h2>" % (startDate, endDate)
    print "<table class='wide' style='border-collapse:collapse; border: 0.01em solid #aaa; text-align: right' ><col style='text-align: left'>"
    
    print "<tr><th></th><th>Total </th>" 
    for month in range(numberOfMonths):
        m = month + int(startDate[5:7]) - 1
        while m > 11: m -= 12  # Modulo in python?
        
        
        print "<th><a href='year-chron.html#m%s'>%s</a></th>" %(("0"+`m+1`)[-2:], monthName[m]),
    print "</tr>"
    
    
    def listFor(c, depth=0):   # Any, because there could be 2 copies of same list :-(
        subs = kb.any(subj = c, pred = owl.disjointUnionOf);
        res = [ (c, depth) ];
        if subs == None:
            subs = kb.each(pred = rdfs.subClassOf, obj = c);
            if len(subs) > 0:
                sys.stderr.write( "Warning: for %s: no disjointUnionOf but subclasses %s\n" %(`c`, `subs`))
            for sub in subs: res += listFor(sub, depth+1)
        else:
            for sub in subs: res += listFor(sub, depth+1)
        return res
        
    printOrder = listFor(qu.Transaction);
    
    for cat, depth in printOrder:
        label = kb.the(subj=cat, pred=rdfs.label)
        if label == None:
            label = `cat`
            sys.stderr.write("@@ No label for "+`cat` +"\n")
        else:
            label = str(label)
        anchor = cat.fragid
        if totals.get(cat, None) != None:
            print monthGridRow(anchor, anchor, totals[cat], byMonth.get(cat, [0] * numberOfMonths),
                numberOfMonths, indent = depth)

    print "<tr><td colspan='14'> ___  </td></tr>"
    print monthGridRow("Income", None,  income, incomeByMonth, numberOfMonths)
    print monthGridRow("Outgoings", None, outgoings, outgoingsByMonth, numberOfMonths)
    print monthGridRow("Balance", None, income + outgoings, monthTotals, numberOfMonths)

    print "</table>"

    
#  Chart of income stacked up against expenses
    print "<p><a href='chart.svg'><p>Chart of day-day income vs expense</p><img src='chart.svg'></a></p>"
    print "<p><a href='all.svg'><p>Chart of all income vs expense</p><img src='all.svg'></a></p>"

    writeChart(filename = "chart.svg",
        categories = bottomCategories + [ qu.UnclassifiedIncome, qu.UnclassifiedOutgoing],
        totals = totals, income=income, outgoings=outgoings, shortTerm = 1)

    writeChart(filename = "all.svg",
        categories = bottomCategories + [ qu.UnclassifiedIncome, qu.UnclassifiedOutgoing],
        totals = totals, income=income, outgoings=outgoings, shortTerm = 0)


    # Output totals
    
    ko = kb.newFormula()    
    for c in quCategories + [ qu.UnclassifiedIncome, qu.UnclassifiedOutgoing]:
        ko.add(subj=c, pred=qu.total, obj=("%7.2f" % totals.get(c,0)))
    ko.add(subj=qu.Transaction, pred=qu.total, obj=("%7.2f" % (income + outgoings)))
    ko.close()
    
    if (totalsFilename):
        fo = open(totalsFilename, "w")
        fo.write(ko.n3String())
        fo.close


    #  Generate a list of errors found
    errstr = ""
    for x, list in errors.items():
        errstr += transactionRow(x)
        for e in list: errstr += "<tr><td colspan='4'>"+`e`+"</td></tr>\n"  #  @@@ encode error string
    if errstr:
        print "<h2>Inconsistencies</h2><table>\n" + errstr + "</table>\n"
    
    # List Unclassified Income and Spending
    
    def transactionList(cat):
        ts = kb.each(pred = rdf.type, obj = cat)
        if len(ts) == 0: return ""
        label = kb.any(cat, rdfs.label)
        st = '<h2>'+label.value()+'</h2>\n<table>\n'
        return st + transactionTable(ts)
    
    for cat in [ qu.UnclassifiedIncome, qu.UnclassifiedOutgoing]:
        print transactionList(cat)

    print reimbursablesCheck();
    
    internalCheck()

    
    print "<h2>Tax Categories</h2>"
    taxCategories = kb.each(pred=rdf_type, obj=tax.Category)
    printCategoryTotalsOnly(taxCategories + [ qu.Unclassified], totals, count)

    print "<h2>Tax stuff</h2>"
    print "<table>"
    print "<tr><th>-<th>Form line</th><th>amount</th></tr>"
    print "</table>"
        
    # print "<h2>Personal Category total</h2>"
    # printCategoryTotalsOnly(quCategories + [ qu.Unclassified], totals, count)

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

reportLink = "year-cat.html"
global yearInQuestion, startDate, endDate

def usage():
    print __doc__

startDate = None
endDate = None
yearInQuestion = None

if __name__ == '__main__':
    global verbose
    #global yearInQuestion, startDate, endDate
    import getopt
    testFiles = []
    totalsFilename = None
    start = 1
    normal = 0
    chatty = 0
    proofs = 0
    verbose = 0
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvy:i:s:e:t:r:",
            ["help",  "verbose", "year=", "input=", "start=", "end=", "totals=", "report="])
    except getopt.GetoptError:
        # print help information and exit:
        print __doc__
        sys.exit(2)
    output = None
    inputURIs = []
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-v", "--verbose"):
            verbose = 1
        if o in ("-t", "--totals"):
            totalsFilename = a
        if o in ("-s", "--start"):
            startDate = a
        if o in ("-e", "--end"):
            endDate = a
        if o in ("-y", "--year"):
            yearInQuestion = a
            if len(yearInQuestion) < 7: yearInQuestion += "-01"
        if o in ("-i", "--input"):
            inputURIs.append(a)
        if o in ("-r", "--report"):
            reportLink = a
            #progress("Report to link to: "+a)

    if yearInQuestion is not None :
        startDate = yearInQuestion + "-01"
        endDate = "%4i" % (int(yearInQuestion[0:4]) + 1) + yearInQuestion[4:7] + "-01" # Date NOT done
    doCommand(startDate=startDate, endDate=endDate, inputURIs=inputURIs, totalsFilename=totalsFilename)

