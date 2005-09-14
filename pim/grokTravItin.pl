#!/usr/bin/perl
# Grok itineraries from Navigant; i.e. turn them
# into RDF/n3, using dublin core and cyc vocabulary.
#
# Hmm... Navigant probably isn't the only travel agency to
# use this format; perhaps it's a SABRE thing?
#
# derived from
#  http://www.w3.org/2001/07dc-bos/grokNavItin.pl
#  Id: grokNavItin.pl,v 1.8 2002/06/04 01:45:38 connolly Exp
#
# $Id$
# see changelog at end
#

use strict;

my($Verbose) = 1;
$| = 1;

my($rdfNS) = "http://www.w3.org/1999/02/22-rdf-syntax-ns#";
my($rdfsNS) = "http://www.w3.org/2000/01/rdf-schema#";
my($dcNS) = "http://purl.org/dc/elements/1.1/";
my($kNS) = "http://opencyc.sourceforge.net/daml/cyc.daml#";
my($dtNS) = "http://www.w3.org/2001/XMLSchema#";
my($tNS) = "http://www.w3.org/2000/10/swap/pim/travelTerms#";
my($aNS) = "http://www.daml.org/2001/10/html/airport-ont#";

my(%Things);
my(%AirportCodes) = &airportNames();

&bind("r", $rdfNS);
&bind("dt", $dtNS); # datatypes
&bind("k", $kNS);
&bind("dc", $dcNS);
&bind("t", $tNS);
&bind("apt", $aNS);


my($gen) = 1;

my(%monthNameToNum);
%monthNameToNum = ('JAN', 1,
		   'FEB', 2,
		   'MAR', 3,
		   'APR', 4,
		   'MAY', 5,
		   'JUN', 6,
		   'JUL', 7,
		   'AUG', 8,
		   'SEP', 9,
		   'OCT', 10,
		   'NOV', 11,
		   'DEC', 12
		  );

# from
# search.cpan.org: Getopt::Long - Extended processing of command line options
# http://search.cpan.org/author/JV/Getopt-Long/lib/Getopt/Long.pm#Options_with_values
use Getopt::Long;
my($aboutMeDoc, $nameInDoc);
GetOptions ('aboutMe=s' => \$aboutMeDoc,
	    'localName=s' => \$nameInDoc);


&grok($aboutMeDoc, $nameInDoc);

