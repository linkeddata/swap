# $Id$

#
# External stuff, i.e. stuff outside this directory
#

W=../../../../..
SWAP=$(W)/2000/10/swap
CWM=$(SWAP)/cwm.py
THREEWEEKSAGO=`date -d "3 weeks ago" "+%Y-%m-%d"`
CVS=cvs

PYTHON=python

XSLTPROC=xsltproc
# http://packages.debian.org/testing/text/xsltproc.html
# http://xmlsoft.org/XSLT/

TRCHECKPOINT=tr-20040601.rdf

all: tr-pg.html tr.rdf tr-editor.html tr-date.html tr-title.html tr-activity.html

# Views of the TR page
# the classical one
tr-pg.html: tr.rdf  rdf2tr.xsl trbase.html
	$(XSLTPROC) --stringparam recent-since $(THREEWEEKSAGO) --novalid --param source '"tr.rdf"' rdf2tr.xsl trbase.html >$@

# By title, date and editor!
tr-title.html: tr.rdf viewBy.xsl trview.html
	$(XSLTPROC) --stringparam type title viewBy.xsl trview.html > $@

tr-date.html: tr.rdf viewBy.xsl trview.html
	$(XSLTPROC) --stringparam type date viewBy.xsl trview.html > $@

tr-editor.html: tr.rdf viewBy.xsl trview.html known-tr-editors.rdf
	$(XSLTPROC) --stringparam type editor viewBy.xsl trview.html > $@

tr-activity.html: tr.rdf viewBy.xsl trview.html clean-activity.xsl
	$(XSLTPROC) --stringparam type activity viewBy.xsl trview.html | xsltproc clean-activity.xsl - > $@

known-tr-editors.rdf: known-tr-editors.n3
	$(PYTHON) $(CWM) known-tr-editors.n3  --rdf >$@


tr.rdf: $(TRCHECKPOINT) new-tr.rdf tr-process.n3 filter-trdata.n3
	TRCHECKPOINT="http://www.w3.org/2002/01/tr-automation/$(TRCHECKPOINT)" $(PYTHON) $(CWM) --chatty=$(CHATTY) tr-process.n3 --think --rdf new-tr.rdf $(TRCHECKPOINT) --filter=filter-trdata.n3 --rdf > $@

CHATTY=0
tr.n3: tr.rdf
	$(PYTHON) $(CWM) --rdf tr.rdf --n3 >$@

publish: tr-title.html tr-editor.html tr-date.html tr-pg.html
	cp tr-title.html tr-editor.html tr-date.html tr-activity.html $(W)/TR/
	cp tr-pg.html $(W)/TR/Overview.html
	cd $(W)/TR/ &&$(CVS) commit tr-title.html tr-editor.html tr-date.html tr-activity.html Overview.html

clean: 
	rm -f tr-pg.html tr.rdf tr-editor.html tr-date.html tr-title.html tr-activity.html
