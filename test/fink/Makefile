# Makefile for test of finkinfo handling in N3
#
# For use on a debian sustem, do domthing like
#     python fink2n3.py /var/dpkg/etc/avaliable
#
F=../../util/fink2n3.py
#P=PYTHONPATH=../.. python
P=python
C=../../cwm.py

.SUFFIXES: .index .maint .def .info3

# From a list of packages, find those no needed by others;
.info3.def:
	$P $C defaults.n3 --think --with $< > $@

# From package info, make list of maintainers:
.info3.maint:
	$P $C $< -filter=byMaintainer.n3 > $@

# From package info, make list of maintainers:
.info3.index:
	$P $C $< --think=closure.n3 > $@

all: stable.maint unstable.maint web.index
	touch all

clean:
	rm *.info3 *.index *.maint

#  Convert fink .info format to n3  (".info3") for later procesing 
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

