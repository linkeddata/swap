#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Summarize and chart one year's balances
    
usage, eg:
    python balances.py -y 2003
        Results for the year 2003-01 through 2003-12
    python balances.py -y 2003-07
        Results for the year 2003-07 through 2004-06
    python balances.py --start 2010-01 --end 2010-06

options:

    -y  --year 2013         Select a year:  -y 2013 is same as -s 2013-01-01 -e 2014-01-01
    -s  --start 2013-01-01  The first date to include
    -e  --end  2014-01-01   The first date NOT to include
    
    -b  --balances foo.ttl  Output beginning and end balances in turtle
    -c  --chart foo.svg     Output a timeline graph in SVG
        --csv  foo.csv      Output a balances through time in CSV

    -v  --verbose           Output more about what you are doing
    -h  --help              Print this message
    
    
    
    The date range must be given explicitly, there is no default.
    Transactions outside that year will be ignored.

$Id$
"""
from swap import llyn, diag, notation3, RDFSink, uripath, myStore

from swap.diag import verbosity, setVerbosity, progress
# from swap.uripath import join
from swap.notation3 import RDF_NS_URI
from swap.myStore import store, load, loadMany,  Namespace
import swap.llyn

global yearInQuestion, startDate, endDate

import string, time, sys
from sys import stderr
from time import gmtime, mktime
from math import log, exp


OFX = Namespace('http://www.w3.org/2000/10/swap/pim/ofx#');
qu = Namespace("http://www.w3.org/2000/10/swap/pim/qif#")
rdf = Namespace(RDF_NS_URI)
rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
# cat = Namespace("categories.n3#")

info = lambda s: sys.stderr.write(s+'\n');

monthName= ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul",
                            "Aug", "Sep", "Oct", "Nov", "Dec"]


kb = None;


def figureBalances(startDate, endDate, inputURIs=["/dev/stdin"]):
    
    
    # The base URI for this process - the Web equiv of cwd
    _baseURI = uripath.base()
    
    _outURI = _baseURI
    option_baseURI = _baseURI   # To start with - then tracks running base


# Load the data:

    kb = loadMany(inputURIs)

    sts = kb.statementsMatching(pred = OFX.BANKTRANLIST);
    #if verbose:
        # print len(sts), " bank transaction lists."
    lists = []
    for st in sts:
        tl = st.object();
        start = str(kb.any(tl, OFX.DTSTART))[:10];
        end = str(kb.any(tl, OFX.DTEND))[:10];
        # print "Transaction list %s - %s " %(start, end)
        
        lists.append((start, end, tl, st.subject()))
        
    lists.sort(reverse = 1);
    # lists.reverse();
    balances = [];
    first = {};

    for s, e, t, stmtrs in lists:
    
        #   Do one statement, working backward to get the balance each date
        ac = kb.any(stmtrs, OFX.BANKACCTFROM);
        if ac == None: ac = kb.the(stmtrs, OFX.CCACCTFROM);
        #info("ac = "+`ac`)
        acid = str(kb.the(ac, OFX.ACCTID))[-4:];

        # info("Bank statment %s  to  %s for %s" % (s, e, acid)); # @@
        
        ledgerBalance = kb.the(stmtrs, OFX.LEDGERBAL);
        balanceDate = str(kb.the(ledgerBalance, OFX.DTASOF))[:10];
        balance = float(str(kb.the(ledgerBalance, OFX.BALAMT)));
        
        transactionsThisStatement = [];
        for tran in kb.each(t, OFX.STMTTRN):
            transactionsThisStatement.append((
                str(kb.the(tran, OFX.DTPOSTED))[:10], 
                float(str(str(kb.the(tran, OFX.TRNAMT))))));
        transactionsThisStatement.sort();
        transactionsThisStatement.reverse();
        
        bal, dat = float(str(balance)), balanceDate;
        for d, a in transactionsThisStatement:
            # assert dat >= d, "Ooops '%s' < '%s'  %d, %d in %s" % (dat, d, len(dat), len(d), acid)
            # print "\t\t%10s  %10s\t%s\t%10.2f\t%10.2f" % (d, dat, acid, a, bal)
            first[acid] = [d, bal];
            balances.append((d, dat, acid, bal));
            bal = bal - a
            dat = d
            
    balances.sort();
    return first, balances

def trackTotalBalance(first, balances):
    "Generate a balances for a dummy account which is the sum of the others"
    totalBalances = [];
    last = {}
    bal = {}
    for ac in first:
        last[ac], bal[ac] = first[ac];
    f2 = None;
    for s, e, acid, b in balances:
        bal[acid] = b;
        sum = 0;
        if first[acid][0] > s:
                info( "@@ internal first: %s, this date: %s" %  (first[acid][0], s));
        for a in first:
            sum += bal[a];
        totalBalances.append((s, None, 'sum', sum));
        if f2 == None:
            f2 = {'sum': (s, sum)};
    return f2, totalBalances;
        
    
def dateToInt(date):
    return time.mktime(time.strptime(date[:10], "%Y-%m-%d"))

def csvTable(first, balances):
    lines = []
    def opLine(ln):
        lines.append(ln);

    acbal = {};
    earliest = "Z";
    for ac in first:
        d, acbal[ac] = first[ac];
        if d < earliest: earliest = d;

    dat = earliest    
    columns = ['date']
    
    for ac in first:
        columns.append(ac)
    delim = ','
    opLine(delim.join(columns))
    
    lastLine = None;
    lastDate = None;
    for s, e, acid, bal in balances:
        acbal[acid] = bal;        
        line = s
        for c in columns[1:]: line += '%s%1.2f' %(delim, acbal[c])
        if (s != lastDate):
            if lastLine != None:
                opLine(lastLine);
        lastLine = line;
        lastDate = s
    opLine(lastLine);
    
    return '\n'.join(lines) + '\n';



def palette(ind):
    # Tim's patented not bit redistribution scheme
    # 0->black, 1-> dark red, etc etc etc
    # Colors are spaced out and consecutive colors always contrast
    #
    rgb = [0,0,0]
    chan, weight = 0, 8;
    i = int(ind);
    while 1:
        if (i == 0 ): return "#%x%x%x" % (rgb[0], rgb[1], rgb[2])
        if i & 1: rgb[chan] += weight;
        i = i / 2
        chan = (chan + 1) % 3
        if (chan == 0): weight = weight/2
        assert weight != 0, " palette index too large %d" % ind




def svgTimelineChart(first, balances):

    viewWidth = 800
    viewHeight = 400
    leftLabels = 50   # Offset for start of axis labels
    lines = [];

    def opLine(ln):
        lines.append(ln); # Note can't assign to non-local variable in python
    
    opLine("""<?xml version="1.0" encoding="iso-8859-1"?>