sub grok{
  my($aboutMeDoc, $nameInDoc) = @_;

  my($state) = 'start';
  my($agency, $traveller);
  my($calday);
  my($event, $trip, $firstEvent);
  $firstEvent = 0;

  $trip = introduce("thisTrip");
  makeStatement("", $rdfNS . "type", $kNS . "ItineraryDocument");
  makeStatement("", $kNS . "containsInformationAbout-Focally", $trip);

  if($aboutMeDoc){
    makeStatement("", $rdfsNS . "seeAlso", $aboutMeDoc);
    
    if($nameInDoc){
      $traveller = "$aboutMeDoc#$nameInDoc";
    }
  }
  $traveller = introduce("thisPassenger") unless $traveller;

  makeStatement($trip, $kNS . "passengers", $traveller);

  while(<>){

    REDO:
      if($state eq 'start'){
	  
	  
	  # skipping these:
	  #e.g.        617 451-4200 TEL
	  #e.g. >  CUSTOMER NBR: 6160150001     TBZTQY         PAGE: 01
	  #e.g. >  REF: 6264400
	  
	  
	  #e.g. >  SALES PERSON: 53     ITINERARY            DATE: 15 JUN
	  #     >01
	  if(/ITINERARY\s+DATE: (\d\d) (\w+)/){
	      my($dd, $mon) = ($1, $2);
	      my($line);
	      $line = <>;
	      if($line =~ /(\d\d)/){
		  my($yy) = $1;
		  
		  makeStatement("", $rdfNS . "type", $kNS . "ItineraryDocument");
		  makeStatement("", $dcNS . "date", '', &fmtDate($dd, $mon, $yy));
	      }
	      else{
		  warn "cannot find year.";
	      }
	  }
	  
	  #e.g. >  FOR: CONNOLLY/DANIEL
	  elsif(m,FOR:\s+(\w+)/(\w+),){
	      my($fam, $given) = ($1, $2, $3);
	      
	      makeStatement($traveller, $kNS . "nameOfAgent", '', "$fam, $given");
	  }
	  
	  
	  #e.g. >  11 JUL 01  -  WEDNESDAY
	  elsif(/(\d\d?) (\w+) (\d\d)?(\d\d)\s*-\s*([A-Za-z]+)/){
	      my($dd, $mon, $cc, $yy, $dow) = ($1, $2, $3, $4, $5);
	      print STDERR "ala 11 JUL 01  -  WEDNESDAY: $dd, $mon, $yy, $dow\n";
	      $calday = theDay($dd, $mon, $yy, $dow);
	      
	      $state = 'inDay';
	  }
	  
	  #e.g. >  SUNDAY, 13 JANUARY
	  elsif(/([SMTWF][A-Z]+), (\d\d) ([A-Z]+)/){
	      my($dow, $dd, $mon)  = ($1, $2, $3);
	      
	      print STDERR "@@ kludged date to 2002. $dow $dd $mon\n";
	      $calday = theDay($dd, $mon, 02, $dow);
	      
	      $state = 'inDay';
	  }
	  
	  else{
	      warn "state $state. skipping: $_" if $Verbose;
	  }
      }
      
      elsif($state eq 'inDay'){
	  
	  #e.g. >     AIR   AMERICAN AIRLINES    FLT:1364   ECONOMY
	  #e.g. American Airlines FLT:592
	  #e.g. American Airlines FLT:3093 Operated by American Eagle
	  if(/FLT:\s*(\d+)\s+([A-Z][A-Z]+)?/){
	      my($flightNum, $flightClassName) = ($1, $2);
	      s/^>\s*//;
	      s/FLT:.*//;
	      s/\s*AIR\s*//;
	      s/\s+$//;
	      my($carrierName) = $_;
	      
	      $event = genSym("flt$flightNum");
	      makeStatement($trip, $kNS . "subEvents", $event);
	      makeStatement($trip, $kNS . "firstSubEvents", $event) unless $firstEvent++;
	      makeStatement($event, $kNS . "startingDate", $calday);
	      makeStatement($event, $tNS . "flightNumber", '', $flightNum);
	      
	      my($carrier);
	      
	      $carrier = the($kNS . 'nameOfAgent', $carrierName, $carrierName);
	      makeStatement($carrier, $rdfNS . 'type', $kNS . 'AirlineCompany');
	      makeStatement($event, $tNS . "carrier", $carrier);
	      
	      if($flightClassName){
		  my($fltcls);
		  $fltcls = the($rdfNS . 'value', $flightClassName, $flightClassName);
		  makeStatement($event, $rdfNS . "type", $fltcls);
	      }
	      $state = 'inEvent';
	  }
	  # sometimes we switch days in flight...
	  elsif(/\bAR /){
	      $state = 'inEvent';
	      goto REDO;
	  }
	  else{
	      warn "inDay $calday; unknown event type? $_" if $Verbose;
	  }
      }
      elsif($state eq 'inEvent'){
	  
	  # LV MCI at 1:20PM Arrive BOS at 5:20PM Non-Stop
	  if(s/^LV (\w\w\w) at (\d\d?):(\d\d)(A|P|N)\S* Arrive (\w\w\w) at (\d\d?):(\d\d)(A|P|N)//){
	      my($airLv, $hh, $mm, $ap, $airAr, $hh2, $mm2, $ap2) =
		  ($1, $2, $3, $4, $5, $6, $7, $8);
	      $hh += 12 if $ap eq 'P' && $hh < 12;
	      $hh = 0 if ($ap eq 'A' && $hh == 12);
	      $hh2 += 12 if $ap2 eq 'P' && $hh2 < 12;
	      $hh2 = 0 if ($ap2 eq 'A' && $hh2 == 12);
	      my($place, $ti);
	      
	      $place = theAirport($airLv);
	      
	      $ti = sprintf("%02d:%02d", $hh, $mm);
	      makeStatement($event, $kNS . 'fromLocation', $place);
	      makeStatement($event, $tNS . 'departureTime', '', $ti);
	      makeStatement($event, $kNS . "startingDate", $calday);
	      
	      $place = theAirport($airAr);
	      $ti = sprintf("%02d:%02d", $hh2, $mm2);
	      makeStatement($event, $kNS . 'toLocation', $place);
	      makeStatement($event, $tNS . 'arrivalTime', '', $ti);
	      makeStatement($event, $kNS . "endingDate", $calday);
	  }
	  #e.g. >       CONNOLLY/DANIEL   SEAT- 9B   AA-XDW5282
	  elsif(/SEAT- *(\w+)/){
	      my($seatName) = ($1);
	      my($sa);
	      $sa = genSym("seat");
	      makeStatement($event, "@@#seatNum", '', $seatName);
	  }
	  
	  elsif(/\bFLT:/){
	      $state = 'inDay';
	      goto REDO;
	  }
	  elsif(/(\d\d?) (\w+) (\d\d)?(\d\d)\s*-\s*(\w+)/ # 16 JAN 02 - WEDNESDAY
		# 7 March 2003-Friday
		|| /[SMTWF]\w+, \d\d? \w+/ # SUNDAY, 13 JANUARY
		){
	      $state = 'start';
	      goto REDO;
	  }else{
	      
	      #e.g. >    LV KANSAS CITY INTL          144P           EQP: MD-80
	      while(s/(LV|AR) ((\S|( [a-zA-Z]))+) \s*(\w\w\w)?\s*(\d\d?)(\d\d)(A|P|N)//){
		  my($dir, $airportName, $st, $hh, $mm, $ap) = ($1, $2, $5, $6, $7, $8);
		  $hh += 12 if $ap eq 'P' && $hh < 12;
		  $hh = 0 if ($ap eq 'A' && $hh == 12);
		  my($place, $ti, $code);
		  
		  if($code = $AirportCodes{$airportName}){
		      $place = theAirport($code, $airportName);
		  }else{
		      die "unknown airport: ", $airportName;
		  }
		  
		  $ti = sprintf("%02d:%02d", $hh, $mm);
		  if($dir eq 'LV'){
		      makeStatement($event, $kNS . 'fromLocation', $place);
		      makeStatement($event, $tNS . 'departureTime', '', $ti);
		  }else{
		      makeStatement($event, $kNS . 'toLocation', $place);
		      makeStatement($event, $tNS . 'arrivalTime', '', $ti);
		      makeStatement($event, $kNS . "endingDate", $calday);
		  }
		  
	      }
	  }
      }
      else{
	  die "unknown state";
      }
  }
  
  makeStatement($trip, $kNS . "lastSubEvents", $event) if $event;
  
}


