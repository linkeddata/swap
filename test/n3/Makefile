
CWM = ../../cwm.py
TESTS := http://www.w3.org/2000/10/swap/test/n3parser.tests ../jena/n3_jena.tests

test_results.html : test_results.n3* makeReport.n3
	$(CWM) $^ makeReport.n3 --crypto --think --purge --strings > test_results.html

test_results.n3 : commandList
	export CLASSPATH=.:..:/usr/share/java/oro.jar:/usr/share/java/regexp.jar:/usr/share/java:/usr/share/java/ant.jar:/usr/share/java/ant-launcher.jar:/usr/share/java/ant:/usr/share/java/ant/ant-apache-oro.jar:/home/syosi/tarballs/jena/Jena-2.1/lib/antlr.jar:/home/syosi/tarballs/jena/Jena-2.1/lib/jena.jar:/home/syosi/tarballs/jena/Jena-2.1/lib/commons-logging.jar:/home/syosi/tarballs/jena/Jena-2.1/lib/xercesImpl.jar && PYTHONPATH=`pwd`/../..:`pwd`/../../..   ./tester.py -c commandList -o test_results.n3 $(TESTS)
