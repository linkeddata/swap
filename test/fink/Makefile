# Makefile for test of finkinfo handling in N3
#

F=../../util/fink2n3.py
#P=PYTHONPATH=../.. python
P=python

.SUFFIXES .def .info3

.info3.def
	$P defaults.n3 --think --with $< > $@

all: stable.n3 unstable.n3
	touch all

clean:
	rm stable.n3 unstable.n3

stable.info3 : $F
	$P $F -r /sw/fink/dists/stable > $@

unstable.info3 : $F
	$P $F -r /sw/fink/dists/unstable > $@

# A smaller dataset
web.info3 : $F
	$P $F -r /sw/fink/dists/stable/main/finkinfo/web > $@


byMaintainer.n3 : stable.n3 maintains.n3
	$P stable.n3 -filter=maintains.n3 > $@

stable-defaults.n3 : stable.n3 defaults.n3

