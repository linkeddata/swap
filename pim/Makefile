
W=../../../..
OWLT=$(W)/2002/03owlt
UMLP=$(OWLT)/umlp

include $(UMLP)/XSLTPROC.mak

.SUFFIXES: .xml .rdf

.xml.rdf:
	$(XSLTPROC) --novalid $(UMLP)/dia2owl.xsl $< > $@

all: travelFig.rdf

travelFig.rdf: travelFig.xml
