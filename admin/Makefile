# $Id$

W=../../../..
PYTHON=python
SWAP=..
PIM=$(SWAP)/pim
CAL=$W/2002/12/cal

.SUFFIXES: .html .py .g .rdf .n3

.n3.rdf:
	$(PYTHON) cwm.py $<  --rdf > $@

.py.html:
	pydoc -w `echo $< | sed -e 's/\.py//'`


# cf
# W3C mailing list search results in RDF
#http://lists.w3.org/Archives/Public/www-rdf-interest/2003Jul/0206.html

bugstatus: N3-Bugs.ics

CWM=PYTHONPATH=$(SWAP) $(PYTHON) $(SWAP)/cwm.py

bugStatus.html: ,bugsToDo.cal3 bugReport.n3
	PYTHONPATH=$(SWAP) $(PYTHON) $(SWAP)/cwm.py ,bugsToDo.cal3 bugReport.n3 --think --strings >$@

N3-Bugs.ics: ,bugsToDo.cal3 $(SWAP)/pim/toIcal.py
	PYTHONPATH=$(SWAP):$(CAL) $(PYTHON) $(SWAP)/pim/toIcal.py ,bugsToDo.cal3 >$@

# Make update means fteches new info from outside this directory.

update:
	mv ,n3bugs0.rdf ,,n3bugs0.rdf
	make N3-Bugs.ics

# Make publlish makes the results avilable using CVS

publish : N3-Bugs.ics
	cvs commit -m "make publish" N3-Bugs.ics


# Make cycle does one cycle of importing data, recalcuating and exprting.

cycle:	update publish
	echo "Cycle complete"


,bugsToDo.cal3: ,n3bugs.rdf $(SWAP)/util/bugstatus.n3
	$(CWM) $(SWAP)/util/bugstatus.n3 --think --n3 --data >$@

# was: $(GET) -H Accept:\ application/rdf+xm

,n3bugs.rdf: ,n3bugs0.rdf ,n3bugs1.rdf ../util/reqThreadFix.n3
	$(CWM) ../util/reqThreadFix.n3 --rdf ,n3bugs0.rdf ,n3bugs1.rdf \
		 --think --data >$@

,n3bugs0.rdf:
	$(CWM) --rdf 'http://www.w3.org/Search/Mail/Public/advanced_search?keywords=n3bugs&resultsperpage=1000&sortby=date&index-grp=Public%2FFULL&index-type=t&type-index=www-archive' >$@

,n3bugs1.rdf:
	$(CWM) --rdf 'http://www.w3.org/Search/Mail/Public/advanced_search?keywords=cwm&resultsperpage=1000&sortby=date&index-grp=Public%2FFULL&index-type=t&type-index=public-cwm-bugs' >$@

#ends

