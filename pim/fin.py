#!/usr/bin/python
"""Summarize and chart one year's finances
    
usage, eg:
    fin -y 2003
        Results for the year 2003-01 through 2003-12
    fin -y 2003-07
        Results for the year 2003-07 through 2004-06
        
    -t foo.n3   --totals=foo.n3  Please output totals in this file     
    
    The year must be given explicitly.
    Transactions outside that year will be ignored.

This is an RDF application.

$Id$
"""
from swap import llyn, diag, notation3, RDFSink, uripath, myStore

from swap.diag import verbosity, setVerbosity, progress
from swap.uripath import join
from swap.notation3 import RDF_NS_URI
from swap.myStore import store, load, loadMany,  Namespace
import swap.llyn

#import uripath

import string
import sys

qu = Namespace("http://www.w3.org/2000/10/swap/pim/qif#")
tax = Namespace("http://www.w3.org/2000/10/swap/pim/tax.n3#")
rdf = Namespace(RDF_NS_URI)
rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
cat_ns = Namespace("categories.n3#")

monthName= ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul",
                            "Aug", "Sep", "Oct", "Nov", "Dec"]


rdf_type = rdf.type
cat = cat_ns
meta = None   # Formula for metadata
    
def sym(uri):
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
    print """<p>In %i transactions, Total income %9.2f, 
    outgoings %9.2f, balance %92f</p>""" % (trans, inc, out, inc + out)



def tableRow(label, anchor, totals, value):
    str = ""
    for month in range(12):
        str = str + "<td class='amt'>%6.2f</td>" % value[month]
    if anchor:
        return "<tr><td><a href='%s'>%s</a></td><td class='total'>%7.2f</td>%s</tr>" %(
                "year-cat.html#" + anchor, label, totals, str)  # @@ add year in filename
    return "<tr><td>%s</td><td class='total'>%7.2f</td>%s</tr>" %(label, totals, str)

def internalCheck():
    global kb
    global cat
    transactions = kb.each(pred=rdf.type, obj=cat_ns.Internal)
    unbalanced = []
    while len(transactions) > 0:
        x = transactions.pop()
        date = str(kb.the(subj=x, pred=qu.date))
        if len(kb.each(subj=x, pred=qu.in_USD)) != 1:
            progress("Ignoring !=1 amount transaction %s" % x)
            continue
        amount = float(str(kb.the(subj=x, pred=qu.in_USD)))
        for y in transactions:
            datey = str(kb.the(subj=y, pred=qu.date))
            if date[0:10] == datey[0:10]:  # precision one day
                if len(kb.each(subj=y, pred=qu.in_USD)) != 1:
                    progress("Error: Ignoring: >1 amount for transaction %s" % y)
                    transactions.remove(y)
                    continue
                if abs(amount +
                        float(str(kb.the(subj=y, pred=qu.in_USD)))) < 0.001:
                    transactions.remove(y)
                    break
        else:
            unbalanced.append(x)
    transaction = unbalanced
    unbalanced = []
    while len(transactions) > 0:
        x = transactions.pop()
        amount = float(str(kb.the(subj=x, pred=qu.in_USD)))
        for y in transactions:
            if abs(amount + float(str(kb.the(subj=y, pred=qu.in_USD)))) < 0.001 : # Floating point ~=
                transactions.remove(y)
                break
        else:
            unbalanced.append((date, x))

    unbalanced.sort()
    print "<h2>Unbalanced internal transactions</h2>"
    print "<table>"
    for da, x in unbalanced:
        amount = float(str(kb.the(subj=x, pred=qu.in_USD)))
        payee = kb.any(subj=x, pred=qu.payee)
        toAccount = kb.the(subj=x, pred=qu.toAccount)
        print "<tr class='%s'><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" %(
            toAccount, da, payee, toAccount, amount)
    print "</table>"
        
    return unbalanced


