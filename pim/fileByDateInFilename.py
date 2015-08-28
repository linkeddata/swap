#   File files away by date in their name
#
import sys, os
for fn in  sys.argv[1:]:
    print "Filename ", fn
    if 0:  # Old 2014 moves format
        space = fn.rfind(' ')
        year = fn[space+1 : space+5]
        m = space + 6  
        dash2 = fn.find('-', m)
        month = fn[m:dash2]
        dot = fn.find('.', dash2)
        day = fn[dash2 + 1 : dot]
        day = ('0' + day) [-2:]
        month = ('0' + month) [-2:]
    else: # new 2015 moves exprt format
        underline = fn.find('_')
        type = fn[0:underline]
        year = fn[underline+1:underline+5]
        month = fn[underline+5:underline+7]
        day = fn[underline+7:underline+9]
        assert fn[underline+9:underline+14] == '.json'
        
    date = year + '-' + month + '-' + day
    print "Date = %s-%s-%s" % (year, month, day)
    assert len(year) == 4
    assert len(month) == 2
    assert len(day) == 2
     
    dir = "/Users/timbl/Documents/%s/%s/%s" % (year, month, day);
    dest = "/Users/timbl/Documents/%s/%s/%s/%s.json" % (year, month, day, type);
    command = 'mkdir -p "%s"; mv "%s" "%s" ' % (dir,fn, dest);
    print command
    os.system(command)