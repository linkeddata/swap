# $Id$

W=../../../..
SWAP=..
PD=$(W)/2001/02pd

XSLTPROC=xsltproc --novalid
PYTHON=python

WGET=wget

P3PBASE=http://www.w3.org/TR/P3P/base

.SUFFIXES: .rdf .n3 .xml

.rdf.n3:
	$(PYTHON) ../cwm.py --rdf $< --n3 >$@

.xml.rdf:
	$(XSLTPROC) -o $@ grokPolicy.xsl $< 


all: forShoppers.rdf forShoppers.n3 anonShop.n3

anonShop.n3: forShoppers.rdf p3pbase.rdf p3pAArules.n3
	$(PYTHON) ../cwm.py --chatty=20 --rdf p3pbase.rdf --n3 p3pAArules.n3 --think >$@

forShoppers.n3: forShoppers.rdf

forShoppers.rdf: grokPolicy.xsl ex32.xml
	$(XSLTPROC) -o $@ grokPolicy.xsl ex32.xml 

#seems Brian already did this...
p3pbase.rdf: grokDataSchema.xsl ,cache-p3pbase.xml
	$(XSLTPROC) -o  $@ grokDataSchema.xsl ,cache-p3pbase.xml

,cache-p3pbase.xml:
	$(WGET) -O $@ $(P3PBASE)
