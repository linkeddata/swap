#    Makefile
#
P=python
W=../../../..
C=../cwm.py

CODE=retest.py ../cwm.py ../notation3.py ../xml2rdf.py

all : $(CODE) regression.n3
	PYTHONPATH=`/bin/pwd`/.. $P retest.py -n -f regression.n3
	touch all

rules12.rdf : rules12.n3
	cwm rules12.n3 -rdf > rules12.rdf

rdfcore-tests.n3: ../../rdf-tests/rdfcore/Manifest.rdf
	$P $C --rdf ../../rdf-tests/rdfcore/Manifest.rdf --n3 > $@

rdfcore-tests.sh: rdfcore-tests.n3 gentest.n3
	$P $C rdfcore-tests.n3 gentest.n3 -think --strings | sed -e 's?http://www.w3.org?/devel/WWW?g' > $@
