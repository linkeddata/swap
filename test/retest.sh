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
tests=0
passes=0

function cwm_test () {
  case=$1; desc=$2
  shift; shift;
  args=$*
  echo
  tests=$(($tests+1))
  echo Test $case: $desc
  echo "   "    cwm $args

  if !(python ../cwm.py -quiet $args | sed -e 's/\$[I]d.*\$//g' > temp/$case);
  then echo CRASH $case;
  elif ! diff -Bbwu ref/$case temp/$case >diffs/$case;
  then echo DIFF FAILS: less diffs/$case;
  elif [ -s diffs/$case ]; then echo FAIL: $case: less diffs/$case "############"; wc ref/$case temp/$case;
  else passes=$(($passes+1)); fi
}

cwm_test animal.n3 "Parse a small RDF file, generate N3" -rdf animal.rdf -n3

cwm_test animal-1.rdf "Parse a small RDF file and regenerate RDF" -rdf animal.rdf

cwm_test reluri-1.rdf "test generation of relative URIs" reluri-1.n3 --rdf

cwm_test contexts-1.n3 "Parse and generate simple contexts" contexts.n3

cwm_test anon-prop-1.n3 "Parse and regen anonymous property" anon-prop.n3

cwm_test daml-ont.n3 "Convert some RDF/XML into RDF/N3" daml-pref.n3 -rdf daml-ont.rdf -n3

cwm_test strquot.n3 "N3 string quoting" -n3 strquot.n3

cwm_test lstring-out.n3 "N3 string nested triple quoting" --n3 syntax/lstring.n3

#oops... misleading test case name.
cwm_test equiv-syntax.n3 "conversion of N3 = to RDF" -n3 equiv-syntax.n3 -rdf

cwm_test daml-ont-piped.n3 "Pipe mode for flat n3 to n3" daml-ont.n3 --pipe

cwm_test lists-simple.n3 "parsing and generation of N3 list () syntax" -n3 lists-simple.n3

cwm_test lists-simple-1.rdf "conversion of N3 list () syntax to RDF" -n3 lists-simple.n3 -rdf

cwm_test prefix1.rdf "Avoiding default namespace on attrs" -rdf norm/fix.rdf

cwm_test prefix2.rdf "Avoiding default namespace on attrs" -rdf norm/fix.rdf -rdf=d

cwm_test prefix3.rdf "Avoiding default namespace on attrs" -rdf norm/fix.rdf -rdf=p


# The prefix file is to give cwm a hint for output. It saves hints across files.
# cwm_test daml-ont.n3 "Convert DAML schema into N3" daml-pref.n3 -rdf daml-ont.rdf -n3
# This seems to be a duplicate of a test above.

cwm_test daml-ex.n3 "Try the examples" daml-pref.n3 -rdf daml-ex.rdf -n3

echo
echo "        Test log:implies rules:"


cwm_test rules12-1.n3 "log:implies Rules - try one iteration first." rules12.n3 -rules

cwm_test rules12-n.n3 "log:implies rules, iterating" rules12.n3 -think

cwm_test rules13-1.n3 "log:implies rules more complex, with means, once" rules13.n3 -rules

cwm_test rules13-n.n3 "log:implies rules more complex, with means, many times" rules13.n3 -think

cwm_test two-route.n3 "test different rules giving same result" two-route.n3 -think

cwm_test schema1.n3 "Schema validity 1" daml-ex.n3 invalid-ex.n3 schema-rules.n3 -think

cwm_test schema2.n3 "Schema validity using filtering out essential output" daml-ex.n3 invalid-ex.n3 schema-rules.n3 -think -filter=schema-filter.n3

cwm_test underbarscope-out.n3 "The scope of _:me should be the document" underbarscope.n3 --think

echo
echo "        Test list handling"

cwm_test li-r1.n3  "Inference using lists"  list/r1.n3 -think

echo
echo "        Test builtins:"

cwm_test bi-t1.n3 "Simple use of log:includes" includes/t1.n3 -think

cwm_test bi-t2.n3 "Simple use of log:includes" includes/t2.n3 -think

cwm_test bi-t3.n3 "Simple use of log:includes" includes/t3.n3 -think

cwm_test bi-t4.n3 "Simple use of log:includes - negative test" includes/t4.n3 -think

# Drop this until/unless we have formulae compare (by internment?) .  The graph isomorphism prob.
#cwm_test bi-t5.n3 "Simple use of log:includes" includes/t5.n3 -think

cwm_test bi-t6.n3 "Simple use of log:includes" includes/t6.n3 -think

cwm_test bi-t7.n3 "Simple use of log:includes" includes/t7.n3 -think

cwm_test bi-t8.n3 "Simple use of string built-ins" includes/t8.n3 -think

cwm_test bi-t9.n3 "Filter event by date using strcmp BI's" includes/t9br.n3 -think

cwm_test bi-t10.n3 "log:resolvesTo and log:includes" includes/t10.n3 -think

cwm_test bi-t11.n3 "log:resolvesTo and log:includes - schema checking" includes/t11.n3 -think

cwm_test endsWith-out.n3 "string:endsWith" string/endsWith.n3 -rules

cwm_test bi-quant.n3 "log:includes handling of univ./exist. quantifiers" includes/quantifiers.n3 -think

cwm_test bi-concat.n3 "Test string concatetnation built-in" includes/concat.n3 -think

