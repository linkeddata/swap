#! /bin/bash
# $Id$
#   Regression test for new versions of cwm - test xml and n3 conversion
#
#
#alias cwm=python ~/swap/cwm.py
# see also: changelog at end of file.
mkdir -p xtemp1
mkdir -p xtemp2
mkdir -p xdiffs
tests=0
passes=0

function xml_n3_test () {
  case=$1;
  shift;
  args=$*
  echo
  tests=$(($tests+1))
  echo Test $case

  cp $case xtemp1/$case  # Keep in same dir 
  if !(cat $case | python ../cwm.py -quiet -n3=d | sed -e 's/\$[I]d.*\$//g' > xtemp1/$case.n3);
  then echo CRASH $case;
  elif !(cat $case|python ../cwm.py -n3 -rdf  > xtemp1/$case.rdf; cat xtemp1/$case.rdf|python ../cwm.py -rdf -n3=d -quiet  | sed -e 's/\$[I]d.*\$//g' > xtemp1/$case.out.n3);
  then echo CRASH $case;
  elif ! diff -Bbwu xtemp1/$case.n3 xtemp1/$case.out.n3 >xtemp1/$case.diff;
  then echo DIFF FAILS: less xtemp1/$case.diff;
  elif [ -s xdiffs/$case ]; then echo FAIL: $case: less xtemp1/$case.diff "############"; wc xtemp1/$case*;
  else passes=$(($passes+1)); fi
}

for i in $*; do
	xml_n3_test $i
done

#ends
