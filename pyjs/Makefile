#  Make tests of the pyjs translated n3parser,js
#
# This is or was http://www.w3.org/2000/10/swap/test/pyjs/Makefile
#
W=../../../..
T=../test/n3

D=http://www.w3.org/2001/sw/DataAccess/df1/tests

# We have a more limited version without the latrge tests whcih are slow
# With no base URI, cannot handle relative URI in @prefixmanifest.ttl 

# The bad turtle tests are often good N3 tets, which we pass.
# http://www.dajobe.org/2004/01/turtle/tests/manifest-bad.ttl


#  ../jena/n3_jena.tests
TESTS := http://www.w3.org/2000/10/swap/test/n3/n3-rdf.tests  http://www.w3.org/2000/10/swap/test/n3/turtle-manifest.n3

S=$W/2000/10/swap
C=$S/cwm.py
J='CLASSPATH="/devel/rhino/rhino1_6R5/js.jar" java org.mozilla.javascript.tools.shell.Main'

n3parser.js : utf8.js missing.js not3.js
	cat  utf8.js missing.js not3.js > n3parser.js

js_results.html : js_results.n30 $T/makeReport.n3
	$C $^ --crypto --think --purge --strings > js_results.html

js_results.n30 : n3parser.js
	$T/tester.py -c js_cmd -o js_results.n3 $(TESTS)

,publish : /devel/dig/2005/ajar/ajaw/js/rdf/n3parser.js
	touch ,publish

/devel/dig/2005/ajar/ajaw/js/rdf/n3parser.js : n3parser.js
	cp n3parser.js /devel/dig/2005/ajar/ajaw/js/rdf/n3parser.js

not3.js : not3a.js fix.sed
	sed < not3a.js -f fix.sed  > not3.js

not3a.js : pyjs.py not3p.py
	python pyjs.py not3p.py > not3a.js

not3p.py : not3.py pre.sed
	sed < not3.py -f pre.sed  > not3p.py


