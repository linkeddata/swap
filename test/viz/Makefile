# Convert DAML ontology to GraphViz
#
C=python ../../cwm.py

.viz.dot :
	$C sed -f viz2dot.sed < $< > $>
foo.dot : foo.viz viz2dot.sed
	sed -f viz2dot.sed < foo.viz > foo.dot

foo.viz : daml2viz.n3
	$C -filter=daml2viz.n3 < ../daml-ex.n3 > foo.viz

