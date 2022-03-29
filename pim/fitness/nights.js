// This file parses data from the `moves` app which was a great
// quantified self style activity tracker which ws boaught by Facebook and eventually turned off.
// I thinbk the idea of this file was to extract from the places file the country a person had been in each niight
// for the puroposes of filling it in when needed on tax forms
//
    var fs = require('fs');
    // var json = require('json');
    var buf = fs.readFileSync('/Users/timbl/Documents/Automation/moves_export/json/full/places.json');
    var list = JSON.parse(buf);
    console.log('length: ' + list.length);

    var d, da, date, segments, t0, t1, location;
    for (var i=0; i<list.length; i++) {
        var d = list[i];
        da = d.date;
        if (d.segments) {
            segments = d.segments;
            for (s=0; s<segments.length; s++) {
                t0 = segments[s].startTime;
                t1 = segments[s].endTime;
                if (t0.slice(0,8) === t1.slice(0,8)) {
                    continue; // same day
                }
                location = segments[s].place.location;
                console.log(t0 + ' - ' + t1 + ' : ' + location.lon);


            }
        }
    }
