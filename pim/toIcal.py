#!/usr/bin/python
"""toIcal.py -- convert RDF to iCalendar syntax

USAGE:
  python toIcal.py foo.rdf > foo.ics
  python toIcal.py foo.n3 > foo.ics
  python toIcal.py http://example/foo.rdf > foo.ics

see also:
  RDF Calendar Workspace
  http://www.w3.org/2002/12/cal/

TODO:
  @@get rid of xprop stuff that's not grounded in URI space
  (i.e. most of the IANATOKEN stuff)
  @@exportGeneral seems too hairy. refactor, test.

"""

"""
References:

  Internet Calendaring and Scheduling Core Object Specification
                              (iCalendar)
  November 1998
  http://www.ietf.org/rfc/rfc2445.txt

  A quick look at iCalendar
  http://www.w3.org/2000/01/foo

$Id$

NOTE: see earlier work:
  http://www.w3.org/2002/01dc-nj/toICal.py

@@cite and use python style
@@use doctest
see changelog at end
"""

# Imports from standard python libraries
from string import strip, maketrans, translate, replace, lstrip, \
                   capitalize, upper, uppercase, rfind, split, join
import sys
try:
    reload (sys)
    sys.setdefaultencoding('iso-8859-1')
except:
    pass


# From SWAP http://www.w3.org/2000/10/swap/
from RDFSink import SUBJ, PRED, OBJ
from myStore import Namespace, load, setStore

# Global Constants:
IANATOKEN = 0 #@@huh? what is this? comment here, please
E_PARAM = 10
E_PROP = 11
ERR_NONE = 100
ERR_ALL = 101
ERR_FAIL = 102
ERR_TEMP = 103
CRLF = chr(13) + chr(10)

# Prints debugging messages:
VERBOSE = ERR_NONE

# store = llyn.RDFStore()   # Not necessary after 
# setStore(store)

# Namespaces
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
ICAL = Namespace('http://www.w3.org/2002/12/cal/ical#')


