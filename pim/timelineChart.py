#!/usr/bin/python
# -*- coding: utf-8 -*-
#  SVG parallel plots of different things against time
#
#

import sys
from swap import isodate, myStore

from swap.myStore import load, Namespace

from time import gmtime, mktime
from math import log, exp
from datetime import datetime;


def timeArgument(s):
    """Allow a relative datetime like -1w3d2h3s"""
    units = { 's': 1, 'm': 60,'h': 3600, 'd': 86400, 'w': 604800 }
    if s[0] in '+-':  # ([+-][0-9]+[smhdw])+ )
	i = 1
	val = 0;
	while i < len(s):
	    j = i;
	    while s[j:j+1] in '0123456789':
		j += 1;
	    if s[j:j+1] in units.keys():
		val += int(s[i:j]) * units[s[j]]
		i = j + 1;
	isonow= datetime.isoformat(datetime.now()) + 'Z';
	now = isodate.parse(isonow);
	if s[0] == '-': val = - val;
	print "That must be ",  isodate.fullString(now + val);
	return now + val;
    else:
	return isodate.parse(s);

def palette(ind):
    # Timbl's patented not bit redistribution scheme
    # 0->black, 1-> dark red, etc etc etc
    # Colors are spaced out and consecutive colors always contrast
    #
    rgb = [0,0,0]
    chan, weight = 0, 8;
    i = int(ind);
    while 1:
        if (i == 0 ): return "#%x%x%x" % (rgb[0], rgb[1], rgb[2])
        if i & 1: rgb[chan] += weight;
        i = i / 2
        chan = (chan + 1) % 3
        if (chan == 0): weight = weight/2
        assert weight != 0, " palette index too large %d" % ind




class Histogram():
    def __init__(self, base, step):
	self.counts = {};
	self.base = base;
	self.step = step;
	self.total = 0;
	self.width = 0; # number of slots
	
    def addPeriod(self,start, end):
	x = 1.0 * (start - self.base) / self.step
	y = 1.0 * (end - self.base) / self.step
	for j in range(int(y) - int(x) + 1):
	    i = int(x) + j
	    overlap = min(y, i+1) - max(x, i)
	    if i not in self.counts:
		self.counts[i] = 0;
	    self.counts[i] += overlap;
	    # print "Adding", start, end, ' as ', x, y, j, i, overlap
	    self.total += overlap
	    if self.width < i+1: self.width = i+1;

##############################################


# Each timeline  series has  ad ifferent Y scale, but shares
# a common time x axis with the others.
#
# bottom and top control which part of the parent
#
# leftLabels poisyions the yaxis 

