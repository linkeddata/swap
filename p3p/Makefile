# $Id$

W=../../../..
SWAP=..
PD=$(W)/2001/02pd

include $(PD)/XSLT.mak
JAVA=java

WGET=wget

P3PBASE=http://www.w3.org/TR/P3P/base

forShoppers.rdf: grokPolicy.xsl ex32.xml
	$(XSLT) ex32.xml grokPolicy.xsl $@

#seems Brian already did this...
p3pbase.rdf: grokDataSchema.xsl ,cache-p3pbase.xml
	$(XSLT) ,cache-p3pbase.xml grokDataSchema.xsl $@

,cache-p3pbase.xml:
	$(WGET) -O $@ $(P3PBASE)