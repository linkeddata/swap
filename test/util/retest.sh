#! /bin/bash
# $Id$
#   Regression test for new versions of cwm
#
# TODO: separate notation3 testing from cwm testing
#
#alias cwm=python ~/swap/cwm.py
# see also: changelog at end of file.
mkdir -p temp
mkdir -p diffs

function cwm_test () {
  case=$1; desc=$2; target=$3;
  shift; shift; shift;
  args=$*
  echo
  echo Test $case: $desc

  echo    cwm -quiet $args --with $target
  (python ../../cwm.py -quiet $args --with $target | sed -e 's/\$[I]d.*\$//g' > temp/$case) || echo CRASH $case
  diff -Bbwu ref/$case temp/$case >diffs/$case
  if [ -s diffs/$case ]; then echo FAIL: $case: less diffs/$case "############"; else echo Pass $case; fi
}

echo
echo "        Test validity tests (needs web access currently):"

cwm_test val-ok.n3 "Simple test of valid file" ok.n3 ../../util/validate.n3 --think -purge

cwm_test valr-ok.n3 "Recursive test of valid file" ok.n3 ../../util/validate.n3 ../../util/recurse.n3 --think -purge

cwm_test val-undec.n3 "Simple test of missing decls" undec.n3 ../../util/validate.n3 --think -purge

cwm_test val-invalid-ex.n3 "Simple test of invalid file" invalid-ex.n3 ../../util/validate.n3 --think -purge



# $Log$
# Revision 1.2  2002-01-04 16:56:26  timbl
# Tests of schema validation, need to be online.
#
# Revision 1.1  2002/01/04 16:19:03  timbl
# Tests for schema validation
#
