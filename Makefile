# $Id$

PYTHON=python2

YAPPS=yapps2.py

rdfn3.py: rdfn3.g
	$(PYTHON) $(YAPPS) rdfn3.g $@