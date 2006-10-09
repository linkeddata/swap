#!/usr/bin/python
"""toIcal.py -- convert RDF to iCalendar syntax

USAGE:
  python toIcal.py foo.rdf > foo.ics
  python toIcal.py foo.n3 > foo.ics
  python toIcal.py http://example/foo.rdf > foo.ics

To override floating times and put them in a timezone:
  python toIcal.py --floattz America/Chicago work.rdf > work.ics

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
see changelog at end


Copyright (C) 2000-2004 World Wide Web Consortium, (Massachusetts
Institute of Technology, European Research Consortium for Informatics
and Mathematics, Keio University). All Rights Reserved. This work is
distributed under the W3C(R) Software License [1] in the hope that it
will be useful, but WITHOUT ANY WARRANTY; without even the implied
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

"""


__version__ = '$Id$'


from string import maketrans, translate

from myStore import Namespace, load, setStore # http://www.w3.org/2000/10/swap/
from RDFSink import LITERAL_DT

#hmm... generate from schema?
from fromIcal import iCalendarDefs # http://www.w3.org/2002/12/cal/ 


CRLF = chr(13) + chr(10)

RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
ICAL = Namespace('http://www.w3.org/2002/12/cal/icaltzd#')
XMLSchema = Namespace('http://www.w3.org/2001/XMLSchema#')



