#   makefile for colored bits from talk
#
# verys sinmplistic overlap of webs
#
C=python ../../cwm.py

all : white.n3 white.rdf
	touch all

white.rdf : red.rdf blue.rdf green.rdf
	$C -rdf red.rdf blue.rdf green.rdf > white.rdf

white.n3 : red.n3 blue.n3 green.n3
	$C red.n3 blue.n3 green.n3 > white.n3

red.rdf : red.n3
	$C red.n3 -rdf > red.rdf

blue.rdf : blue.n3
	$C blue.n3 -rdf > blue.rdf

green.rdf : blue.n3
	$C green.n3 -rdf > green.rdf
