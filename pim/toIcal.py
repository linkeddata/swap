#!/usr/bin/python
"""toICal.py -- convert RDF to iCalendar syntax

references:

  A quick look at iCalendar
  http://www.w3.org/2000/01/foo

  Internet Calendaring and Scheduling Core Object Specification
                              (iCalendar)
  November 1998
  http://www.ietf.org/rfc/rfc2445.txt

$Id$

NOTE: see earlier work:
  http://www.w3.org/2002/01dc-nj/toICal.py

see changelog at end
"""

from string import strip, maketrans, translate

import RDFSink, llyn # from SWAP http://www.w3.org/2000/10/swap/
from RDFSink import SYMBOL, FORMULA, SUBJ, PRED, OBJ
from thing import Namespace, load

import sys
try:
    reload (sys)
    sys.setdefaultencoding('iso-8859-1')
except:
    pass

CRLF = chr(13) + chr(10)

ProdID = "-//w3.org/2002/01dc-nj/toICal.py//NONSGML v1.0/EN" #@@bogus?


RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")

ICAL = Namespace('http://www.w3.org/2002/12/cal/ical#')

#@@owe update to these folks:
# by Libby and company; e.g.
# SWWS data http://swordfish.rdfweb.org:8085/swws/index.html
#IH = "http://ilrt.org/discovery/2001/06/schemas/ical-full/hybrid.rdf#"
#VEVENT = IH + "Vevent"

class CalWr:
    def __init__(self, writeFun):
        self._w = writeFun
        
    def export(self, sts, addr):
        """export calendar objects from an RDF graph in iCalendar syntax
        """

        w = self._w

        for cal in sts.each(pred = RDF.type, obj = ICAL.Vcalendar):
            # cf  4.4. iCalendar Object of
            # http://www.ietf.org/rfc/rfc2445.txt

            w("BEGIN:VCALENDAR" + CRLF) #hmm... SAX interface?
            w("PRODID:%s%s" % (ProdID, CRLF) ) #@@grab?
            w("VERSION:2.0" + CRLF) #@@ grab these from the RDF?
            w("CALSCALE:GREGORIAN" +CRLF) #@@ grab?

            #hmm... method? cf 3.2 Parameters


            for comp in sts.each(subj = cal, pred = ICAL.component):
                if sts.statementsMatching(RDF.type, comp, ICAL.Vevent):
                    self.exportEvent(sts, comp)
                elif sts.statementsMatching(RDF.type, comp, ICAL.Vtimezone):
                    self.exportTimezone(sts, comp)
                else:
                    progress("@@skipping component with types: ",
                             sts.each(subj = comp, pred = RDF.type))
        
            w("END:VCALENDAR" + CRLF)


    def exportTimezone(self, sts, tz):
        w = self._w
        
        w("BEGIN:VTIMEZONE" +CRLF)
        self.textProp(sts, "tzid", tz)

        for subcomp in sts.each(subj = tz, pred = ICAL.standard):
            self.exportTZSub(sts, subcomp, 'standard')
        for subcomp in sts.each(subj = tz, pred = ICAL.daylight):
            self.exportTZSub(sts, subcomp, 'daylight')
        w("END:VTIMEZONE" +CRLF)

    def exportTZSub(self, sts, tzs, n):
        w = self._w

        w("BEGIN:%s%s" % (n, CRLF))
        self.textProp(sts, 'tzoffsetfrom', tzs)
        self.textProp(sts, 'tzoffsetto', tzs)
        self.textProp(sts, 'tzname', tzs)
        self.timeProp(sts, "dtstart", tzs)
        self.recurProp(sts, "rrule", tzs)
        w("END:%s%s" % (n, CRLF))


    def exportEvent(self, sts, event):
        w = self._w

        w("BEGIN:VEVENT"+CRLF)
        uid = self.textProp(sts, "uid", event)
        # 4.8.2.4 Date/Time Start
        self.timeProp(sts, "dtstart", event)
        self.timeProp(sts, "dtend", event)
        self.timeProp(sts, "dtstamp", event)
        self.timeProp(sts, "lastModified", event) #@@ last-modified
        txt = self.textProp(sts, "summary", event)
        self.textProp(sts, "description", event)
        self.textProp(sts, "location", event)
        self.textProp(sts, "priority", event)
        self.recurProp(sts, "rrule", event)

        other = sts.statementsMatching(None, event, None)
        for s in other:
            if s[PRED] not in (ICAL.dtstart, ICAL.dtend,
                               ICAL.lastModified, ICAL.dtstamp,
                               ICAL.uid,
                               ICAL.summary, ICAL.description,
                               ICAL.location, ICAL.priority,
                               RDF.type,
                               ICAL.rrule):
                progress("@@skipping ", s[PRED], " of [", txt, "] = [", \
                                 s[OBJ], "]")
        w("END:VEVENT"+CRLF)
            


    def recurProp(self, sts, pn, subj):
        r  = sts.any(subj, ICAL.sym(pn))
        if r:
            w = self._w
            w("RRULE:")
            freq = sts.any(r, ICAL.freq)
            if freq: w("FREQ=%s;" % freq)
            ival = sts.any(r, ICAL.interval)
            if freq: w("INTERVAL=%s;" % ival)
            by = sts.any(r, ICAL.byday)
            if by: w("BYDAY=%s;" % by)
            by = sts.any(r, ICAL.bymonth)
            if by: w("BYMONTH=%s;" % by)
            #@@ more
            w(CRLF)


    def textProp(self, sts, pn, subj):
        # "Property names, parameter names and enumerated parameter values are
        # case insensitive."
        #  -- 4.5 Property, http://www.ietf.org/rfc/rfc2445.txt
        w = self._w
        txt  = sts.any(subj, ICAL.sym(pn))
        if txt is None: return txt
        v = strip(str(txt))
        w("%s:%s%s" % (pn.upper(), v, CRLF)) #@@linebreaks?
        return v
    
    def timeProp(self, sts, pn, subj):
        w = self._w
        when = sts.any(subj, ICAL.sym(pn))

        if when:
            whenV = sts.any(when, ICAL.dateTime)
            if whenV:
                whenV = translate(str(whenV), maketrans("", ""), "-:")
                whenTZ = sts.any(when, ICAL.tzid)
                if whenTZ:
                    w("%s;VALUE=DATE-TIME;TZID=%s:%s%s" % (pn.upper(), str(whenTZ),
                                           whenV, CRLF))
                else:
                    w("%s:VALUE=DATE-TIME;%s%s" % (pn.upper(), whenV, CRLF))
            else:
                whenV = sts.any(when, ICAL.date)
                if whenV:
                    whenV = translate(str(whenV), maketrans("", ""), "-:")
                    w("%s:VALUE=DATE;%s%s" % (pn.upper(), whenV, CRLF))
                else:
                    progress("@@no value for ", when)


