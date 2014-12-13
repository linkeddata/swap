#!/bin/perl
#
# $Id$
# see changelog at end

use strict;

# http://www.oplnk.net/~ajackson/software/PostScript-MailLabels-2.02.tar.gz
# md5sum 2853fa006708d5473dc21b54ef211320 PostScript-MailLabels-2.02.tar.gz
use PostScript::MailLabels;

my($mm) = .1; # milimeter; .1 centimeters
my($paA, $paBL, $paBR, $paC);

if(0){
# jobie is an Epson Stylus Color 740
# http://support.epson.com/hardware/printer/inkjet/sc740_/documentation.html
# User Manual  
# http://files.support.epson.com/pdf/sc740_/sc740_u1.pdf
# from p171, Printable Area

$paA = 3 * $mm; #minimum top
$paBL = 3 * $mm; # minimum left
$paBR = 9 * $mm; # minimum right, letter
$paC = 14 * $mm; # minimum bottom
}else{
# pesco is an HP PSC 2510 Photosmart All-in-One
# 
# pg 118 of the manual
# http://h10032.www1.hp.com/ctg/Manual/c00043654.pdf

$paA = 1.8 * $mm; #minimum top
$paBL = 8 * $mm; # minimum left # DWC 6.4 didn't work
$paBR = 2 * $mm; # minimum right, letter
$paC = 11.7 * $mm; # minimum bottom
}

main();

# Hmm... what schema to use for labels?
# the MailingLabels demo/std_business.pl claims
# to implement "USPS standard components". Using those
# keywords with google, I found this, which looks relevant:
#
# Publication 63 - Designing Flat Mail
# http://pe.usps.gov/cpim/ftp/pubs/Pub63/Pub63.pdf

sub main{
  my($labels);

  $labels = PostScript::MailLabels->new;
  $labels->labelsetup(Units => 'metric',

		      Printable_Left => $paBL,
		      Printable_Right => $paBR,
		      Printable_Top => $paA,
		      Printable_Bot => $paC,

		      avery => 5160, # the product I have is 8160, but I peeked at the definitions and this is evidently how the 8160 stuff is known to the MailLabels module
		      x_adjust => 0.1, # what units?

		     );

  my(@addrs) = readLabels();

  print $labels->makelabels(\@addrs);
}


sub readLabels{
  my(@ret);
  my(@fields);
  my(%schema);
  %schema = ('recipientName' => 0,
	     # skip last name
	     'deliveryAddress' => 2,
	     'cityName' => 3,
	     'stateAbbr' => 4,
	     'zipCode' => 5 );

  while(<>){
    if(/<(\w+:)?MailingLocation>/ #@@KLUDGE namespace prefix
       || /<(\w+:)?Description>/ #@@KLUDGE again!
      ){
      @fields = (undef, undef, undef, undef, undef, undef, undef, undef);
    }

    elsif(m,</(\w+:)?MailingLocation>,
	  || m,</(\w+:)?Description>, #@@KLUDGE again!
	 ){
      print STDERR "@@ record: ", join("|", @fields), "\n";

      push(@ret, [@fields]);
    }
    
    if(m,<(\w+:)?(\w+)>([^>]+)</(\w+)>,){
      my($pfx, $n, $d) = ($1, $2, $3);
      $d =~ s/&#38;/&/g;
      $d =~ s/&amp;/&/g;

      print STDERR "@@ $n `$d' [ $schema{$n} ]\n";

      if(defined($schema{$n})){
	$fields[$schema{$n}] = $d;
      }
    }
  }

  return @ret;
}

# $Log$
# Revision 1.4  2004-12-20 18:38:16  connolly
# tweaked for PescoPrinter, an HP PSC 2510
#
# Revision 1.3  2003/04/14 17:29:02  connolly
# 25Dec: markup tweak
#
# Revision 1.2  2002/06/12 15:41:05  connolly
# tweak of 16 Apr
#
# Revision 1.1  2002/01/21 23:16:49  connolly
# works in at least one test case
#
# Revision 1.3  2001/12/30 08:22:03  connolly
# I am starting to be able to project families onto the globe
#
# Revision 1.2  2001/12/30 00:36:00  connolly
# labels working...
#
# Revision 1.1  2001/12/29 22:00:56  connolly
# Initial revision
#
