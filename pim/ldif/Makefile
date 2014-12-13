# LDIF conversion

S=../..

.SUFFIXES: .rdf .n3 .ldif

.ldif.n3:
	python $S/pim/ldif2n3.py $< > $@

.n3.rdf:
	python $S/cwm.py --n3 $< --rdf --quiet > $@

,all: zac.rdf
	touch ,all
