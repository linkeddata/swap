# $Id$

W=../../../..
# Dan Connolly's process diagram stuff
PD=$W/2001/02pd/

#XT=~connolly/src/xtdebug
#XT=~connolly/src/xt
#XSLT=/cygdrive/c/winnt/system32/sabcmd
#DOT=$W/2000/10/swap/test/viz/dot.exe

include $(PD)XSLT.mak
include $(PD)GVDOT.mak

PYTHON=python
CWM=$W/2000/10/swap/cwm.py

.SUFFIXES: .rdf .n3

.n3.rdf:
	$(PYTHON) $(CWM) -n3 $<  style.n3 -think -purge  -bySubject -rdf > $@

.rdf.dot:
	$(XSLT) $< $(PD)rdf2dot.xsl  $@

#	$(XSLT) $(PD)rdf2dot.xsl  $< $@

all: infoset-diagram.svg infoset-diagram.svg infoset-diagram.png infoset.svg

clean:
	$(RM) infoset.{rdf,dot,ps,svg,png} infoset-diagram.{rdf,dot,ps,svg,png}

infoset.rdf: infoset.n3 infoset-labels.n3 style.n3 $(PD)rdf2dot.xsl
	$(PYTHON) $(CWM) infoset.n3 infoset-labels.n3 style.n3 -think -purge -bySubject -rdf >$@


infoset-diagram.rdf: infoset-daml.n3 infoset-labels.n3 style-arcprop.n3 $(PD)rdf2dot.xsl
	$(PYTHON) $(CWM) infoset-daml.n3 infoset-labels.n3 style-arcprop.n3 -think -purge -bySubject -base=bogus: -rdf >$@


#swws.dot: swws.rdf
#	sabcmd ../../02pd/rdf2dot.xsl swws.rdf >$@


#ends
