#  Issue tracking test data
#

CWM=python ../../cwm.py
XML=python ../../xml2infoset.py


.SUFFIXES: .xml .n3 .infoset .html

.n3.xml:
	$(CWM) --n3 $< --rdf > $@

.html.infoset:
	$(XML) $< | $(CWM) > $@

all : track-ex.xml 
	touch all

track-ex.xml: track-ex.n3

tag.infoset : tag.html
	$(XML) tag.infoset | $(CWM) > $@


#ends
