for ((i=1;i<8;i=i+1))
	do
	mkdir $i
	( (cd /devel/WWW/2002/01/tr-automation; cvs update -p -r 1.$i tr.rdf) > $i/tr.rdf)
	done
