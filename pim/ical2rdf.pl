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

my($ICal_ns) = 'http://www.w3.org/2000/10/swap/ical#';
my($X_ns) = 'http://www.w3.org/2000/01/foo-X@@#'; #@@ get this from command-line? or from PRODID?

my(@stack);
my($intag);
my($field, $line);
my($nsDone);

$field = <>;

my(@symbolProps) = ('calscale', 'action', 'class', 'transp', 'start',
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

my(@component) = ("Vevent" , "Vtodo" , "Vjournal" , "Vfreebusy"
                        , "Vtimezone" ); # / x-name / iana-token)

# PRODID should be a URI, but it's not, so we just
# treat it as text. sigh. hmm... use it as namespace
# for x- fields?

# VERSION: likewise, kinda worthless.

# RRULE: @@parse the value


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
	  printf("</%s>\n", $m);
	}
	printf "<%s>", $n;
      }
      elsif(grep(lc($_) eq lc($n), @resProps)){
	$n = camelCase($n);

	printf "<%s rdf:parseType='Resource'>", $n;
      }else{
	$n = camelCase($n);
	printf "<%s>", $n;
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

    printf "</%s\n>", $m;
  }
  elsif($field =~ s/^([\w-]+)([;:])\s*/$2/){
    my($n) = ($1);
    my($enc, $iprop, %attrs, $attrp, $xprop);

    if($n =~ s/^X-//i){ $xprop = 1 };
    $n = camelCase($n);
    if($xprop){ $n = "x:" . $n };

    printf "<%s", $n;

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
	printf "<rdf:value rdf:resource='%s'/>\n", asAttr($v);

	my($an);
	foreach $an (keys %attrs){
	  my($av) = $attrs{$an};
	  printf("<%s>%s</%s>\n", $an, asContent($av), $an);
	  #warn "serialized attr $an = $av";
	}

	warn "conflicting VALUE param $iprop on $n" if $iprop;

	printf "</%s>\n", $n;
      }
      elsif(grep($_ eq $n, @valProps)){
	printf(" rdf:parseType='Resource'>\n");

	if($n eq 'rrule'){
	  while($v =~ s/^([\w-]+)=([^;:]+);?//){
	    my($an, $av) = (camelCase($1), $2);
	    $attrs{$an} = $av;
	  }
	}elsif($iprop){
	  printf("<%s>%s</%s>\n", $iprop, asContent($v), $iprop);
	}
	else{
	  #warn "no iprop for $n; using rdf:value";
	  printf("<rdf:value>%s</rdf:value>\n", asContent($v));
	}


	my($an); #@@duplicated code
	foreach $an (keys %attrs){
	  my($av) = $attrs{$an};
	  printf("<%s>%s</%s>\n", $an, asContent($av), $an);
	  #warn "serialized attr $an = $av";
	}

	printf "</%s>\n", $n;
      }elsif($iprop){
	printf(" i:%s='%s'/>\n", $iprop, $v);
	warn "unexpected attrs on $n" if $attrp;
      }else{
	printf ">%s</%s>\n", asContent($v), $n;
	warn "unexpected attrs on $n" if $attrp;
      }
    }else{
      warn "field garbage: [", $field, "]"
    }
  }

  else{
    warn "what???", $_;
  }

  $field = $line;
}

printf "\n>" if $intag;
printf "</rdf:RDF>\n";



sub startDoc{
  my($n) = @_;

  printf(
"<rdf:RDF
  xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'
  xmlns='%s'
  xmlns:i='%s'
  xmlns:x='%s'
><%s rdf:about=''>",
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
# Revision 1.1  2002-07-17 20:34:55  connolly
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
