#!/usr/bin/perl
#
# usage: perl ical2rdf.pl something.ics >something.rdf
#
# copyright (c) W3C (MIT, INRIA, Keio)
# Open Source. share and enjoy.
# see http://www.w3.org/Status for license details
#
# REFERENCES
#
# Internet Calendaring and Scheduling Core
# Object Specification (iCalendar)
# November 1998
# http://www.imc.org/rfc2445
#
#  NOTE: I haven't read it thoroughly yet.
#
# Building an RDF model: A quick look at iCalendar
# http://www.w3.org/2000/01/foo
# TimBL 2000/10/02
#
# see also:
#  http://www.ietf.org/internet-drafts/draft-ietf-calsch-many-xcal-00.txt 
#  http://xml.coverpages.org/iCal-DTD-20011103.txt
#
# versions up to
#    vcal2xml.pl,v 1.6 2002/07/16 05:02:23 connolly
# were released under...
#   http://dev.w3.org/cvsweb/2001/palmagent/
#   
# $Id$
# see change log at end of file.

use strict;

# from
# search.cpan.org: Getopt::Long - Extended processing of command line options
# http://search.cpan.org/author/JV/Getopt-Long/lib/Getopt/Long.pm#Options_with_values
use Getopt::Long;
my($X_ns);
GetOptions ('xnames=s' => \$X_ns);

my($ICal_ns) = 'http://www.w3.org/2000/10/swap/pim/ical#';

my(@stack);
my($intag);
my($field, $line);
my($nsDone);

$field = <>;

my(@symbolProps) = ('action', 'class', 'transp', 'start',
		   'partstat', 'rsvp', 'role', 'cutype');
my(@resProps) = ('standard', 'daylight',
		 'valarm', 'trigger',#@@mismatch?
		);
my(@refProps) = ('attendee', 'organizer',
		 'X' # from mozilla calendar stuff. @@OK?
		);
my(@valProps) = ('dtstart', 'dtend', 'trigger',
		 'rrule', # special...
		 'exdate' #@@comma-separated
		);

my(%ValueType) = (
		  'calscale', 'text', # 4.7.1 Calendar Scale
		  'prodid', 'text', # 4.7.3 Product Identifier
		  'version', 'text', # 4.7.4 Version
		  'dtstamp', 'date-time', # 4.8.7.2 Date/Time Stamp
		  'lastModified', 'date-time',    
		  'status', 'text',   # @@@ tbl 200410 should be enum type @@ was missing
		  'tzid',   'text' ,  # @@@@@ tbl " 
		  'action',   'text' ,  # @@@@@ tbl " enum?
		  'duration',	'fooBar',
		  'lastmodified', 'date-time',
		  'tzoffsetto', 'text',   # @@
		  'tzoffsetfrom', 'text',   
		  'tzname', 'text',   
		  'summary', 'text',
		  'sequence', 'integer', # 4.8.7.4 Sequence Number
		  'uid', 'text', # 4.8.4.7 Unique Identifier
		 );

my(%ValueTypeD) = ('dtend', 'date-time', # 4.8.2.2 Date/Time End
		   'dtstart', 'date-time' # 4.8.2.4 Date/Time Start
		  );

my(@component) = ("Vevent" , "Vtodo" , "Vjournal" , "Vfreebusy"
                        , "Vtimezone" ); # / x-name / iana-token)

# PRODID should be a URI, but it's not, so we just
# treat it as text. sigh. hmm... use it as namespace
# for x- fields?

# VERSION: likewise, kinda worthless.

