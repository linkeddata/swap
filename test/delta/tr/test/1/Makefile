#  Generate and check one step in a sequence
# $Id$
P=python2.3

S=../../../../..
C=$S/cwm.py
CANT=$S/cant.py

# file name
X=tr

.SUFFIXES:  .check  .nt2 .cant .nt  .rdf

.rdf.nt:
	$P $C --rdf $< --ntriples > $>
.nt.cant:
	$P $(CANT) < $< > $@

#.rdf.delta:
#	$P $S/delta.py -f previous/$< -t $< > $>
#.delta.nt2:
#	$P $C previous/tim-other.rdf --patch=$< --ntriples > 
#	$P $C 


$X.checked: $X.nt $X.nt2 $X.cant
	$P $S/cant.py -f $X.nt -d $X.nt2
	touch $X.checked

$X.nt:  $X.rdf
	$P $C --rdf $X.rdf --ntriples > $X.nt

previous/$X.rdf: previous

previous:
	echo "try, e.g.: ln -s ../280 previous"
	exit 1

$X.delta:  $X.rdf previous/$X.rdf ../../assumptions.n3
	$P $S/delta.py -f previous/$X.rdf -t $X.rdf \
		--meta=../../assumptions.n3 > $X.delta
$X.nt2: previous/$X.rdf $X.delta
	$P $C previous/$X.rdf --patch=$X.delta --ntriples > $X.nt2 


