#  Makefile for crypto test
#
#  This is a little authentication demonstration
#  All the files are in one directory. The .private files would
#  in reality be kept secure by the relevant groups or people.
#
CWM=python ../../cwm.py --crypto

W=/devel/WWW
RM=$W/2001/04/roadmap
PD=$W/2001/02pd

include $(PD)/GVDOT.mak

.SUFFIXES: .response .request .public .private

.request.response:
	$(CWM) access-rule.n3 --think --purge --with $< > $@

.private.public:
	$(CWM) $< access-onlyPublic.n3 --think --purge > $@

#all: access-1.response
#	touch all

all: access-1.response

clean:
#	rm *.response *.cert *.public 
	rm make.graph make.dot make.n3

# First, the parties involved create the keys they need.

# Alan makes a master key to use as the final authority in all this.
# It contains his matching public and private keys. He keeps this file safe.
access-master.private : access-gen-master.n3
	$(CWM) access-gen-master.n3 --think --purge > access-master.private

# From that, Alan makes a public file to announce only the public key.

access-master.public : access-master.private

# Kari makes a keypair to use in his role as a delegated authority.
access-elisa.private : access-gen-elisa.n3
	$(CWM) access-gen-elisa.n3 --think --purge --with "Elisa" > access-elisa.private

access-elisa.public : access-elisa.private


#  Alan now signs a certificate for Kari, to indicate that he is representative of Elisa.
#  (Alan makes a note of who he gave this cert to, for tracking.)
#  He uses his private key for this, but only need Elisa's public key,
# which Kari brings him.

access-elisa.cert : access-elisa.public access-master.private
	$(CWM) access-elisa.public access-master.private access-sign-member-cert.n3 --think --purge --with "Elisa" > $@


# Tiina's browser (or w3C script) makes a keypair for her to use for access to the site.
# (She can reuse the same key pair for many sites.) 
access-tiina.private : access-gen-tiina.n3
	$(CWM) access-gen-tiina.n3 --think --purge  > access-tiina.private

access-tiina.public : access-tiina.private

#  Kari now signs a certificate for Tiina, to indicate that she is an employee of Elisa.
#  (Kari makes a note of who he gave this cert to, for tracking.)
#  He uses his private key for this, but only need Tiina's public key, which she brings him.

access-tiina.cert : access-tiina.public access-elisa.private
	$(CWM) access-tiina.public access-elisa.private access-sign-cert.n3 --think --purge --with "Tiina" > $@


# When she wants to browse the W3C member site, Tiina's software signs a request with her public key:
access-1.request : access-tiina.private access-sign-request.n3
	$(CWM) access-tiina.private access-sign-request.n3 --think --purge --with http://www.w3.org/Member > $@

# The response to the request is generated in the server by access-rule.n3 
# It checks that the chain of authority has been satisfied by appropriate signed statements.
access-1.response : access-1.request access-rule.n3 access-tiina.public access-tiina.cert access-elisa.cert access-master.public

######################### Makefile diagram

make.n3 : Makefile $W/2000/10/swap/util/make2n3.py
	python $W/2000/10/swap/util/make2n3.py Makefile > $@

make.graph: make.n3 $(RM)/make-style.n3
	$(CWM) make.n3 $(RM)/make-style.n3 --think >$@

make.dot: make.graph
	TARGET=$< $(CWM) $(RM)/todot.n3 -think --strings | sed -f $(RM)/fix-amp.sed > $@

make.svg: make.dot

# ends
