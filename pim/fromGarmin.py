#!/usr/bin/python
"""Download GPS data from serial link to an RDF/N3 file.

Options:
 -d=xxx --device=xxx     Device GPS is attached to, eg /dev/cu.KeySerial1  com1 etc
 -o=xxx --output=xxx     Output filename required, default is gpsData.n3
 -v     --verbose        Print data between reading GPS and writing file
 -t     --tracks         Get tracks from the GPS
 -w     --waypoints      Get waypoints from the GPS
 -h     --help           Print this message
 
If neither --tracks or --waypoints are asked for, nothing will happen.

This is an RDF application.
See also Morten F's http://www.wasab.dk/morten/2003/10/garmin2rdf.py
$Id$
"""

# Regular python library
import os, sys, time

# SWAP  http://www.w3.org/2000/10/swap

#import swap
from swap.myStore import Namespace, formula, symbol, intern, bind
from swap.diag import progress
from swap import uripath
from swap.uripath import join, base
from swap.notation3 import RDF_NS_URI
import swap.notation3           # N3 parsers and generators
from swap import isodate  # for isodate.fullString

# import toXML          #  RDF generator

# PyGarmon  http://pygarmin.sourceforge.net/
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

def doCommand(serialDevice=None, outputURI=None, doTracks=1, doWaypoints=1, verbose=0):

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
        if verbose: print "Getting waypoints"
        wpts = gps.getWaypoints()
        for w in wpts:
            if verbose: progress(`w`)
            wpt = symbol(uripath.join(base, w.ident))
            f.add(record, GPS.waypoint, wpt)
            f.add(wpt, WGS.lat, obj=intern(degrees(w.slat)))
            f.add(wpt, WGS.long, obj=intern(degrees(w.slon)))


   if doTracks:
      # show track
      if verbose: print "Getting tracks"
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
                f.add(point, WGS.lat, obj=intern(degrees(p.slat)))
                f.add(point, WGS.long, obj=intern(degrees(p.slon)))
#               if verbose: progress("    time=", p.time)
#                progress('p.time='+`p.time`) # @@
                if p.time == 0 or p.time == 0xffffffffL:
                    if verbose: progress("time=%8x, ignoring" % p.time)
                else:
                    f.add(point, WGS.time, obj=intern(isodate.fullString(TimeEpoch+p.time)))

   phys.f.close()  # Should really be done by the del() below, but isn't
   del(phys) # close serial link (?)
   f = f.close()
   if verbose:
        progress("Beginning output. You can disconnect the GPS now.")
   s = f.n3String(base=base, flags="d")   # Flag - no default prefix, preserve gps: prefix hint
   if outputURI != None:
        op = open(outputURI, "w")
        op.write(s)
        op.close()
   else:
        print s 


        
############################################################ Main program

def usage():
    print __doc__
        
if __name__ == '__main__':
    import getopt
    verbose = 0
    doTracks = 0
    doWaypoints = 0
    outputURI = "gpsData.n3"
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvtwd:o:",
            ["help",  "verbose", "tracks", "waypoints", "device=", "output="])
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
        if o in ("-t", "--tracks"):
            doTracks = 1
        if o in ("-w", "--waypoints"):
            doWaypoints = 1
        if o in ("-d", "--device"):
            deviceName = a
        if o in ("-o", "--output"):
            outputURI = a

    doCommand(serialDevice=deviceName, outputURI=outputURI, doTracks=doTracks,
                doWaypoints=doWaypoints, verbose=verbose)

