#  Build stuff uop from the BNF

SWAP=..
P=python2.2
C=$(SWAP)/cwm.py

all :  n3-selectors.n3 n3-report.html
	touch all

n3-selectors.n3 : n3.n3 bnf-rules.n3
	time $P $C n3.n3 bnf-rules.n3 --think --purge --data > $@

n3-report.big:  n3.n3 bnf2html.n3
	time $P $C n3.n3 bnf2html.n3 --chatty=21 --think --data > $@


n3-report.html : n3-report.big
	time $P $C  n3-report.big --strings > $@