class TimelineSeries:
    def __init__(self, chart, values, bottom = 0.0, top = 1.0, leftLabels = 50, color = 'black', style = None):
	self.chart = chart;
	self.values = values;
	self.maxy = -10e10
	self.miny = 10e10
	self.viewHeight = self.chart.viewHeight * (top-bottom);
	self.viewBottom = self.chart.viewHeight * bottom;
	self.viewTopMargin = self.chart.viewHeight * (1.0 - top);
	self.leftLabels = leftLabels
	self.color = color; # CSS color
	self.style = style;
	self.name = None;
	if style is None:
	    self.style = 'fill:none; stroke: %s;' % color;
        self.preFlight();

    def yscale(self, y):  # Flip y axis to normal math way around
	# print "y=",y, self.viewHeight, self.viewTopMargin,  ((self.maxy - y)/(self.maxy - self.miny)
	#			    * (self.viewHeight * .8)
	#	 + (self.viewHeight * .1))   +  self.viewTopMargin
	assert y is not None;
	assert self.miny is not None;
	assert self.maxy is not None;
	return ((self.maxy - y)/(self.maxy - self.miny)
				    * (self.viewHeight * .8)
		 + (self.viewHeight * .1))   +  self.viewTopMargin;

    def xscale(self, x):
	return self.chart.xscale(x);

    def align(self, others):
	assert self.miny is not None;
	for other in others:
	    if other.miny is None: print "YT@#$@#$#@$% WTF ", other.name;
	    assert other.miny is not None;
	    
	    self.miny = min(self.miny, other.miny);
	    self.maxy = max(self.maxy, other.maxy);
	for other in others:
	    other.miny = self.miny;
	    other.maxy = self.maxy;
	 
    def opLine(self, line):
	return self.chart.opLine(line);

    def horizontal(self, y):
        self.line(self.chart.minx - 5, y, self.chart.maxx, y,'#ddd');
        self.opLine( "<text x='%d' y='%d' style='%s'>%s</text>" % (
            self.xscale(self.chart.minx) - self.leftLabels, self.yscale(y),
            self.chart.axisStyle + "fill: #444;", self.chart.kMGT(y)));

    def yaxis(self):
        bottom = self.miny
        if self.miny > 0 and (self.maxy - self.miny) > 9 * self.miny:
            bottom = 0  # Avoid missing widow axis if 0 almost included
	if 0 >= bottom and 0 <= self.maxy:  # 0 is in the picture
	    h = max(self.maxy, - bottom);
	    a = log(h)/log(10.0)
	    k = int(a) 
	    step = 10**k
            if h/step < 2.0: step = step/2.0 # Do every .5
            print "Y axis 1 ", h, a, k, step, h/step
	    # print "yaxis: ", h, a, k, step
	    y = 0;
	    while y < self.maxy:
                self.horizontal(y);
		y += step;
	    y = -step;
	    while y > bottom:
                self.horizontal(y);
		y -= step;
	else:
	    h = self.maxy - bottom;
	    a = log(h)/log(10.0)
	    k = int(a) 
	    step = 10**k
            if h/step < 2.0: step = step/2 # Do every 5
            print "Y axis 2 ", h, a, k, step, h/step
	    y = (int(bottom/step) + 1 ) * step;
	    while y < self.maxy:
                self.horizontal(y);
		y += step;
	return

    def line(self, x1, y1, x2, y2, color='black', width="0.5px"):
	self.opLine("\t<path style='fill:none; stroke: %s; stroke-width: %s;' d='M %d %d L %d %d'/>"
	    % (color, width, self.xscale(x1), self.yscale(y1), self.xscale(x2), self.yscale(y2)));

    def preflightOne(self, x, y):
	assert y is not None, "None y for "+ `x`
	if x < self.chart.clip_x_low or x > self.chart.clip_x_high:
	    return;
	if self.chart.minx > x: self.chart.minx = x;
	if self.chart.maxx < x: self.chart.maxx = x;
	if self.maxy < y: self.maxy = y;
	if self.miny > y: self.miny = y;

    def preFlight(self):
	for x, y in self.values:
	    self.preflightOne(x,y);
    

    def draw(self):
	#if color is None: color = self.color;
	#style = 'fill:none; stroke:%s' % color;
	for i in range(len(self.values)-1):
	    x, y = self.values[i];
	    if x < self.chart.clip_x_low or x > self.chart.clip_x_high:
		continue;
	    self.opLine("<path style='%s' d='M %d %d L %d %d'/>"
		% (self.style,
		self.chart.xscale(self.values[i][0]), self.yscale(self.values[i][1]),
		self.chart.xscale(self.values[i+1][0]), self.yscale(self.values[i+1][1]),
		));
	self.yaxis();
	

    
##############################

class StepLineSeries(TimelineSeries):

    def draw(self):
	if self.style is None:
	    style = 'fill:none; stroke:%s' % self.color;
	else:
	    style = self.style;
	n = len(self.values) -1;
	chart = self.chart
	for i in range(n):
	    x1, y1 = self.values[i];
	    x2, y2 = self.values[i+1];
	    if x2 < chart.clip_x_low or x1 > chart.clip_x_high: # Complete miss
		continue;
	    
	    if x1 < chart.clip_x_low: x1 = chart.clip_x_low;  # Clip
	    if x2 > chart.clip_x_high:
		x2 = chart.clip_x_high;
		y2 = y1;      # Don't do second part of line if clipped
	    self.opLine("<path   style='%s' d='M %d %d L %d %d L %d %d'/>"
		% (style,
		chart.xscale(x1), self.yscale(y1),
		chart.xscale(x2), self.yscale(y1),  # Move x first
		chart.xscale(x2), self.yscale(y2),
		));

	self.opLine("<path   style='%s' d='M %d %d L %d %d'/>"
	    % (style,
	    chart.xscale(self.values[n][0]), self.yscale(self.values[n][1]),
	    chart.xscale(chart.maxx), self.yscale(self.values[n][1]),  # To end of chart
	    ));

	self.yaxis();
	
