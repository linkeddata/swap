#!/usr/bin/perl
#
# converts n-triples to KIF
#
# USAGE:
#  perl n-triples2kif.pl <foo.nt > foo.kif
#
# REFERENCES
#  n-triples:  working specification
#    is a message I sent 30 May
#    http://lists.w3.org/Archives/Public/w3c-rdfcore-wg/2001May/0264.html
#    ratified in RDF Core WG 1 Jun telcon
#    http://lists.w3.org/Archives/Public/w3c-rdfcore-wg/2001Jun/0008.html "
#
#  KIF
#    Knowledge Interchange Format draft proposed American National Standard (dpANS)
#    NCITS.T2/98-004
#    Last Modified: Thursday, 25-Jun-98 22:31:37 GMT 
#    http://logic.stanford.edu/kif/dpans.html
#
# TODO:
#  integrate this into cwm? offer the resulting RDF->KIF
#  conversion as an HTTP service?
#  ... other issues noted @@ below
#
# $Id$
# see changelog at end

use strict;

my (@Ex, @Conjuncts);

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
  my($s, $t, $f);

  print "(exists (";
  foreach $t (@Ex){
    print "$t ";
  }
  print ")\n (and \n";

  foreach $f (@Conjuncts){
    my($p, $s, $o);
    ($s, $p, $o) = @$f;

    print "  (PropertyValue $p\n     $s\n     $o)\n"; #@@ PropertyValue ala DAML axiomatic semantics. not holds, because I don't think we want to interpret RDF predicates as 1st-order predicates.
  }

  print ") )\n";
}


sub statement{
  my($s, $p, $o) = @_;

  push(@Conjuncts, [$s, $p, $o]);
}

sub term{
  my($t, $litOK) = @_;

  if($t =~ s/^<//){
    if($t =~ s/>$//){

      $t =~ s/([^a-zA-Z0-9])/\\$1/g; # escape all but letters and digits
      #@@ actually, KIF is case-insensitive, so I should escape the lowercase letters too. But I consider that a KIF bug, not something to fix here.
      # also, I could escape fewer characters; I haven't checked which characters are allowed in a kif word unescaped.
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
      push(@Ex, $t) unless grep($_ eq $t, @Ex);
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
# Revision 1.4  2001-06-07 20:03:37  connolly
# debugged sneaky ; vs . thing
#
# Revision 1.3  2001/06/07 19:49:48  connolly
# rather: _:1 -> ?x1 to match the test data I already generated
#
# Revision 1.2  2001/06/07 19:48:34  connolly
# handle _:1 -> ?ex1
#
# Revision 1.1  2001/06/07 19:22:43  connolly
# works, at least on the RDF schema for DAML
#

