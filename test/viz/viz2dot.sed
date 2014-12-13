#  Change N3 notation for Graphviz to its own format
#
s/;//g
s/\([a-zA-Z:]*\) *a :node/node \1;/g
s/:from//g
s/:to/->/g
#s/\]/;/g
#s/\[//g
s/\.$/ ;/g
 