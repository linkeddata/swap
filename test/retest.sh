#! /bin/bash
#   Regression test for new versions of cwm
#
#alias cwm=python ~/swap/cwm.py
# Parse a small RDF file:
python ../cwm.py -rdf animal.rdf -n3 | sed -e 's/^#.*//' > temp/animal.n3
diff temp/animal.n3 ref
#
# Parse a small RDF file:
python ../cwm.py -rdf animal.rdf > temp/animal-1.rdf
diff temp/animal-1.rdf ref
#
python ../cwm.py daml-pref.n3 -rdf daml-ont.rdf -n3 | sed -e 's/^#.*//' > temp/daml-ont.n3
diff temp/daml-ont.n3 ref
#
# Try the examples
python ../cwm.py daml-pref.n3 -rdf daml-ex.rdf -n3 | sed -e 's/^#.*//' > temp/daml-ex.n3
diff temp/daml-ex.n3 ref
#
# Try some inference:
python ../cwm.py rules12.n3 -rules | sed -e 's/^#.*//' > temp/rules12-1.n3
diff temp/rules12-1.n3 ref
#
# Try some inference:
python ../cwm.py rules12.n3 -think | sed -e 's/^#.*//' > temp/rules12-n.n3
diff temp/rules12-n.n3 ref
#
# Try some inference:
python ../cwm.py rules13.n3 -rules | sed -e 's/^#.*//' > temp/rules13-1.n3
diff temp/rules13-1.n3 ref
#
# Try some inference:
python ../cwm.py rules13.n3 -think | sed -e 's/^#.*//' > temp/rules13-n.n3
diff temp/rules13-n.n3 ref
#
#
# Schema validity:
python ../cwm.py daml-ex.n3 invalid-ex.n3 schema-rules.n3 -think > temp/schema1.n3
diff temp/schema1.n3 ref
#
python ../cwm.py daml-ex.n3 invalid-ex.n3 schema-rules.n3 -think -filter=schema-filter.n3 > temp/schema2.n3
diff temp/schema2.n3 ref
#

