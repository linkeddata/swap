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

all : result.n3 axioms.rdf purged2.n3
	touch all

C=python ../../cwm.py

axioms.rdf : axioms.n3
	$C axioms.n3 -rdf > axioms.rdf

axioms.n3 : axioms0.n3
	$C axioms0.n3 > axioms.n3

axioms0.n3 : axioms.txt axioms.sed
	sed -f axioms.sed <axioms.txt >axioms0.n3

# Kludge : believe all KIF statements in the axiom file but not the theorems for now

temp-axioms2.n3 : axioms.n3 kludge.n3
	$C axioms.n3 -filter=kludge.n3 | grep -v :Th > temp-decl.n3
	cat axioms.n3 temp-decl.n3 > temp-axioms2.n3	

consts.n3 : consts.sed axioms.n3
	sed -f consts.sed <axioms.n3 | sort -u > consts.n3

# Below we have to tell cwm to take the stuff as it were from axioms.n3

result.n3 : axioms.n3 kludge.n3 convert.n3 consts.n3
#	$C -base=axioms.n3  -size convert.n3 -size -think -size <temp-axioms2.n3 > result.n3
	$C axioms.n3 -apply=kludge.n3 consts.n3 -size convert.n3 -size -think -size > result.n3

purged.n3 : result.n3
	$C result.n3 -purge > purged.n3
 
purged2.n3 : purged.n3 noKIF.n3
	$C purged.n3 noKIF.n3 -purge > purged2.n3

a001-conv.n3 : a001.n3 ../../cwm.py ../../notation3.py convert.n3
	$C a001.n3 convert.n3 -think > a001-conv.n3

a001-purged.n3 : a001-conv.n3
	$C a001-conv.n3 -purge > a001-purged.n3

a001-purged2.n3 : a001-purged.n3 noKIF.n3
	$C a001-conv.n3 noKIF.n3 -purge > a001-purged2.n3

#---------------------------------------------------------

a127-conv.n3 : a127.n3 ../../cwm.py ../../notation3.py convert.n3
	$C a127.n3 convert.n3 -think > a127-conv.n3

a127-purged.n3 : a127-conv.n3
	$C a127-conv.n3 -purge > a127-purged.n3

a127-purged2.n3 : a127-purged.n3 noKIF.n3
	$C a127-conv.n3 noKIF.n3 -purge > a127-purged2.n3

# ends
