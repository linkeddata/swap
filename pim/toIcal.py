#!/usr/bin/python
"""toIcal.py -- convert RDF to iCalendar syntax

USAGE:
  python toIcal.py foo.rdf > foo.ics
  python toIcal.py foo.n3 > foo.ics
  python toIcal.py http://example/foo.rdf > foo.ics

see also:
  RDF Calendar Workspace
  http://www.w3.org/2002/12/cal/

"""

"""
References:

  Internet Calendaring and Scheduling Core Object Specification
                              (iCalendar)
  November 1998
  http://www.ietf.org/rfc/rfc2445.txt

  A quick look at iCalendar
  http://www.w3.org/2000/01/foo

NOTE: see earlier work:
  http://www.w3.org/2002/01dc-nj/toICal.py

@@cite and use python style
@@use doctest
see changelog at end


Copyright ©  2000-2004 World Wide Web Consortium, (Massachusetts Institute
of Technology, European Research Consortium for Informatics and Mathematics,
Keio University). All Rights Reserved. This work is distributed under the
W3C® Software License [1] in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 FOR A PARTICULAR PURPOSE.

"""


__version__ = '$Id$'


from string import maketrans, translate

from myStore import Namespace, load, setStore # http://www.w3.org/2000/10/swap/

#hmm... generate from schema?
from fromIcal import iCalendarDefs # http://www.w3.org/2002/12/cal/ 


CRLF = chr(13) + chr(10)

RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
ICAL = Namespace('http://www.w3.org/2002/12/cal/ical#')



class CalWr:
    def __init__(self, writeFun):
        self._w = writeFun
        
    def export(self, sts, addr):
        """export calendar objects from an RDF graph in iCalendar syntax
        """

        for cal in sts.each(pred = RDF.type, obj = ICAL.Vcalendar):
            self.doComponent(sts, cal, "VCALENDAR", iCalendarDefs)


    def doComponent(self, sts, comp, name, decls):
        w = self._w

        w("BEGIN:%s%s" % (name, CRLF))

        className, props, subs = decls[name]
        
        for prop in props.keys():
            predName, valueType = props[prop][:2]
            val  = sts.any(comp, ICAL.sym(predName))
            if val:
                if valueType == 'TEXT':
                    self.doTEXT(sts, val, prop, predName)
                elif valueType == 'INTEGER':
                    self.doINTEGER(sts, val, prop, predName)
                elif valueType == 'URI':
                    self.doURI(sts, val, prop, predName)
                elif valueType == 'DATE-TIME':
                    self.doDateTime(sts, val, prop, predName)
                elif valueType == 'DURATION':
                    self.doDuration(sts, val, prop, predName)
                elif valueType == 'RECUR':
                    self.doRecur(sts, val, prop, predName)
                elif valueType == 'CAL-ADDRESS':
                    self.doCalAddress(sts, val, prop, predName)
                else:
                    raise RuntimeError, "value type not implemented: " + \
                          valueType + " on " + prop


        for sub in sts.each(subj = comp, pred = ICAL.component):
            for subName in subs.keys():
                className, p, s = subs[subName]
                if sts.statementsMatching(RDF.type, sub, ICAL.sym(className)):
                    self.doComponent(sts, sub, subName, subs)
                    break
            else:
                raise ValueError, "no component class found"


        # timezone standard/daylight components use a different structure
        # hmm... is this a good idea?
        if name == 'VTIMEZONE':
            for part in subs.keys():
                n, p, c = subs[part]
                sub = sts.any(subj = comp, pred=ICAL.sym(n))
                if sub:
                    self.doComponent(sts, sub, part, subs)
        w("END:%s%s" % (name, CRLF))


    def doTEXT(self, sts, val, propName, predName):
        # @@TODO: wrap at 75 cols
        w = self._w
        text = str(val)
        for c in ('\\', ';', ','):
            text = text.replace(c, "\\"+c)
        text = text.replace('\n', "\\n")
        w("%s:%s%s" % (propName, text, CRLF))


    def doINTEGER(self, sts, val, propName, predName):
        w = self._w
        i = int(str(val))
        w("%s:%d%s" % (propName, i, CRLF))


    def doURI(self, sts, sym, propName, predName):
        """ handle reference properties
        i.e. properties with value type URI
        
        http://www.w3.org/2002/12/cal/rfc2445#sec4.3.13

        @@perhaps add support for example from 4.2.8 Format Type
        http://www.w3.org/2002/12/cal/rfc2445#sec4.2.8

        ATTACH;FMTTYPE=application/binary:ftp://domain.com/pub/docs/agenda.doc
        """

        w = self._w
        uri = sym.uriref() #@@need to encode non-ascii chars
        w("%s;VALUE=URI:%s%s" % (propName, uri, CRLF))


    def doDateTime(self, sts, when, propName, predName):
        """ helper function to output general date value"""
        w = self._w

        whenV = sts.any(when, ICAL.dateTime)
        if whenV:
            whenV = translate(str(whenV), maketrans("", ""), "-:")
            whenTZ = sts.any(when, ICAL.tzid)
            if whenTZ:
                w("%s;VALUE=DATE-TIME;TZID=%s:%s%s" %  
                  (propName, str(whenTZ), whenV, CRLF))
            else:
                z = ""
                if whenV[-1:] == "Z":
                    z = "Z"
                    whenV = whenV[:-1]
                whenV = (whenV + "000000")[:15] # Must include seconds
                w("%s:%s%s%s" % (propName, whenV, z, CRLF))
        else:
            whenV = sts.any(when, ICAL.date)
            if whenV:
                whenV = translate(str(whenV), maketrans("", ""), "-:")
                w("%s;VALUE=DATE:%s%s" % (propName, whenV, CRLF))
            else:
                raise ValueError, "no ical:dateTime or ical:date for " + str(when)

    def doDuration(self, sts, r, propName, predName):
        w = self._w
        w(propName)

        related = sts.any(r, ICAL.related)
        if related: w(";RELATED=" + str(related))

        dur = sts.the(r, ICAL.duration)
        w(":" + str(dur))
        w(CRLF)


    def doRecur(self, sts, r, propName, predName):
        w = self._w
        w(propName + ":")
        freq = sts.any(r, ICAL.freq)
        if freq: w("FREQ=%s;" % freq)
        ival = sts.any(r, ICAL.interval)
        if freq: w("INTERVAL=%s;" % ival)
        by = sts.any(r, ICAL.byday)
        if by: w("BYDAY=%s;" % by)
        by = sts.any(r, ICAL.bymonth)
        if by: w("BYMONTH=%s;" % by)
        w(CRLF)


    def doCalAddress(self, sts, who, propName, predName):

        w = self._w

        w(propName)
        #@@ hmm... are there others?
        for sym, paramName in ((ICAL.cn, "CN"),
                               (ICAL.dir, "DIR"),
                               (ICAL.cutype, "CUTYPE"),
                               (ICAL.language, "LANGUAGE"),
                               (ICAL.partstat, "PARTSTAT"),
                               (ICAL.role, "ROLE"),
                               (ICAL.rsvp, "RSVP"),
                               (ICAL.sentBy, "SENT-BY"),
                               ):
            v = sts.any(who, sym)
            if v:
                v = str(v)
                if ';' in v or ' ' in v or ':' in v:
                    w(";%s=\"%s\"" % (paramName, v))
                else:
                    w(";%s=%s" % (paramName, v))
        address = str(sts.the(who, ICAL.calAddress, None))

        # MAILTO seems to be capitalized in the iCalendar world. odd.
        if address.startswith("mailto:"):
            address = "MAILTO:" + address[7:]
        w(":" + address + "\n")