<svg xmlns="http://www.w3.org/2000/svg"
    xmlns:l="http://www.w3.org/1999/xlink" width="%dpt" height="%dpt" viewBox="0 0 %d %d">
""" % ( viewWidth, viewHeight, viewWidth, viewHeight ));
    svgBottom = """</svg>
""";
    
    minx = miny = 10e10;
    maxx = maxy = -10e10;
    for s, e, acid, bal in balances:
        x1 = dateToInt(s);
        if x1 < minx: minx = x1;
        if x1 > maxx: maxx = x1;
        if bal < miny: miny = bal;
        if bal > maxy: maxy = bal;
        
    def xscale(x):
        return (x - minx)/(maxx - minx) * (viewWidth * .8) + (viewWidth * .1)

    def yscale(y):  # Flip y axis to normal math way around
        return (maxy - y)/(maxy - miny) * (viewHeight * .8) + (viewHeight * .1)

    def line(x1, y1, x2, y2, color='black', width="0.5px"):
        opLine("\t<path   style='fill:none; stroke: %s; stroke-width: %s;' d='M %d %d L %d %d'/>"
            % (color, width, xscale(x1), yscale(y1), xscale(x2), yscale(y2)));

    axisStyle = "font-size:70%; font-family: sans-serif;";
    
    monthname = ["January", "February", "March", "April", "May", "June", 
            "July", "August", "Spetember", "October", "November", "December"]; # @@ I18N
    
    def timeAxis():
        ym1, ym2 = gmtime(minx), gmtime(maxx)
        months = (ym2[0] - ym1[0]) * 12 + (ym2[1] - ym1[1])
        assert months > 0
        ym = (ym1[0], ym1[1], 1, 0, 0, 0, 0, 0, 0);
        for m in range(months+1):
            if  ym[1] % 12 == 1: col = '#44f';
            else:
                if ym[1] % 3 == 1: col = '#aaf'
                else: col = '#ddf';
            line(mktime(ym), miny, mktime(ym), maxy, col);
            if xscale(86400 * 28) - xscale(0) > 50 : label =  monthname[ym[1]-1]
            else: label = ym[1];
            opLine("<text x='%d' y='%d' style='%s'>%s</text>\n" % (
                xscale( mktime(ym)) + 10,
                yscale(miny) + 10,
                axisStyle +"fill: #77f;",   #   was + "text-align:center;",
                label));
            if ym[1] ==1: opLine( "<text x='%d' y='%d' style='%s'>%s</text>" % (
                xscale( mktime(ym)) + 10,
                yscale(miny) + 25,
                axisStyle +"fill: #77f;",   #   was + "text-align:center;",
                str(ym[0])));
            ym = (ym[0]+ym[1]/12, ym[1] % 12 + 1, 1, 0, 0, 0, 0, 0, 0);

    # Use engineering suffixes to abbreviate round numbers"
    def kMGT(x):
        if x == 0: return '0';
        scale = int(log(x)/log(10)  + 0.00001)  # In case bad rounding
        level = int(scale / 3);
        suffix = ['n', 'µ', 'm', '', 'k', 'M', 'G', 'T'][level+3];
        x2 = x /(10**(level*3));
        if x2 == int(x2): return "%d%s" % (x2, suffix) # @@ need Approx
        s = ("%f" % x2)
        if level != 0:
            s = s.replace('.', suffix);
            while (s[-1:] == '0'): s = s[:-1]; # Trim round numbers
        return s
        
        
    def yaxis():
        h = str(int(max(maxy, -miny)));
        k = len(h)
        step = int('1'+'0'*(k-1))
        y = 0;
        while y < maxy:
            line(minx - 5, y, maxx, y,'#ddd');
            opLine( "<text x='%d' y='%d' style='%s'>%s</text>" % (
                xscale(minx) - leftLabels, yscale(y), 
                axisStyle + "fill: #444;", kMGT(y)));
            y += step;
        return 


    timeAxis(); # Underneath the data to come
    yaxis();
    
    series = []; # Let's have an ordered list for once
    for ac in first:
        if ac == 'sum': series.insert(0, ac)  # sum is special, colour 0, black.
        else: series.append(ac);
        
    lastBalance = {};
    lastTime = {};
    path = {}
    ix = 0;
    n = len(series);
    keyY = yscale(maxy)-20;
    keyWidth = (maxx-minx)/n;
    
    for ix in range(len(series)):
        ac = series[ix];
        d, lastBalance[ac] = first[ac];
        lastTime[ac] = dateToInt(d);
        path[ac] = ( "<path   style='fill:none; stroke:%s' d='M %d %d" % 
                    ( palette(ix), xscale(lastTime[ac]), yscale(lastBalance[ac] )))
        # Add a key:
        opLine( "<path style='fill:none; stroke:%s' d='M %d %d L %d %d'/>" % (
                    palette(ix), xscale(minx + ix*keyWidth), keyY, 
                    xscale(minx + (ix+0.4)*keyWidth), keyY));
        opLine("<text style='fill:%s; font-size:60%%; font-family:sans-serif' x='%d' y='%d'>%s</text>" %(
                    palette(ix), xscale(minx + (ix+0.5)*keyWidth), keyY, ac));

    for s, e, ac, bal in balances:
        x1= dateToInt(s);
        if (x1 != lastTime[ac]): path[ac] += " L %d %d" % (xscale(x1), yscale(lastBalance[ac]));
        if (bal != lastBalance[ac]): path[ac] += " L %d %d" % (xscale(x1), yscale(bal));
        lastTime[ac] = x1;
        lastBalance[ac] = bal;

    for ac in first:
        opLine( path[ac] + "'/>");
        
    opLine(svgBottom);
    
    return '\n'.join(lines) + '\n';
    
        
def balancesReport(dates, first, balances):
    dp = 0;
    lastTime = {};
    res = "";
    series = []; # Let's have an ordered list for once
    for ac in first:
        if ac == 'sum': series.insert(0, ac)  # sum is special, colour 0, black.
        else: series.append(ac);
        d, lastTime[ac]  = first[ac];

    res += 'date'
    for a in series:
        res += ','+ a
    res += '\n'

    def line(d):
        r = d
        tot = 0
        for a in series:
            r +=  (',%10.2f' % lastTime[a]);
            if a != 'sum': tot += lastTime[a]
        if lastTime['sum'] != tot:
            print "Error: sum %10.2f but total here %10.2f" % ( lastTime['sum'], tot);
        return r + '\n';

    for s, e, ac, bal in balances:
        lastTime[ac] = bal
        if s >= dates[dp]:
            res += line(dates[dp]);
            dp += 1;
            
        if dp >= len(dates):
            return res;

    #print "Didn't find all dates.", dp 
    res += line(dates[dp]);    
    return res
    

    
        
############################################################ Main program

reportLink = "year-cat.html"
global yearInQuestion, startDate, endDate

startDate = None
endDate = None
yearInQuestion = None

if __name__ == '__main__':
    global verbose
    #global yearInQuestion, startDate, endDate
    import getopt
    testFiles = []
    start = 1
    normal = 0
    chatty = 0
    proofs = 0
    verbose = 0
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvy:i:b:c:s:e:r:",
            ["help",  "verbose", "year=", "input=", "balances=", "chart=", "csv=", "start=", "end=", "report="])
    except getopt.GetoptError:
        # print help information and exit:
        print __doc__
        sys.exit(2)
    output = None
    inputURIs = []
    balancesFileName , svgFileName, csvFileName = None, None, None
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-v", "--verbose"):
            verbose = 1
        if o in ("-b", "--balances"):
            balancesFileName = a
        if o in ("-c", "--chart"):
            svgFileName = a
        if o in ("--csv"):
            csvFileName = a
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

    for a in args:
        inputURIs.append(a)

    if yearInQuestion is not None :
        startDate = yearInQuestion + "-01"
        endDate = "%4i" % (int(yearInQuestion[0:4]) + 1) + yearInQuestion[4:7] + "-01" # Date NOT done

    first, balances = figureBalances(startDate=startDate,
            endDate=endDate, inputURIs=inputURIs)
    firstSum, totalBalances = trackTotalBalance(first, balances)
    balances = balances + totalBalances
    first.update(firstSum)
    
    if svgFileName :
        opf = open(svgFileName, 'w');
        opf.write(svgTimelineChart(first, balances));
        opf.close();

    if csvFileName :
        opf = open(csvFileName, 'w');
        opf.write(csvTable(first, balances));
        opf.close();

    if balancesFileName :
        opf = open(balancesFileName, 'w');
        opf.write(balancesReport([startDate, endDate], first, balances));
        opf.close();
        

