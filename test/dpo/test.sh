#!/bin/bash
#
cwm="python ../../cwm.py"
$cwm -rdf daml+oil.daml > daml+oil-r.rdf
$cwm -rdf daml+oil.daml -n3 > daml+oil-n.n3
$cwm daml+oil-n.n3 -rdf > daml+oil-nr.rdf
$cwm -rdf daml+oil-r.rdf -n3 > daml+oil-rn.n3
diff daml+oil-r.rdf daml+oil-nr.rdf
diff daml+oil-n.n3 daml+oil-rn.n3


