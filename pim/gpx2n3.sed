1i\
@prefix gps: <http://hackdiary.com/ns/gps#> .\
@prefix wgs84: <http://www.w3.org/2003/01/geo/wgs84_pos#> .\
\
<#ThisRecord> a gps:Record.\

s/<trkpt lat="\([0-9\.]*\)" lon="\([0-9\.]*\)">/gps:trackpoint [wgs84:lat \1e+00; wgs84:long \2e+00;/
s?</trkpt>?];?
s?<ele>\([0-9\.]*\)</ele>?   wgs84:altitude \1e0;?
s?<time>\([_A-Z:0-9\.-]*\)</time>?   wgs84:time "\1";?
/<speed>.*<.speed>/d
/<course>.*<.course>/d
s?<trkseg>??
s?</trkseg>??
s?<trk>?<#ThisRecord> gps:track [?
s?</trk>?].?
/<gpx/,/<bounds/d
s?</gpx>??
/<wpt/,/<\/wpt/d
/<?xml/d
# Remove any remaining XML lines:
/<[A-Za-z]*>.*<\/[A-Za-z]*>/d
