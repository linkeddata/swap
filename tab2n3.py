#! /usr/bin/python
"""  Convert tab-separated text to n3 notation
  This has been hacked in 2000 to work with the "Tab separated (Windows)" output from
 MS Outlook export of contact files.
 Hacked again to allow input from XHTML files for BoA mortgage page 2012
 To parse HTML files use "tidy -asxml" first.
 
 Runtime options:

    -comma          Use comma as delimited instead of tab
    -xhtml          Read XHTML and look for a table, instead of CSV or TSV
    -sheet          Read the XML sheet file from an unzipped Excel .xlsx file
    -stringTableFileName foo  gives the string table XML file for excel
    -id             Generate sequential URIs for the items described by each row
    -reverse        Generate the URIs in reverse order (e.g for reve chron order) 
    -startId        With -id, start ids at this number (default 0) eg -startId 1
    -idfield        Use column 'id' to form the URI for each item
    -type           Declare each thing as of a type <#Item>.
    -namespace xxx  Properties are in namespace <xxx#> note added hash
    -schema         Generate a little RDF schema
    -nostrip        Do not strip empty cells
    -help           Display this message and exit.
    
This is or was http://www.w3.org/2000/10/swap/tab2n3.py
It is open source under the W3C software license.
http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231
"""
import sys
import string
from sys import argv
import sys
import xml
import xml.etree.ElementTree as etree


#   Convert data from tables in XHTML
#

def info(s):
    sys.stderr.write(s + '\n');
    return

class DataTable(list):
    """An array of rows in a 2-d table whch has also
    column headings etc"""
    
    def __init__(self):
        self.tab = {}
        self.col = -1
        self.row = -1
        self.numberOfColumns = 0;
        self.idOffset = 0;
        self.headings, self.tips = [], []
        self.cellType = ''
        self.kludge = 0; # Kludge: we are following a <br>
        
        self.htmlTags = {
            'table':    ['table'], 
            'row':      ['tr'],
            'cell':     [ 'td', 'th' ] 
        }
        self.sheetTags = {
            'table':    ['sheetdata'], 
            'row':      ['row'],
            'cell':     [ 'c', ] 
        }
 
#  Unzipped Excel spreadsheet
          
    def parseSheet(self, infile, stringTableFile):
        self.parseSharedStringTable(stringTableFile);
        tree = etree.parse(infile);
        root = tree.getroot();
        self.doElement(root, self.sheetTags, None)
        self.cleanup()
        
        print self.diagnosticString()
        print 'self:', self
        return;

    def parseSharedStringTable(self, infile):
        tree = etree.parse(infile);
        self.shortStrings = []
        root = tree.getroot();
        tag = root.tag.split('}')[1];
        assert tag == 'sst'
        count = 0
        for si in root:
            assert si.tag.split('}')[1] == 'si'
            t = si[0]
            assert t.tag.split('}')[1] == 't'
            if t.text: 
                self.shortStrings.append(t.text)
                print "Short string %i:" % count, t.text 
            else:
                self.shortStrings.append('')
            count += 1

