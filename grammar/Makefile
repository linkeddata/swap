#  Build stuff uop from the BNF

SWAP=..
P=python2.2
C=$(SWAP)/cwm.py

all : n3-checked.txt n3-report.html n3rdf-report.html n3rules-report.html
	touch all

n3-checked.txt: n3-selectors.n3
	python check-grammar.py n3-selectors.n3 > $@

n3-selectors.n3 : n3.n3 bnf-rules.n3
	time $P $C n3.n3 bnf-rules.n3 --think --purge --data > $@

n3-report.big:  n3.n3 bnf2html.n3
	time $P $C n3.n3 bnf2html.n3 --chatty=21 --think --data > $@

n3-report.html : n3-report.big
	time $P $C  n3-report.big --strings > $@


# N3-RDF

n3rdf-checked.txt: n3rdf-selectors.n3
	python check-grammar.py n3rdf-selectors.n3 > $@

n3rdf-selectors.n3 : n3-rdf.n3 bnf-rules.n3
	time $P $C n3-rdf.n3 bnf-rules.n3 --think --purge --data > $@

n3rdf-report.big:  n3-rdf.n3 bnf2html.n3
	time $P $C n3-rdf.n3 bnf2html.n3 --chatty=21 --think --data > $@


n3rdf-report.html : n3rdf-report.big
	time $P $C  n3rdf-report.big --strings > $@

# N3-Rules

n3rules-selectors.n3 : n3-rules.n3 bnf-rules.n3
	time $P $C n3-rules.n3 bnf-rules.n3 --think --purge --data > $@

n3rules-report.big:  n3-rules.n3 bnf2html.n3
	time $P $C n3-rules.n3 bnf2html.n3 --chatty=21 --think --data > $@


n3rules-report.html : n3rules-report.big
	time $P $C  n3rules-report.big --strings > $@

