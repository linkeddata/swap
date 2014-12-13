# Cross-correlate photo times with GPS track
#
# Get photo metadata for today's photos:
#

W=/devel/WWW
S=$W/2000/10/swap

locations.n3 : PhotoMeta.n3
	python $S/pim/day.py --gpsData . > $@


PhotoMeta.n3 :

#	jhead -n3 `pwd | sed -e 's:Documents:Pictures/iPhoto\\ Library:'`*.JPG > $@
	jhead -n3 ../../../../Pictures/iPhoto\ Library/`pwd | sed -e 's:.*Documents/::'`/*.JPG > $@

# 

gpsData.n3:
	PYTHONPATH=/devel/pygarmin/:$S python \
	/devel/WWW/2000/10/swap/pim/fromGarmin.py --verbose --tracks \
	 --device=`ls /dev/cu.USA19H191P1.1`