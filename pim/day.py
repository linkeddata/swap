#!/usr/bin/python
"""Correlate GPS data with Photo metadata

options:

--help      -h
--gpsData   -g   dir   Input file directory containing gpsData.n3 and Photometa.n3
--verbose   -v

is or was http://www.w3.org/2000/10/swap/pim/day.py
"""

# Regular python library
import os, sys, time
from math import sin, cos, tan, sqrt
from urllib import urlopen

# SWAP  http://www.w3.org/2000/10/swap
from swap import myStore, diag, uripath, notation3, isodate
from swap.myStore import Namespace, formula, symbol, intern, bind, load
from swap.diag import progress
#import uripath
from swap.uripath import refTo, base

from swap.notation3 import RDF_NS_URI
import swap.notation3           # N3 parsers and generators
from swap import  isodate  # for isodate.fullString

# import toXML          #  RDF generator

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

def saveAs(uri, filename):
    gifStream = urlopen(uri)
    gifData = gifStream.read()
    gifStream.close
    progress("curl \"%s\" > %s" % (uri, filename))
    saveStream = open(filename, "w")
    saveStream.write(gifData)
    saveStream.close()

################################ Map class

class Map:
    def __init__(self, minla, maxla, minlo, maxlo, svgStream=None):
    
        def getSize(s, atr):
            i = s.find(atr+'="') + len(atr) + 2
            val = ""
            while s[i] in '0123456789':
                val += s[i]
                i = i+1
            x = int(val)
            progress("Found attribute %s=%i" %(atr,x))
            return x
    
        progress("Lat between %f and %f, Long %f and %f" % (minla, maxla, minlo, maxlo))
    
        pageLong_m = 10.5 * 25.4 / 1000   # Say for 8.5 x 11" US Paper YMMV
        pageShort_m = 8.0 * 25.4 / 1000     #This is printable

        if svgStream==None: self.wr = sys.stdout.write
        else: self.wr = svgStream.write
        
        self.marks = []  # List of marks on the map to avoid overlap
        
        self.midla = (minla + maxla)/2.0
        self.midlo = (minlo + maxlo)/2.0
        self.total_m = 0 # Meters
        self.last = None   # (lon, lat, date)
        
        pi = 3.14159265358979323846 # (say)
        degree = pi/180
        # r_earth = 6400000.0 # (say) meters
        phi = self.midla * degree
        
        # See http://en.wikipedia.org/wiki/Earth_radius
        a = 6.378137e6 # m
        b = 6.3567523e6 #m
        r_earth = sqrt(  ((a*a*cos(phi))**2 + ((a*a*sin(phi)))**2)/
                        ((a*cos(phi))**2 + ((a*sin(phi)))**2))
        print "Local radius of earth = ", r_earth
        
        self.y_m_per_degree = r_earth * pi /180
        self.x_m_per_degree = self.y_m_per_degree * cos(self.midla*degree)
        progress('Metres per degree: (%f,%f)' % (self.x_m_per_degree, self.y_m_per_degree))
        # OpsenStreetMap Map
        
        hila = maxla + (maxla - minla) * 0.1  # Make  margins an extra 10% all round
        hilo = maxlo + (maxlo - minlo) * 0.1
        lola = minla - (maxla - minla) * 0.1
        lolo = minlo - (maxlo - minlo) * 0.1

        subtended_x = (hilo - lolo) * self.x_m_per_degree
        subtended_y = (hila - lola) * self.y_m_per_degree
        

        progress("Area subtended  %f (E-W)  %f (N-S) meters" %(subtended_x, subtended_y))

        vertical = subtended_y > subtended_x
        if vertical:
            if subtended_y / pageLong_m >  subtended_x/pageShort_m:  # constrained by height
                osmScale = subtended_y / pageLong_m
                hilo = self.midlo + 0.5 * (pageShort_m * osmScale/self.x_m_per_degree)
                lolo = self.midlo - 0.5 * (pageShort_m * osmScale/self.x_m_per_degree)
            else: # constrained by width
                osmScale = subtended_x/pageShort_m
                hila = self.midla + 0.5 * (pageLong_m * osmScale/self.y_m_per_degree)
                lola = self.midla - 0.5 * (pageLong_m * osmScale/self.y_m_per_degree)
            
        else:
            if subtended_x / pageLong_m >  subtended_y/pageShort_m:  # constrained by long width
                osmScale = subtended_x / pageLong_m
                hila = self.midla + 0.5 * (pageShort_m * osmScale/self.y_m_per_degree)
                lola = self.midla - 0.5 * (pageShort_m * osmScale/self.y_m_per_degree)
            else: # constrained by short height
                osmScale = subtended_y/pageShort_m
                hilo = self.midlo + 0.5 * (pageLong_m * osmScale/self.x_m_per_degree)
                lolo = self.midlo - 0.5 * (pageLong_m * osmScale/self.x_m_per_degree)

        progress("Area subtended  %f (E-W)  %f (N-S) meters" %(subtended_x, subtended_y))

        # osmScale = 10000  # say
        #self.pixels_per_m = 122.94/25.4 * 1000 / osmScale  # pixels per metre on the ground - dpi was 120 now 123
        #self.pixels_per_m = 85 /25.4 * 1000 / osmScale #  Calculating this doesn't sem to work -- lets look at the actual map
        #self.page_x = (hilo-lolo) * self.x_m_per_degree * self.pixels_per_m
        #self.page_y = (hila-lola) * self.y_m_per_degree * self.pixels_per_m
        

        # Like http://tile.openstreetmap.org/cgi-bin/export?bbox=-71.2118,42.42694,-71.19273,42.44086&scale=25000&format=svg
        OSM_URI = ("http://tile.openstreetmap.org/cgi-bin/export?bbox=%f,%f,%f,%f&scale=%i&format=svg" % (lolo, lola, hilo, hila, osmScale))
        progress("FYI OSM map at: ", OSM_URI)
        try:
            pass
            #saveAs(OSM_URI, "background-map.svg")
            osmStream = urlopen(OSM_URI)
            osmData = osmStream.read()  # Beware of server overloaded errors
            osmStream.close

        except IOError:
            progress("Unable to get OSM map")
            sys.exit(4)  # @@ should extract the error code from somwhere

        i = osmData.rfind('</svg>')
        if i <0:
            progress("Invalid SVG file from OSM:\n" + osmData[:1000])
            sys.exit(5)
        self.wr(osmData[:i])  # Everything except for the last </svg>

        # Set up parametrs for point mapping:
        self.page_x = getSize(osmData, 'width')
        self.page_y = getSize(osmData, 'height')
        self.lolo = lolo
        self.lola = lola
        self.hilo = hilo
        self.hila = hila
        self.pixels_per_deg_lat = self.page_y / (hila-lola)
        self.pixels_per_deg_lon = self.page_x / (hilo-lolo)