def writeChart(filename, categories, totals, income, outgoings, shortTerm=0):
    """Chart income vs outgoing
    
    Scaled chart
    """
    global meta
    chart = open(filename, "w")
    chart.write("""<?xml version="1.0" encoding="iso-8859-1"?>
<svg xmlns="http://www.w3.org/2000/svg"
    xmlns:l="http://www.w3.org/1999/xlink">
""")
#"
    vc = []

    for c in categories:
        if totals.get(c, 0) == 0: continue
        
        label = meta.the(subj=c, pred=rdfs.label)
        if label == None:
            label = `c`
            sys.stderr.write("Warning: No label for category"+`c` +"\n")
        else:
            label = str(label)
        
        if shortTerm and meta.contains(subj=c, pred=rdf.type, obj=qu.LongTerm):
            continue  # ignore in budget diagram
        volatility = meta.the(subj=c, pred=qu.volatility)
        if volatility == None:
            volatility = 50
            sys.stderr.write("No volatility for "+ c.uriref() +"\n")
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
        height="20px">%s</text>
""" %(20, yearInQuestion))

    
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


def doCommand(yearInQuestion, inputURIs=["/dev/stdin"],totalsFilename=None):
        """Fin - financial summary
        
 <command> <options> <inputURIs>
 Totals transactions by classes to which they are known to belong 
 This is or was  http://www.w3.org/2000/10/swap/pim/fin.py
 
