<<<<<<< Makefile
# $Id$

# Dan Connolly's process diagram stuff
PD=../../02pd/
#XT=~connolly/src/xtdebug
XT=~connolly/src/xt
XSLT=/cygdrive/c/winnt/system32/sabcmd
DOT=../../../2000/10/swap/test/viz/dot.exe

#include $(PD)XSLT.mak
include $(PD)GVDOT.mak

PYTHON=python
CWM=../../../2000/10/swap/cwm.py

.SUFFIXES: .rdf .n3

.n3.rdf:
	$(PYTHON) $(CWM) -n3 $< w3c.n3 style.n3 -think -purge  -bySubject -rdf=c > $@

.rdf.dot:
#	$(XSLT) $< $(PD)rdf2dot.xsl  $@
	$(XSLT) $(PD)rdf2dot.xsl  $< $@

all: all.dot all.ps all.svg all.png  goals.svg eb.png eb.gif eb.svg annotea.svg \
	sw.svg ws.svg swws.svg about.svg about.png about.gif

clean:
	$(RM) swws.{rdf,dot,ps,svg,png}

all.rdf: all.n3 w3c.n3 style.n3 ../../02pd/rdf2dot.xsl
#	$(PYTHON) $(CWM) all.n3 w3c.n3 style.n3 -think -purge -bySubject -rdf=c >$@

ws.rdf: ws.n3 w3c.n3 style.n3 ../../02pd/rdf2dot.xsl

sw.rdf: sw.n3 w3c.n3 style.n3 ../../02pd/rdf2dot.xsl

goals.rdf: goals.n3 w3c.n3 style.n3 ../../02pd/rdf2dot.xsl


#swws.dot: swws.rdf
#	sabcmd ../../02pd/rdf2dot.xsl swws.rdf >$@

# XML Processing model
xmlpm.rdf: xmlpm.n3
	$(PYTHON) $(CWM) -n3 xmlpm.n3  -think -purge  -bySubject -rdf=c > xmlpm.rdf


.rdf.dot:

#  Organization structure stuff:

groups.rdf: ../../../Member/Mail/Overview.html groups.xsl
	sabcmd groups.xsl ../../../Member/Mail/Overview.html >$@

# Should come from ../../../2000/04/mem-news/groups.rdf or http://...
groups1.n3: 
	$(PYTHON) $(CWM) -rdf groups0.rdf -n3 > $@

#ends
=======
# $Id$

# Dan Connolly's process diagram stuff
PD=../../02pd/
#XT=~connolly/src/xtdebug
XT=~connolly/src/xt
XSLT=/cygdrive/c/winnt/system32/sabcmd
DOT=../../../2000/10/swap/test/viz/dot.exe

include $(PD)XSLT.mak
include $(PD)GVDOT.mak

PYTHON=python
CWM=../../../2000/10/swap/cwm.py

.SUFFIXES: .rdf .n3

.n3.rdf:
	$(PYTHON) $(CWM) -n3 $< w3c.n3 style.n3 -think -purge  -bySubject -rdf > $@

.rdf.dot:
	$(XSLT) $< $(PD)rdf2dot.xsl  $@
#	$(XSLT) $(PD)rdf2dot.xsl  $< $@

all: all.dot all.ps all.svg all.png  goals.svg eb.png eb.gif eb.svg annotea.svg \
	sw.svg ws.svg swws.svg about.svg about.png about.gif

clean:
	$(RM) swws.{rdf,dot,ps,svg,png}

all.rdf: all.n3 w3c.n3 style.n3 ../../02pd/rdf2dot.xsl
#	$(PYTHON) $(CWM) all.n3 w3c.n3 style.n3 -think -purge -bySubject -rdf >$@

ws.rdf: ws.n3 w3c.n3 style.n3 ../../02pd/rdf2dot.xsl

sw.rdf: sw.n3 w3c.n3 style.n3 ../../02pd/rdf2dot.xsl

goals.rdf: goals.n3 w3c.n3 style.n3 ../../02pd/rdf2dot.xsl


#swws.dot: swws.rdf
#	sabcmd ../../02pd/rdf2dot.xsl swws.rdf >$@


#  Organization structure stuff:

groups.rdf: ../../../Member/Mail/Overview.html groups.xsl
	sabcmd groups.xsl ../../../Member/Mail/Overview.html >$@

# Should come from ../../../2000/04/mem-news/groups.rdf or http://...
groups1.n3: 
	$(PYTHON) $(CWM) -rdf groups0.rdf -n3 > $@

#ends
>>>>>>> 1.9