#@@added? that's for the cvs log, not for the code.
# ADDED: a dictionary mapping things (@@things?) to their possible symbols.
# @@ perhaps a doctest style unittest to show what's going on here?
symbolVals = {
        'ACTION':       [[ICAL.audio, 'AUDIO'],
                         [ICAL.email, 'EMAIL'],
                         [ICAL.display, 'DISPLAY'], 
                         [ICAL.procedure, 'PROCEDURE'],
                         [IANATOKEN,]],
        'CUTYPE':       [[ICAL.individual, 'INDIVIDUAL'], 
                         [ICAL.room, 'ROOM'],
                         [ICAL.group, 'GROUP'],
                         [ICAL.unknown, 'UNKNOWN'],
                         [ICAL.resource, 'RESOURCE'],
                         [IANATOKEN,]],
        'CLASS':        [[ICAL.public, 'PUBLIC'],
                         [ICAL.private, 'PRIVATE'],
                         [ICAL.confidential, 'CONFIDENTIAL'], 
                         [IANATOKEN,]],
        'ROLE':         [[ICAL.chair, 'CHAIR'],
                         [ICAL.reqParticipant, 'REQ-PARTICIPANT'],
                         [ICAL.optParticipant, 'OPT-PARTICIPANT'],
                         [ICAL.nonParticipant, 'NON-PARTICIPANT'],
                         [IANATOKEN,]],
       'TRANSP':        [[ICAL.opaque, 'OPAQUE'],
                         [ICAL.transparent, 'TRANSPARENT']],
       'PARTSTAT':      [[ICAL.needsAction, 'NEEDS-ACTION'],
                         [ICAL.accepted, 'ACCEPTED'],
                         [ICAL.declined, 'DECLINED']],
       'RSVP':          [[ICAL.true, 'TRUE'],
                         [ICAL.false, 'FALSE']],
       'RELATED':       [[ICAL.end, 'END'],
                         [ICAL.start, 'START']],
       'LANGUAGE':      [[IANATOKEN,]],
       'CN':            [[IANATOKEN,]],
       'DESCRIPTION':   [[IANATOKEN,]],
       'FMTTYPE':       [[IANATOKEN,]],
       'TZID':          [[IANATOKEN,]],
       'TZOFFSETFROM':  [[IANATOKEN,]],
       'TZOFFSETTO':    [[IANATOKEN,]],
       'TZNAME':        [[IANATOKEN,]],
       'SEQUENCE':      [[IANATOKEN,]],
       'COMMENT':       [[IANATOKEN,]],
       'CATEGORIES':    [[IANATOKEN,]],
       'UID':           [[IANATOKEN,]],
       'DURATION':      [[IANATOKEN,]],
       'SUMMARY':       [[IANATOKEN,]],
       'LOCATION':      [[IANATOKEN,]],
       'PRIORITY':      [[IANATOKEN,]],
       'STATUS':        [[ICAL.confirmed, 'CONFIRMED'], [IANATOKEN,]],
       'PRODID':        [[IANATOKEN,]],
       'VERSION':       [[IANATOKEN,]],
       'CALSCALE':      [[IANATOKEN,]],
       'METHOD':        [[IANATOKEN,]]
             }

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

            # ADDED:
            # grab PRODID, VERSION, CALSCALE, METHOD. 
            #; 'prodid' and 'version' are both REQUIRED,
            #; but MUST NOT occur more than once
            #; 'calscale' and 'method' are optional,
            #; but MUST NOT occur more than once
            # -- 4.6 Calendar Components http://www.ietf.org/rfc/rfc2445.txt
            # @@ check for number of occurances? (cf. llyn.the)

            self.exportGeneral(E_PROP, sts, cal, ICAL.prodid, "PRODID")
            self.exportGeneral(E_PROP, sts, cal, ICAL.version, "VERSION")
            self.exportGeneral(E_PROP, sts, cal, ICAL.calscale, "CALSCALE")
            ##hmm... method? cf 3.2 Parameters
            ## added: METHOD handler; @@ sync with MIME method parameter?
            ## should be safe to include METHOD separate of method parameter...
            self.exportGeneral(E_PROP, sts, cal, ICAL.method, "METHOD")

            #ADDED:write X- fields outside of any component
            self.exportXFields(sts, cal)

            for comp in sts.each(subj = cal, pred = ICAL.component):
                if sts.statementsMatching(RDF.type, comp, ICAL.Vevent):
                    self.exportEvent(sts, comp)
                elif sts.statementsMatching(RDF.type, comp, ICAL.Vtimezone):
                    self.exportTimezone(sts, comp)
                elif sts.statementsMatching(RDF.type, comp, ICAL.Vtodo):
                    self.exportTodo(sts, comp)
                else:
                    progress("@@skipping component with types: ",
                             sts.each(subj = comp, pred = RDF.type))
        
            w("END:VCALENDAR" + CRLF)
	#enddef export

    #ADDED:
    def exportXFields(self, sts, subj):
        """ support for any nodes in the x: namespace

        @@ this is an ugly hack and an abstraction violation!
        but it works. :)

        it depends on the X- namespace being named 'x'. 

        @@ does ical2rdf.pl strip any xparam and
        languageparam property parameters? 

        see http://www.ietf.org/rfc/rfc2445.txt 4.8.8.1
        """
        w = self._w

        # pred subj obj
        nodes = sts.statementsMatching(None, subj, None)
        for n in nodes:
            if str(n[1])[0:2] == "x:": 
                # strip the x:, so xstr looks like fooBarBlah
                xstr = str(n[1])[2:]
                xstr = "X-" + self.unCamel(xstr)
                # the actual data is in the node's third list item
                w(xstr + ":" + str(n[3]) + "\n") 
	#enddef exportXFields #@@ ew. let's stick to python styleguide
    
    def unCamel(self, xstr):
        """a procedure to reverse-camel a string

	@@ why is this a method? I don't see any reference to self.
	@@ odd algorithm... seems to do a lot of work twice.

        ical2rdf.pl performs camelCase() on X- attributes. namely,
        (1) it strips '-' characters, (2) tokenizes the stuff in between
        (3) and joins it, either capitalizing: 
            (a) the first letter of every word, or
            (b) all first letters except the initial one.
        ex: X-FOO-BAR-BLAH becomes fooBarBlah or FooBarBlah.
        note: this isn't technically a camelCase.
         -- http://c2.com/cgi/wiki?CamelCase

        also used in timeProp() now (cf. lastModified)
        """
        # xstr looks like fooBarBlah
        xtab = maketrans(uppercase, "-"*26)
        ystr = translate(xstr, xtab)
        # now, ystr looks like -oo-ar-lah; fix missing letters
        # look for -; replace "-lah" with " Blah"
        # rfind returns -1 with no occurances
        yind = ystr.rfind("-")  
        while yind > -1:
            ystr = ystr[0:yind] + " " + xstr[yind:yind+1] \
                   + ystr[yind+1:]
            yind = ystr.rfind("-") 
        # have "Foo Bar Blah", possibly a leading space if 
        # xstr was originally capitalized. strip leading space:
        ystr = lstrip(ystr)
        ywords = split(ystr, " ")
        ystr = upper(join(ywords, "-"))
        return ystr

    def exportTimezone(self, sts, tz):
        """ support for VTIMEZONE components """
        w = self._w
        
        w("BEGIN:VTIMEZONE" + CRLF)

        self.exportGeneral(E_PROP, sts, tz, ICAL.tzid, "TZID")

        for subcomp in sts.each(subj = tz, pred = ICAL.standard):
            self.exportTZSub(sts, subcomp, 'standard')
        for subcomp in sts.each(subj = tz, pred = ICAL.daylight):
            self.exportTZSub(sts, subcomp, 'daylight')

        self.exportXFields(sts, tz)
        self.exportGeneral(E_PROP, sts, tz, ICAL.comment, "COMMENT")
        w("END:VTIMEZONE" +CRLF)
    #enddef exportTimezone

    def exportTZSub(self, sts, tzs, n):
        """ helper function for VTIMEZONE component properties """
        w = self._w

        w("BEGIN:%s%s" % (n, CRLF))
        # the next three fields are of type UTC-OFFSET but we treat
        # them as strings.
        self.exportGeneral(E_PROP, sts, tzs, 
                           ICAL.tzoffsetfrom, "TZOFFSETFROM")
        self.exportGeneral(E_PROP, sts, tzs, 
                           ICAL.tzoffsetto, "TZOFFSETTO")
        self.exportGeneral(E_PROP, sts, tzs, ICAL.tzname, "TZNAME")
        self.timeProp(sts, "dtstart", tzs)
        self.recurProp(sts, "rrule", tzs)
        w("END:%s%s" % (n, CRLF))
    #enddef exportTZSub

	# ADDED:
    def exportAlarm(self, sts, alarm):
        """ support for the VALARM component
        @@ incomplete! @@how so?
        -- 4.6.6 http://www.ietf.org/rfc/rfc2445.txt
        """
        w = self._w
        
        w("BEGIN:VALARM" +CRLF)
        # ADDED: action -- 4.8.6.1
        self.exportGeneral(E_PROP, sts, alarm, ICAL.action, "ACTION")
        self.exportGeneral(E_PROP, sts, alarm, ICAL.attach, "ATTACH")
        self.exportGeneral(E_PROP, sts, alarm, ICAL.repeat, "REPEAT")
        self.exportGeneral(E_PROP, sts, alarm, ICAL.summary, "SUMMARY")
        self.exportGeneral(E_PROP, sts, alarm, ICAL.duration, "DURATION")
        self.exportGeneral(E_PROP, sts, alarm, ICAL.description, "DESCRIPTION")
        self.exportTrigger(sts, alarm)
        self.exportXFields(sts, alarm)
        self.exportAttach(sts, alarm)
        w("END:VALARM" +CRLF)
    #enddef exportAlarm


    def exportTodo(self, sts, comp):
        """ see test
        http://www.w3.org/2002/12/cal/test/todo1.rdf
        """
        
        w = self._w

        w("BEGIN:VTODO"+CRLF)
        self.timeProp(sts, "dtstart", comp)
        self.exportGeneral(E_PROP, sts, comp, ICAL.summary, "SUMMARY")
        self.exportGeneral(E_PROP, sts, comp, ICAL.uid, "UID")
        self.exportGeneral(E_PROP, sts, comp, ICAL.description, "DESCRIPTION")
        self.exportGeneral(E_PROP, sts, comp, ICAL.location, "LOCATION")
        self.exportGeneral(E_PROP, sts, comp, ICAL.priority, "PRIORITY")
        self.exportGeneral(E_PROP, sts, comp, ICAL.status, "STATUS")
        self.timeProp(sts, "completed", comp)


        # notes on 4.8.4.6 Uniform Resource Locator
        # http://www.w3.org/2002/12/cal/rfc2445#sec4.8.4.6
        #
        # This is very muddled modelling; url makes sense as
        # a value type, but not as a property name. It's a grab-bag
        # for concepts like foaf:homePage, dc:related (which
        # is another grab bag) etc.
        self.refProp(sts, comp, "url")

        w("END:VTODO"+CRLF)

        
    def exportEvent(self, sts, event):
        """ support for VEVENT components """
        w = self._w

        w("BEGIN:VEVENT"+CRLF)
		# ADDED: @@ sequence must be an integer. write intProp()?
		# -- 4.8.7.4 Sequence Number http://www.ietf.org/rfc/rfc2445.txt
        self.exportGeneral(E_PROP, sts, event, ICAL.sequence, "SEQUENCE")
        # ADDED: comment:
        # @@ handle property parameters?
		# -- 4.8.1.4 http://www.ietf.org/rfc/rfc2445.txt
        self.exportGeneral(E_PROP, sts, event, ICAL.comment, "COMMENT")
        # ADDED: transp: 
        self.exportGeneral(E_PROP, sts, event, ICAL.transp, "TRANSP")
        # ADDED: class:
        self.exportGeneral(E_PROP, sts, event, ICAL.sym("class"), "CLASS")
        # ADDED: categories
        self.exportGeneral(E_PROP, sts, event, ICAL.categories, "CATEGORIES")
        # ADDED: organizer
        # rfc doesn't say how many times it can appear per commponent,
        # assuming once. @@ does mention that it must appear in some cases.
        # -- 4.8.4.3 http://www.ietf.org/rfc/rfc2445.txt 
        self.exportOrganizer(sts, event)
        # ADDED: attendee
        # @@ annoyingly complex set of context requirements for when
        # attendee and its parameters can be used. i haven't accounted
        # for any of it.
        # -- 4.8.4.1 http://www.ietf.org/rfc/rfc2445.txt 
        self.exportAttendee(sts, event)
        # ADDED: attach
        # -- 4.8.1.1 http://www.ietf.org/rfc/rfc2445.txt 
        self.exportAttach(sts, event)
        # ADDED: valarm
        # -- 4.6.6 http://www.ietf.org/rfc/rfc2445.txt 
        for alarm in sts.each(subj = event, pred = ICAL.valarm):
            self.exportAlarm(sts, alarm)

        self.exportGeneral(E_PROP, sts, event, ICAL.uid, "UID")

        # 4.8.2.4 Date/Time Start
        self.timeProp(sts, "dtstart", event)
        self.timeProp(sts, "dtend", event)
        self.exportGeneral(E_PROP, sts, event, ICAL.duration, "DURATION")
        self.timeProp(sts, "dtstamp", event)
        self.timeProp(sts, "lastModified", event) 
        self.exportGeneral(E_PROP, sts, event, ICAL.summary, "SUMMARY")
        self.exportGeneral(E_PROP, sts, event, ICAL.description, "DESCRIPTION")
        self.exportGeneral(E_PROP, sts, event, ICAL.location, "LOCATION")
        self.exportGeneral(E_PROP, sts, event, ICAL.priority, "PRIORITY")
        self.exportGeneral(E_PROP, sts, event, ICAL.status, "STATUS")
        self.refProp(sts, event, "url")
        self.recurProp(sts, "rrule", event)

        self.exportXFields(sts, event)

        # pred subj obj
        other = sts.statementsMatching(None, event, None)
        #ADDED: some support types to the list. check for x: 
        for s in other:
            if s[PRED] not in (ICAL.dtstart, ICAL.dtend, ICAL.duration,
                               ICAL.lastModified, ICAL.dtstamp,
                               ICAL.uid, ICAL.summary, ICAL.description,
                               ICAL.location, ICAL.priority,
                               RDF.type, ICAL.sequence, ICAL.comment, 
                               ICAL.transp, ICAL.sym("class"), 
                               ICAL.categories, ICAL.organizer, 
                               ICAL.attendee, ICAL.valarm,
                               ICAL.status,
                               ICAL.rrule, ICAL.url) and \
               str(s[1])[0:2] != "x:": 
                progress("@@skipping ", s[PRED], " of [", '@@txt', "] = [", \
                                 s[OBJ], "]")
        w("END:VEVENT"+CRLF)
    #enddef exportEvent

    # ADDED:
    def exportOrganizer(self, sts, subj):
        """ support for the ICAL.organizer node

        spec doesn't seem to say explicitly whether it can only appear 
        once or not... assuming it can only appear once from
        ``the organizer''

        this export is a little different than the other exports like
        exportClass and exportTransp; we have to search the organizer
        subnode for its properties.

        @@ doesn't handle xparam

        -- 4.8.4.3 http://www.ietf.org/rfc/rfc2445.txt 
		CAL-ADDRESS -- 4.3.3
        """
        w = self._w

        # pred subj obj
        nodes = sts.statementsMatching(ICAL.organizer, subj, None)   

        # @@ there are some situations where organizer is required
        if len(nodes) == 0: return 

        for n in nodes:
            w("ORGANIZER")
            # @@ abstraction violation: n[3] seems to be the 
            # organizer node
            self.exportGeneral(E_PARAM, sts, n[3], ICAL.cn, "CN")
            self.exportGeneral(E_PARAM, sts, n[3], ICAL.dir, "DIR")
            self.exportGeneral(E_PARAM, sts, n[3], ICAL.sentBy, "SENT-BY")
            self.exportGeneral(E_PARAM, sts, n[3], ICAL.language, "LANGUAGE")

            self.exportCalAddress(sts, n[3])
    # enddef exportOrganizer

    # ADDED:
    def exportAttendee(self, sts, subj):
        """ support for the ICAL.attendee node

        makes sense for ICAL.attendee to appear multiple times
        this is similar to ICAL.organizer

        @@ only partially implemented! need to take care of
        member, delegated-to, delegated-from, sent-by parameters
        (really delegated-to and delegated-from are the hard ones)
        this will also require parallel hacking in $CAL/ical2rdf.pl
        to get it to match comma-separated calAddress lists ;(

        @@ doesn't handle xparam

        -- 4.8.4.1 http://www.ietf.org/rfc/rfc2445.txt 
		CAL-ADDRESS -- 4.3.3
        """
        w = self._w

        # pred subj obj
        nodes = sts.statementsMatching(ICAL.attendee, subj, None)   

        # @@ there are some situations where organizer is required
        if len(nodes) == 0: return 

        for n in nodes:
            w("ATTENDEE")
            # @@ abstraction violation: n[3] seems to be the 
            # organizer node
            self.exportGeneral(E_PARAM, sts, n[3], ICAL.cn, "CN")
            self.exportGeneral(E_PARAM, sts, n[3], ICAL.cn, "DIR")
            self.exportGeneral(E_PARAM, sts, n[3], ICAL.role, "ROLE")
            self.exportGeneral(E_PARAM, sts, n[3], ICAL.rsvp, "RSVP")
            self.exportGeneral(E_PARAM, sts, n[3], ICAL.cutype, "CUTYPE")
            self.exportGeneral(E_PARAM, sts, n[3], ICAL.partstat, "PARTSTAT")
            self.exportGeneral(E_PARAM, sts, n[3], ICAL.language, "LANGUAGE")

            self.exportCalAddress(sts, n[3])
    # enddef exportAttendee

    # ADDED: 
    def exportTrigger(self, sts, subj):
        """ support for the ICAL.trigger node

        @@ doesn't handle xparam

		trigger must appear once in valarm
        -- 4.8.6.3 http://www.ietf.org/rfc/rfc2445.txt 
        """
        w = self._w

        # subj pred obj
        trigger = sts.the(subj, ICAL.trigger, None)   
        w("TRIGGER")

        # pred subj obj
        nodes = sts.statementsMatching(ICAL.duration, trigger, None)
        if(nodes): w(";VALUE=DURATION")
        else: 
            nodes = sts.statementsMatching(ICAL.dateTime, trigger, None)
            if(nodes): w(";VALUE=DATE-TIME")

        self.exportGeneral(E_PARAM, sts, trigger, ICAL.related, "RELATED")

        w(":" + str(nodes[0][3]) + "\n")
    # enddef exportTrigger

    # ADDED: 
    def exportAttach(self, sts, subj):
        """ support for the ICAL.attach node

        -- 4.8.1.1 http://www.ietf.org/rfc/rfc2445.txt 
        """
        w = self._w

        # pred subj obj
        nodes = sts.statementsMatching(ICAL.attach, subj, None)   
        for n in nodes:
            w("ATTACH")
            # pred subj obj
            self.exportGeneral(E_PARAM, sts, subj, ICAL.fmttype, "FMTTYPE")
            w(":" + str(n[3]) + "\n")
    # enddef exportTrigger

    # ADDED:
    def exportGeneral(self, outtype, sts, subj, pred, pref):
        """ a general function to export ICAL params and properties 

        @@ abstraction violation: the value of the param seems
        to be in subnodes[0][3]
        """
        def egWrite(w, outtype, pref, val):
            """ a helper function to write exportGeneral values """
            if outtype == E_PARAM:
                v = ";" + pref + "=" + val 
            elif outtype == E_PROP:
                v = pref + ":" + val + CRLF
            w(self.wrapString(v, 75)) #@@magic number. move to top. does it come from the RFC?
        #enddef egWrite

        w = self._w

        # pred subj obj
        subnodes = sts.statementsMatching(pred, subj, None) 
        if len(subnodes) <= 0: 
            debug("exportGeneral: " + pref + " No statements found!", ERR_FAIL)
            return # @@when is this not ok?

        # else: found some subnodes
        m = subnodes[0][1]
        n = subnodes[0][3]
        debug("exportGeneral: Looking for " + str(n), ERR_ALL)

        # the new modular way to accomplish exporting. 
        # see symbolVals
        found_sv = 0
        text_allowed = 0
        if symbolVals.has_key(pref): 
            for sv in symbolVals[pref]:
                debug("  Comparing to " + str(sv[0]), ERR_ALL)
                if n == sv[0]: 
                    debug("    Success!", ERR_ALL)
                    found_sv = 1
                    egWrite(w, outtype, pref, sv[1])
                elif sv[0] == IANATOKEN: 
                    debug("    iana-tokens allowed", ERR_ALL)
                    text_allowed = 1
            if not found_sv and text_allowed:
                egWrite(w, outtype, pref, str(n))
            elif not found_sv: 
                progress("Field '" + pref
                         + "' has invalid value: " 
                         + str(n))
        elif pred == ICAL.dir: # special case 4.2.6
            # the DIR node is a uri, which is an rdf:resource
            # see cal02.ics; it works now.
            subnodes = sts.statementsMatching(ICAL.uri, n, None) 
            egWrite(w, E_PARAM, pref, '"'+subnodes[0][3].uriref()+'"')
    #enddef exportGeneral

    def wrapString(self, str, slen):
        """ helper function to wrap a string iCal-style
	@@ why is this a method? I don't see any reference to self.
	"""
        #@@linebreaks? <-- what did this comment mean?
        x = ''
        while(len(str) > slen):
            x += str[0:slen-1] + CRLF + ' '
            str = str[slen-1:]
        x += str
        return x

    # ADDED:
    def exportCalAddress(self, sts, subj):
        """ helper function to output a calAddress node """
        w = self._w

        # there must be a calAddress; use the() (might totally bail!)
        # @@ use statementsMatching instead?
        # subj pred obj
        address = str(sts.the(subj, ICAL.calAddress, None))
        # MAILTO should be capitalized
        if address[:6] == "mailto": 
            address = "MAILTO" + address[6:]
        w(":" + address + "\n")
    #enddef exportCalAddress

    def refProp(self, sts, subj, pn):
        """ handle reference properties
        i.e. properties with value type URI
        
        http://www.w3.org/2002/12/cal/rfc2445#sec4.3.13

        @@perhaps add support for example from 4.2.8 Format Type
        http://www.w3.org/2002/12/cal/rfc2445#sec4.2.8

        ATTACH;FMTTYPE=application/binary:ftp://domain.com/pub/docs/agenda.doc
        """

        sym  = sts.any(subj, ICAL.sym(pn))
        if sym:
            w = self._w
            uri = sym.uriref() #@@need to encode non-ascii chars
				# iCal won't take spaces.
	    uri = hexify(uri)
            w("%s;VALUE=URI:%s%s" % (pn.upper(), uri, CRLF))


    def recurProp(self, sts, pn, subj):
        """ helper function to output an RRULE node """
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
    #enddef recurProp

    def timeProp(self, sts, pn, subj):
        """ helper function to output general date value"""
        w = self._w

        when = sts.any(subj, ICAL.sym(pn))
        if when:
            whenV = sts.any(when, ICAL.dateTime)
            if whenV:
                whenV = translate(str(whenV), maketrans("", ""), "-:")
                whenTZ = sts.any(when, ICAL.tzid)
                if whenTZ:
                    w("%s;VALUE=DATE-TIME;TZID=%s:%s%s" %  
                      (self.unCamel(pn), str(whenTZ), whenV, CRLF))
                else:
		    z = ""
		    if whenV[-1:] == "Z":
			z = "Z"
			whenV = whenV[:-1]
		    whenV = (whenV + "000000")[:15] # Must include seconds
                    w("%s:%s%s%s" % (self.unCamel(pn), whenV, z, CRLF))
            else:
                whenV = sts.any(when, ICAL.date)
                if whenV:
                    whenV = translate(str(whenV), maketrans("", ""), "-:")
                    w("%s;VALUE=DATE:%s%s" % (self.unCamel(pn), whenV, CRLF))
                else:
                    progress("@@no ical:dateTime or ical:date for ", when)
    #enddef timeProp