"""
        
        #import urllib
        import time
        import sys
        global sax2rdf
        global kb
        
        # The base URI for this process - the Web equiv of cwd
        _baseURI = uripath.base()
        
        _outURI = _baseURI
        option_baseURI = _baseURI   # To start with - then tracks running base


# Load the data:

#       print "Data from", inputURI
        kb=load(inputURIs[0])
        for inputURI in inputURIs[1:]:
            progress("Data also from " + inputURI)
            kb.store.load(uri=inputURI, openFormula=kb)
        
#       print "Size of kb: ", len(kb)
        
        global meta
        meta = loadMany(["categories.n3", "classify.n3"])  # Category names etc
#       print "Size of meta", len(meta)
        
        qu_date = qu.date
        qu_in_USD = qu.in_USD
        qu_amount = qu.amount
        qu_payee = qu.payee
        qu_Classified = qu.Classified
        qu_Unclassified = qu.Unclassified
        taxCategories = meta.each(pred=rdf_type, obj=tax.Category)
        if verbose:
            print "Tax categories", taxCategories
        specialCategories = taxCategories + [qu.Classified, qu_Unclassified]

####### Analyse the data:
        monthTotals = [0] * 12 
        incomeByMonth = [0] * 12 
        income, outgoings = 0,0
        outgoingsByMonth = [0] * 12 

        quCategories = meta.each(pred=rdf_type, obj=qu.Cat)
        
        totals = {}  # Total by all classes of transaction
        count = {}  # Number of transactions
        byMonth = {}
        satis = tax.Category, qu.Cat  # Satisfactory classes
        classified =  kb.each(pred=rdf_type, obj=qu_Classified)
        unclassified = kb.each(pred=rdf_type, obj=qu_Unclassified)
        for t in classified: assert t not in unclassified, "Can't be classified and unclassified!"+`t`
        for s in classified + unclassified:
#           progress( "Transaction ", `s`)
            t_ok, c_ok = 0, 0
            date = kb.any(subj=s, pred=qu_date).__str__()
            cats = kb.each(subj=s, pred=rdf_type)
            if date == "None":
#               raise ValueError("No date for transaction %s" % s)
                progress("No date for transaction %s -- ignoring\n" % s)
                continue
            m = int(date[0:4]) * 12 + int(date[5:7])
            monthInQuestion = int(yearInQuestion[0:4]) * 12 + int(yearInQuestion[5:7])
            month = m - monthInQuestion
            if month < 0 or  month > 11: continue

#           print year, yearInQuestion, `s`
#            if  int(year) != int(yearInQuestion): continue
#            month = int(date[5:7]) -1
#            if month not in range(12): raise ValueError("Month %i"% month)
            
            payees = kb.each(subj=s, pred=qu_payee)
            if str(payees[0]) == "Check" and len(payees) >1: payee = payees[1]
            else: payee = payees[0]
            amounts = kb.each(subj=s, pred=qu_in_USD)
            if len(amounts) == 0:
                amounts = kb.each(subj=s, pred=qu_amount)
                if len(amounts) == 0:
                    progress("@@@ Error: No amount for "+`s`)
                else:
                    progress("Warning: No USD amount for "+`s`+", assuming USD")
            if len(amounts) >1:
                if (cat_ns.Internal not in cats or
                    len(amounts) != 2 ):
                
                    progress(
            "Error: More than one amount %s for transaction %s -- ignoring!\n"
                            % (amounts,s))
                else:
                    sum = float(amounts[0]) + float(amounts[1])
                    if sum != 0:
                        progress("2 amounts %s for internal transaction %s.\n"
                            % (amounts,s))
                continue

            if len(amounts) != 1:
                progress("@@@ Error: No amount for "+`s`);
                progress("... where s.uri is "+s.uriref())
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

            normalCats = []
            for c in cats:
                totals[c] = totals.get(c, 0) + amount
                byMonth[c] = byMonth.get(c, [0] * 12)
                count[c] = count.get(c, 0) + 1
                byMonth[c][month] = byMonth[c][month] + amount
                if c not in specialCategories:
                    normalCats.append(c)
            if len(normalCats) != 1:
                progress("Error: %s Transaction with %s for %10s in >1 category: %s!!"
                            %(date, payee, amount, normalCats))
    

        print '<html xmlns="http://www.w3.org/1999/xhtml">'
        print """<head>
            <title>Annual Summary by month</title>
            <link rel="Stylesheet" href="report.css">
        </head>
        <body>
        """
#           <img src="sand-dollar.gif" alt="dollar" align="right"/>
        


        version = "$Id$"
#       if not option_quiet:
#       _outSink.makeComment("<address>Processed by " + version[1:-1]+"</address>") # Strip $ to disarm


#   TABLE OF CATEGORY BY MONTH

                
        print "<h2>%s Personal categories and month</h2><table class='wide'><tr><th></th><th>Year </th>" % yearInQuestion
        for month in range(12):
            m = month + int(yearInQuestion[5:7]) - 1
            if m > 11: m -= 12  # Modulo in python?
            
            
            print "<th><a href='year-chron.html#m%s'>%s</a></th>" %(("0"+`m+1`)[-2:], monthName[m]),
        print "</tr>"
        for cat in quCategories + [ qu.UnclassifiedIncome, qu.UnclassifiedOutgoing]:
            label = meta.the(subj=cat, pred=rdfs.label)
            if label == None:
                label = `cat`
                sys.stderr.write("@@ No label for "+`cat` +"\n")
            else:
                label = str(label)
            anchor = cat.fragid
            try:
                print tableRow(anchor, anchor, totals[cat], byMonth.get(cat, [0] * 12))
            except KeyError:
                continue

        print "<tr><td colspan='14'></td></tr>"
        print tableRow("Income", None,  income, incomeByMonth)
        print tableRow("Outgoings", None, outgoings, outgoingsByMonth)
        print tableRow("Balance", None, income + outgoings, monthTotals)

        print "</table>"

        
#  Chart of income stacked up against expenses
        print "<p><a href='chart.svg'><p>Chart of day-day income vs expense</p><img src='chart.svg'></a></p>"
        print "<p><a href='all.svg'><p>Chart of all income vs expense</p><img src='all.svg'></a></p>"

        writeChart(filename = "chart.svg",
            categories=quCategories + [ qu.UnclassifiedIncome, qu.UnclassifiedOutgoing],
            totals = totals, income=income, outgoings=outgoings, shortTerm = 1)
    
        writeChart(filename = "all.svg",
            categories=quCategories + [ qu.UnclassifiedIncome, qu.UnclassifiedOutgoing],
            totals = totals, income=income, outgoings=outgoings, shortTerm = 0)
    

        # Output totals
        
        ko = kb.newFormula()    
        for c in quCategories + [ qu.UnclassifiedIncome, qu.UnclassifiedOutgoing]:
            ko.add(subj=c, pred=qu.total, obj=("%7.2f" % totals.get(c,0)))
        ko.close()
        
        if (totalsFilename):
            fo = open(totalsFilename, "w")
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
            
#       print "<h2>Personal Categories</h2>"
#       printCategories(quCategories + [ qu.Unclassified], totals, count)

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
    import getopt
    testFiles = []
    totalsFilename = None
    start = 1
    normal = 0
    chatty = 0
    proofs = 0
    global verbose
    global yearInQuestion
    verbose = 0
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvy:i:t:",
            ["help",  "verbose", "year=", "input=", "totals="])
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
        if o in ("-y", "--year"):
            yearInQuestion = a
            if len(yearInQuestion) < 7: yearInQuestion += "-01"
        if o in ("-i", "--input"):
            inputURIs.append(a)

    doCommand(yearInQuestion=yearInQuestion, inputURIs=inputURIs, totalsFilename=totalsFilename)