class CalWr:
    def __init__(self, writeFun):
        self._w = writeFun
        self.floatTZ = None # timezone for floating times
        
    def export(self, sts, addr):
        """export calendar objects from an RDF graph in iCalendar syntax
        """

        for cal in sts.each(pred = RDF.type, obj = ICAL.Vcalendar):
            self.doComponent(sts, cal, "VCALENDAR", iCalendarDefs)


    def doComponent(self, sts, comp, name, decls):
        w = self._w

        w("BEGIN:%s%s" % (name, CRLF))

        className, props, subs = decls[name]

        if self.floatTZ and name == "VCALENDAR":
            # In the floatTZ case, we write out a timezone decl,
            # but it has a fully-qualified TZID, which Apple iCal doesn't
            # seem to grok (@@bug report pending).
            # So we use the short TZID to refer to this timezone,
            # which works even though it shouldn't.
            tzaddr = TZD + self.floatTZ
            progress("loading timezone...", tzaddr)
            tzkb = load(tzaddr)
            for tzc in tzkb.each(pred = RDF.type, obj = ICAL.Vtimezone):
                progress("exporting timezone...", tzc)
                save, self.floatTZ = self.floatTZ, None
                self.doComponent(tzkb, tzc, "VTIMEZONE", subs)
                self.floatTZ = save

        propNames = props.keys()
        propNames.sort()
        for prop in propNames:
            predName, valueType = props[prop][:2]
            for val in sts.each(comp, ICAL.sym(predName)):
                if valueType == 'TEXT':
                    self.doSIMPLE(mkTEXT(val, sts), prop)
                elif valueType == 'INTEGER':
                    self.doSIMPLE(mkINTEGER(val), prop)
                elif valueType == 'FLOAT':
                    self.doSIMPLE(mkFLOAT(val), prop)
                elif valueType == 'URI':
                    self.doURI(val, prop)
                elif valueType == 'DATE-TIME':
                    self.doDateTime(sts, val, prop, predName)
                elif valueType == 'DURATION':
                    self.doDuration(sts, val, prop, predName)
                elif valueType == 'RECUR':
                    self.doRecur(sts, val, prop, predName)
                elif valueType == 'CAL-ADDRESS':
                    self.doCalAddress(sts, val, prop, predName)
                elif type(valueType) == tuple: 
                    itemType = valueType[0]
                    if itemType not in ('TEXT', 'INTEGER', 'FLOAT'): 
                        raise RuntimeError, "list value type not implemented"
                    values = []
                    while 1: 
                        first = val.first
                        val = val.rest
                        mkSIMPLE = {'TEXT': mkTEXT, 
                                    'INTEGER': mkINTEGER, 
                                    'FLOAT': mkFLOAT}[itemType]
                        v = mkSIMPLE(first)
                        values.append(v)
                        if val == RDF.nil: break
                    self.doSIMPLE(';'.join(values), prop)
                else:
                    raise RuntimeError, "value type not implemented: " + \
                          str(valueType) + " on " + str(prop)


        compToDo = []
        for sub in sts.each(subj = comp, pred = ICAL.component):
            for subName in subs.keys():
                className, p, s = subs[subName]
                if sts.statementsMatching(RDF.type, sub, ICAL.sym(className)):
                    compToDo.append((sts, sub, subName, subs))
                    break
            else:
                raise ValueError, "no component class found: %s" % subName

        # compToDo.sort(key=compKey) # darn... only in python 2.4
        compToDo.sort(componentOrder)
        for sts, sub, subName, subs in compToDo:
            self.doComponent(sts, sub, subName, subs)


        # timezone standard/daylight components use a different structure
        # hmm... is this a good idea?
        if name == 'VTIMEZONE':
            self.doTimeZone(sts, comp, subs)

        w("END:%s%s" % (name, CRLF))


    def doTimeZone(self, sts, comp, subs):
        partNames = subs.keys()
        partNames.sort()
        for part in partNames:
            n, p, c = subs[part]
            sub = sts.any(subj = comp, pred=ICAL.sym(n))
            if sub:
                self.doComponent(sts, sub, part, subs)

        
    def doSIMPLE(self, v, propName): 
        w = self._w
        w("%s:%s%s" % (propName, v, CRLF))

    def doURI(self, sym, propName):
        """ handle reference properties
        i.e. properties with value type URI
        
        http://www.w3.org/2002/12/cal/rfc2445#sec4.3.13

        @@perhaps add support for example from 4.2.8 Format Type
        http://www.w3.org/2002/12/cal/rfc2445#sec4.2.8

        ATTACH;FMTTYPE=application/binary:ftp://domain.com/pub/docs/agenda.doc
        """
        uri = sym.uriref() #@@need to encode non-ascii chars

        w = self._w
        w("%s;VALUE=URI:%s%s" % (propName, uri, CRLF))


    def doDateTime(self, sts, when, propName, predName):
        """ helper function to output general date/dateTime value"""
        w = self._w

        tk, tv = when.asPair()
        if tk is LITERAL_DT:
            tlit, dt = tv
            if dt == XMLSchema.date.uriref():
                w("%s;VALUE=DATE:%s%s" % (propName, mkDATE(tlit), CRLF))
            else:
                tlit = tlit.replace("-", "").replace(":", "")
                z = ""
                if tlit[-1:] == "Z":
                    z = "Z"
                    tlit = tlit[:-1]
                tlit = (tlit + "000000")[:15] # Must include seconds

                if dt == XMLSchema.dateTime.uriref():
                    w("%s:%s%s%s" % (propName, tlit, z, CRLF))
                elif dt == ICAL.dateTime.uriref():
                    if self.floatTZ:
                        w("%s;TZID=%s:%s%s%s" % (propName,
                                                 self.floatTZ, tlit, z, CRLF))
                    else:
                        w("%s:%s%s%s" % (propName, tlit, z, CRLF))
                else:
                    whenTZ = tzid(dt)
                    w("%s;VALUE=DATE-TIME;TZID=%s:%s%s" %  
                      (propName, str(whenTZ), tlit, CRLF))

    def doDuration(self, sts, r, propName, predName):
        w = self._w
        w(propName)

        related = sts.any(r, ICAL.related)
        if related: w(";RELATED=" + str(related))

        dur = sts.the(r, RDF.value)
        w(":" + str(dur))
        w(CRLF)


    def doRecur(self, sts, r, propName, predName):
        w = self._w
        w(propName + ":")
        freq = sts.any(r, ICAL.freq)
        if freq: w("FREQ=%s" % freq)
        else: raise ValueError, "no freq in recur"
        
        when = sts.any(r, ICAL.until)
        if when: w(";UNTIL=%s" % mkDATE(when))

        ival = sts.any(r, ICAL.count)
        if ival: w(";COUNT=%s" % ival)
        ival = sts.any(r, ICAL.interval)
        if ival: w(";INTERVAL=%s" % ival)
        by = sts.any(r, ICAL.byday)
        if by: w(";BYDAY=%s" % by)
        by = sts.any(r, ICAL.bymonthday)
        if by: w(";BYMONTHDAY=%s" % by)
        by = sts.any(r, ICAL.bymonth)
        if by: w(";BYMONTH=%s" % by)
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
                if sym is ICAL.dir: v = v.uriref()
                else: v = v.string.encode('utf-8')
                if ';' in v or ' ' in v or ':' in v:
                    #@@hmm... what if " in v?
                    w(";%s=\"%s\"" % (paramName, v))
                else:
                    w(";%s=%s" % (paramName, v))
        address = str(sts.the(who, ICAL.calAddress, None))

        # MAILTO seems to be capitalized in the iCalendar world. odd.
	# hmm... perhaps not in apple's world
        #if address.startswith("mailto:"):
        #    address = "MAILTO:" + address[7:]
        w(":" + address + "\n")


