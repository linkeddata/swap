# $Id$

PYTHON=python2

YAPPS=yapps2.py

TESTIN=test/sameDan.n3

.SUFFIXES: .g .py

.g.py:
	$(PYTHON) $(YAPPS) $< $@


all: test doc

test: rdfn3_yapps.py rdfn3_yappstest.py
	$(PYTHON) rdfn3_yappstest.py <$(TESTIN) >,xxx.n3

rdfn3_yapps.py: rdfn3.g
	$(PYTHON) $(YAPPS) rdfn3.g $@

doc: rdfn3-gram.html

rdfn3-gram.html: rdfn3.g gram2html.py
	$(PYTHON) gram2html.py rdfn3.g "RDF Notation3 Grammar" >$@

