# $Id$

# Dan Connolly's process diagram stuff
#PD=../../02pd/
#XT=~connolly/src/xtdebug
#XT=~connolly/src/xt
#XSLT=/cygdrive/c/winnt/system32/sabcmd
W=../../../..
DOT=$(W)/2000/10/swap/test/viz/dot.exe
RM=$(W)/2001/04/roadmap

#include $(PD)XSLT.mak
#include $(PD)GVDOT.mak

PYTHON=python
CWM=$(W)/2000/10/swap/cwm.py

.SUFFIXES: .svg .dot .graph .n3

# $(RM)/w3c.n3  $(RM)/style.n3

.n3.graph:
	$(PYTHON) $(CWM) $< -think -purge  -bySubject -rdf=c > $@

.graph.svg:
	TARGET=$< $(PYTHON) $(CWM) $(RM)/todot.n3 -think --strings | dot -Tsvg > $@
 
#.rdf.dot:
##	$(XSLT) $< $(PD)rdf2dot.xsl  $@
#	$(XSLT) $(PD)rdf2dot.xsl  $< $@


states.svg: states.graph

clean:
	$(RM) swws.{rdf,dot,ps,svg,png}


#ends