##############################

class ScatterSeries(TimelineSeries):

    def draw(self):
        e = 2;  # Size of the mark drawn 
	if self.style is None:
	    style = 'fill:none; stroke:%s' % self.color;
	else:
	    style = self.style;
	n = len(self.values) -1;
	chart = self.chart
	for i in range(n):
	    x1, y1 = self.values[i];
	    if x1 < chart.clip_x_low or x1 > chart.clip_x_high: # Complete miss
		continue;
	    
	    self.opLine("<path   style='%s' d='M %d %d L %d %d M %d %d L %d %d'/>"
		% (style,
		chart.xscale(x1) - e , self.yscale(y1),
		chart.xscale(x1) + e , self.yscale(y1),
		chart.xscale(x1), self.yscale(y1) - e ,
		chart.xscale(x1), self.yscale(y1) + e ,

		));

	self.yaxis();
	
##############################

class BooleanSeries(TimelineSeries):

    def draw(self,  color = None):
	chart = self.chart
	if color is None: color = self.color;
	n = len(self.values);
	for i in range(n-1): # all but one
	    x1, y1 = self.values[i];
	    x2, y2 = self.values[i+1];

	    if y1:
		if x1 > chart.clip_x_high or x2 < chart.clip_x_low: continue; # missed
		if x1 < chart.clip_x_low: x1 = chart.clip_x_low; # clip
		if x1 < chart.clip_x_low: x1 = chart.clip_x_low;
		if x2 > chart.clip_x_high: x2 = chart.clip_x_high;

		self.opLine("<path style='fill:%s; stroke:%s; stroke-width: 0; ' d='M %d %d L %d %d L %d %d L %d %d L %d %d'/>"
		    % (color, color,
		    chart.xscale(x1), self.yscale(0),
		    chart.xscale(x2), self.yscale(0),  # Move x first
		    chart.xscale(x2), self.yscale(1), # then y
		    chart.xscale(x1), self.yscale(1), # then x back
		    chart.xscale(x1), self.yscale(0),   # and back to start
		    ));

	# self.yaxis();
	


##############################


class BalanceSeries(TimelineSeries):

    def prefFight(self):

	
	first, balances = self.values
	for s, e, acid, bal in balances:
	    x1 = dateToInt(s);
	    if x1 < self.chart.minx: self.chart.minx = x1;
	    if x1 > self.chart.maxx: self.chart.maxx = x1;
	    if bal < self.miny: self.miny = bal;
	    if bal > self.maxy: self.maxy = bal;
	

    def draw(self):
    
	first, balances = self.values

	self.yaxis(); # Staggering on many?
	
	series = []; # Let's have an ordered list for once
	for ac in first:
	    if ac == 'sum': series.insert(0, ac)  # sum is special, colour 0, black.
	    else: series.append(ac);
	    
	lastBalance = {};
	lastTime = {};
	path = {}
	ix = 0;
	n = len(series);
	keyY = yscale(maxy)-20;
	keyWidth = (maxx-minx)/n;
	
	for ix in range(len(series)):
	    ac = series[ix];
	    d, lastBalance[ac] = first[ac];
	    lastTime[ac] = dateToInt(d);
	    if lastTime[ac] < self.chart.clip_x_low or lastTime[ac] > self.chart.clip_x_high:
		continue;
	    path[ac] = ( "<path   style='fill:none; stroke:%s' d='M %d %d" % 
			( palette(ix), xscale(lastTime[ac]), yscale(lastBalance[ac] )))
	    # Add a key:
	    self.opLine( "<path style='fill:none; stroke:%s' d='M %d %d L %d %d'/>" % (
			palette(ix), xscale(minx + ix*keyWidth), keyY,
			xscale(minx + (ix+0.4)*keyWidth), keyY));
	    self.opLine("<text style='fill:%s; font-size:60%%; font-family:sans-serif' x='%d' y='%d'>%s</text>" %(
			palette(ix), xscale(minx + (ix+0.5)*keyWidth), keyY, ac));

	for s, e, ac, bal in balances:
	    x1= dateToInt(s);
	    if (x1 != lastTime[ac]): path[ac] += " L %d %d" % (xscale(x1), yscale(lastBalance[ac]));
	    if (bal != lastBalance[ac]): path[ac] += " L %d %d" % (xscale(x1), yscale(bal));
	    lastTime[ac] = x1;
	    lastBalance[ac] = bal;

	for ac in first:
	    self.opLine( path[ac] + "'/>");
	    

