# See HEADER.html for more details
# danbri@w3.org

# compare:
# eg 4suite packaging
# http://prdownloads.sourceforge.net/foursuite/4Suite-0.12.0a3.tar.gz?download
# also rdflib ?


PACKAGE=swap-cwm
#MAINVERSION=0.91
MAINVERSION=0.9
DEBVERSION=1
FULLNAME=$(PACKAGE)_$(MAINVERSION)-$(DEBVERSION)

 
package:	update debianize repofiles list 
website:	package publish
 
#todo: debian/docs should be built with find, excluding the format dir

update:
	# grab latest version of files from development tree
	mkdir -p $(PACKAGE)-$(MAINVERSION)/doc ; \
	mkdir -p $(PACKAGE)-$(MAINVERSION)/lib ; \
	cd $(PACKAGE)-$(MAINVERSION)/lib; tar -zxvf ../../../../cwm.tgz
	(cd ./debian-files && tar cf - .  --exclude CVS) | (cd  $(PACKAGE)-$(MAINVERSION)  && tar xf -)
	(cd ../.. && tar cf - doc  --exclude CVS --exclude format ) | (cd $(PACKAGE)-$(MAINVERSION)/  && tar xf -)
	cp setup.py $(PACKAGE)-$(MAINVERSION)/
	

test:
	cd $(PACKAGE)-$(MAINVERSION)/test/; make test\

list:
	dpkg -c $(FULLNAME)_all.deb

debianize:
	echo "Generating debian package: $(FULLNAME) "
	cd $(PACKAGE)-$(MAINVERSION)/ ; \
	dpkg-buildpackage -rfakeroot -uc -us
 	# -us -uc switches off signing

repofiles:
	/usr/bin/apt-ftparchive packages . >Packages
	cat Packages | gzip -9 >Packages.gz
	/usr/bin/apt-ftparchive sources . >Sources
	cat Sources | gzip -9 >Sources.gz

publish: finkhack
	cvs commit 

clean:
	rm -f Packages Packages.gz Sources Sources.gz
	rm -f $(FULLNAME).dsc $(PACKAGE)-$(MAINVERSION).tar.gz $(FULLNAME).tar.gz $(FULLNAME)_all.deb $(FULLNAME)_$(ARCH).changes
	rm -rf $(PACKAGE)-$(MAINVERSION)/

 
install:
	dpkg -i $(PACKAGE)_$(MAINVERSION)-$(DEBVERSION)_all.deb

uninstall:
	dpkg -r $(PACKAGE)




# This separate fink bundle doesn't work yet
# and may never do...
#
finktree:
	# grab latest version of files from development tree
	mkdir -p fink/$(PACKAGE)-$(MAINVERSION)/lib
	mkdir -p fink/$(PACKAGE)-$(MAINVERSION)/doc
	(cd ../../pack && tar cf - lib --exclude CVS) | (cd fink/$(PACKAGE)-$(MAINVERSION)  && tar xf -)
	(cd ../../pack && tar cf - doc --exclude CVS) | (cd fink/$(PACKAGE)-$(MAINVERSION)  && tar xf -)
	(cd ./debian-files && tar cf - .  --exclude CVS) | (cd fink/$(PACKAGE)-$(MAINVERSION)  && tar xf -)
	cp ./fink.config.save fink/$(PACKAGE)-$(MAINVERSION)/config.save
	cp ../../pack/install.rb fink/$(PACKAGE)-$(MAINVERSION)

	@echo "Generating Fink package: $(FULLNAME) "
	cd fink/$(PACKAGE)-$(MAINVERSION)/ ; \
	dpkg-buildpackage -rfakeroot -uc -us
        
	@echo "Generating package files for Fink tree."
	/usr/bin/apt-ftparchive packages ./fink/ >fink/Packages
	cd fink; cat Packages | gzip -9 >Packages.gz
	/usr/bin/apt-ftparchive sources ./fink/ >fink/Sources
	cd fink; cat Sources | gzip -9 >Sources.gz

	cd fink; cp $(PACKAGE)_$(MAINVERSION)-$(DEBVERSION).tar.gz $(PACKAGE)-$(MAINVERSION).tar.gz

