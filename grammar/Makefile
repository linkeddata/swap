#  Build stuff uop from the BNF

SWAP=..
P=python2.2
C=$(SWAP)/cwm.py

all : n3-checked.txt n3-report.html \
		n3rdf-report.html \
		n3rules-report.html \
		n3ql-report.html
	echo all done


#  N3 Full:


n3-yacc.c : n3-selectors.n3-yacc.y
	yacc -o $@ n3-selectors.n3-yacc.y

n3-selectors.n3-yacc.y : n3-selectors.n3
#n3-checked.txt: n3-selectors.n3
	python check-grammar.py n3-selectors.n3 \
		http://www.w3.org/2000/10/swap/grammar/n3#document> $@

n3-selectors.n3 : n3.n3 bnf-rules.n3
	time $P $C n3.n3 bnf-rules.n3 --think --purge --data > $@

n3-report.big:  n3.n3 bnf2html.n3
	time $P $C n3.n3 bnf2html.n3 --chatty=21 --think --data > $@

n3-report.html : n3-report.big
	time $P $C  n3-report.big --strings > $@

n3.rdf : n3.n3 
	$C --n3 n3.n3  --rdf > $@

# N3-RDF

n3rdf-checked.txt: n3rdf-selectors.n3
	python check-grammar.py n3rdf-selectors.n3 \
		http://www.w3.org/2000/10/swap/grammar/n3rules#document > $@

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

# N3-QL

n3ql-checked.txt: n3ql-selectors.n3
	python check-grammar.py n3ql-selectors.n3 \
		http://www.w3.org/2000/10/swap/grammar/n3ql#document > $@

n3ql-selectors.n3 : n3-ql.n3 bnf-rules.n3
	time $P $C n3-ql.n3 bnf-rules.n3 --think --purge --data > $@

n3ql-report.big:  n3-ql.n3 bnf2html.n3
	time $P $C n3-ql.n3 bnf2html.n3 --chatty=21 --think --data > $@


n3ql-report.html : n3ql-report.big
	time $P $C  n3ql-report.big --strings > $@

