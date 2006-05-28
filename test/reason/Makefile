# make

SWAP=../..
CWM=time python $(SWAP)/cwm.py

.SUFFIXES: .checked .pml .proof .result .n3

.n3.proof:
	python $(SWAP)/cwm.py $< --think --base=foo --why > $@
.n3.result:
	python $(SWAP)/cwm.py $< --think --base=foo > $@

#--mode=mrse
.proof.pml:
	python $(SWAP)/cwm.py  $< ../../reason.n3 --think=to-pml.n3 --data --rdf=b > $@

.proof.checked:
	python $(SWAP)/check.py < $< > $@

all : t1.checked t2.checked t3.checked t4.checked t5.checked judy-proof.n3

clean :
	rm *.proof *.result *.checked *.diff

t5.diff: t5.result  t5.checked
	diff t5.result t5.checked > $@

judy-proof.n3:
	$(CWM) --chatty=10 --n3=B \
	http://dig.csail.mit.edu/2005/09/rein/examples/judy-req.n3 \
	http://dig.csail.mit.edu/2005/09/rein/engine.n3 \
	--mode=h --think \
	--filter="http://dig.csail.mit.edu/2005/09/rein/filter.n3"  --why \
					> judy-proof.n3

judy-out.n3:
	$(CWM) --n3=B \
	http://dig.csail.mit.edu/2005/09/rein/examples/judy-req.n3 \
	http://dig.csail.mit.edu/2005/09/rein/engine.n3 \
	--mode=h --think \
	--filter="http://dig.csail.mit.edu/2005/09/rein/filter.n3"  \
					> judy-out.n3

animals-proof.n3: animals.n3 animal-goal.n3 ../../util/rdfs-nice.n3 ../../util/owlth.n3
	$(CWM) animals.n3 ../../util/rdfs-nice.n3 ../../util/owlth.n3 \
		--think --filter=animal-goal.n3 --why >$@
#ends
