#    Makefile
#
CODE=../cwm.py ../notation3.py ../xml2rdf.py

all : $(CODE) retest.sh
	./retest.sh
	touch all

rules12.rdf : rules12.n3
	cwm rules12.n3 -rdf > rules12.rdf

