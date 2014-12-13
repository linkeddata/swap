
# http://www.dajobe.org/2004/01/turtle/tests/manifest.ttl  incldues long ones
# Note http://www.w3.org/2001/sw/DataAccess/df1/tests is the same stuff,
# in cvs-accessible space.
# turtle-manifest.n3 doesn't

CWM = ../../cwm.py
D=http://www.w3.org/2001/sw/DataAccess/df1/tests


TESTS := http://www.w3.org/2000/10/swap/test/n3parser.tests ../jena/n3_jena.tests  turtle-manifest.n3 $D/manifest-bad.ttl

#TESTS := http://www.w3.org/2000/10/swap/test/n3parser.tests http://www.dajobe.org/2004/01/turtle/tests/manifest.ttl http://www.dajobe.org/#2004/01/turtle/tests/manifest-bad.ttl
#=======
#TESTS := http://www.w3.org/2000/10/swap/test/n3parser.tests ../jena/n3_jena.tests  turtle-manifest.n3 http://www.dajobe.org/2004/01/turtle/#tests/manifest-bad.ttl

test_results.html : test_results.n3* makeReport.n3
	$(CWM) $^ makeReport.n3 --crypto --think --purge --strings > test_results.html

js_results.html : js_results.n30 makeReport.n3
	$(CWM) $^ --crypto --think --purge --strings > js_results.html

js_results.n30 : ../../pyjs/js_cmd ../../pyjs/n3parser.js
	export CLASSPATH=.:..:/usr/share/java/oro.jar:/usr/share/java/regexp.jar:/usr/share/java:/usr/share/java/ant.jar:/usr/share/java/ant-launcher.jar:/usr/share/java/ant:/usr/share/java/ant/ant-apache-oro.jar:/home/syosi/tarballs/jena/Jena-2.1/lib/antlr.jar:/home/syosi/tarballs/jena/Jena-2.1/lib/jena.jar:/home/syosi/tarballs/jena/Jena-2.1/lib/commons-logging.jar:/home/syosi/tarballs/jena/Jena-2.1/lib/xercesImpl.jar && PYTHONPATH=`pwd`/../..:`pwd`/../../..   ./tester.py -c js_cmd -o js_results.n3 ../n3parser.tests

test_results.n3* : commandList
	export CLASSPATH=.:..:/usr/share/java/oro.jar:/usr/share/java/regexp.jar:/usr/share/java:/usr/share/java/ant.jar:/usr/share/java/ant-launcher.jar:/usr/share/java/ant:/usr/share/java/ant/ant-apache-oro.jar:/home/syosi/tarballs/jena/Jena-2.1/lib/antlr.jar:/home/syosi/tarballs/jena/Jena-2.1/lib/jena.jar:/home/syosi/tarballs/jena/Jena-2.1/lib/commons-logging.jar:/home/syosi/tarballs/jena/Jena-2.1/lib/xercesImpl.jar && PYTHONPATH=`pwd`/../..:`pwd`/../../..   ./tester.py -c commandList -o test_results.n3 $(TESTS)
