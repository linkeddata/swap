# $Id$

PYTHON=python

YAPPS=yapps2.py

TESTIN=test/sameDan.n3

.SUFFIXES: .g .py .html .rdf .n3

.g.py:
	$(PYTHON) $(YAPPS) $< $@

.n3.rdf:
	$(PYTHON) cwm.py $<  --rdf > $@
	cvs commit -m "Automatic: see Makefile" $@

#all: yappstest yappsdoc math.rdf log.rdf db.rdf os.rdf string.rdf crypto.rdf

all: math.rdf log.rdf db.rdf os.rdf string.rdf crypto.rdf time.rdf LICENSE.rdf cwm.tar.Z

# Can't make dependencies on *.py :-(

cwm.tar.Z: cwm.py notation3.py llyn.py  RDFSink.py toXML.py
	tar -cf cwm.tar *.py
	compress -f cwm.tar

yappstest: rdfn3_yapps.py rdfn3_yappstest.py
	$(PYTHON) rdfn3_yappstest.py <$(TESTIN) >,xxx.kif

rdfn3_yapps.py: rdfn3.g
	$(PYTHON) $(YAPPS) rdfn3.g $@

yappsdoc: rdfn3-gram.html relaxNG-gram.html

rdfn3-gram.html: rdfn3.g gram2html.py
	$(PYTHON) gram2html.py rdfn3.g "RDF Notation3 Grammar" >$@

relaxNG-gram.html: relaxNG.g gram2html.py
	$(PYTHON) gram2html.py relaxNG.g "Relax NG non-XML Grammar" >$@

kifExpr.py: kifExpr.g

kifExpr.html: kifExpr.g gram2html.py
	$(PYTHON) gram2html.py kifExpr.g "KIF Expression Grammar" >$@

kifForm.py: kifForm.g

kifForm.html: kifExpr.g gram2html.py
	$(PYTHON) gram2html.py kifForm.g "KIF Form Grammar" >$@

SemEnglish.html: SemEnglish.g gram2html.py
	$(PYTHON) gram2html.py SemEnglish.g "SemEnglish Grammar (from Seth)" >$@

log.rdf: log.n3
	$(PYTHON) cwm.py log.n3 --rdf > log.rdf