#        self.pixels_per_deg_lat = self.pixels_per_m * r_earth * pi /180
#        self.pixels_per_deg_lon = self.pixels_per_deg_lat * cos(self.midla*degree)
        
        
        

#        page_x = 800.0  # pixels
#        page_y = 600.0
#        max_x_scale = page_x / subtended_x
#        max_y_scale = page_y / subtended_y
#        self.pixels_per_m = min(max_x_scale, max_y_scale)    * 0.9  # make margins

        #self.page_x = int(subtended_x * self.pixels_per_m)
        #self.page_y = int(subtended_y * self.pixels_per_m)

       # TIGER map

        if 0:

            map_wid = subtended_x /0.9
            map_ht  = subtended_y /0.9
            tigerURI = ("http://tiger.census.gov/cgi-bin/mapper/map.gif?"
                    +"&lat=%f&lon=%f&ht=%f&wid=%f&"
                    +"&on=CITIES&on=majroads&on=miscell&on=places&on=railroad&on=shorelin&on=streets"
                    +"&on=interstate&on=statehwy&on=states&on=ushwy&on=water"
                    +"&tlevel=-&tvar=-&tmeth=i&mlat=&mlon=&msym=bigdot&mlabel=&murl=&conf=mapnew.con"
                    +"&iht=%i&iwd=%i")  % (self.midla, self.midlo, map_ht, map_wid, self.page_y, self.page_x)

            progress("Getting tiger map ", tigerURI)
            try:
                saveAs(tigerURI, "tiger.gif")
            except IOError:
                progress("Offline? No tigermap.")
                
#       tigerURI = ("http://tiger.census.gov/cgi-bin/mapper/map.gif?&lat=%f&lon=%f&ht=%f"
#           +"&wid=%f&&on=majroads&on=miscell&tlevel=-&tvar=-&tmeth=i&mlat=&mlon=&msym=bigdot&mlabel=&murl="
#           +"&conf=mapnew.con&iht=%i&iwd=%i" ) % (self.midla, self.midlo,  maxla-minla, maxlo-minlo, self.page_y, self.page_x)


        if 0: self.wr("""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!DOCTYPE svg PUBLIC '-//W3C//DTD SVG 1.0//EN'
 'http://www.w3.org/TR/2001/REC-SVG-20010904/DTD/svg10.dtd'>
<!-- Generated by @@@ -->
<svg
    width="%ipx"
    height="%ipx"
    xmlns='http://www.w3.org/2000/svg'
    xmlns:xlink='http://www.w3.org/1999/xlink'>
 <g>
 """  %   (self.page_x,self.page_y))  #"
 
        progress('Map page size (%f,%f)'% (self.page_x,self.page_y))

# <rect x='0' y='0' width='%ipx' height='%ipx' style='fill:#ddffbb'/>
# <image width="100%%" height="100%%"  xlink:href="background-map.svg"/>


    def deg_to_px(self, lon, lat):
        "Note the lon, lat order on input like x,y"
