# Make tests for builtins

CODE=../../cwm.py ../../notation3.py ../../xml2rdf.py
C=python ../../cwm.py

RESULTS=t1.result t2.result t3.result t4.result t5.result t6.result t7.result t8.result

.n3.result:
	$C $< -think > $>

all: $(RESULTS)
	cat $(RESULTS) > all

t1.result: t1.n3 $(CODE) 
	$C $< -think > $@
t2.result: t2.n3 $(CODE) 
	$C $< -think > $@
t3.result: t3.n3 $(CODE) 
	$C $< -think > $@
t4.result: t4.n3 $(CODE) 
	$C $< -think > $@
t5.result: t5.n3 $(CODE) 
	$C $< -think > $@
t6.result: t6.n3 $(CODE) 
	$C $< -think > $@
t7.result: t7.n3 $(CODE) 
	$C $< -think > $@
t8.result: t8.n3 $(CODE) 
	$C $< -think > $@
