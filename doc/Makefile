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

SCHEMAS= ../log.n3 ../crypto.n3 ../math.n3 ../os.n3 ../string.n3 ../time.n3 

.SUFFIXES: .svg .dot .graph .n3

# $(RM)/w3c.n3  $(RM)/style.n3

.n3.graph:
	$(PYTHON) $(CWM) $< -think -purge  -bySubject -rdf=c > $@

.graph.svg:
	TARGET=$< $(PYTHON) $(CWM) $(RM)/todot.n3 -think --strings | dot -Tsvg > $@
 
#.rdf.dot:
##	$(XSLT) $< $(PD)rdf2dot.xsl  $@
#	$(XSLT) $(PD)rdf2dot.xsl  $< $@


all:	CwmBuiltins.html formats-example1
	touch all

CwmBuiltins.html : $(SCHEMAS)
	$(PYTHON) $(CWM) $(SCHEMAS) schema2html.n3 --think --strings > $@

formats-example1:: formats-example1.jpg \
		formats-example1.svg \
		formats-example1.png \
		formats-examplex1.ps

formats-example1.jpg: formats-example1.dot
	dot -Tjpg $< > $@
formats-example1.svg: formats-example1.dot
	dot -Tsvg $< > $@
formats-example1.png: formats-example1.dot
	dot -Tpng $< > $@
formats-examplex1.ps: formats-example1.dot
	dot -Tps $< | grep -v '^%%' | grep -v '^endpage' > $@


states.svg: states.graph

print: tutorial.pdf tutorial.ps

#@@cwm.html -- remove junk
#@@CwmBuiltins.html -- reformat
TUTFILES=Overview.html ../Primer.html formats.html CwmInstall.html CwmHelp.html Shortcuts.html ontologies.html Rules.html Processing.html Built-In.html rule-systems.html Glossary.html

HTML2PS=html2ps # debian package originally from http://www.tdb.uu.se/~jan/html2ps.html
 # user guide http://www.tdb.uu.se/~jan/html2psug.html
tutorial.ps: $(TUTFILES)
	$(HTML2PS) -o $@ -2 --xref $(TUTFILES)

PS2PDF=ps2pdf # ghostscript? acroread?
tutorial.pdf: tutorial.ps
	$(PS2PDF) tutorial.ps

cwm-help.txt : ../cwm.py ../notation3.py
	cwm --help > cwm-help.txt

CwmHelp.html : CwmHelp-template.html cwm-help.txt
	sed -e '/<pre>/rcwm-help.txt' < CwmHelp-template.html > CwmHelp.html


clean:
	$(RM) swws.{rdf,dot,ps,svg,png}


#ends
