# TEst difference system
for i in test/*; do (python ../cal/fromIcal.py --base http://www.w3.org/2002/12/calendar/tim-other $i/tim-other.ics > $i/tim-other.rdf); done
