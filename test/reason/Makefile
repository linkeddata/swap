# make

SWAP=../..

.SUFFIXES: .checked .proof .result .n3

.n3.proof:
	python $(SWAP)/cwm.py $< --think --base=foo --why > $@
.n3.result:
	python $(SWAP)/cwm.py $< --think --base=foo > $@
.proof.checked:
	python $(SWAP)/check.py $< > $@

all : t1.checked t2.checked t3.checked t4.checked t5.checked

clean :
	rm *.proof *.result *.checked *.diff

t5.diff: t5.result  t5.checked
	diff t5.result t5.checked > $@

#ends
