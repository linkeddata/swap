#  Makefile for crypto test
#
#  This is a little authentication demonstration
#  All the files are in one directory. The .private files would
#  in reality be kept secure by the relevant groups or people.
#
CWM=python ../../cwm.py

.SUFFIXES: .response .request .public .private

.request.response:
	$(CWM) access-rule.n3 --think --purge --with $< > $@

.private.public:
	$(CWM) $< access-onlyPublic.n3 --purge > $@

#all: access-1.response
#	touch all

access-1.response : access-1.request access-rule.n3 access-tiina.public access-tiina.cert access-master.public

# Sign a request by Tiina for the W3C member page:
access-1.request : access-tiina.private access-sign-request.n3
	$(CWM) access-tiina.private access-sign-request.n3 --think --purge --with http://www.w3.org/Member > $@

# Elisa (Kari for example) signs a certificate for Tiina
#   Kari makes a note of who he gave this cert to, for tracking

access-tiina.cert : access-tiina.public access-elisa.private
	$(CWM) access-tiina.public access-elisa.private access-sign-cert.n3 --think --purge --with "Tiina" > $@

# Generate public keys and secret key pairs:

access-elisa.public : acecss-elisa.private

access-master.public : access-master.private
access-tiina.public : access-tiina.private

access-master.private : access-gen-master.n3
	$(CWM) access-gen-master.n3 --think --purge > access-master.private

access-elisa.private : access-gen-elisa.n3
	$(CWM) access-gen-elisa.n3 --think --purge --with "Elisa" > access-elisa.private

access-tiina.private : access-gen-tiina.n3
	$(CWM) access-gen-tiina.n3 --think --purge  > access-tiina.private


