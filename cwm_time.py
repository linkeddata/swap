#! /usr/bin/env python 
#
#
# TODO:
# - extraction os fields should extend date time if necessary
#
# See http://www.python.org/doc/current/lib/module-time.html
#

import string
import re
import thing
import notation3    # N3 parsers and generators, and RDF generator
import isodate	    # Local, by mnot. implements <http://www.w3.org/TR/NOTE-datetime>


from thing import LightBuiltIn, Function, ReverseFunction, progress # here
import time, calendar # Python standard distribution


#TIME_NS_URI = "http://www.mnot.net/2002/02/25/time#"
TIME_NS_URI = "http://www.w3.org/2000/10/swap/time#"

#LITERAL_URI_prefix = "data:application/n3;"
#DATE_NS_URI = "http://www.mnot.net/2002/01/11/date#"

__version__ = "0.3"

DAY = 24 * 60 * 60

class BI_inSeconds(LightBuiltIn, Function, ReverseFunction):
    def evaluateObject(self, store, context, subj, subj_py):
        try:
            return store._fromPython(context, str(isodate.parse(subj_py)))
        except:
            return None

    def evaluateSubject(self, store, context, obj, obj_py):
	return store._fromPython(context, isodate.asString(int(obj_py)))


class BI_year(LightBuiltIn, Function):
    def evaluateObject(self, store, context, subj, subj_py):
        try:
            return store._fromPython(context, subj_py[:4])
        except:
            return None

class BI_month(LightBuiltIn, Function):
    def evaluateObject(self, store, context, subj, subj_py):
        try:
            return store._fromPython(context, subj_py[5:7])
        except:
            return None

class BI_day(LightBuiltIn, Function):
    def evaluateObject(self, store, context, subj, subj_py):
        try:
            return store._fromPython(context, subj_py[8:10])
        except:
            return None

class BI_hour(LightBuiltIn, Function):
    def evaluateObject(self, store, context, subj, subj_py):
        try:
            return store._fromPython(context, subj_py[11:13])
        except:
            return None

class BI_minute(LightBuiltIn, Function):
    def evaluateObject(self, store, context, subj, subj_py):
        try:
            return store._fromPython(context, subj_py[14:16])
        except:
            return None

class BI_second(LightBuiltIn, Function):
    def evaluateObject(self, store, context, subj, subj_py):
        try:
            return store._fromPython(context, subj_py[17:19])
        except:
            return None

tzone = re.compile(r'.*([-+]\d{1,2}:\d{2,2})')
class BI_timeZone(LightBuiltIn, Function):
    def evaluateObject(self, store, context, subj, subj_py):
	m = tzone.match(subj_py)
	if m == None: return None
	return store._fromPython(context, m.group(1))

class BI_dayOfWeek(LightBuiltIn, Function):
    def evaluateObject(self, store, context, subj, subj_py):
	weekdayZero = time.gmtime(0)[6]
	return store._fromPython(context,
		(weekdayZero + int(isodate.parse(subj_py)/DAY)) % 7 )


#
class BI_format(LightBuiltIn, Function):
    def evaluateObject(self, store, context, subj, subj_py):
	"""params are ISO time string, format string. Returns reformatted. Ignores TZ@@"""
        if thing.verbosity() > 80: progress("strTime:format input:"+`subj_py`)
        str, format = subj_py
        try:
            return store._fromPython(context, 
              time.strftime(format, time.gmtime(isodate.parse(str))))
        except:
            return None

#
class BI_gmTime(LightBuiltIn, Function):
    def evaluateObject(self, store, context, subj, subj_py):
	"""Subject is  (empty string for standard formatting or) format string.
	Returns formatted."""
        if thing.verbosity() > 80: progress("time:gmTime input:"+`subj_py`)
        format = subj_py
	if format =="" : format="%Y-%M-%dT%H:%m:%SZ"
        try:
            return store._fromPython(context, 
		time.strftime(format, time.gmtime(time.time())))
        except:
            return isodate.asString(time())

class BI_localTime(LightBuiltIn, Function):
    def evaluateObject(self, store, context, subj, subj_py):
	"""Subject is format string or empty string for std formatting.
	Returns reformatted. @@@@ Ignores TZ"""
        if thing.verbosity() > 80: progress("time:localTime input:"+`subj_py`)
        format = subj_py
	if format =="" : return store._fromPython(context,
		    isodate.asString(time.time()))
	return store._fromPython(context, 
              time.strftime(format, time.localtime(time.time())))



#  original things from mNot's cwm_time.py:
#
#  these ise Integer time in seconds from epoch.
#
class BI_formatSeconds(LightBuiltIn, Function):
    def evaluateObject(self, store, context, subj, subj_py):
	"""params are epoch-seconds time string, format string. Returns reformatted"""
        if thing.verbosity() > 80: progress("strTime:format input:"+`subj_py`)
        str, format = subj_py
        try:
            return store._fromPython(context, 
              time.strftime(format, time.gmtime(int(str))))
        except:
            return None

class BI_parseToSeconds(LightBuiltIn, Function):
    def evaluateObject(self, store, context, subj, subj_py):
        if thing.verbosity() > 80: progress("strTime:parse input:"+`subj_py`)
        str, format = subj_py
        try:
            return store._fromPython(context, 
              calendar.timegm(time.strptime(str, format)))
        except:
            return None




#  Register the string built-ins with the store
def register(store):
    str = store.internURI(TIME_NS_URI[:-1])
    str.internFrag("inSeconds", BI_inSeconds)
    str.internFrag("year", BI_year)
    str.internFrag("month", BI_month)
    str.internFrag("day", BI_day)
    str.internFrag("hour", BI_hour)
    str.internFrag("minute", BI_minute)
    str.internFrag("second", BI_second)
    str.internFrag("dayOfWeek", BI_dayOfWeek)
    str.internFrag("timeZone", BI_timeZone)
    str.internFrag("gmTime", BI_gmTime)
    str.internFrag("localTime", BI_localTime)
    str.internFrag("format", BI_format)
#    str.internFrag("parse", BI_parse)
    str.internFrag("formatSeconds", BI_formatSeconds)  # Deprocate?
    str.internFrag("parseToSeconds", BI_parseToSeconds)  # Deprocate?


# ends
