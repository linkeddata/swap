# $Id$

W=../../../..
# Dan Connolly's process diagram stuff
PD=$W/2001/02pd/
#XT=~connolly/src/xtdebug
XT=~connolly/src/xt
XSLT=/cygdrive/c/winnt/system32/sabcmd
DOT=$W/2000/10/swap/test/viz/dot.exe

#include $(PD)XSLT.mak
include $(PD)GVDOT.mak

PYTHON=python
CWM=$W/2000/10/swap/cwm.py

.SUFFIXES: .rdf .n3

.n3.rdf:
	$(PYTHON) $(CWM) -n3 $<  style.n3 -think -purge  -bySubject -rdf > $@

.rdf.dot:
#	$(XSLT) $< $(PD)rdf2dot.xsl  $@
	$(XSLT) $(PD)rdf2dot.xsl  $< $@

all: infoset.svg

clean:
	$(RM) swws.{rdf,dot,ps,svg,png}

infoset.rdf: all.n3 infoset.n3 style.n3 $(PD)rdf2dot.xsl
#	$(PYTHON) $(CWM) all.n3 infoset.n3 style.n3 -think -purge -bySubject -rdf >$@


#swws.dot: swws.rdf
#	sabcmd ../../02pd/rdf2dot.xsl swws.rdf >$@


#ends
