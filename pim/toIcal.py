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

see changelog at end
"""

from string import strip, maketrans, translate

import RDFSink, llyn # from SWAP http://www.w3.org/2000/10/swap/
from RDFSink import SYMBOL, FORMULA, SUBJ


CRLF = chr(13) + chr(10)

ProdID = "-//w3.org/2002/01dc-nj/toICal.py//NONSGML v1.0/EN" #@@bogus?

RDF_ns = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDF_type_URI = RDF_ns + "type"

# by Libby and company; e.g.
# SWWS data http://swordfish.rdfweb.org:8085/swws/index.html
IH = "http://ilrt.org/discovery/2001/06/schemas/ical-full/hybrid.rdf#"
VEVENT = IH + "Vevent"

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
        ty = kb.internURI(RDF_type_URI)
        
        progress("@@skipping timezones and lots of other component types")
        progress("querying for type ", VEVENT, " in ", ctx )
        eventHits = ctx.statementsMatching(ty,
                                           None,
                                           kb.internURI(VEVENT))
        
        for hit in eventHits:
            event = hit[SUBJ]
            w("BEGIN:VEVENT"+CRLF)
            txt = self.textProp(kb, ctx, "SUMMARY", event)
            uid = self.textProp(kb, ctx, "UID", event)
            self.timeProp(kb, ctx, "DTSTART", event)
            self.timeProp(kb, ctx, "DTEND", event)
            progress("@@skipping other properties of ", txt)
            w("END:VEVENT"+CRLF)
            
        w("END:VCALENDAR" + CRLF)

    def textProp(self, kb, ctx, pn, subj):
        w = self._w
        txt  = kb.any((ctx, kb.internURI(IH+pn.lower()), subj, None))
        v = strip(str(txt))
        w("%s:%s%s" % (pn, v, CRLF)) #@@linebreaks?
        return v
    
    def timeProp(self, kb, ctx, pn, subj):
        w = self._w
        when = kb.any((ctx, kb.internURI(IH+pn.lower()), subj, None))
        whenV = kb.any((ctx, kb.internURI(RDF_ns+"value"), when, None))
        whenTZ = kb.any((ctx, kb.internURI(IH+"tzid"), when, None))

        whenV = translate(str(whenV), maketrans("", ""), "-:")
	if whenTZ:
	    if len(whenV) == 8:
		whenV = whenV + "T000000"
	    else:
		whenV = whenV+"000000"
		whenV = whenV[:15] # 8 for date, 1 for T, 6 for time
            w("%s;TZID=%s:%s%s" % (pn, str(whenTZ), whenV, CRLF))
        else:
	    if whenV[-1:] != "Z":
		progress("@@@@@ No timezone and no Z for "+ whenV)
	    else:
		whenV = whenV[:-1]+"000000"
		whenV = whenV[:15] + "Z"
            w("%s:%s%s" % (pn, str(whenV), CRLF))

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
# Revision 1.1  2002-07-20 17:14:39  timbl
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
