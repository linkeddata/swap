# $Id$

W=../../../..
# Dan Connolly's process diagram stuff
PD=$W/2001/02pd/

include $(PD)XSLTPROC.mak
include $(PD)GVDOT.mak

PYTHON=python
CWM=$W/2000/10/swap/cwm.py
SWELL=$W/2001/03swell

.SUFFIXES: .rdf .n3

.n3.rdf:
	$(PYTHON) $(CWM) -n3 $<  style.n3 -think -purge  -bySubject -rdf > $@

.rdf.dot:
	$(XSLTPROC) --novalid $(PD)rdf2dot.xsl $< >$@

#	$(XSLT) $(PD)rdf2dot.xsl  $< $@

all: infoset-diagram.svg infoset-diagram.svg infoset-diagram.png infoset.svg

clean:
	$(RM) infoset.{rdf,dot,ps,svg,png} infoset-diagram.{rdf,dot,ps,svg,png} xmlContent-diagram.{rdf,dot,ps,svg,png}

infoset.rdf: infoset.n3 infoset-labels.n3 style.n3 $(PD)rdf2dot.xsl
	$(PYTHON) $(CWM) infoset.n3 infoset-labels.n3 style.n3 -think -purge -bySubject -rdf >$@


INFS=$(SWELL)/lists.n3 $(SWELL)/listsAx.n3 $(SWELL)/finiteSets.n3 \
	infoset-daml.n3 infosetUtil.n3 style-arcprop.n3 
infoset-diagram.rdf: $(INFS) $(PD)rdf2dot.xsl
	$(PYTHON) $(CWM) $(INFS) -think -purge -bySubject -base=bogus: -rdf >$@

INFS2=$(SWELL)/lists.n3 $(SWELL)/listsAx.n3 $(SWELL)/finiteSets.n3 \
	xmlContent.n3 infosetUtil.n3 style-arcprop.n3 
xmlContent-diagram.rdf: $(INFS2) $(PD)rdf2dot.xsl
	$(PYTHON) $(CWM) $(INFS2) --think --purge --bySubject --base=bogus: --rdf >$@


#swws.dot: swws.rdf
#	sabcmd ../../02pd/rdf2dot.xsl swws.rdf >$@


#ends
