#!/usr/bin/python
"""Sales tax
    
usage, eg:
    python salesTax.py -y 2003 -i year.unc
    
    The year must be given explicitly. Transactions outside that year will be ignored.

This is an RDF application.

$Id$
"""
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


state = Namespace("/devel/WWW/2000/10/swap/test/dbork/data/USRegionState.n3#")
qu = Namespace("http://www.w3.org/2000/10/swap/pim/qif#")
tax = Namespace("http://www.w3.org/2000/10/swap/pim/tax.n3#")
rdf = Namespace(RDF_NS_URI)
rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
cat_ns = Namespace("categories.n3#")
ma = Namespace("http://www.w3.org/2000/10/swap/pim/massachusetts#") # Mass tax specials
contact = Namespace("http://www.w3.org/2000/10/swap/pim/contact#") # Personal contact info

import thing
import uripath
import re

#store = llyn.RDFStore()
#thing.setStore(store)

cat = cat_ns

form = """
<html>
<head>
  <meta http-equiv="Content-Type" content="text/html">
  <link link type="text/css" rel="Stylesheet" href="st11.css" />
  <title>Massachusetts Department of Revenue FORM ST-11 Individual Use Tax
  Return</title>
</head>

<body bgcolor="#ffffff" vlink="blue" link="blue">

<table border="None">
<tr>
<td width="108pt"><span class="formno">FORM ST-11</span><br/>(after rev 4/96)</td>
<td class="title"><span class="title">Massachusetts Department of Revenue<br/>Individual Use Tax Return</span></td>
<td width="108pt">&nbsp;</td>
</tr>
</table>
<table border="1" cellpadding="0">
  <tbody>
    <tr>
      <td rowspan="8" width="50%">
        <table border="0">
          <tbody>
            <tr class="ruled">
              <td><sup>Name</sup>
                <br/><span class="data">$name$</span>
              </td>
              <td><sup>Social Security Number</sup>
                <br/><span class="data">$ssn$</span>
              </td>
              <td></td>
            </tr>
            <tr class="ruled">
              <td><sup>Address</sup><br>
                <span class="data">$address$</span></td>
              <td><sup>State                     Zip</sup><br>
                <span class="data">$state$</span>         <span class="data">$zip$</span></td>
              <td></td>
            </tr>
            <tr>
              <td colspan="2">Return is due with payment on or before
                April 15 for purchases made in the prior calendar year. Make
                check payable to the Commonwealth of Massachusetts. Mail to:
                Massachusetts Department of Revenue,PO Box 7009, Boston, MA
                02204
                <p></p>
              </td>
              <td></td>
            </tr>
            <tr>
              <td colspan="2">I declare under the penalties of perjury that
                this return has been examined by me and to the best of my
                knowledge and belief is a true, correct and complete
              return.</td>
              <td></td>
            </tr>
          </tbody>
        </table>
      </td>
      <td class="lineno">1.</td>
      <td>Year purchases made</td>
      <td class="lineno">1</td>
      <td class="amount">$l1$</td>
    </tr>
    <tr>
      <td class="lineno">2.</td>
      <td>Total purchases from line 9 on reverse</td>
      <td class="lineno">2</td>
      <td class="amount">$l2$</td>
    </tr>
    <tr>
      <td class="lineno">3.</td>
      <td>Use tax (5% of line 2)</td>
      <td class="lineno">3</td>
      <td class="amount">$l3$</td>
    </tr>
    <tr>
      <td class="lineno">4.</td>
      <td>Total credit for sales/use tax paid to other states or
        jurisdictions. From line 10 on reverse</td>
      <td class="lineno">4</td>
      <td class="amount">$l4$</td>
    </tr>
    <tr>
      <td class="lineno">5.</td>
      <td>Balance. <em>Subtract line 4 from line 3</em>.<br>
        Not less than 0.</td>
      <td class="lineno">5</td>
      <td class="amount">$l5$</td>
    </tr>
    <tr>
      <td class="lineno">6.</td>
      <td>Penalty</td>
      <td class="lineno">6</td>
      <td class="amount">$l6$</td>
    </tr>
    <tr>
      <td class="lineno">7</td>
      <td>Interest</td>
      <td class="lineno">7</td>
      <td class="lineno">$l7$</td>
    </tr>
    <tr>
      <td class="lineno">8</td>
      <td>Total amount due</td>
      <td class="lineno">8</td>
      <td class="amount">$l8$</td>
    </tr>
  </tbody>
</table>
<table width="100%"><tr><td><sup>Signature</sup><br/></td><td><sup>Date</sup><br/></td></tr></table>
<hr/>
<table border=1>
<tr><th width="81pt">Date of<br/>purchase</th><th width="108pt">Name of seller,<br/>city and state</th>
<th>Quantity and description<br/>of property purchased</th><th width="72pt">A. Sales<br/>price</th>
<th width="99pt">B. Sales/use tax paid<br/> to other jurisdcitions <br/><em>or</em>5% of sales price - <br/><em>whichever is less</em></th></tr>
$rows$
<tr><td colspan="3"><span class="lineno">9.</span> Total purchases. Add all of the purchase prices listed in column A.
<br/>Enter the result here and in line 2 on the front.</td><td class='amount'>$l9$</td><td>&nbsp;</td></tr>
<tr><td colspan="4"><span  class="lineno">10.</span> Total sales/use tax paid to other states or jusisdictions.
Add all the amounts listed in column B.<br/>
Enter the result here and in line 4 on the front.</td><td class='amount'>$l10$</td></tr>
</table>
</body>
</html>
"""
#"

