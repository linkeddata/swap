# Makefile
#

all: p3p-rdf-schema.n3 schema2.n3
	touch all

# The first schema p3p-rdf-schema

p3p-rdf-schema.n3 : p3p-rdf-schema.noents
	python ../../cwm.py -rdf p3p-rdf-schema.noents -n3 > p3p-rdf-schema.n3

p3p-rdf-schema.sed : p3p-rdf-schema.xml ent1.sed
	sed -f ent1.sed < p3p-rdf-schema.xml > p3p-rdf-schema.sed

p3p-rdf-schema.noents: p3p-rdf-schema.sed p3p-rdf-schema.xml
	sed -f p3p-rdf-schema.sed < p3p-rdf-schema.xml > p3p-rdf-schema.noents


# The second schema appendix B in the note

schema2.n3 : schema2.noents
	python ../../cwm.py -rdf schema2.noents -n3 > schema2.n3

schema2.sed : schema2.xml ent1.sed
	sed -f ent1.sed < schema2.xml > schema2.sed

schema2.noents: schema2.sed schema2.xml
	sed -f schema2.sed < schema2.xml > schema2.noents


