# $Id$

# Dan Connolly's process diagram stuff
#PD=../../02pd/
#XT=~connolly/src/xtdebug
#XT=~connolly/src/xt
#XSLT=/cygdrive/c/winnt/system32/sabcmd
W=../../../..
DOT=$(W)/2000/10/swap/test/viz/dot.exe
ROADMAP=$(W)/2001/04/roadmap

#include $(PD)XSLT.mak
#include $(PD)GVDOT.mak

PYTHON=python
CWM=$(W)/2000/10/swap/cwm.py

SCHEMAS= ../log.n3 ../crypto.n3 ../list.n3 ../math.n3 ../os.n3 ../string.n3 ../time.n3 

.SUFFIXES: .svg .dot .graph .n3

.n3.graph:
	$(PYTHON) $(CWM) $< -think -purge  -bySubject -rdf=c > $@

.graph.svg:
	TARGET=$< $(PYTHON) $(CWM) $(ROADMAP)/todot.n3 -think --strings | dot -Tsvg > $@
 
#.rdf.dot:
##	$(XSLT) $< $(PD)rdf2dot.xsl  $@
#	$(XSLT) $(PD)rdf2dot.xsl  $< $@


all:	CwmBuiltins.html formats-example1 CwmHelp.html
	echo all done

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

print: tutorial-1.pdf tutorial-1.ps tutorial.pdf tutorial.ps appendix.pdf appendix.ps

#@@cwm.html -- remove junk
#@@CwmBuiltins.html -- reformat
TUTFILES=Overview.html ../Primer.html Shortcuts.html ontologies.html Rules.html Processing.html Built-In.html Trust.html ../pim/travel.html Glossary.html
TUTFIGS=../../../../DesignIssues/diagrams/arcs-1.gif ../../../../DesignIssues/diagrams/arcs-3.gif ../../../../2002/Talks/04-sweb/elisaaccess.png ../test/crypto/make.jpg

APPENDICES=formats.html CwmInstall.html CwmHelp.html rule-systems.html
APPFIGS=formats-examplex1.ps

HTML2PS=html2ps # debian package originally from http://www.tdb.uu.se/~jan/html2ps.html
# user guide http://www.tdb.uu.se/~jan/html2psug.html

tutorial.ps: $(TUTFILES) print.css formats-examplex1.ps $(TUTFIGS)
	$(HTML2PS) -f print.css -2 --xref -o $@ $(TUTFILES)

PS2PDF=ps2pdf # ghostscript? acroread?
tutorial.pdf: tutorial.ps
	$(PS2PDF) tutorial.ps

tutorial-1.ps: $(TUTFILES) print.css formats-examplex1.ps $(TUTFIGS)
	$(HTML2PS) -f print.css --xref -o $@ $(TUTFILES)

tutorial-1.pdf: tutorial-1.ps
	$(PS2PDF) tutorial-1.ps

appendix.ps: $(APPENDICES) print.css $(APPFIGS)
	$(HTML2PS) -f print.css --xref -o $@ $(APPENDICES)


#@@factor out .ps.pdf rule
appendix.pdf: appendix.ps
	$(PS2PDF) appendix.ps


HTMLDOC=htmldoc # DebianPackage:htmldoc, http://www.easysw.com/htmldoc/htmldoc.html
tutorial-book.pdf: $(TUTFILES) $(TUTFIGS) tutorial-bookstyle
	echo htmldoc doesn't have a noprint thingy. Lose.
	$(HTMLDOC) --batch tutorial-bookstyle -f $@ $(TUTFILES)

cwm-help.txt : ../cwm.py ../notation3.py ../sax2rdf.py ../toXML.py
	$(PYTHON) $(CWM) --help | sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' > cwm-help.txt

CwmHelp.html : CwmHelp-template.html cwm-help.txt
	sed -e '/<pre>/rcwm-help.txt' < CwmHelp-template.html > CwmHelp.html


travelFigs:
	(cd ../pim; make travelFigs)

clean:
	$(RM) tutorial.ps tutorial.pdf tutorial-book.pdf cwm-help.txt CwmHelp.html appendix.ps appendix.pdf formats-examplex1.ps



#ends
