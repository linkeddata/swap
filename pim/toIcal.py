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


CRLF = chr(13) + chr(10)

ProdID = "-//w3.org/2002/01dc-nj/toICal.py//NONSGML v1.0/EN" #@@bogus?

class Namespace:
    """A collection of URIs witha common prefix.

    ACK: AaronSw / #rdfig
    http://cvs.plexdev.org/viewcvs/viewcvs.cgi/plex/plex/plexrdf/rdfapi.py?rev=1.6&content-type=text/vnd.viewcvs-markup
    """
    def __init__(self, nsname): self.nsname = nsname
    def __getattr__(self, lname): return self.nsname + lname
    def sym(self, lname): return self.nsname + lname

RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")

ICAL = Namespace('http://www.w3.org/2000/10/swap/pim/ical#')

#@@owe update to these folks:
# by Libby and company; e.g.
# SWWS data http://swordfish.rdfweb.org:8085/swws/index.html
#IH = "http://ilrt.org/discovery/2001/06/schemas/ical-full/hybrid.rdf#"
#VEVENT = IH + "Vevent"

class CalWr:
    def __init__(self, writeFun):
        self._w = writeFun
        
    def export(self, kb, ctx):
        """export calendar objects from an RDF KB
        in iCalendar syntax
        """

        w = self._w
        
        # cf  4.4. iCalendar Object of
        # http://www.ietf.org/rfc/rfc2445.txt

        w("BEGIN:VCALENDAR" + CRLF) #hmm... SAX interface?
        w("VERSION:2.0" + CRLF) #hmm... SAX interface?
        w("PRODID:%s%s" % (ProdID, CRLF) )#@@ bogus?
        w("CALSCALE:GREGORIAN" +CRLF)

        #hmm... method? cf 3.2 Parameters

        ctx = kb.intern((FORMULA, ctx + "#_formula"))
        ty = kb.internURI(RDF.type)
        
        progress("@@skipping timezones and lots of other component types")
        progress("querying for type ", ICAL.Vevent, " in ", ctx )
        eventHits = ctx.statementsMatching(ty,
                                           None,
                                           kb.internURI(ICAL.Vevent))
        
        for hit in eventHits:
            event = hit[SUBJ]
            w("BEGIN:VEVENT"+CRLF)
            txt = self.textProp(kb, ctx, "summary", event)
            self.textProp(kb, ctx, "description", event)
            uid = self.textProp(kb, ctx, "uid", event)

            # 4.8.2.4 Date/Time Start
            self.timeProp(kb, ctx, "dtstart", event)

            self.timeProp(kb, ctx, "dtend", event)

            other = ctx.statementsMatching(None, event, None)
            for s in other:
                if str(s[PRED]) not in ('dtstart', 'dtend', 'uid', 'summary', 'description'):
                    progress("@@skipping ", s[PRED], " of [", txt, "] = [", \
                             s[OBJ], "]")
            w("END:VEVENT"+CRLF)
            
        w("END:VCALENDAR" + CRLF)

    def textProp(self, kb, ctx, pn, subj):
        # "Property names, parameter names and enumerated parameter values are
        # case insensitive."
        #  -- 4.5 Property, http://www.ietf.org/rfc/rfc2445.txt
        w = self._w
        txt  = kb.any((ctx, kb.internURI(ICAL.sym(pn)), subj, None))
        if txt is None: return txt
        v = strip(str(txt))
        w("%s:%s%s" % (pn.upper(), v, CRLF)) #@@linebreaks?
        return v
    
    def timeProp(self, kb, ctx, pn, subj):
        w = self._w
        when = kb.any((ctx, kb.internURI(ICAL.sym(pn)), subj, None))
        whenV = kb.any((ctx, kb.internURI(ICAL.value), when, None)) \
                or kb.any((ctx, kb.internURI(ICAL.date), when, None)) \
                or kb.any((ctx, kb.internURI(ICAL.dateTime), when, None))
        if not whenV:
            progress("@@no value for ", when)
        whenTZ = kb.any((ctx, kb.internURI(ICAL.tzid), when, None))

        whenV = translate(str(whenV), maketrans("", ""), "-:")
	if whenTZ:
	    if len(whenV) == 8:
		whenV = whenV + "T000000"
	    else:
		whenV = whenV+"000000"
		whenV = whenV[:15] # 8 for date, 1 for T, 6 for time
            w("%s;TZID=%s:%s%s" % (pn.upper(), str(whenTZ), whenV, CRLF))
        else:
	    if whenV[-1:] != "Z":
		pass # local time. hmm...
	    else:
		whenV = whenV[:-1]+"000000"
		whenV = whenV[:15] + "Z"
            w("%s:%s%s" % (pn.upper(), str(whenV), CRLF))

import sys, os
import uripath

def main(args):
    addr = uripath.join("file:" + os.getcwd() + "/", args[1])
    
    c = CalWr(sys.stdout.write)
    kb = llyn.RDFStore()
    kb.reset("http://example/@@uuid-here#something")
    progress("loading...", addr)
    llyn.loadToStore(kb, addr)

    progress("exporting...")
    c.export(kb, addr)

def progress(*args):
    for i in args:
        sys.stderr.write(str(i))
    sys.stderr.write("\n")

import thing
thing.chatty_flag=30 # thing interface?

if __name__ == '__main__':
    main(sys.argv)


# $Log$
# Revision 1.3  2002-07-23 23:09:31  connolly
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
