# $Id$

PYTHON=python

YAPPS=yapps2.py

TESTIN=test/sameDan.n3

HTMLS= term.html formula.html pretty.html myStore.html check.html query.html RDFSink.html cwm.html cwm_crypto.html cwm_list.html cwm_math.html cwm_maths.html cwm_os.html cwm_string.html cwm_time.html cwm_times.html diag.html llyn.html notation3.html sax2rdf.html rdflib2rdf.html tab2n3.html thing.html toXML.html uripath.html xml2infoset.html why.html

DOC=doc/CwmHelp.html

.SUFFIXES: .html .py .g .rdf .n3

.g.py:
	$(PYTHON) $(YAPPS) $< $@

.n3.rdf:
	$(PYTHON) cwm.py $<  --rdf > $@

.py.html:
	pydoc -w `echo $< | sed -e 's/\.py//'`

#all: yappstest yappsdoc math.rdf log.rdf db.rdf os.rdf string.rdf crypto.rdf


tested : package
	(cd test; make all)
	echo "Test worked, now can make release"
	touch tested

doc.made : cwm.py notation3.py
	(cd doc; make all)
	touch doc.made

release : tested doc.made message.txt
	cvs commit -F message.txt
	rm message.txt
	touch release

package: math.rdf maths.rdf log.rdf db.rdf os.rdf string.rdf crypto.rdf time.rdf times.rdf LICENSE.rdf cwm.tgz $(HTMLS)

# Can't make dependencies on *.py :-(

# cwm.py notation3.py llyn.py  RDFSink.py toXML.py
cwm.tgz:  $(HTMLS)
	cvs update
	tar -czf cwm.tgz *.py $(HTMLS) LX/*.py LX/*/*.py  LX/*/*.P dbork/*.py ply/*.py *.py


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


#######

GET=curl

# cf
# W3C mailing list search results in RDF
#http://lists.w3.org/Archives/Public/www-rdf-interest/2003Jul/0206.html

bugstatus: bugsToDo.ics

CWM=$(PYTHON) cwm.py

bugsToDo.ics: bugsToDo.cal3
	PYTHONPATH=. $(PYTHON) pim/toIcal.py bugsToDo.cal3 >$@


bugsToDo.cal3: n3bugs.rdf util/bugstatus.n3
	$(CWM) util/bugstatus.n3 --think --n3 --data >$@


n3bugs.rdf:
	GET -H Accept:\ application/rdf+xml 'http://www.w3.org/Search/Mail/Public/advanced_search?keywords=n3bugs&resultsperpage=1000&sortby=date&index-grp=Public%2FFULL&index-type=t&type-index=www-archive' >$@
