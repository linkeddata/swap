#!/usr/bin/python
"""Download GPS data from serial link

This is an RDF application.

See also Morten F's http://www.wasab.dk/morten/2003/10/garmin2rdf.py

$Id$
"""

# Regular python library
import os, sys, time

# SWAP  http://www.w3.org/2000/10/swap
from myStore import Namespace, formula, symbol, intern, bind, load
from diag import progress
import uripath
from notation3 import RDF_NS_URI
import notation3    	# N3 parsers and generators
import isodate  # for isodate.fullString

# import toXML 		#  RDF generator

# PyGarmon  http://www
#from garmin import Win32SerialLink, Garmin, UnixSerialLink, degrees, TimeEpoch, \
#    TrackHdr



RDF = Namespace(RDF_NS_URI)
# RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
GPS = Namespace("http://hackdiary.com/ns/gps#")
bind("gps", "http://hackdiary.com/ns/gps#")  # Suggest as prefix in RDF file
WGS =  Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")
bind("wgs84",  "http://www.w3.org/2003/01/geo/wgs84_pos#")

EXIF = Namespace("http://www.w3.org/2000/10/swap/pim/exif#")
FILE = Namespace("http://www.w3.org/2000/10/swap/pim/file#")

monthName= ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


rdf_type = RDF.type


def compareByTime(a, b):
    if a[0] < b[0]: return -1
    if a[0] > b[0]: return +1
    return 0


############################################################ Main program
    
if __name__ == '__main__':
    import getopt
    verbose = 0
    gpsData = "/Users/timbl/Documents/2004/02/17" # root of data
    outputURI = "correlation.n3"
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvg:o:",
	    ["help",  "verbose", "gpsData=", "output="])
    except getopt.GetoptError:
        # print help information and exit:
        print __doc__
        sys.exit(2)
    output = None
    for o, a in opts:
        if o in ("-h", "--help"):
            print __doc__
            sys.exit()
        if o in ("-v", "--verbose"):
	    verbose = 1
        if o in ("-g", "--gpsData"):
            gpsData = a
        if o in ("-o", "--output"):
            outputURI = a

    if verbose: progress( "Loading Photo data...")
    f = load(gpsData  + "/PhotoMeta.n3")
    if verbose: progress( "Loaded.")
    ss = f.statementsMatching(pred=FILE.date)
    events = []
    for s in ss:
	ph = s.subject()
	photo = str(ph)
	date = str(s.object())
	da = f.any(subj=ph, pred=EXIF.dateTime)
	if da != None:
	    date = str(da)
	else:
	    progress("Warning: using file date %s for %s" %(date, photo))
	events.append((date, "P", (ph, photo)))
	if verbose: progress("%s: %s" %(date, photo))
    
#    photos.sort()

    if verbose: progress( "Loading GPS data...")
    f = load(gpsData + "/gpsData.n3")
    if verbose: progress( "Loaded.")
    records = f.each(pred=rdf_type, obj=GPS.Record)
    progress( `len(records)`, "records")
#    trackpoints = []
    for record in records:
	tracks = f.each(subj=record, pred=GPS.track)
	progress ("  ", `len(tracks)`, "tracks")
	for track in tracks:
	    points = f.each(subj=track, pred=GPS.trackpoint)
	    for point in points:
		t = str(f.the(subj=point, pred=GPS.time))
		la = str(f.the(subj=point, pred=GPS.lat))
		lo = str(f.the(subj=point, pred=GPS.longitude))
		events.append((t, "T", (la, lo)))

    events.sort(compareByTime)
    
    last = None
    n = len(events)

    if verbose: progress( "First event:" , `events[0]`, "Last event:" , `events[n-1]`)

    conclusions = formula()
    for i in range(n):
	dt, ty, da = events[i]
	if ty == "T": # Trackpoint
	    last = i
	elif ty == "P":
	    ph, photo = da
	    if last == None:
		progress("%s: Photo %s  before any trackpoints" %(dt, photo))
		continue
	    j = i+1
	    while j < n:
		dt2, ty2, da2 = events[j]
		if ty2 == "T": break
		j = j+1
	    else:
		progress( "%s: Photo %s off the end of trackpoints"% (dt, photo))
		continue
	    t = isodate.parse(dt)
	    dt1, ty1, (la1, lo1) = events[last]
	    lat1, long1 = float(la1), float(lo1)
	    t1 = isodate.parse(dt1)
	    dt2, ty2, (la2, lo2) = events[j]
	    lat2, long2 = float(la2), float(lo2)
	    t2 = isodate.parse(dt2)
	    delta = t2-t1
	    progress( "%s: Photo %s  between trackpoints %s and %s" %(dt, da, dt1, dt2))
#	    print "    Delta", delta, "seconds between", events[last], "and", events[j]
	    a = (t - t1) / (t1-t2)
	    lat = lat1 +  a * (lat2-lat1)
	    long = long1 + a * (long2-long1)
	    progress( "%s: Before (%f, %f)" % (dt1, lat1, long1))
	    progress( "%s: Guess  (%f, %f)" % (dt, lat, long))
	    progress( "%s: After  (%f, %f)" % (dt2, lat2, long2))
	    
	    where = conclusions.newBlankNode()
	    conclusions.add(ph, GPS.approxLocation, where)
	    conclusions.add(where, GPS.lat, f.newLiteral("%f" % lat))
	    conclusions.add(where, GPS.longitude, f.newLiteral("%f" % long))

#	    guess = isodate.fullString(...)

    progress("Start Output")
    print conclusions.close().n3String()
    

    