# Test difference system

# Skip 1 and 2 as 1 has file://home/connolly namespace which screws up diff

for ((i=3; i<100; i++))
	do
	#echo python2.3 $SWAP/diff.py -f $(($i-1))/tr.rdf -t $i/tr.rdf
	#(python2.3 $SWAP/diff.py -f $(($i-1))/tr.rdf -t $i/tr.rdf > $i/tr.delta) || exit
	(cd test/$i; ln -s ../$(($i-1)) previous)
	(cd test/$i; make -f ../1/Makefile) || exit
	ls -l test/$i/tr.delta
	done
echo end