#######################################


class ParallelChart:

    def __init__(self, viewWidth = 800, viewHeight = 400, start = -10e10, end = 10e10):
	self.viewWidth = viewWidth;
	self.viewHeight = viewHeight;

	self.clip_x_low = start; # Clipping if necessary
	self.clip_x_high = end;

	self.maxx = -10e10
	self.minx = 10e10
	self.lines = [];
	self.axisStyle = "font-size:70%; font-family: sans-serif;";
	

	self.opLine("""<?xml version="1.0" encoding="iso-8859-1"?>
    <svg xmlns="http://www.w3.org/2000/svg"
	xmlns:l="http://www.w3.org/1999/xlink" width="%dpt" height="%dpt" viewBox="0 0 %d %d">
    """ % ( self.viewWidth, self.viewHeight, self.viewWidth, self.viewHeight ));
	self.svgBottom = """</svg>
    """;


    def opLine(self, ln):
	self.lines.append(ln); # Note can't assign to non-local variable in python


    def svgString(self):
	return '\n'.join(self.lines) + '\n' + self.svgBottom;

    def writeFile(self, fn):
	opf = open(fn, 'w')
	opf.write(self.svgString());
	opf.close();


    def xscale(self, x):
	# print self.minx, self.maxx, x, (x - self.minx), (self.maxx - self.minx), 1.0e0 * (x - self.minx)/(self.maxx - self.minx)
	return ( 1.0e0 * (x - self.minx)/(self.maxx - self.minx)
				    * (self.viewWidth * .8)
		    + (self.viewWidth * .1));

    def vertical(self, x1, color='black', width="0.5px", bot = 0.1 , top = 0.9):
	self.opLine("\t<path   style='fill:none; stroke: %s; stroke-width: %s;' d='M %d %d L %d %d'/>"
	    % (color, width, self.xscale(x1), self.viewHeight * bot, self.xscale(x1), self.viewHeight * top));

    def labelledVertical(self, x, color='#88f', width="0.5px", bot = 0.1 , top = 0.9):
        self.vertical(x, color, width, bot, top);
        self.opLine( "<text x='%d' y='%d' style='%s'>%s</text>" % (
            self.xscale(x) - 3 , (self.viewHeight * .95),
            self.axisStyle + "fill: #444;", self.kMGT(x)));


    def xaxis(self):
        bottom = self.minx
        if self.minx > 0 and (self.maxx - self.minx) > 9 * self.minx:
            bottom = 0  # Avoid missing widow axis if 0 almost included
	if 0 >= bottom and 0 <= self.maxx:  # 0 is in the picture
	    h = max(self.maxx, - bottom);
	    a = log(h)/log(10.0)
	    k = int(a) 
	    step = 10**k
            if h/step < 2.0: step = step/2.0 # Do every .5
            print "X axis inc zero ", h, a, k, step, h/step
	    x = 0;
	    while x < self.maxx:
                self.labelledVertical(x);
		x += step;
	    x = -step;
	    while x > bottom:
                self.labelledVertical(x);
		x -= step;
	else:
	    h = self.maxx - bottom;
	    a = log(h)/log(10.0)
	    k = int(a) 
	    step = 10**k
            if h/step < 2.0: step = step/2 # Do every 5
            print "X axis no zero ", h, a, k, step, h/step
	    x = (int(bottom/step) + 1 ) * step;
	    while x < self.maxx:
                self.labelledVertical(x);
		x += step;
	return

    # Use engineering suffixes to abbreviate round numbers"
    def kMGT(self, x):
        if x < 0: return '-' + self.kMGT(-x);
	if x == 0: return '0';
	scale = int(log(x)/log(10)  + 0.00001)  # In case bad rounding
	level = int(scale / 3);
	suffix = ['n', 'µ', 'm', '', 'k', 'M', 'G', 'T'][level+3];
	x2 = x /(10**(level*3));
	if x2 == int(x2): return "%d%s" % (x2, suffix) # @@ need Approx
	s = ("%f" % x2)
	if level != 0:
	    s = s.replace('.', suffix);
        while (s[-1:] == '0'): s = s[:-1]; # Trim round numbers
	return s



