#!/usr/bin/python
"""Download GPS data from serial link

This is an RDF application.

See also Morten F's http://www.wasab.dk/morten/2003/10/garmin2rdf.py

$Id$
"""

# Regular python library
import os, sys, time

# SWAP  http://www.w3.org/2000/10/swap
from myStore import Namespace, formula, symbol, intern, bind
from diag import progress
import uripath
from uripath import join, base
from notation3 import RDF_NS_URI
import notation3    	# N3 parsers and generators
import isodate  # for isodate.fullString

# import toXML 		#  RDF generator

# PyGarmon  http://www
from garmin import Win32SerialLink, Garmin, UnixSerialLink, degrees, TimeEpoch, \
    TrackHdr



RDF = Namespace(RDF_NS_URI)
# RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
GPS = Namespace("http://hackdiary.com/ns/gps#")
bind("gps", "http://hackdiary.com/ns/gps#")  # Suggest as prefix in RDF file
WGS =  Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")
bind("wgs84",  "http://www.w3.org/2003/01/geo/wgs84_pos#")

monthName= ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


rdf_type = RDF.type


#########  Get GPS Data

def doCommand(serialDevice=None, outputURI=None, doWaypoints=1, doTracks=1, verbose=0):

   if os.name == 'nt':
      if not serialDevice: serialDevice =  "com1"
      phys = Win32SerialLink(serialDevice)
   else:
      if not serialDevice:  serialDevice =  "/dev/ttyS0"
#      serialDevice =  "/dev/cu.USA19H191P1.1"
      phys = UnixSerialLink(serialDevice)
      
   gps = Garmin(phys)

   print "GPS Product ID: %d Descriptions: %s Software version: %2.2f" % \
         (gps.prod_id, gps.prod_descs, gps.soft_ver)


   f = formula() # Empty store of RDF data
   base = uripath.base()
   
   record = f.newBlankNode()
   f.add(record, RDF.type, GPS.Record)

   if doWaypoints:
        # show waypoints
        wpts = gps.getWaypoints()
        for w in wpts:
	    if verbose: progress(`w`)
	    wpt = symbol(uripath.join(base, w.ident))
	    f.add(record, GPS.waypoint, wpt)
	    f.add(wpt, GPS.lat, obj=intern(degrees(w.slat)))
	    f.add(wpt, GPS.long, obj=intern(degrees(w.slon)))


   if doTracks:
      # show track
      tracks = gps.getTracks()
      for t in tracks:
	track = f.newBlankNode()
	f.add(record, GPS.track, track)
	for p in t:
	    if isinstance(p, TrackHdr):
		if verbose: progress(`p`)
		f.add(track, GPS.disp, intern(p.dspl))
		f.add(track, GPS.color, intern(p.color))
		f.add(track, GPS.trk_ident, intern(p.trk_ident))
	    else:
		if verbose: progress(`p`)
		point = f.newBlankNode()
		f.add(track, GPS.trackpoint, point)
		f.add(point, GPS.lat, obj=intern(degrees(p.slat)))
		f.add(point, GPS.long, obj=intern(degrees(p.slon)))
#		if verbose: progress("    time=", p.time)
		if p.time == 0 or p.time == 0xffffffffL:
		    if verbose: progress("time=%8x, ignoring" % p.time)
		f.add(point, GPS.time, obj=intern(isodate.fullString(TimeEpoch+p.time)))


   f = f.close()
   if verbose:
	progress("Beginning output")
   s = f.n3String(base=base, flags="d")   # Flag - no default prefix
   if outputURI != None:
	op = open(outputURI, "w")
	op.write(s)
	op.close()
   else:
	print s 


        
############################################################ Main program
    
if __name__ == '__main__':
    import getopt
    verbose = 0
    outputURI = "gpsData.n3"
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvd:o:",
	    ["help",  "verbose", "device=", "output="])
    except getopt.GetoptError:
        # print help information and exit:
        print __doc__
        sys.exit(2)
    output = None
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-v", "--verbose"):
	    verbose = 1
        if o in ("-d", "--device"):
            deviceName = a
        if o in ("-o", "--output"):
            outputURI = a

    doCommand(serialDevice=deviceName, outputURI=outputURI, verbose=verbose)

