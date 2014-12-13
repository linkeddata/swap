#  Make validation utilities
#
#  No -- now validate.n3 is the source.
#validate.n3: recurse.n3 valp.n3 valc.n3
#	cwm valp.n3 valc.n3 recurse.n3 > validate.n3

#end

PYTHON=python
SWAP=..
CWM=$(SWAP)/cwm.py

.SUFFIXES: .n3 .rdf

.n3.rdf:
	$(PYTHON) $(CWM) $< --purge --rdf >$@

sniffSchema.rdf: sniffSchema.n3
