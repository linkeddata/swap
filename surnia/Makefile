

output::
	time python surnia.py --maxSeconds 10 -t http://www.w3.org/2002/03owlt/editors-draft/draft/Manifest.rdf | tee output
	@echo 'PASSED ' `grep PASSED output | wc -l`
	cp output old-results/output-`date +%Y-%m-%dT%H:%m:%S`