sub fmtDate{
  my($dd, $mon, $yy) = @_;
  $mon = uc(substr($mon, 0, 3));
  my($mm);
  $mm = $monthNameToNum{$mon};
  die "bad month: $mon" unless $mm >= 1 && $mm <= 12;
  return sprintf("%04d-%02d-%02d",
		 2000+$yy, #@@BUG: y3k
		 $mm, $dd);
}

sub theDay{
  my($dd, $mon, $yy, $dow) = @_;
  my($day, $d);

  $day = fmtDate($dd, $mon, $yy);
  $d = the($dtNS . 'date', $day, "day$dow$dd");

  if($dow =~ /^MONDAY|TUESDAY|WEDNESDAY|THURSDAY|FRIDAY|SATURDAY|SUNDAY$/i){
    $dow = ucfirst(lc($dow));
    makeStatement($d, $rdfNS . 'type', $kNS . $dow);
    makeStatement($kNS . $dow, $rdfNS . 'type', $kNS . 'DayOfWeekType'); #@@ not yet a published part of opencyc, but mentioned in comments.
    makeStatement($kNS . $dow, $kNS . 'nameString', '', $dow);
  }
  return $d;
}


sub makeStatement{
  my($s, $p, $or, $ol) = @_;

  # keep existentials existential...
  $s = "<$s>" unless $s =~ /^_:/;
  $p = "<$p>" unless $p =~ /^_:/;
  
  if($or){
    $or = "<$or>" unless $or =~ /^_:/;
    print "$s $p $or.\n";
  }else{
    print "$s $p \"$ol\".\n"; #@@BUG: string quoting
  }
}

sub bind{
  my($pfx, $ns) = @_;
  printf("\@prefix %s: <%s>.\n", $pfx, $ns);
}

sub introduce{
  my($id, $cls) = @_;

  my($it) = "#$id";
  makeStatement($it, $rdfNS . 'type', $cls) if $cls;

  return $it;
}

sub genSym{
  my($hint) = @_;

  $hint =~ s/[^a-zA-Z0-9]//g; # make it a safe name

  $gen++;
  return "_:${hint}_$gen";
}


sub the{
  # this assumes $prop is a daml:UniqueProperty
  my($prop, $val, $hint) = @_;
  my($ret);

  $ret = $Things{$prop, $val};
  return $ret if $ret;
  $ret = genSym($hint);
  makeStatement($ret, $prop, '', $val);
  $Things{$prop, $val} = $ret;
  return $ret;
}

