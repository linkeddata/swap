# make

SWAP=../..

.SUFFIXES: .proof .n3

.n3.proof:
	python $SWAP/cwm.py $< --think --base=foo --why > $>
.proof.check:
	python check.py $<
	touch $>

all : t5.proof


#ends
