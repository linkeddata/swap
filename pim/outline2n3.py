#! /usr/bin/python
"""  Convert Outline files text to n3 notation
 
 Runtime options:

    -namespace xxx  Properties are in namespace <xxx#> note added hash
    -help           Display this message and exit.
    
This is or was http://www.w3.org/2000/10/swap/pim/outline2n3.py
It is open source under the W3C software license.
http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231
"""
import sys
import string
from sys import argv
import sys, codecs
import xml
import xml.etree.ElementTree as etree


predicateList = [ 'dc:title', 's:comment', 'flow:attachment' ];

predicateTypeList = [ 'string', 'string', 'uri' ];

#   Convert data from tables in XHTML
#

def info(s):
    sys.stderr.write(s + '\n');
    return

class OutlineTree(list):
    """An array of rows in a 2-d table whch has also
    column headings etc"""
    
    def __init__(self):
        self.nextId = 0
        self.col = -1
        self.row = -1
        self.numberOfColumns = 0;
        self.idOffset = 0;
        self.headings, self.tips = [], []
        self.cellType = ''
        self.kludge = 0; # Kludge: we are following a <br>
 
#  XML
          
    def parseXML(self, infile, encoding="utf-8"):
        tree = etree.parse(sys.stdin);
        root = tree.getroot();
        self.doElement(root)
        self.cleanup()
        return;
   
    def newThing(self, id = None):
        if id != None:
            return '<#%s>' % id;
        self.nextId = self.nextId + 1;
        return '<#n%i>' % self.nextId;

    def anyTextContent(self, e): # Order not preseved if mixed content
        if e.tag.split('}')[1] == 'style': return "";
        str = e.text or "";
        for c in e:
            str += self.anyTextContent(c);
        if (e.tail) : str += e.tail;        
        return str.strip();
    
    def stringEncodeforN3(self, s):
        return '"""' + s.replace('"', r'\"') + '"""';
    
    def doElement(self, e, level=0,  context = None, pn = 'P', num = 1):
        
        if not context: context = self.newThing();
        indent = '    ' * level;
        child_pn = pn
        tag = e.tag.split('}')[1];
        
        if tag == 'root':
            self.root = self.newThing();
            self.context = self.root;

        if tag in [ 'style', 'columns' ]:
            return;

        elif tag == 'item':
            item = self.newThing(e.attrib.get('id'));
            
            assert e[0].tag.split('}')[1] == 'values';
            values = e[0];
            assert e[0][0].tag.split('}')[1] == 'text', "Tag is not text but " + e[0][0].tag.split('}')[1];
            title = self.anyTextContent(e[0][0]);   # values/text child

            
            self.outln("# pn = %s, level = %i, num = %i, values=%i"  %(pn, level, num, len(e[0])));
            if not (level % 2):
                child_pn = pn + '' + str(num);
            else:
                child_pn = pn + '' + str(unichr((ord('a')+num)));
            item = '<#%s>' % child_pn
            
            if title[:3] in ['But', 'but']:
                relation =  ' arg:opposition '
                title = title[4:];
            else:
                relation =  ' arg:support '
            self.outln(indent + context + relation + item + ' .');
            self.outln(indent + item + ' dc:title """' + title + '""".');

            for i in range(len(values)):
                v = self.anyTextContent(values[i]);
                if i != 0  and v: # first col is special cased above
                    if predicateTypeList[i] == 'uri':
                        self.outln(indent + item + ' '+predicateList[i]+' <' + v + '>.'); # @@encoding
                    else:
                        self.outln(indent + item + ' '+predicateList[i] + ' ' + self.stringEncodeforN3(v) + '.'); # @@encoding

            
            for x in e:
                self.doElement(x, level + 1, item, child_pn, num);
            return;
            
        # Child elements

        elif tag == 'children' or tag == 'root':
            n = 0
            for x in e:
                n = n + 1
                self.doElement(x, level, context, child_pn, n);
            return
            
        # Default recurision for everything other than children:
        for x in e:
            self.doElement(x, level, context, pn, num);


        #  End tag actions:

 
    def cleanup(self):
        r = range(len(self));
        r.reverse();
        for i in r:
            if len(self[i]) < 10:
                info( "# row = %i/%i, was %i long," % (i, len(self), len(self[i])));
                del self[i];
        return;

##############

    def diagnosticString(self):
        s = ""
        s +=  " %i rows  Data: %s\n" % (len(self), `self`);
        s += " %i headings:%s\n" % (len(self.headings), `self.headings`);
        s+= " %i Tips: %s\n" % (len(self.tips),  `self.tips`)
        s += "%i columns:\n" % (self.numberOfColumns)
        for row in range(len(self)):
            if len(self[row]) != len(self.headings):
                s += "Row %i has %i columns!\n" % (row, len(self[row]))
        return s



###########################
        
    def headers(self, namespace):
        self.outln("@prefix : <%s>." % namespace);
        self.outln("@prefix arg: <%s>." % namespace);
        self.outln("""@prefix dc: <http://purl.org/dc/elements/1.1/>.
        @prefix flow: <http://www.w3.org/2005/01/wf/flow#>.
        @prefix s: <http://www.w3.org/2000/01/rdf-schema#> .
        """);
#        self.outln( "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>.");


 
    def outln(self, s):
        self.outFP.write(s + '\n');
    
    def convert(self, argv, inFP):
        
        # Command line args:
        
        self.outFP =  codecs.open("/dev/stdout", "w", "utf-8");
#        self.outFP = outFP

        namespace = 'http://www.w3.org/ns/pim/arg#';
        for i in range(len(argv)-2):
            if argv[i+1] == '-namespace': namespace = argv[i+2] + '#'
            if argv[i+1] == '-startId': self.idOffset = int(argv[i+2])
                
        if "-help" in argv[1:]:
            info( __doc__);
            return
            
        if "-comma" in argv[1:]:
            delim = ','
        else:
            delim = '\t'
            
        self.headers(namespace);
        self.parseXML(inFP);
        self.outln( "# Ends");

        return
    

t = OutlineTree();
t.convert(sys.argv, sys.stdin);



#ENDS