sub theAirport{
  my($iata, $name) = @_;

  my($apt) = "http://www.daml.org/cgi-bin/airport?" . $iata;

  makeStatement($apt, $kNS . "nameString", '', $name) if $name;
  makeStatement($apt, $rdfNS . "type", $kNS . "Airport-Physical");
  makeStatement($apt, $aNS . "iataCode", '', $iata);

  return $apt;
}


sub airportNames{
  my($data, $ln, %ret);

  # good place to look these up is
  # http://home.hccnet.nl/de.bock/icao/iataairp/mcod.htm#m
  #
  # http://www.ar-group.com/icaoiata.htm seems 404
  # (from http://www.daml.org/2001/10/html/)
  $data = <<EODATA;
AHO ALGHERO
BOS BOSTON
CDG PARIS DE GAULLE
DCA WASHINGTON REAGAN
DFW DALLAS FT WORTH
EWR NEWARK
FCO ROME FIUMICINO
LHR LONDON HEATHROW
MCI KANSAS CITY INTL
NCE NICE
ORD CHICAGO OHARE
PIT PITTSBURGH
SFO SAN FRANCISCO
STL ST LOUIS INTL
YMX MONTREAL DORVALQC
YVR VANCOUVER BC
BRS BRISTOL
DTW DETROIT METRO
AMS AMSTERDAM
GLA GLASGOW
YYZ TORONTO ON
MAN MANCHESTER UK
SNA JOHN WAYNE INTL
MIA MIAMI INTERNTNL
ZRH ZURICH
BUD BUDAPEST
CMH COLUMBUS OH
IAD WASHINGTON DULLES
NRT TOKYO NARITA
MSP MINNEAPOLIS ST PL
MEM MEMPHIS
BRU BRUSSELS
ATL ATLANTA
HEL HELSINKI VANTAA
MKE MILWAUKEE
EDI EDINBURGH
EODATA

    # SNA confirmed via http://www.ocair.com/
    # MKE from http://www.world-airport-codes.com/usa/milwaukee-airport-4729.html

    #
    foreach $ln (split(/\n/, $data)){
      my($code, $name) = split(/ /, $ln, 2);
      #print STDERR "[$ln] [$code] [$name]\n";
      $ret{$name} = $code;
    }

  return %ret;
}


# $Log$
# Revision 1.20  2005-09-14 22:38:42  connolly
# EDI
#
# Revision 1.19  2005/02/24 15:06:23  connolly
# MKE
#
# Revision 1.18  2004/12/23 15:42:16  connolly
# HEL airport
#
# Revision 1.17  2004/08/19 21:23:36  connolly
# oops... BRUSSELS is BRU
#
# Revision 1.16  2004/08/19 21:16:10  connolly
# BRS
#
# Revision 1.15  2004/03/31 21:25:58  connolly
# added MSP, MEM
#
# Revision 1.14  2003/09/16 14:57:54  connolly
# added NRT
#
# Revision 1.13  2003/05/08 22:50:50  connolly
# added CMH, IAD
#
# Revision 1.12  2003/04/14 21:20:51  connolly
# ical section done
#
# Revision 1.11  2003/03/12 15:01:02  connolly
# added MIA
#
# Revision 1.10  2003/02/26 23:45:51  connolly
# support link to foafwho file via seeAlso
# and explicit name for traveller
#
# Revision 1.9  2002/10/18 20:45:14  connolly
# well-known airport names rather than bnodes
#
# Revision 1.8  2002/09/27 21:16:04  connolly
# handle overnight flights
#
# Revision 1.7  2002/09/22 21:56:46  connolly
# handle overnight flights; for TAG trip, WebOnt trip
#
# Revision 1.6  2002/09/11 13:36:44  connolly
# declare the apt namespace
#
# Revision 1.5  2002/08/28 20:26:49  connolly
# moved airport code lookup to grokTravItin.pl; airportNames is now obsolete
#
# Revision 1.4  2002/07/23 23:09:45  connolly
# deal with a little > fluff
#
# Revision 1.3  2002/06/12 20:36:15  connolly
# factored out common stuff from travel tools
#
# Revision 1.2  2002/06/12 15:42:27  connolly
# grokTravItin.pl seems to be working now
#
# Revision 1.1  2002/06/12 06:57:23  connolly
# sorta working; a few terms missing from cyc
#
