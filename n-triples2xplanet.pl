#!/usr/bin/perl
#
# converts n-triples to xplanet marker file
#
# USAGE:
#  perl n-triples2xplanet.pl <foo.nt > foo.txt
#  xplanet -window -markerfile foo.txt
#
# REFERENCES
#  n-triples:  working specification
#    is a message I sent 30 May
#    http://lists.w3.org/Archives/Public/w3c-rdfcore-wg/2001May/0264.html
#    ratified in RDF Core WG 1 Jun telcon
#    http://lists.w3.org/Archives/Public/w3c-rdfcore-wg/2001Jun/0008.html "
#
# xplanet
#  http://xplanet.sourceforge.net/
#  debian xplanet package
#
# $Id$
# see changelog at end

use strict;

my (@Markers, %X, %Y, %Label, %Align, %Color);
my ($Map) = 'http://www.w3.org/2000/10/swap/pim/earthMap';

&slurp();
&burp();

sub slurp{
  while(<>){
    my($S, $P, $O, $st, $pt, $ot);
    
    next unless /\S/; # skip blank lines
    s/^\s*//; # trim leading space
    s/\s*\.\s*$//; # trim trailing space and .
    
    ($S, $P, $O) = split(/ +/, $_, 3);
    if($st = term($S, 0)){
      # OK
    }
    else{
      die "bogus subject: $S";
    }
    
    if($pt = term($P, 0)){
      # OK
    }
    else{
      die "bogus predicate: $P";
    }
    
    if($ot = term($O, 1)){
      statement($st, $pt, $ot);
    }
    else{
      die "bogus object: $O";
    }
  }
}

sub burp{
  my($m);
  foreach $m (@Markers){
    if($Y{$m} && $X{$m}){
      printf ("%s %s %s", $Y{$m}, $X{$m}, $Label{$m});
      printf (" align=%s", $Align{$m}) if $Align{$m};
      printf (" color=%s", $Color{$m}) if $Color{$m};
      print "\n"
    };
  }
}


sub statement{
  my($s, $p, $o) = @_;

  #print STDERR "statement: {$s} {$p} {$o}\n";

  if ($p eq 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
      && $o eq "$Map#Marker"){
    push(@Markers, $s);
  }
  elsif ($p eq "$Map#label"){
    $Label{$s} = $o;
  }
  elsif ($p eq "$Map#x"){
    $o =~ s/^\"//; $o =~ s/\"$//;
    $X{$s} = $o;
  }
  elsif ($p eq "$Map#y"){
    $o =~ s/^\"//; $o =~ s/\"$//;
    $Y{$s} = $o;
  }
  elsif ($p eq "$Map#xDMSd"){
    $X{$s} = fromDMSd($o);
  }
  elsif ($p eq "$Map#yDMSd"){
    $Y{$s} = fromDMSd($o);
  }
  elsif ($p eq "$Map#align"){
    $o =~ s/^\"//; $o =~ s/\"$//;
    $Align{$s} = $o;
  }
  elsif ($p eq "$Map#color"){
    $o =~ s/^\"//; $o =~ s/\"$//;
    $Color{$s} = $o;
  }
}

sub fromDMSd{
  my($o) = @_;
  my($ret);

  $o =~ s/^\"//; $o =~ s/\"$//;
  my($d, $m, $s, $dir);
  if($o =~ /(\d+)(-(\d+)(-(\d+))?)?([NSEW])/){
    ($d, $m, $s, $dir) = ($1, $3, $5, $6);
    $dir = ($dir eq 'N' || $dir eq 'E') ? 1 : -1;
    $ret = $dir * ($d + ($m + ($s / 60.0)) / 60.0);
    #print STDERR " fromDMSd: $o ==> $d $m $s ==> $ret\n";
    return $dir * ($d + ($m + ($s / 60.0)) / 60.0);
  }

  die "bad DMSs: $o";
}


sub term{
  my($t, $litOK) = @_;

  if($t =~ s/^<//){
    if($t =~ s/>$//){

      return $t;
    }
    else{
      return undef
    }
  }
  elsif($t =~ s/^\"//){
    if($litOK && $t =~ s/\"$//){
      #@@string unquoting
      return "\"$t\"";
    }
    else{
      return undef;
    }
  }
  elsif($t =~ s/^\_\://){
    if($t =~ /^[a-zA-Z0-9]+$/){
      $t = '?x' . "$t";
      return $t;
    }
    else{
      return undef;
    }
  }
  else{
    return undef;
  }
}
    

# $Log$
# Revision 1.4  2002-02-10 03:26:42  connolly
# Jan 23: namespace is in swap/pim now
#
# Revision 1.3  2001/11/11 07:52:07  connolly
# no blank lines (trying to debug xplanet's display of these marker files)
#
# Revision 1.2  2001/11/11 03:46:06  connolly
# handles marker color now
#
# Revision 1.1  2001/11/11 03:34:52  connolly
# works for a few WebOnt WG members
#

