# Generate different forms for an ontology from OILED
#
C=python ../../cwm.py

pathway.rdf: pathway.n3
	$C pathway.n3 -rdf > pathway.rdf

pathway.n3 : pathway.dpo pathway.anons
	$C pathway.anons -rdf pathway.dpo -n3  > pathway.n3

pathway.anons: pathway.noents fix.sed
	grep _anon pathway.noents | sed -f fix.sed > pathway.anons

# Make version using daml-plus-oil namespace

pathway.dpo : pathway.noents
	sed -f daml2dpo.sed < pathway.noents > pathway.dpo

# expand entities
#pathway.noents : pathway.daml pathway.sed
#	sed -f pathway.sed pathway.daml > pathway.noents

# get entity declarations (hack)
pathway.sed : pathway.daml
	grep "ENTITY" pathway.daml | sed -f ent1.sed > pathway.sed


#ends
