# $Id$

PERL=perl
PYTHON=python

W=../../../..
OWLT=$(W)/2002/03owlt
UMLP=$(OWLT)/umlp
SWAP=..
PIMTEST=$(SWAP)/test/pim
CWM=$(SWAP)/cwm.py

include $(UMLP)/XSLTPROC.mak

.SUFFIXES: .xml .rdf .n3

.xml.rdf:
	$(XSLTPROC) --novalid $(UMLP)/dia2owl.xsl $< > $@

.n3.rdf:
	$(PYTHON) $(CWM) $< --rdf >$@

all: travelFig.rdf ical

travelFig.rdf: travelFig.xml

ical: ical.n3 ical.rdf


ical.rdf: ical.n3

ical.n3: $(PIMTEST)/testCal.rdf $(PIMTEST)/testTasks.rdf ,chi.rdf
	$(PYTHON) $(CWM) --rdf $(PIMTEST)/testCal.rdf $(PIMTEST)/testTasks.rdf ,chi.rdf --filter=http://www.w3.org/2000/10/swap/util/sniffSchema.n3 --n3 >$@

,chi.rdf: ical2rdf.pl /usr/share/libical-evolution/zoneinfo/America/Chicago.ics
	$(PERL) ical2rdf.pl /usr/share/libical-evolution/zoneinfo/America/Chicago.ics >$@

$(PIMTEST)/testCal.rdf: $(PIMTEST)/testCal.ics ical2rdf.pl
	$(PERL) ical2rdf.pl $(PIMTEST)/testCal.ics >$@

$(PIMTEST)/testTasks.rdf: $(PIMTEST)/testTasks.ics ical2rdf.pl
	$(PERL) ical2rdf.pl $(PIMTEST)/testTasks.ics >$@

clean:
	$(RM) $(PIMTEST)/testCal.rdf $(PIMTEST)/testTasks.rdf ,chi.rdf ical.n3 ical.rdf