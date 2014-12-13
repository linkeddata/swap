#   File jason files away by date
#
import sys, os
for fn in  sys.argv[1:]:
    buf = open(fn).read()
    y = buf.find('"date"')
    colon = buf.find(':', y);
    quote = buf.find('"', colon);
    da = buf[quote+1:quote+9];
    print da
    dir = "~/Documents/%s/%s/%s" % (da[0:4], da[4:6], da[6:8]);
    command = 'mkdir -p %s; mv %s %s/%s ' % (dir,fn, dir, 'jsonstoryline.json');
    print command
    os.system(command)