#
# Make axioms files
#
# axioms.txt was obtained by cutting and pasting the
# text from the axiomatic semantic html file
# and removing a few typos by hand. Also, all open/close double quotes
# in whatever chrset they wewre in were manually replaced with ascii 22 '"'.
# tbl
#
# default build:

all : result.n3 axioms.rdf
	touch all

C=python ../../cwm.py

axioms.rdf : axioms.n3
	$C axioms.n3 > axioms.rdf
axioms.n3 : axioms0.n3
	$C axioms0.n3 > axioms.n3

axioms0.n3 : axioms.txt axioms.sed
	sed -f axioms.sed <axioms.txt >axioms0.n3

# Kludge : believe all KIF statements in the axiom file but not the theorems for now

temp-axioms2.n3 : axioms.n3 kludge.n3
	$C axioms.n3 -filter=kludge.n3 | grep -v :Th> temp-decl.n3
	cat axioms.n3 temp-decl.n3 > temp-axioms2.n3	

# Below we have to tell cwm to take the stuff as it were from axioms.n3

result.n3 : axioms.n3 kludge.n3 convert.n3
#	$C -base=axioms.n3  -size convert.n3 -size -think -size <temp-axioms2.n3 > result.n3
	$C axioms.n3 -apply=kludge.n3 -size convert.n3 -size -think -size > result.n3


# ends
