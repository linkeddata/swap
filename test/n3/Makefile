
CWM = ../../cwm.py
TESTS = ../n3parser.tests ../jena/n3_jena.tests

test_results.html : test_results.n3 makeReport.n3
	$(CWM) test_results.n3 makeReport.n3 --crypto --think --purge --strings > test_results.html

test_results.n3 : commandList $(TESTS)
	export CLASSPATH=/home/syosi/tarballs/jena/Jena-2.1/lib/antlr.jar:/home/syosi/tarballs/jena/Jena-2.1/lib/jena.jar:/home/syosi/tarballs/jena/Jena-2.1/lib/commons-logging.jar:/home/syosi/tarballs/jena/Jena-2.1/lib/xercesImpl.jar && PYTHONPATH=`pwd`/../..:`pwd`/../../..   ./tester.py -c commandList -o test_results.n3 $(TESTS)