import sys, os
import uripath

def main(args):
    addr = uripath.join("file:" + os.getcwd() + "/", args[1])
    
    c = CalWr(sys.stdout.write)
#    kb = llyn.RDFStore()
#    kb.reset("http://example/@@uuid-here#something")
    progress("loading...", addr)
    sts = load(addr)

    progress("exporting...")
    c.export(sts, addr)

def progress(*args):
    for i in args:
        sys.stderr.write(str(i))
    sys.stderr.write("\n")

import diag
diag.setVerbosity(0)

if __name__ == '__main__':
    main(sys.argv)


# $Log$
# Revision 1.11  2003-03-24 20:18:01  ryanlee
# first pass at making toIcal understand non-ascii characters
#
# Revision 1.10  2003/03/14 06:01:04  connolly
# cleaned up DATE-TIME vs DATE stuff
#
# Revision 1.9  2003/03/14 03:17:23  connolly
# oops! forgot begin/end around vtimezone.
# clearly I don't have any good way to test this code.
#
# Revision 1.8  2003/03/14 03:12:35  connolly
# update to 2002/12 namespace
# export timezones, at least well enough for one case
# export rrules well enough for one test case
# update to each()/any() API
# kill dead (commented out) Namespace class code
#
# Revision 1.7  2003/01/13 19:48:23  timbl
# Changed API, using thing.Namespace
#
# Revision 1.6  2002/12/12 22:58:07  timbl
# minor
#
# Revision 1.5  2002/09/22 21:53:44  connolly
# handle location, priority
#
# Revision 1.4  2002/08/28 22:00:24  connolly
# updated to diag interface
#
# Revision 1.3  2002/07/23 23:09:31  connolly
# grumble... evo is case-sensitive where the RFC says not to be
#
# Revision 1.2  2002/07/23 21:44:16  connolly
# - updated ICAL namespace pointer, case of RDF terms
# - handle description, as well as summary
# - be more clear about what properties we skip/don't handle
# - don't complain about floating/local time
# - pointer to earlier work
# - used Namespace() trick
#
# Revision 1.1  2002/07/20 17:14:39  timbl
# DanC's with slight updates
#
# Revision 1.7  2002/06/27 02:36:27  timbl
# Extend datetimes to allways have 15 chars on output
#
# Revision 1.6  2002/05/29 20:12:12  connolly
# moved to formula-based API from store.every()
#
# Revision 1.5  2002/05/29 19:53:42  connolly
# tweak timezone handling
#
# Revision 1.4  2002/03/20 16:48:42  connolly
# more strict URI handling
#
# Revision 1.3  2002/01/11 04:45:54  connolly
# decided the main class is a writer
#