def hexify(ustr):
    """Use URL encoding to return an ASCII string corresponding to the given unicode"""
#    progress("String is "+`ustr`)
#    s1=ustr.encode('utf-8')
    str  = ""
    for ch in ustr:  # .encode('utf-8'):
	if ord(ch) > 126 or ord(ch) <33:
	    ch = "%%%02X" % ord(ch)
	else:
	    ch = "%c" % ord(ch)
	str = str + ch
    return str
    

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
    verbosity = args[-1:][0]
    args = args[:-1]
    if ((verbosity == ERR_FAIL  
         and (VERBOSE == ERR_ALL or VERBOSE == ERR_FAIL))
       or (verbosity == ERR_ALL and VERBOSE == ERR_ALL)
       or verbosity == ERR_TEMP):
        for i in args:
            sys.stderr.write(str(i))
        sys.stderr.write("\n")

def errorOut(*args):
    for i in args:
        sys.stderr.write(str(i))
    sys.stderr.write("\n")
    raise ValueError

import diag
diag.setVerbosity(0)

if __name__ == '__main__':
    main(sys.argv)


# $Log$
# Revision 2.11  2004-02-04 17:57:07  timbl
# Passes regresion tests. see admin/N3-Bugs.ics for oustanding bugs
#
# Revision 2.10  2004/02/03 22:55:33  timbl
# mmm
#
# Revision 2.9  2004/02/02 19:38:56  timbl
# re-fix after spurious clash
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

