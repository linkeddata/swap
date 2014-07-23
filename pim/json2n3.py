#!/usr/bin/python2.6
#   Need 2,6 or later for json module.
#
#
"""Convert json to Turtle

Usage:
    python2.6 json2n3.py -namespace http://www.w3.org/ns/pim/moves < foo.json > foo.ttl

If ommitted the namepsace reverts to the local namespace of the file.

"""
import json, sys, codecs
from sys import argv

#from swap import 


def getArg(key):
    for i in range(len(argv)):
        if argv[i] == key and i+1 < len(argv):
            return argv[1+1]
    return None;

class Turtleizer():
    def __init__(self, outFp):
        self.outs = outFp;
        return

    def writeln(self, str):
        self.outs.write(str + '\n');
        
    def toTurtle(self, x, level = 0):
        indent = '  ' * level;
        if level == 0:
            ns = getArg('-namespace');
            if ns:
                self.writeln('@prefix : <%s#>.' % ns); # Note arg WITHOUT THE HASH
            self.writeln('<> :value ');
        
        # self.writeln(indent + '#' + `x`[:30])
        if type(x) == type([]):
            self.writeln(indent + '(');
            for y in x:
                self.toTurtle(y, level + 1)
            self.writeln(indent + ')');
        elif type(x) == type({}):
            self.writeln(indent + '[');
            for key, value in x.items():
                self.writeln(indent + ':'+key + ' ');
                self.toTurtle(value, level + 1);
                self.writeln(indent + ';')
            self.writeln(indent + ']');
        elif type(x) == type(u''):
            self.writeln('"""' + x.replace('"', '\\"') + '"""')
        elif x == None:
            self.writeln(indent + `()`);
        elif `x` == 'True':
            self.writeln(indent + 'true');  #  Python to n3
        elif `x` == 'False':
            self.writeln(indent + 'false');
        else:
            self.writeln(indent + `x`);


        if level == 0:
            self.writeln('.\n#ends ')


inFile = json.load(open('/dev/stdin'));   ##  @@@@ decode utf-8?
outFile =  codecs.open('/dev/stdout', 'w', 'utf-8');
ttl = Turtleizer(outFile);
ttl.toTurtle(inFile);

# print `foo`;