#  XHTML (or spreadsheet XML)
          
    def parseXHTML(self, infile):
        tree = etree.parse(infile);
        root = tree.getroot();
        self.doElement(root, self.htmlTags, None);
        self.cleanup()
        return;
   
    def pokeString(self, s, hide):
        print "Pokestring at %i,%i " % (self.row, self.col), s
        if self.row >= -1 and self.col >= 0:
            s = s.strip()
            if self.row > 0:
                self[self.row][self.col] += s;
            else:   # tr th p span   or    tr th span 
                if not hide:
                    if len(self.headings) < self.col + self.kludge + 1:
                        self.headings.append('')
                        self.tips.append('')
                    self.headings[self.col+self.kludge] += s;
                else:
                    self.tips[self.col] += s;

    def doElement(self, e, tags, parent, level=0, hide = 0):
        
        def newColumn():
            self.col += 1
            if self.col >= self.numberOfColumns: self.numberOfColumns = self.col + 1
            if self.row >= 0:
                self[self.row].append('');
            else:
                self.headings.append('');
                self.tips.append('');
            return

        tag = e.tag.split('}')[1];
        if tag in tags['table']:
            self.row = -2;
        elif tag in tags['row']:
            self.row += 1;
            self.append([]);
            self.col = -1;
            
        elif tag in tags['cell']: #   or (tag =='br' and col >= 0):

            self.cellType = tag
            newColumn()
            print "         column ", self.col
            
        elif tag == 'br':
            self.kludge = 1  #  A break moves temporarily to the next stacked column

        elif tag == 'v':  # A reference in excel to the string table.
            if parent.attrib.get('t','') == 's':
                self.pokeString(self.shortStrings[int(e.text)], hide);
                # print " tttt ", self.shortStrings[int(e.text)], 'at', self.row, self.col
            elif parent.attrib.get('s', ''):
                self.pokeString('date '+e.text, hide);
                # print " ssss ", 'date '+e.text, 'at', self.row, self.col
            else:
                print parent.tag, parent.attrib,  e.tag, e.attrib, e.text
                assert False
 
        #   Now poke any text content into the array:
        
        if tag != 'v' and (e.text) : self.pokeString(e.text, hide);        

        # Child elements

        for x in e:
            self.doElement(x, tags, e, level+1, hide or e.attrib.get('class',"") == 'hide')

        if (e.tail) :
            print "Tail ", e.tail
            self.pokeString(e.tail, hide);        

        #  End tag actions:

        self.kludge = 0;        
        if tag == 'table':
            self.row = self.col = -1;
        if e.attrib.get('class',"") == 'row-top' and not hide:  # BoA special
            newColumn()

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