#       progress("lon %f from center %f is offset %f, ie %f meters" % (
#               lon, self.midlo, lon - self.midlo, ((lon - self.midlo) * self.pixels_per_deg_lon)))
        return   ((lon - self.lolo) * self.pixels_per_deg_lon,
                  (self.hila - lat) * self.pixels_per_deg_lat)
            
    def startPath(self, lon, lat, date):
        x, y = self.deg_to_px(lon, lat)
        self.last = (lon, lat, date)
        self.walking = 0.0
        self.wr("  <path   style='fill:none; stroke:red' d='M %f %f " % (x,y))

    def straightPath(self, lon, lat, date):
        x, y = self.deg_to_px(lon, lat)
        self.wr("L %f %f " % (x,y))
        lastlon, lastlat, lastdate = self.last
        dx = (lon-lastlon) * self.x_m_per_degree
        dy = (lat-lastlat) * self.y_m_per_degree
        ds = sqrt(dx*dx + dy*dy)

        t1 = isodate.parse(lastdate)
        t2 = isodate.parse(date)
        dt = t2-t1
        if dt > 0:
            speed = ds/dt  # m/s
        else:
            speed = 0.0  # well, infinity
        # progress('Path length: %sm, speed: %f m/s ' %(`ds`, speed))
        if speed > 0.5 and speed < 2.0:
            self.walking += dt
        self.total_m += ds
        self.last = (lon, lat, date)

    def skipPath(self, lon, lat, date):
        x, y = self.deg_to_px(lon, lat)
        self.wr("M %f %f " % (x,y))
        self.last = (lon, lat, date)

    def endPath(self):
        progress('Track length so far:/m: %f' % (self.total_m))
        progress('Time spent walking/min: %f' % (self.walking/60.0))
        self.wr("'/>\n\n")

    def photo(self, uri, lon, lat):
        x, y = self.deg_to_px(lon, lat)
        rel = refTo(base(), uri)
        while 1:
            for x2, y2 in self.marks:
                if sqrt((x-x2)*(x-x2) + (y-y2)*(y-y2)) < 7:
                    x, y = x + 9, y - 9  # shift
                    break
            else:
                break
        self.marks.append((x, y))
        self.wr("""<a xlink:href='%s'>
                    <rect x='%i' y='%i' width='14' height='8' style='fill:#777;stroke:black'/>
                    <circle cx='%i' cy='%i' r='3'/>
                    </a>""" %(rel, x-7, y-4, x, y))
        
    def close(self):
        self.wr("</svg>\n")
        




############################################################ Main program
    
if __name__ == '__main__':
    import getopt
    verbose = 0
    gpsData = "." # root of data
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
                t = str(f.the(subj=point, pred=WGS.time))
                la = str(f.the(subj=point, pred=WGS.lat))
                lo = str(f.the(subj=point, pred=WGS.long))
                events.append((t, "T", (la, lo)))

    events.sort(compareByTime)
    
    last = None
    n = len(events)

    if verbose: progress( "First event:" , `events[0]`, "Last event:" , `events[n-1]`)

    minla, maxla = 90.0, -90.0
    minlo, maxlo = 400.0, -400.0
    conclusions = formula()
    for i in range(n):
        dt, ty, da = events[i]
        if ty == "T": # Trackpoint
            last = i
            (la, lo) = float(da[0]), float(da[1])
            if la < minla: minla = la
            if la > maxla: maxla = la
            if lo < minlo: minlo = lo
            if lo > maxlo: maxlo = lo
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
#           print "    Delta", delta, "seconds between", events[last], "and", events[j]
            a = (t - t1) / (t1-t2)
            lat = lat1 +  a * (lat2-lat1)
            long = long1 + a * (long2-long1)
            progress( "%s: Before (%f, %f)" % (dt1, lat1, long1))
            progress( "%s: Guess  (%f, %f)" % (dt, lat, long))
            progress( "%s: After  (%f, %f)" % (dt2, lat2, long2))
            
            where = conclusions.newBlankNode()
            conclusions.add(ph, GPS.approxLocation, where)
            conclusions.add(where, WGS.lat, lat)
            conclusions.add(where, WGS.long, long)

    
#           guess = isodate.fullString(...)

    progress("Start Output")
    print conclusions.close().n3String(base=base())

    svgStream = open("map.svg", "w")
    map = Map(minla, maxla, minlo, maxlo, svgStream=svgStream)

    pathpoint = None
    for i in range(n):
        date, ty, da = events[i]
        if ty == "T": # Trackpoint
            (la, lo) = float(da[0]), float(da[1])
            if pathpoint == None:
                map.startPath(lo, la, date)
                pathpoint = 1
            else:
                map.straightPath(lo, la, date)
        elif ty == "P":
            pass
    map.endPath()


    for st in conclusions.statementsMatching(pred=GPS.approxLocation):
        photo = st.subject()
        loc = st.object()
        long = conclusions.the(subj=loc, pred=WGS.long)
        lat = conclusions.the(subj=loc, pred=WGS.lat)
        progress("Photo %s at lat=%s, long=%s" %(photo.uriref(), lat, long))
        la, lo = float(lat), float(long)
        map.photo(photo.uriref(), lo, la)
    map.close()
    svgStream.close()

def min(x, y):
        if x<y: return x
        return y

#ends