#######################################


class TimelineChart(ParallelChart):

    def timeAxis(self, secondsBehindGMT):
	minLocal, maxLocal = self.minx - secondsBehindGMT , self.maxx - secondsBehindGMT
	print "Time axis raw:        ", self.minx, ' -> ', self.maxx, ' i.e. ', self.maxx - self.minx
	print "Time axis range:        ", isodate.fullString(self.minx), ' - ', isodate.fullString(self.maxx)
	print "Time axis (local time): ", isodate.fullString(minLocal), ' - ', isodate.fullString(maxLocal)

        duration = self.maxx - self.minx; # Seconds
	ym1, ym2 = gmtime(minLocal), gmtime(maxLocal)
	monthname = ["January", "February", "March", "April", "May", "June", 
		"July", "August", "Spetember", "October", "November", "December"]; # @@ I18N
    
        labelHeight = 5
	def graticule(spacing, color, secondsBehindGMT, labelHeight):
            separation  = self.xscale(spacing) - self.xscale(0)
	    if separation <= 5 : # Enough space for line?
                return 0
            print "Doing grating on the time axis ", spacing, "seconds, i.e. pixels: ", separation
            tl = minLocal - minLocal % spacing;
            while tl < maxLocal:
                t = tl + secondsBehindGMT;
                self.vertical(t, color, 0.8);
                # print "Notch at ", t
                if self.xscale(spacing) - self.xscale(0) > 10 : # Enough width for label?  was 10
                    if tl < maxLocal - (spacing/10):  # tl < maxLocal - spacing:
                        ts = isodate.fullString(t)
                        if spacing == 1 or spacing == 10 : lab = ts[17:19]
                        elif spacing == 60 or spacing == 600 : lab = ts[14:16]
                        elif spacing == 3600: lab = ts[11:13]
                        else: lab = ts[8:10]
                        self.opLine("<text x='%d' y='%d' style='%s'>%s</text>\n" % (
                            self.xscale(t) + 2,
                            (self.viewHeight * .1) - labelHeight,
                            self.axisStyle + ("fill: %s;" % (color)),   #   was + "text-align:center;",
                            str(int(lab))));
                tl += spacing;
            if separation > 10 : # Enough width for label?
                return 2
            return 1
	
        timeunits = [ 1, 10, 60, 600, 3600, 86400 ];
        colours = [ '#eef', '#ddf', '#ccf' ]; 
        col = 0;
        for u in range(len(timeunits)):
            spacing = timeunits[u];
            res = graticule(spacing, colours[col], secondsBehindGMT, labelHeight);
            if res > 0:
                col += 1
                if res == 2:  # included label
                    labelHeight += 12;
                    if spacing == 1 or spacing ==  60:
                        col += 1  # Skip 10 or 600
                if col >= len(colours):
                    break;
                            
	if duration > 86400:
            months = (ym2[0] - ym1[0]) * 12 + (ym2[1] - ym1[1])
            if months > 0:
                print "Doing months on the axis."
                ym = (ym1[0], ym1[1], 1, 0, 0, 0, 0, 0, 0);
                for m in range(months+1):
                    if  ym[1] % 12 == 1: col = '#44f';
                    else:
                        if ym[1] % 3 == 1: col = '#aaf'
                        else: col = '#ddf';
                    self.vertical(mktime(ym), col);
                    if self.xscale(86400 * 28) - self.xscale(0) > 50 : label =  monthname[ym[1]-1]
                    else: label = ym[1];
                    self.opLine("<text x='%d' y='%d' style='%s'>%s</text>\n" % (
                        self.xscale( mktime(ym)) + 10,
                        (self.viewHeight * .1) + 10,
                        self.axisStyle +"fill: #77f;",   #   was + "text-align:center;",
                        label));
                    if ym[1] ==1: self.opLine( "<text x='%d' y='%d' style='%s'>%s</text>" % (
                        self.xscale( mktime(ym)) + 10,
                        (self.viewHeight * .9) + 25,
                        self.axisStyle +"fill: #77f;",   #   was + "text-align:center;",
                        str(ym[0])));
                    ym = (ym[0]+ym[1]/12, ym[1] % 12 + 1, 1, 0, 0, 0, 0, 0, 0);

	
	

    

 

def main(args):
    pass # @@ test chart

if __name__=='__main__':
    main()


#
