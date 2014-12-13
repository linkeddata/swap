#  Issue tracking test data
#

CWM=python ../../cwm.py
XML=python ../../xml2infoset.py


.SUFFIXES: .xml .n3 .infoset .html

.n3.xml:
	$(CWM) --n3 $< --rdf > $@

.html.infoset:
	$(XML) $< | $(CWM) > $@

.infoset.actions:
	$(CWM) $< actions.n3 -think > $@

all : track-ex.xml 11-tag.actions
	touch all

track-ex.xml: track-ex.n3

11-tag.infoset : 11-tag.html ../../xml2infoset.py
	$(XML) 11-tag.html | $(CWM) > $@

11-tag.actions : 11-tag.infoset actions.n3
	$(CWM) 11-tag.infoset actions.n3 -think > $@

#ends
