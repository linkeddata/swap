# Generate different forms for an ontology from OILED
#
C=python ../../cwm.py

tambis.rdf: tambis.n3
	$C tambis.n3 -rdf > tambis.rdf

tambis.n3 : tambis.daml tambis.anons
	$C tambis.anons -rdf tambis.daml -n3  > tambis.n3

tambis.anons: tambis.daml tambis-fix.sed
	grep _anon tambis.daml | sed -f tambis-fix.sed > tambis.anons

# Make version using daml-plus-oil namespace

tambis.daml : tambis-no-ents.daml
	sed -f daml2dpo.sed < tambis-no-ents.daml > tambis.daml
#ends
