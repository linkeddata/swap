#   File files away by date in their name
#
import sys, os
for fn in  sys.argv[1:]:
    print "Filename ", fn
    space = fn.rfind(' ')
    year = fn[space+1 : space+5]
    m = space + 6  
    dash2 = fn.find('-', m)
    month = fn[m:dash2]
    dot = fn.find('.', dash2)
    day = fn[dash2 + 1 : dot]
    day = ('0' + day) [-2:]
    month = ('0' + month) [-2:]
    date = year + '-' + month + '-' + day
    print "Date = %s-%s-%s" % (year, month, day)
    assert len(year) == 4
    assert len(month) == 2
    assert len(day) == 2
     
    dir = "/Users/timbl/Documents/%s/%s/%s" % (year, month, day);
    command = 'mkdir -p "%s"; mv "%s" "%s" ' % (dir,fn, dir);
    print command
    os.system(command)