while(1){
  while(($line = <>) =~ s/^\s+//){  # continuation lines
    $field .= $line;
  }

  $field =~ s/\r?\n//g; # get rid of newlines

  if($field =~ /^BEGIN:(\w+)/i){
    my($n) = ($1);
    printf "\n>" if $intag;
    if($nsDone){
      if(grep(lc($_) eq lc($n), @component)){
	$n = camelCase($1, 1);

	if($#stack == 0){ # jump out of VCALENDAR
	  my($m);
	  $m=pop(@stack);
	  printf("  </%s>\n", $m);
	}
	printf "  <%s>\n", $n;
      }
      elsif(grep(lc($_) eq lc($n), @resProps)){
	$n = camelCase($n);

	printf "  <%s rdf:parseType='Resource'>", $n;
      }else{
	$n = camelCase($n);
	printf "  <%s>", $n;
      }
    }else{
      $n = camelCase($n, 1);
      &startDoc($n);
      $nsDone = 1;
    }
    push(@stack, $n);
  }
  elsif($field =~ /^END:(\w+)/i){
    my($n) = $1;
    printf "\n>" if $intag;
    $intag = 0;

    last if ($#stack < 0 && lc($n) eq 'vcalendar');

    my($m);
    $m=pop(@stack);
    warn "mismatch [$n] expected [$m]" unless lc($n) eq lc($m);

    printf "  </%s>\n", $m;
  }
  elsif($field =~ s/^([\w-]+)([;:])\s*/$2/){
    my($n) = ($1);
    my($enc, $iprop, %attrs, $attrp, $xprop);

    if($n =~ s/^X-//i){
      if(!$X_ns){
	warn "@@ TODO: implement getting X- namespace URI from command line or PRODID: $n\n";
	$field = $line;
	next;
      }
      $xprop = 1
    };
    $n = camelCase($n);
    if($xprop){ $n = "x:" . $n };

    printf "    <%s", $n;

    while($field =~ s/^;([\w-]+)=([^;:]+)//){
      my($an, $av) = (camelCase($1), $2);
      if($an eq 'value'){
	$iprop = camelCase($av);
      }else{
	$attrs{$an} = $av;
	#warn "found attr on $n: $an = $av";
	$attrp = 1;
      }
    }

    if(! $iprop) { $iprop = $ValueType{$n} || $ValueTypeD{$n} };

    if(! $iprop) { die "no value type given, default unknown: $n $field" };


    while($field =~ s/^;([\w-]+)//){
      $enc = $1;
    }

    if($field =~ s/^:\s*(.*)//){
      my($v) = ($1);
      if($enc eq 'QUOTED-PRINTABLE'){ #@@ case sensitive?
	$v =~ s/=(..)/hex($1)/ge;
      }
      elsif($enc){
	warn "unkown enc", $enc;
      }

      if(grep($_ eq $n, @symbolProps)){
	$v = camelCase($v);
	#hmm... another namespace for enumerated values?
	printf(" rdf:resource='%s%s'/>\n", $ICal_ns, $v);
      }
      elsif(grep($_ eq $n, @refProps)){
	$v =~ s/^MAILTO:/mailto:/; #fix borkenness

	printf(" rdf:parseType='Resource'>\n");
	printf "      <value rdf:resource='%s'/>\n", asAttr($v);

	my($an);
	foreach $an (keys %attrs){
	  my($av) = $attrs{$an};
	  printf("      <%s>%s</%s>\n", $an, asContent($av), $an);
	  #warn "serialized attr $an = $av";
	}

	warn "conflicting VALUE param $iprop on $n" if $iprop;

	printf "    </%s>\n", $n;
      }
      elsif(grep($_ eq $n, @valProps)){
	printf(" rdf:parseType='Resource'>\n");

	if($n eq 'rrule'){
	  while($v =~ s/^([\w-]+)=([^;:]+);?//){
	    my($an, $av) = (camelCase($1), $2);
	    $attrs{$an} = $av;
	  }
	}else{
	  $v = lexForm($iprop, $v);
	  printf("      <%s>%s</%s>\n", $iprop, asContent($v), $iprop);
	}

	my($an); #@@duplicated code
	foreach $an (keys %attrs){
	  my($av) = $attrs{$an};
	  printf("      <%s>%s</%s>\n", $an, asContent($av), $an);
	  #warn "serialized attr $an = $av";
	}

	printf "    </%s>\n", $n;

      }
      else{

	$v = lexForm($iprop, $v);
	printf ">%s</%s>\n", asContent($v), $n;

	warn "unexpected attrs on $n" if $attrp;
      }
    }else{
      warn "field garbage: [", $field, "]"
    }
  }

  else{
    last if eof;
    warn "what???", $_;
  }

  $field = $line;
}

printf "\n>" if $intag;
printf "</rdf:RDF>\n";



sub startDoc{
  my($n) = @_;

  #@@TODO: add X- namespace
  printf(
"<rdf:RDF
  xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'
  xmlns='%s'
  xmlns:i='%s'
  xmlns:x='%s'
><%s rdf:about=''>
",
	 $ICal_ns, $ICal_ns, $X_ns, $n);
}

sub asContent{
    my($c) = @_;

    $c =~ s,&,&amp;,g;
    $c =~ s,<,&lt;,g;
    $c =~ s,>,&gt;,g;
    $c =~ s/[\200-\377]/'&#'.ord($&).';'/ge;

    #@@hhm... protect newlines too?

    return $c
}

sub lexForm{
  my($iprop, $v) = @_;

  if($iprop eq 'text'
     || $iprop eq 'uri'
     || $iprop eq 'integer'){
    # do nothing
  }
  elsif($iprop eq 'date-time'){
    $v =~ s/(\d\d\d\d)(\d\d)(\d\d)T(\d\d)(\d\d)(\d\d)(.*)/$1-$2-$3T$4:$5:$6$7/;
  }else{
    die "unknown iprop $iprop; dunno what to do with value '$v'";
  }

  return $v;
}


sub asAttr{
  my($c) = @_;
  
  $c =~ s,&,&amp;,g;
  $c =~ s,<,&lt;,g;
  $c =~ s,>,&gt;,g;
  $c =~ s,\",&quot;,g;
  $c =~ s,\',&apos;,g;
  $c =~ s/[\200-\377]/'&#'.ord($&).';'/ge;
  
  #@@hhm... protect newlines too?
  
  return $c
}


sub camelCase{
  my($n, $initialCap) = @_;

  my(@words) = map(lc, split(/-/, $n));

  if($initialCap){
    return join('', map(ucfirst, @words));
  }else{
    return $words[0] . join('', map(ucfirst, @words[1..$#words]));
  }
}

sub testCamelCase{
  my(@cases, $n);

  @cases = ("DTSTART", "LAST-MODIFIED");
  foreach $n (@cases){
    printf "case: %s: prop: %s class: %s\n",
      $n, camelCase($n), camelCase($n, 1);
  }
}


# Reading thru the ical spec
#  http://www.ietf.org/rfc/rfc2445.txt
#
# @@TODO: unfolding
# @@TODO: params

# $Log$
# Revision 1.8  2004-10-28 17:42:00  timbl
# Fix bugs in cwm --patch
# diff.py now can generate weak deltas when necessary, when the graphs are not solid.
# Offline working hack in webaccess.py
# Fixed bug in lllyn.py with interning of datatyped literals giving diff objects for same type  sometimes.
#
# Revision 1.7  2003/04/14 21:20:51  connolly
# ical section done
#
# Revision 1.6  2002/12/13 18:55:21  connolly
# added --xnames option to give namespace
# for X- properties
#
# Revision 1.5  2002/09/03 17:20:41  connolly
# handle individual vevents
#
# Revision 1.4  2002/07/18 05:26:36  connolly
# be more conservative about X- stuff
#
# Revision 1.3  2002/07/18 05:16:32  connolly
# oops! got ical URI wrong! thx daml validator
#
# Revision 1.2  2002/07/17 20:59:40  connolly
# using ical:value in stead of rdf:value
#
# Revision 1.1  2002/07/17 20:34:55  connolly
# moving from palmagent
#
# Revision 1.6  2002/07/16 05:02:23  connolly
# rudimentary rrule parsing
#
# Revision 1.5  2002/07/16 04:36:46  connolly
# camelCase
#
# Revision 1.4  2002/06/29 06:13:51  connolly
# produces pretty good RDF from my evolution calendar now;
# handles several different flavors of properties.
#
# Revision 1.3  2002/06/29 04:19:40  connolly
# turns some ical files (from evolution) into nearly RDF.
# it's wf XML, at least.
# need to deal with VALUE= attributes and such.
#
# Revision 1.2  2001/07/27 16:47:43  connolly
#  seems to work on my korganizer calendar (addeds support for
#     ;params and QUOTED-PRINTABLE).
#
# 1.1 seems to work on two test files from my nokia cellphone.
