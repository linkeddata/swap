#  Make tests of smushing etc
#

W=../../../../../..
S=../../..
P=python2.3
C=$S/cwm.py
D=$S/diff.py
N=$S/cant.py

.SUFFIXES: .cnt .nt .n3

.n3.nt:
	$P $C $< --ntriples > $@
.nt.cnt:
	$P $N < $< > $@

all: smushed-regen.nt to-smushed.nt
	$P $N -f smushed-regen.nt -d to-smushed.nt

from-smushed.n3 : from.n3 $D
	$P $D --from from.n3 > $@

to-smushed.n3 : to.n3 $D
	$P $D --from to.n3 > $@

patch.n3 : from.n3 to.n3 $D
	$P $D --from from.n3 --to to.n3 > $@

smushed-patch.n3 : from-smushed.n3 to-smushed.n3
	- $P $D  --from from-smushed.n3 --to to-smushed.n3 > $@

smushed-regen.n3 : from-smushed.n3 smushed-patch.n3
	$P $C from-smushed.n3 --patch=smushed-patch.n3 > $@

smushed-regen.nt : from-smushed.n3 smushed-patch.n3
	$P $C from-smushed.n3 --patch=smushed-patch.n3 --ntriples > $@

#smushed-regen.nt : smushed-regen.n3
#	$P $C smushed-regen.n3 --ntriples > $@

to-smushed.nt: to-smushed.n3 $C
	$P $C to-smushed.n3 --ntriples > $@

# Then cant.py -f to-smushed.nt -d smushed-regen.nt

