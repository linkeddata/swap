#  Generate and check one step in a sequence
P=python2.3

S=../../../../..
C=$S/cwm.py
CANT=$S/cant.py
CAL=$W/2002/12/cal

# file name
X=tr
# Published as what URI?  Used namespace for calendar
PUBURL=http://www.w3.org/2002/12/calendar/$X

.SUFFIXES:  .check  .nt2 .cant .nt  .rdf .ics

.ics.rdf:
	$P $CAL/fromIcal.py --base=$PUBURL $<  > $>
.rdf.nt:
	$P $C --rdf $< --ntriples > $>
.nt.cant:
	$P $(CANT) < $< > $@

#.rdf.delta:
#	$P $S/diff.py -f previous/$< -t $< > $>
#.delta.nt2:
#	$P $C previous/tim-other.rdf --patch=$< --ntriples > 
#	$P $C 


$X.checked: $X.nt $X.nt2 $X.cant
	$P $S/cant.py -f $X.nt -d $X.nt2
	touch $X.checked

#$X.rdf: $X.ics
#	$P $CAL/fromIcal.py --base=$PUBURL $X.ics  > $X.rdf
$X.nt:  $X.rdf
	$P $C --rdf $X.rdf --ntriples > $X.nt
$X.delta:  $X.rdf previous/$X.rdf
	$P $S/diff.py -f previous/$X.rdf -t $X.rdf \
		--meta=../../assumptions.n3 > $X.delta
$X.nt2: previous/$X.rdf $X.delta
	$P $C previous/$X.rdf --patch=$X.delta --ntriples > $X.nt2 