def componentOrder(a, b):
    return cmp(compKey(a), compKey(b))


def compKey(item):
    """extract a sort key from a component item
    
    >>> from myStore import formula, literal, symbol, existential
    >>> f=formula()
    >>> e1=symbol("http://example#e1")
    >>> w1=existential("t", f, None)
    >>> e2=symbol("http://example#e2")
    >>> w2=existential("t", f, None)
    >>> f.add(e1, ICAL.uid, literal("abcdef"))
    1
    >>> f.add(e1, ICAL.dtstart, w1)
    1
    >>> f.add(e2, ICAL.dtstart, w2)
    1
    >>> f.add(w1, ICAL.date, literal("2002-12-23"))
    1
    >>> f.add(w2, ICAL.dateTime, literal("2002-12-23T12:32:31Z"))
    1
    >>> compKey((f, e1, 'dummy', []))
    ('abcdef', '2002-12-23')
    >>> compKey((f, e2, 'dummy', []))
    (None, '2002-12-23T12:32:31Z')
    """

    # " help emacs

    sts, sub, subName, subs = item
    uid = sts.any(sub, ICAL.uid)
    if uid: uid = str(uid)
    when = sts.any(sub, ICAL.dtstart)
    if when:
        whenV = sts.any(when, ICAL.date)
        if whenV: when = str(whenV)
        else:
            whenV = sts.any(when, ICAL.dateTime)
            if whenV: when = str(whenV)
    return (uid, when)


def mkTEXT(val, fmla=None):
    # @@TODO: wrap at 75 cols
    try:
        text = val.string.encode('utf-8')
    except AttributeError:
        text = fmla.the(val, RDF.value).string.encode('utf-8')
    for c in ('\\', ';', ','):
        text = text.replace(c, "\\"+c)
    text = text.replace('\n', "\\n")
    return text

def mkINTEGER(val):
    i = int(str(val))
    return "%i" % i

def mkFLOAT(val):
    n = float(str(val))
    return "%f" % n

def mkDATE(val):
    """
    >>> mkDATE('2004-11-19')
    '20041119'
    """
    
    return translate(str(val), maketrans("", ""), "-:")


TZD = "http://www.w3.org/2002/12/cal/tzd/"

def tzid(tzi):
    """convert timezones from RdfCalendar norms to iCalendar norms

    ASSUME we're using one of the 2002/12/cal timezones. @@
    """
    
    rel = uripath.refTo(TZD, tzi)
    short = uripath.splitFrag(rel)[0]
    return "/softwarestudio.org/Olson_20011030_5/" + short


import sys, os
import uripath

def usage():
    print __doc__


