# Go though the output of an OILED DAML file and find anon nodes
#
s/.*\(_anon[0-9]*\).*/     <\1>,/g
/_anon/!d
1i\
@prefix log: <http://www.w3.org/2000/10/swap/log.n3#> .\
<> log:forSome
$s/,/./
# ends