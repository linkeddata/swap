# $Id$

PYTHON=python

YAPPS=yapps2.py

TESTIN=test/sameDan.n3

HTMLS= check.html RDFSink.html cwm.html cwm_crypto.html cwm_math.html cwm_os.html cwm_string.html cwm_time.html diag.html llyn.html notation3.html sax2rdf.html tab2n3.html thing.html toXML.html uripath.html xml2infoset.html why.html

#xml2rdf.html
#de-cr.html
#SemEnglish.html
#converter-cgi.html
#gram2html.html
#isodate.html
#kifForm.html
#n3spark.html
#rdf2dot.html
#rdfn3_yapps.html
#rdfn3_yappstest.html
#rdfx2kif.html
#spark.html
#timegm.html
#xmllib.html
#yapps2.html
#yappsrt.html

.SUFFIXES: .html .py .g .rdf .n3

.g.py:
	$(PYTHON) $(YAPPS) $< $@

.n3.rdf:
	$(PYTHON) cwm.py $<  --rdf > $@
	cvs commit -m "Automatic: see Makefile" $@

.py.html:
	pydoc -w `echo $< | sed -e 's/\.py//'`

#all: yappstest yappsdoc math.rdf log.rdf db.rdf os.rdf string.rdf crypto.rdf

tested : package
	(cd test; python retest.py -n -c -f regression.n3)
	echo "Test worked, now can release"
	touch tested

release : test
	cvs commit -m "Passes regression test"
	touch release

package: math.rdf log.rdf db.rdf os.rdf string.rdf crypto.rdf time.rdf LICENSE.rdf cwm.tar.Z $(HTMLS)

# Can't make dependencies on *.py :-(

# cwm.py notation3.py llyn.py  RDFSink.py toXML.py
cwm.tar.Z::
	tar -cf cwm.tar *.py $(HTMLS) LX/*.py LX/*/*.py  LX/*/*.P dbork/*.py ply/*.py
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