def wrapString(self, str, slen):
    """ helper function to wrap a string iCal-style
    """

    x = ''
    while(len(str) > slen):
        x += str[0:slen-1] + CRLF + ' '
        str = str[slen-1:]
    x += str
    return x


import sys, os
import uripath

def usage():
    print __doc__


def main(args):
    if not args[1:]:
        usage()
        sys.exit(1)
    addr = uripath.join("file:" + os.getcwd() + "/", args[1])
    
    c = CalWr(sys.stdout.write)
    progress("loading...", addr)

    sts = load(addr)

    progress("exporting...")
    c.export(sts, addr)


def progress(*args):
    for i in args:
        sys.stderr.write(str(i))
    sys.stderr.write("\n")


def debug(*args):
    for i in args:
        sys.stderr.write(str(i))
    sys.stderr.write("\n")

import sys

if __name__ == '__main__':
    main(sys.argv)


# $Log$
# Revision 2.14  2004-03-06 20:39:40  timbl
# See http://www.w3.org/2000/10/swap/doc/changes.html for details
# - Regresssion test incorporates the RDF Core Positive Parser Tests except XMLLiteral & reification
# - xml:base support was added in the parser.
# - Use the --rdf=R flag to allow RDF to be parsed even when there is no enveloping <rdf:RDF> tag
# - nodeid generated on RDF output
# - Automatically generated terms with no URIs sort after anything which has a URI.
# - Namespace prefix smarts on output - default ns used for that most frequently used.
# - suppresses namespace prefix declarations which are not actually needed in the output.
# - Cwm will also make up prefixes when it needs them for a namespace, and none of the input data uses one.-
# - Will not use namespace names for URIs which do not have a "#". Including a "/" in the flags overrides.
#
# Revision 2.13  2004/02/23 16:50:54  connolly
# schema-based rewrite. might have regressed a bit.
#
# Revision 2.8  2004/02/02 16:46:50  connolly
# more tweaks for status; fixed a progress message
#
# Revision 2.7  2004/01/31 00:45:10  timbl
# Add COMPLETED:
#
# Revision 2.6  2004/01/31 00:11:06  connolly
# todo status support; no test; blech
#
# Revision 2.5  2004/01/29 21:28:13  timbl
# Changed ONE newline to a CRLF, suspect many more should be changed. iCal needs both
#
# Revision 2.4  2004/01/29 21:09:16  timbl
# Added DTSTART and UID to events. iCal needs DTSTART it seems. Fixed VALUE=URI format.
#
# Revision 2.3  2004/01/29 19:41:57  timbl
# minor fixes
#
# Revision 2.2  2004/01/29 15:20:05  connolly
# - added some Vtodo support (@@owe tests; struggling with cal test harness)
# - added uri property support (@@I18N bugs)
# - updated to thing API changes (which turns out to be obsolete. oops)
# - unexpected usage gives help text rather than backtrace
# - a few more code review notes
#
# Revision 2.1  2003/08/28 15:49:04  connolly
# various code review notes that I want to discuss with ghuo
#
# Revision 2.0  2003/08/23 08:40:40  ghuo
# Added support for numerous new properties and parameters.
# Added the VALARM component. Restructured the export
# procedures. Fixed various output bugs.
#
# Revision 1.14  2003/06/13 22:06:10  timbl
# Fixed DATE-TIMEs to be always 15char and punctuation bug in some datetimes
#
# Revision 1.13  2003/06/03 17:35:38  connolly
# added duration support
#
# Revision 1.12  2003/04/16 17:21:01  ryanlee
# more rfc2445 fixes in textProp
#
# Revision 1.11  2003/03/24 20:18:01  ryanlee
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

