#    Makefile
#
P=python
W=../../../..
C=../cwm.py
RC=../../rdf-tests/rdfcore

CODE=retest.py ../cwm.py ../notation3.py ../xml2rdf.py ../query.py ../llyn.py
# etc ...

TESTS=regression.n3 list/detailed.tests online.tests \
	math/detailed.tests \
	norm/detailed.tests \
	cwm/detailed.tests \
# 	i18n/detailed.tests \
	ntriples/detailed.tests \
	delta/detailed.tests \
	rdfcore-tests.n3 testmeta.n3

all : pyc-check $(CODE) $(TESTS)
	PYTHONPATH=`/bin/pwd`/.. $P retest.py -c $(TESTS)

fast : $(CODE) regression.n3
	PYTHONPATH=`/bin/pwd`/.. $P retest.py -n -f regression.n3


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
	PYTHONPATH=`/bin/pwd`/.. $P retest.py -n -c -f flatten-tests.n3