cwm_test bi-uri-startswith.n3 "Dan's bug case with uri and startswith" includes/uri-startswith.n3 -think

cwm_test resolves-rdf.n3 "log:resolvesTo with RDF/xml syntax" resolves-rdf.n3 -think

cwm_test sameDan.n3 "dealing with multiple descriptions of the same thing using log:lessThan, log:uri, daml:equivalentTo" sameDan.n3 sameThing.n3 --think --apply=forgetDups.n3 --purge

cwm_test timet1.n3 "basic ISo time handling functions" time/t1.n3 --think --purge

cwm_test smush.rdf "Data aggregation challenge from Jan 2001" --rdf smush-examples.rdf --n3 smush-schema.n3 sameThing.n3 --think --apply=forgetDups.n3 --purge --filter=smush-query.n3 --rdf

cwm_test vblsNotURIs-out.n3 "Should not get URIs of anonymous nodes" --rdf animal.rdf --n3 vblsNotURIs.n3 --think

cwm_test n3ExprFor-out.n3 "Parsing strings with n3ExprFor" includes/n3ExprFor.n3 --think

TEST_PARAMETER_1=TEST_VALUE_1; export TEST_PARAMETER_1 
cwm_test environ.n3 "Read operating system environment variable" os/environ.n3 -think

TARGET=roadmap/test.graph; export TARGET
cwm_test roadmap-test.dot "using notIncludes and --strings to make a graphviz file"  roadmap/todot.n3 --think --strings

cwm_test conjunction.n3 "log:conjunction of formulae" includes/conjunction.n3 --think

cwm_test conclusion.n3  "log:conclusion deductive closure" includes/conclusion.n3 --think

cwm_test argv-1.n3 "os:argv argument values"  os/argv.n3 --think --with foo bar baz

cwm_test argv-2.n3 "os:argv argument other values"  os/argv.n3 --think --with boof

# echo  "Test applications"

echo "Passed $passes out of $tests tests."

# $Log$
# Revision 1.37  2002-07-01 20:46:53  timbl
# mmm
#
# Revision 1.36  2002/06/23 21:08:31  timbl
# Add cwm_time.py.  Thanks, Mark Nottingham! mnot.com
#
# Revision 1.35  2002/06/07 13:45:29  timbl
# Missing test
#
# Revision 1.34  2002/05/21 00:13:30  timbl
# Add string:endsWith
#
# Revision 1.32  2002/03/30 22:06:24  timbl
# Add test for n3ExprFor
#
# Revision 1.30  2002/03/17 04:24:12  timbl
# catch up
#
# Revision 1.29  2002/03/12 20:57:17  timbl
# Passed test/retest.sh
#
# Revision 1.28  2002/02/22 04:14:26  timbl
# Add norm/fix.rdf tests for namespaces on attributes
#
# Revision 1.27  2002/01/10 01:40:50  timbl
# Add os:argv tests
#
# Revision 1.26  2001/12/31 04:33:23  timbl
# Simple tests on log:conjunction and log:conclusion seem to work
#
# Revision 1.25  2001/12/29 04:00:42  timbl
# Minor fixes. See ./util for bits of validator
#
# Revision 1.23  2001/12/02 22:42:28  timbl
# Added roadmap test
#
# Revision 1.22  2001/11/19 15:25:16  timbl
# quantifiers
#
# Revision 1.21  2001/11/15 22:11:24  timbl
# --string added, list output bugs fixed, quotation choices changed on output, log:includes hudes handles quantified variables better
#
# Revision 1.20  2001/09/19 19:14:28  timbl
# new schemas for builtins etc
#
# Revision 1.19  2001/09/17 02:59:32  timbl
# split up
#
# Revision 1.18  2001/09/07 02:07:52  timbl
# string.concatenation
#
# Revision 1.17  2001/08/30 21:29:16  connolly
# resolves-rdf.n3 case
#
# Revision 1.16  2001/08/27 12:45:57  timbl
# Runs most of retest, not all builtins. List handling started but not tested.
#
# Revision 1.15  2001/08/09 21:38:09  timbl
# See cwm.py log
#
# Revision 1.14  2001/07/20 16:21:59  connolly
# split smush-query out of smush-schema; added expected results, entry in retest.sh
#
# Revision 1.13  2001/07/19 16:56:00  connolly
# whoohoo! node merging works!
#
# Revision 1.12  2001/06/25 06:35:51  connolly
# fixed some bugs in def relativeURI(base, uri):
#
# Revision 1.11  2001/06/13 23:58:48  timbl
# Fixed bug in log:includes that bindings were not taken into target of includes
#
# Revision 1.10  2001/05/30 22:03:40  timbl
# mmm
#
# Revision 1.9  2001/05/21 14:35:47  connolly
# sorted @prefix directives by prefix on output
#
# Revision 1.8  2001/05/21 13:04:02  timbl
# version field expansion deletion was expanded -- now fixed
#
# Revision 1.7  2001/05/21 11:27:48  timbl
# Ids stripped
#
# Revision 1.5  2001/05/10 06:04:23  connolly
# remove more Id stuff
#
# Revision 1.4  2001/05/09 15:06:36  connolly
# fixed string parsing, updated DAML+OIL namespace; added tests for string parsing and bits of N3 syntax that depend on the choice of DAML namespace
#
# Revision 1.3  2001/05/08 05:37:46  connolly
# factored out common parts of retest.sh; got two test cases working. don't grok the rest.
#
