#    Makefile
#
P=python
W=../../../..
C=../cwm.py
RC=../../rdf-tests/rdfcore

CODE=retest.py ../cwm.py # ../notation3.py ../query.py ../llyn.py
# etc ...

OFFLINETESTS=regression.n3 list/detailed.tests \
	ql/detailed.tests \
	math/detailed.tests \
	norm/detailed.tests \
	cwm/detailed.tests \
	ntriples/detailed.tests \
	delta/detailed.tests \
	syntax/detailed.tests \
	n3parser.tests \
	testmeta.n3
#	reify/detailed.tests \
# 	i18n/detailed.tests \

TESTS=online.tests rdfcore-tests.n3 $(OFFLINETESTS)

post-install : pyc-check $(CODE) $(OFFLINETESTS)
	PYTHONPATH=`/bin/pwd`/..:`/bin/pwd`/../.. $P retest.py -c $(OFFLINETESTS)

pre-release : pyc-check $(CODE) $(TESTS) rdflib
	PYTHONPATH=`/bin/pwd`/..:`/bin/pwd`/../.. $P retest.py -c $(TESTS)


filelist : pyc-check $(CODE) $(OFFLINETESTS)
	export CWM_LIST_FILES=1; PYTHONPATH=`/bin/pwd`/..:`/bin/pwd`/../.. $P retest.py --cwm=./file_list.py -c $(OFFLINETESTS)
	sort testfilelist > testfilelist3
	uniq testfilelist3 > testfilelist
	rm testfilelist3

rdflib: rdfcore-tests.n3
	CWM_RDF_PARSER="rdflib" PYTHONPATH=`/bin/pwd`/..:`/bin/pwd`/../.. $P retest.py -c rdfcore-tests.n3


mellow : pyc-check $(CODE) $(TESTS) 
	PYTHONPATH=`/bin/pwd`/..:`/bin/pwd`/../.. $P retest.py --ignoreErrors -c $(TESTS)

just_work : pyc-check $(CODE) $(TESTS) 
	PYTHONPATH=`/bin/pwd`/..:`/bin/pwd`/../.. $P retest.py --overwrite -c $(TESTS)

fast : $(CODE) regression.n3
	PYTHONPATH=`/bin/pwd`/..:`/bin/pwd`/../.. $P retest.py -n -f regression.n3


pyc-check : $(CODE)
	rm -f ../*.pyc
	touch pyc-check

loopback :
	./n3-xml-test.sh `cat tests-work.txt`

rules12.rdf : rules12.n3
	cwm rules12.n3 -rdf > rules12.rdf

rdfcore-tests.n3: ../../rdf-tests/rdfcore/Manifest.rdf
	$P $C --rdf ../../rdf-tests/rdfcore/Manifest.rdf --n3 > $@

# Crashes :-(
#testmeta.n3 : rdfcore-tests triage.n3
#	$P $C rdfcore-tests --filter=triage.n3 > $@

rdfcore-tests.sh: rdfcore-tests.n3 gentest.n3
	$P $C rdfcore-tests.n3 gentest.n3 -think --strings | sed -e 's?http://www.w3.org?/devel/WWW?g' > $@

annotation.n3 :
	find $(RC) -name "*.nt" -exec grep -l "22-rdf-syntax-ns#predicate" {} \; | \
		sed -e 's/^/</' -e 's/.nt/.nt> a <#ReificationFile>./' > $@

flatten::
	PYTHONPATH=`/bin/pwd`/..:`/bin/pwd`/../.. $P retest.py -n -c -f flatten-tests.n3
