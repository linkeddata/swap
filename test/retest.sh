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
  case=$1; desc=$2
  shift; shift;
  args=$*
  echo
  echo TEST $case: $desc
  echo TEST cwm $args
  # Hmm... this suggests a --nocomments flag on cwm
  (python ../cwm.py $args | perl -ne 'print unless /^\s*#/ || /\$Id/ || /Id:/' > temp/$case) || echo CRASH $case
  diff -bwu ref/$case temp/$case >diffs/$case
  if [ -s diffs/$case ]; then echo FAIL: $case: see diffs/$case; else echo PASS $case; fi
}

cwm_test animal.n3 "Parse a small RDF file, generate N3" -rdf animal.rdf -n3

cwm_test animal-1.rdf "Parse a small RDF file" -rdf animal.rdf

cwm_test strquot.n3 "N3 string quoting" -n3 strquot.n3

cwm_test equiv-syntax.n3 "conversion of N3 = to RDF" -n3 equiv-syntax.n3 -rdf

cwm_test lists-simple.n3 "parsing and generation of N3 list () syntax" -n3 lists-simple.n3

cwm_test lists-simple-1.rdf "conversion of N3 list () syntax to RDF" -n3 lists-simple.n3 -rdf

exit 0 # Tim, please update the expected results (ref/*)
       # of the rest of these tests. -- DWC

cwm_test daml-ont.n3 "dan doesn't grok this one@@" daml-pref.n3 -rdf daml-ont.rdf -n3


cwm_test daml-ex.n3 "Try the examples" daml-pref.n3 -rdf daml-ex.rdf -n3

cwm_test rules12-1.n3 "Try some inference @@what is this test really about?" rules12.n3 -rules

cwm_test rules12-n.n3 "Try some inference @@what is this test really about?" rules12.n3 -think

cwm_test rules13-1.n3 "Try some inference @@what is this test really about?" rules13.n3 -rules

cwm_test rules13-n.n3 "Try some inference" rules13.n3 -think

cwm_test schema1.n3 "Schema validity" daml-ex.n3 invalid-ex.n3 schema-rules.n3 -think

cwm_test schema2.n3 "@@test case description?" daml-ex.n3 invalid-ex.n3 schema-rules.n3 -think -filter=schema-filter.n3

# $Log$
# Revision 1.5  2001-05-10 06:04:23  connolly
# remove more Id stuff
#
# Revision 1.4  2001/05/09 15:06:36  connolly
# fixed string parsing, updated DAML+OIL namespace; added tests for string parsing and bits of N3 syntax that depend on the choice of DAML namespace
#
# Revision 1.3  2001/05/08 05:37:46  connolly
# factored out common parts of retest.sh; got two test cases working. don't grok the rest.
#