def substitute(form, dict):
    "Substitute values from dictionary into $vvv$ places in form string"
    str = form[:]
    r = re.compile(r"^(.*)(\$[_A-Za-z0-9]*\$)(.*)$", re.MULTILINE)
    while 1:
	m = r.search(str)
	if m == None: break
	start, end = m.start(2), m.end(2)
	progress( "Matched start, end", start, end, str[start:end])
	str = str[:start] + dict[str[start:end][1:-1]] + str[end:]
    return str

def doCommand(year, inputURI="/dev/stdin"):
        """Fin - financial summary
        
 <command> <options> <inputURIs>
 Totals transactions by classes to which they are known to belong 
 This is or was  http://www.w3.org/2000/10/swap/pim/fin.py
 
"""
        
        import sys
        global sax2rdf
        import thing
	from thing import load
	global kb
        #from thing import chatty
        #import sax2rdf
	import os

# Load the data:
	home = os.environ["HOME"]
	personalInfo = load(home + "/.personal.n3")
	me = personalInfo.statementsMatching(pred=contact.ssn)[0].subject()
	myname = (personalInfo.the(subj=me, pred=contact.givenName).string + " " +
	    personalInfo.the(subj=me, pred=contact.familyName).string)
	myssn = personalInfo.the(subj=me, pred=contact.ssn).string
	myhome = personalInfo.the(subj=me, pred=contact.home)
	mystreet = personalInfo.the(subj=myhome, pred=contact.street).string
	mystate = personalInfo.the(subj=myhome, pred=contact.stateOrProvince).string
	myzip = personalInfo.the(subj=myhome, pred=contact.postalCode).string
	assert myname and myssn and mystreet and mystate and myzip
	 
	progress("Data from", inputURI)
	kb=load(inputURI)
#	print "# Size of kb: ", len(kb)
	
	# for /devel/WWW read http://www.w3.org/ when we have persistent cache
	stateInfo = load("/devel/WWW/2000/10/swap/test/dbork/data/USRegionState.n3")
	stateCodes = []
	for s in stateInfo.statementsMatching(pred=state.code):
	    stateCodes.append(s.object().string)
	progress("#", len(stateCodes), "state codes")
	
	categories = kb.each(pred=rdf.type, obj=qu.Cat)
	progress("%i categories found" % len(categories))

	maUseTaxable = kb.each(pred=rdf.type, obj=ma.useTaxable)

	total = 0
	rows = ""
	for s in maUseTaxable:
	    date = kb.any(subj=s, pred=qu.date).__str__()
	    year = int(date[0:4])
	    if  int(year) != int(yearInQuestion): continue
	    
	    payees = kb.each(subj=s, pred=qu.payee)
	    if str(payees[0]) == "Check" and len(payees) >1: payee = payees[1]
	    else: payee = payees[0]
	    payee=payee.string
	    if payee[-3:-2] == " ":
		sc = payee [-2:]
		if sc in stateCodes and sc != "MA":
		    amount = -float(kb.the(subj=s, pred=qu.amount).__str__())
		    mycat = "@@@"
		    classes = kb.each(subj=s, pred=rdf.type)
		    for c in classes:
			if c in categories:
			    mycat = kb.the(subj=c, pred=rdfs.label)
		    progress( "# %s  %40s  %10s" %(date, payee, `amount`))
		    rows = rows + """    <tr><td>%s</td><td>%s</td><td>%s</td>
		    <td class='amount'>%7.2f</td><td class='amount'>0</td></tr>\n""" %(
			date[:10], payee, mycat, amount)
		    total = total + amount
		
	progress('<%s>\n\t<%s> "%7.2f".' % ( ma.useTaxable.uriref(), qu.total.uriref(), total))
	progress( "# ie sales tax of 5%% would be $%7.2f" % (total*0.05))

	
	values = { "name": myname, "ssn": myssn,
		    "address": 	mystreet,
		    "state": 	mystate,
		    "zip":	myzip,
		    "l1":	yearInQuestion,
		    "l2":	"%7.2f" % total,
		    "l3":	"%7.2f" % (total * 0.05),
		    "l4":	"0",
		    "l5":	"%7.2f" % (total * 0.05),
		    "l6":	"0",
		    "l7":	"0",
		    "l8":	"%7.2f" % (total * 0.05),
		    "l9":	"%7.2f" % total,
		    "l10":	"0",
		    "rows":	rows
		     }

	print substitute(form, values)
        
############################################################ Main program
    
if __name__ == '__main__':
    import getopt
    testFiles = []
    start = 1
    normal = 0
    chatty = 0
    proofs = 0
    global verbose
    global yearInQuestion
    verbose = 0
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvy:i:",
	    ["help",  "verbose", "year=", "input="])
    except getopt.GetoptError:
        # print help information and exit:
        print __doc__
        sys.exit(2)
    output = None
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-v", "--verbose"):
	    verbose = 1
        if o in ("-y", "--year"):
            yearInQuestion = a
        if o in ("-i", "--input"):
            inputURI = a

    doCommand(year=yearInQuestion, inputURI=inputURI)

#end
