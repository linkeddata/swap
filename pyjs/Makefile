
W=../../../..
S=$W/2000/10/swap
C=python $S/cwm.py


not3a.js : pyjs.py not3.py
	python pyjs.py not3.py > not3a.js

not3.js : not3a.js fix.sed
	sed < not3a.js -f fix.sed  > not3.js

