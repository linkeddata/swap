#!/usr/bin/env python

""" As provided by Guido in response to a question on c.l.p """
#  Not needed --- now since pyuthon 2 this exists in the calendar module
#

def timegm(tmtuple):
	''' returns epoch seconds from a GMT time tuple. '''
	import calendar
	EPOCH = 1970
	year, month, day, hour, minute, second = tmtuple[:6]
	if year < EPOCH:
		if year < 69:
			year = year + 2000
		else:
			year = year + 1900
		if year < EPOCH:
			raise ValueError, 'invalid year'
	if not 1 <= month <= 12:
		raise TypeError, 'invalid month'
	days = 365 * (year-EPOCH) + calendar.leapdays(EPOCH, year)
	for i in range(1, month):
		days = days + calendar.mdays[i]
	if month > 2 and calendar.isleap(year):
		days = days + 1
	days = days + day - 1
	hours = days * 24 + hour
	minutes = hours * 60 + minute
	seconds = minutes * 60 + second
	return seconds
		
