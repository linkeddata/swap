#  Manipulate calendar and contact information
#
#  Usage:    make PW=<mypassword> teleconference.n3
#
P=python
C=/devel/WWW/2000/10/swap/cwm.py
W=/devel/WWW
PIM=$W/2000/10/swap/pim
CALFOLDER=/Users/timbl/evolution/local/calendar

.SUFFIXES: .ics3 .icsx .ics .html .cal .ocal

YYYY=2002
MM=06

.cal.html:
	$P $C $< cal2html.n3 --think --strings > $@

.cal.ics:
	$P $(PIM)/toIcal.py $<  > $@

.ocal.cal:
	$P $C $(PIM)/mso2hybrid.n3 $< --think > $@

.ics.icsx:
	perl $(PIM)/ical2rdf.pl $< > $@
.icsx.ics3:
	$P $C --rdf $< --n3 > $@

all :  conf.ics # 2002-06.html 2002.html


myconf.cal : teleconference.n3 $(PIM)/conf2cal.n3 participants.n3
	$P $C teleconference.n3 participants.n3 -filter=$(PIM)/conf2cal.n3 > $@

conf.cal : teleconference.n3 $(PIM)/conf2cal-all.n3
	$P $C teleconference.n3 -filter=$(PIM)/conf2cal-all.n3 > $@

conferences.cal: teleconference.n3
	$P $C teleconference.n3 -filter=$(PIM)/conf2cal-all.n3 > $@

teleconference.n3 :
	wget --http-user=$(USER) --http-passwd=$(PW) http://www.w3.org/Guide/1998/08/teleconference.rdf
	$P $C -rdf teleconference.rdf -n3 > $@
# ends