def main(args):
    if not args[1:]:
        usage()
        sys.exit(1)

    c = CalWr(sys.stdout.write)
    if args[3:] and args[1] == '--floattz':
        tz = args[2]
        c.floatTZ = tz
        del args[1:3]

    addr = uripath.join("file:" + os.getcwd() + "/", args[1])
    
    progress("loading...", addr)

    sts = load(addr)

    progress("exporting...")
    c.export(sts, addr)


def _test():
    import doctest
    doctest.testmod()

def progress(*args):
    for i in args:
        sys.stderr.write(str(i))
    sys.stderr.write("\n")


def debug(*args):
    for i in args:
        sys.stderr.write(str(i))
    sys.stderr.write("\n")


if __name__ == '__main__':
    if '--test' in sys.argv: _test()
    else: main(sys.argv)


# $Log$
# Revision 2.38  2006-10-09 13:32:20  connolly
# refine the --floattz hack
#
# Revision 2.37  2006/10/03 05:31:23  connolly
# for --floattz, add timezone component by reading from the web
#
# Revision 2.36  2006/10/03 05:09:35  connolly
# add --floattz option to override timezone of floating events
#
# Revision 2.35  2006/07/13 23:04:10  connolly
# fix name clobbering with more than one value of a list-typed property
#
# Revision 2.34  2006/07/06 01:19:09  connolly
# support rdf:value on text fields
#
# Revision 2.33  2005/11/10 14:40:32  connolly
# updated duration handling
#
# Revision 2.32  2005/09/05 23:53:35  connolly
# handle bymonthday
#
# Revision 2.31  2005/08/26 15:21:35  connolly
# undo borken commit
#
# Revision 2.29  2005/04/18 14:33:25  connolly
# try not capitalizing mailto:
#
# Revision 2.28  2005/04/18 13:21:37  connolly
# handle non-ascii chars in attendee names
#
# Revision 2.27  2005/03/30 15:33:23  connolly
# switched namespace name to stop abusing the old one
#
# Revision 2.26  2005/03/19 14:10:46  connolly
# COUNT param
# timezones as datatypes
#
# Revision 2.25  2005/02/17 23:34:37  connolly
# each, not just any value, e.g. for EXDATE
#
# Revision 2.24  2005/02/17 23:02:27  connolly
# - sort components by uid, dtstart
# - sort properties by name
# - added --test arg to run doctest tests
# - pychecker fixes: warn() not imported,
# - got rid of wrapString() deadcode (though there's an @@ in mkTEXT)
#
# Revision 2.23  2004/11/13 17:02:58  connolly
# fixed punctuation of UNTIL; factored out mkDATE
# added --test option for doctest style testing
#
# Revision 2.22  2004/11/13 16:51:14  connolly
# added UNTIL support in doRecur (IOU a test)
#
# Revision 2.21  2004/09/08 15:46:05  connolly
# - update to using timezones as properties
# - kinda kludge converting timezone URIs to tzids
#
# Revision 2.20  2004/04/15 22:39:46  connolly
# integrated patch from SeanP:
# - adds support for list of float/int/text (e.g. GEO)
# - refactor doTEXT etc. as mkTEXT, doSIMPLE
#
# Revision 2.19  2004/04/09 22:19:44  connolly
# working on encoding issues in doTEXT.
# not sure this is exactly the right fix.
#
# Revision 2.18  2004/03/30 00:17:41  connolly
# found bug in INTERVAL handling while porting to rdflib
#
# Revision 2.17  2004/03/13 00:01:37  connolly
# fixed the punctuation of RECUR values
#
# Revision 2.16  2004/03/10 00:04:55  connolly
# slightly nicer error message
#
# Revision 2.15  2004/03/09 23:29:40  connolly
# removed non-ascii chars from copyright blurb
# reformatted changelog to 79chars
#
# Revision 2.14  2004/03/06 20:39:40  timbl
# added copyright blurb.
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
# Changed ONE newline to a CRLF, suspect many more should be changed.
# iCal needs both
#
# Revision 2.4  2004/01/29 21:09:16  timbl
# Added DTSTART and UID to events. iCal needs DTSTART it seems.
# Fixed VALUE=URI format.
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

