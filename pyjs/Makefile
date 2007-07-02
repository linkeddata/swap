
W=../../../..
T=../test/n3

#  ../jena/n3_jena.tests
TESTS := ../test/n3parser.tests

S=$W/2000/10/swap
C=$S/cwm.py
J='CLASSPATH="/devel/rhino/rhino1_6R5/js.jar" java org.mozilla.javascript.tools.shell.Main'

n3parser.js : missing.js not3.js
	cat  missing.js not3.js > n3parser.js

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

not3a.js : pyjs.py not3.py
	python pyjs.py not3.py > not3a.js