############# CSV:

    # Column headings can have newlines embedded
    def sanitize(self,s):
        return s.replace('\n', ' ')
                
    def sanitizeID(self, s):
        res = ""
        for ch in s:
            if ch in string.ascii_letters or ch in string.digits:
                res += ch
            else:
                if res[-1:] != '_':
                    res += '_'
        while res[-1:] == '_':
            res = res[:-1]
        return res
        

    def readTabs(self,delim, inFp):
        result = []

        l = inFp.readline()
        if len(l) == 0 : return result #EOF
        while l != "" and l[-1:] in "\015\012" :
            l=l[:-1]  # Strip CR and/or LF

        while 1: # Next field
            if l == "": return result  

            if l[0] == '"':  # Is this a quoted string?
                l = l[1:]  # Chop leading quote
                result.append("")
                while 1:
                    j = string.find(l, '"')  # Is it terminated on this line?
                    if j >= 0:   # Yes!
                        if l[j+1:j+2] == '"': # Two doublequotes means embedded doublequote
                            result[-1] =  result[-1] + l[:j] + '\\"'
                            l = l[j+2:]
                            continue
                        result[-1] = result[-1] + l[:j]
                        l = l[j+1:]
                        if l == "":  # End of values
                            return result
                        else:
                            if l[0] ==  delim:
                                l = l[1:]  # redundancy: tab follows quote
                            else:
                                raise "CSV parse error: No tab after close quote: "+l;
                                
                        break
                    else:  # Notterminated on this line
                        result[-1] = result[-1] + l + "\n" # wot no loop?
                        l = inFp.readline()
                        if len(l) == 0 : return result #EOF
                        while l != "" and l[-1:] in "\015\012" :
                            l=l[:-1]  # Strip CR and/or LF

            else:  # No leading quote: Must be tab or newline delim
                i=string.find(l, delim)
                if i>=0:
                    result.append(l[:i])
                    l = l[i+1:]
                else:
                    result.append(l)
                    return result           # end of values
         
    def readCSV(self, inFP, delim):
        
        self.headings = [ "" ];

        while len(self.headings) <2: # Hack for fidelity files which have pre-heading items
            self.headings = self.readTabs(delim, inFP)
            for jj in range(len(self.headings)):
                self.headings[jj] = self.headings[jj].strip()
                if len(self.headings[jj]) == 0:
                    self.headings[jj] = unichr(65+jj) #  Default to "A",  "B", etc
            while self.headings[-1:] == [""]: self.headings = self.headings[:-1]; # Strip trailing comma on heading line (paypal)
            info( "# headings found: %i  %s" % (len(self.headings), self.headings))

        while 1:
            values = self.readTabs(delim, inFP)
            if values == []: break
            if len(values) < 2: continue;
            if len(values) != len(self.headings):
                info( "#  Warning: %i headings but %i values" % (len(self.headings), len(values)))
            self.append(values);
        return
        
    def generateTurtle(self, argv, namespace):
        records = 0
        
        # Convert headings into Predicates:
        
        labels = []
        for i in range(0,len(self.headings)):
            h = self.headings[i]
            labels.append(h) # raw heading field
            self.headings[i] = self.sanitizeID(self.headings[i]);
            #for j in range(0,len(h)):
            #    if h[j] not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_":
            #        self.headings[i] = self.headings[i][:j] + "_" + self.headings[i] [j+1:]
            self.headings[i] = self.headings[i][:1].lower() + self.headings[i][1:] # Predicates initial lower case 
                    
        if namespace: self.outln( "@prefix : <%s>." % namespace);
        if "-schema" in argv[1:]:
            self.outln( "# Schema");
            # print "@prefix : <> ."
            self.outln( "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.");
            self.outln( "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>.");
            for i in range(0,len(self.headings)):
                self.outln( "  :%s  a rdf:Property; rdfs:label \"%s\"" % \
                        ( self.headings[i], self.sanitize(labels[i])  ))
                if i < len(self.tips) and self.tips[i]: self.outln( '; rdfs:comment """'+self.tips[i]+'"""')
                self.outln( ".");
            self.outln('');
     

        lastId = None;

        for rowNumber in range(len(self)):
            rowNumberIn = rowNumber
            if "-reverse" in argv[1:]:
                rowNumberIn = len(self) - rowNumber - 1

            values = self[rowNumberIn];
            open = False  # Open means the predicate object syntax needs to be closed
            str = ""
            this_id = None
            if "-type" in argv[1:]:
                str += " a <#Item> "
                open = True
            for i in range(len(values)):
                v = values[i].strip()
                if ((len(v) and v!="0/0/00"
                    and v!="\n") or  ("-nostrip" in argv[1:]))  :  # Kludge to remove void Exchange dates & notes
                    if i < len(self.headings) : pred = self.headings[i]
                    else: pred = 'column%i' % (i)
                    if ('-idfield' in argv[1:]) and self.headings[i] == 'id':
                        this_id = self.sanitizeID(v)
                    else:
                        if open:  str+= "; "
                        if string.find(v, "\n") >= 0:
                            str += '\n    :%s """%s"""' % (pred, v)
                        else:
                            str += '\n    :%s "%s"' % (pred, v)
                        open = True
            if open: str += "."
            open = False
            if str != "":
                thisId = '[]';
                if "-id" in argv[1:]:
                    thisId =  "<#n%i>" % (rowNumber + self.idOffset)
                elif  "-idfield" in argv[1:]:
                    thidId = "<#n%s>" % this_id;
                    
                if thisId != '[]' and lastId and '-next' in argv[1:]:
                    self.outln( '  %s :next %s .' % (lastId, thisId)); 
                self.outln( thisId + str);
                lastId = thisId;

        self.outln( "# Total number of records: %i" % len(self));

    def outln(self, s):
        self.outFP.write(s + '\n');
    
    def convert(self, argv, inFP, outFP):
        
        # Command line args:
        
        self.outFP = outFP

        namespace = None;
        for i in range(len(argv)-2):
            if argv[i+1] == '-namespace': namespace = argv[i+2] + '#'
            if argv[i+1] == '-startId': self.idOffset = int(argv[i+2])
            if argv[i+1] == '-sheet': self.sheetRootFileName = argv[i+2]
            
                
        if "-help" in argv[1:]:
            info( __doc__);
            return
            
        if "-comma" in argv[1:]:
            delim = ','
        else:
            delim = '\t'
            
        if "-sheet" in argv[1:]:
            sheetFile = open(self.sheetRootFileName + '/worksheets/sheet1.xml');
            sstFile = open(self.sheetRootFileName + '/sharedStrings.xml');
            self.parseSheet(sheetFile, sstFile);
        elif "-xhtml" in argv[1:]:
            self.parseXHTML(inFP);
        else:
            self.readCSV(inFP, delim);
        self.generateTurtle(argv, namespace);
        return
    

t = DataTable();
t.convert(sys.argv, sys.stdin, sys.stdout);



#ENDS
