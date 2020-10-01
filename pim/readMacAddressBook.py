#!/usr/bin/python2.7
# MIT License.  (c)timbl, Richard Newman
#test
# This is or was http://www.w3.org/2000/10/swap/pim/readMacAddressBook.py
# See also http://www.w3.org/2000/10/swap/pim/vcard2n3.py

# 2014-08-28 Adapted by timbl from the from the original Mac Address Book to FOAF Script
# Copyright 2003--2005 Richard Newman
# r.newman@reading.ac.uk

# Todo:
# done Generate full name
# - do hasName
# - option for different name order
# done figure out relations
#

# For programmer reference:
# Useful keys:
# AIMInstant, MSNInstant, ICQInstant, Address(values: City, Country, State, Street, ZIP), Birthday, Email(values), First, Last, (Middle), JobTitle, HomePage, Organization, Phone(values), UID.


# See https://developer.apple.com/library/mac/documentation/userexperience/Conceptual/AddressBook/AddressBook.html
import AddressBook, objc, array

import requests # https://stackoverflow.com/questions/111945/is-there-any-way-to-do-http-put-in-python

import PIL
from PIL import Image

import sha
import sys, codecs, os
import getopt

global globalExcFile
global globalUseFOAF
global globalNS
global globalIncFile
global globalRels
global globalIDList

globalIDList = {}
globalExcFile = ""
globalIncFile = False
globalUseFOAF = False


# The following from https://developer.apple.com/library/prerelease/mac/documentation/UserExperience/Reference/AddressBook/Miscellaneous/AddressBook_Constants/



defaultMultivalueListLabels = [

    AddressBook.kABHomePageLabel,
    AddressBook.kABEmailWorkLabel,
    AddressBook.kABEmailHomeLabel,
   # AddressBook.kABEmailMobileMeLabel,
    AddressBook.kABAddressHomeLabel,
    AddressBook.kABAddressWorkLabel,
    AddressBook.kABAnniversaryLabel,
    AddressBook.kABFatherLabel,
    AddressBook.kABMotherLabel,
    AddressBook.kABParentLabel,
    AddressBook.kABBrotherLabel,
    AddressBook.kABSisterLabel,
    AddressBook.kABChildLabel,
    AddressBook.kABFriendLabel,
    AddressBook.kABSpouseLabel,
    AddressBook.kABPartnerLabel,
    AddressBook.kABAssistantLabel,
    AddressBook.kABManagerLabel,
    AddressBook.kABPhoneWorkLabel,
    AddressBook.kABPhoneHomeLabel,
    AddressBook.kABPhoneiPhoneLabel,
    AddressBook.kABPhoneMobileLabel,
    AddressBook.kABPhoneMainLabel,
    AddressBook.kABPhoneHomeFAXLabel,
    AddressBook.kABPhoneWorkFAXLabel,
    AddressBook.kABPhonePagerLabel ];

GenericMultivalueListLabels = [
    AddressBook.kABWorkLabel,
    AddressBook.kABHomeLabel,
    AddressBook.kABOtherLabel,
    AddressBook.kABMobileMeLabel  ];

defaultRecordCreationProperties = [
    AddressBook.kABUIDProperty,
    AddressBook.kABCreationDateProperty,
    AddressBook.kABModificationDateProperty ];

defaultGroupProperties = [ AddressBook.kABGroupNameProperty ];

defaultPersonProperties = [
    AddressBook.kABFirstNameProperty,
    AddressBook.kABLastNameProperty,
    AddressBook.kABFirstNamePhoneticProperty,
    AddressBook.kABLastNamePhoneticProperty,
    AddressBook.kABNicknameProperty,
    AddressBook.kABMaidenNameProperty,
    AddressBook.kABBirthdayProperty,
    AddressBook.kABBirthdayComponentsProperty,
    AddressBook.kABOrganizationProperty,
    AddressBook.kABJobTitleProperty,
    AddressBook.kABHomePageProperty,
    AddressBook.kABURLsProperty,
    AddressBook.kABCalendarURIsProperty,
    AddressBook.kABEmailProperty,
    AddressBook.kABAddressProperty,
    AddressBook.kABOtherDatesProperty,
    AddressBook.kABOtherDateComponentsProperty,
    AddressBook.kABRelatedNamesProperty,
    AddressBook.kABDepartmentProperty,
    AddressBook.kABPersonFlags,
    AddressBook.kABPhoneProperty,
    AddressBook.kABInstantMessageProperty,
    AddressBook.kABNoteProperty,
    AddressBook.kABSocialProfileProperty,
    AddressBook.kABMiddleNameProperty,
    AddressBook.kABMiddleNamePhoneticProperty,
    AddressBook.kABTitleProperty,
    AddressBook.kABSuffixProperty ];

addressKeys = [
    AddressBook.kABAddressStreetKey,
    AddressBook.kABAddressCityKey,
    AddressBook.kABAddressStateKey,
    AddressBook.kABAddressZIPKey,
    AddressBook.kABAddressCountryKey,
    AddressBook.kABAddressCountryCodeKey
];

MacToVCard = {
    'Birthday': { 'predicate': 'vcard:anniversary'},
    'Email': { 'predicate': 'vcard:hasEmail', 'uriScheme' : 'mailto:'},
    'Address': { 'predicate': 'vcard:hasAddress'},  #  @@@  Add 'has' automatically where object property?
    'Creation': { 'predicate': 'dc:created'},
    'GroupName': { 'predicate': 'vcard:fn'},
    'JobTitle': { 'predicate': 'vcard:title' },
    'Modification': { 'predicate': 'dc:modified'},
    'Note': { 'predicate': 'vcard:note'},
    'Organization': { 'predicate': 'vcard:organization-name'},
    'Phone': { 'predicate': 'vcard:hasTelephone', 'uriScheme' : 'tel:'},
    'ABRelatedNames': { 'predicate': 'vcard:hasRelated' },
    'UID': { 'predicate': 'vcard:hasUID' , 'uriScheme' : 'urn:uuid:'},   # @@@ Warning the data form ' url lower case
    'URLs': { 'predicate': 'vcard:url', 'uriScheme' : ''},  # @@ Needs <> not ""

# Top level in AB but under vcard:hasName in Vcard.

    'Title': { 'predicate': 'vcard:honorific-prefix', 'path': 'vcard:hasName' },
    'First': { 'predicate': 'vcard:given-name', 'path': 'vcard:hasName' },
    'Middle': { 'predicate': 'vcard:additional-name', 'path': 'vcard:hasName' },
    'Last': { 'predicate': 'vcard:family-name', 'path': 'vcard:hasName' },
    'Suffix': { 'predicate': 'vcard:honorific-suffix', 'path': 'vcard:hasName' },

# Sub parts of address:
    'Street': { 'predicate': 'vcard:street-address'},
    'City': { 'predicate': 'vcard:locality'},
    'State': { 'predicate': 'vcard:region'},
    'ZIP': { 'predicate': 'vcard:postal-code'},
    'Country': { 'predicate': 'vcard:country-name'},
    'CountryCode': { 'predicate': 'vcard:country-code'},  #  @@@ Not in current VCARD spec
};

MacIgnore = [ AddressBook.kABBirthdayComponentsProperty ]

nameParts = [
    AddressBook.kABTitleProperty,
    AddressBook.kABFirstNameProperty,
    AddressBook.kABLastNameProperty,
    AddressBook.kABMiddleNameProperty,
    AddressBook.kABSuffixProperty ];

emailRelated = [
    AddressBook.kABEmailProperty,
    AddressBook.kABEmailWorkLabel,
    AddressBook.kABEmailHomeLabel];

def prefixes():
  """Spit out the RDF etc. at the start of a FOAF file.
"""
  return """@prefix vcard: <http://www.w3.org/2006/vcard/ns#>.
@prefix ab: <http://www.w3.org/ns/pim/ab#>.
@prefix dc: <http://purl.org/dc/elements/1.1/>.
@prefix xsd: <http://www.w3.org/2001/XMLSchema#>.

"""

def enquote(s):
    t = s.replace('\\', '\\\\').replace('"', "\\\"")
    if '\n' in s:
        return '"""' + t + '"""'
    return '"' + t + '"'


def cleanLabel(lab):
    res = ''
    for ch in lab:
        if ch in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789':
            res += ch;
    return 'vcard:' + res;

def translatePredicate(mac):
    map = MacToVCard.get(mac, None );
    if map is None: return 'ab:' + mac;
    return map['predicate'];

def targetURIscheme(mac):
    map = MacToVCard.get(mac, None );
    if map is None: return None;
    return map.get('uriScheme', None);

def URIforPerson(person):
    itemUID = person.valueForKey_(AddressBook.kABUIDProperty);
    return unicode('Person/%s/index.ttl#this' % (uuid(person)))

def URIforPersonPhoto(person):
    itemUID = person.valueForKey_(AddressBook.kABUIDProperty);
    return unicode('Person/%s/image.png' % (uuid(person)))


def URIforGroup(group):
#    return 'Groups/%s.ttl#this' % uuid(group)
    name = unicode(group.valueForKey_('GroupName')).replace(' ', '_').replace('__', '_');
    return 'Group/%s/index.ttl#this' % name

def documentPart(uri):
    return uri.split('#')[0]

def localPart(uri):
    return uri.split('#')[1]

def uuid(item):
    itemUID = item.valueForKey_(AddressBook.kABUIDProperty);
    return itemUID.split(':')[0]

def fullName(person):
    sv = '';
    for p in [ 'Title', 'First', 'Middle', 'Last', 'Suffix']:
        name = person.valueForKey_(p);
        if name is not None:
            if len(sv) > 0: sv += ' ';
            sv += name;
    if sv == '':
        sv = person.valueForKey_('Organization'); # hack
        if (sv is None):
            sv = ''
    return sv

def renderComplexName(person):
    sv = '';
    for p in [ 'Title', 'First', 'Middle', 'Last', 'Suffix']:
        sv +=  renderPropertyAndValue(person, p);
    if sv == '': return '';
    return 'vcard:hasName [' + sv + '];\n';

def renderOneGroup(group):
    sv = ' a vcard:Group;\n';
    for p in defaultGroupProperties + defaultRecordCreationProperties:
        if p not in MacIgnore:
            sv +=  renderPropertyAndValue(group, p);
    sv += ' .\n';
    members = group.members();
    # print "# Members - ", members.count();
    lines = []
    for i in range(members.count()):
        item = members[i];
        assert 'Person' in `type(item)`   # This is an assumption we make at the moment @@
        itemUID = item.valueForKey_(AddressBook.kABUIDProperty);
        webid = getWebid(item)
        if webid:
            lines.append('<%s> vcard:fn %s; is vcard:hasMember of <#this>; = <../../%s> .' % (webid, enquote(fullName(item)), URIforPerson(item)));
        else:
            lines.append('<../../%s> vcard:fn %s; is vcard:hasMember of <#this>.' % (URIforPerson(item), enquote(fullName(item))));
    lines.sort();  # maintainstability for source code control
    return sv + '\n'.join(lines) + '\n';

def renderGroupName(group):
    sv = ' a vcard:Group;\n';
    for p in defaultGroupProperties:
        if p not in MacIgnore:
            sv +=  renderPropertyAndValue(group, p);
    sv += ' .\n';
    return sv

def cardClass(s):
    if s.valueForKey_('ABPersonFlags') == 1:
        return 'Organization'
    else:
        return 'Individual'


def renderOnePerson(s):
    # sys.stderr.write(uuid(s)+ '\n'); # @@@ debug
    if s.valueForKey_('ABPersonFlags') == 1:
        sv = ' a vcard:Organization; vcard:fn %s;\n' % enquote(fullName(s));
    else:
        sv = ' a vcard:Individual; vcard:fn %s;\n' % enquote(fullName(s));
    sv += renderComplexName(s);

    image = s.imageData();
    if image is not None:
        sv += ' vcard:hasPhoto <../../%s>;\n' % URIforPersonPhoto(s);


    for p in defaultPersonProperties + defaultRecordCreationProperties:
        if p not in MacIgnore + nameParts:
            sv +=  renderPropertyAndValue(s, p);
    if sv[-2:] == ';\n': return sv[:-2] + '.\n'
    return sv + '.\n';

def getWebid(s):
    p = AddressBook.kABURLsProperty
    v = s.valueForProperty_(p)
    if v is None: return None
    a = v
    if type(a) is AddressBook.ABMultiValueCoreDataWrapper:
        for i in range(a.count()):
            v = (a.valueAtIndex_(i))
            label = (a.labelAtIndex_(i));
            lab2 = cleanLabel(label)
            # print "# Label " + `label`
            if lab2.lower() == 'vcard:webid':  # Decision: be case-tolerant
                if type(v) is objc.pyobjc_unicode:
                    # print "# URL is unicode: " +  enquote(v)
                    return v
                else:
                    raise "  Bad URL type: " + `type(v)`
            else:
                pass
                # print "# Still looking ", lab2
        return None
    else:
        raise "Wrong type for webid URL: ", type(a)


def renderNameAndEmail(s):
    sv = ' a vcard:%s; vcard:fn %s;\n' % (cardClass(s), enquote(fullName(s)));
    for p in emailRelated:
        sv +=  renderPropertyAndValue(s, p);
    if sv[-2:] == ';\n': return sv[:-2] + '.\n'
    return sv + '.\n';

def writeOutImage(s, root):
    image = s.imageData();
    if image is not None:
        l = image.length();
        tempFileName = ',temp.tiff'
        # sys.stderr.write('URIforPersonPhoto(s) '+`URIforPersonPhoto(s)` + '\n')

        fn = fileNameFromURI(root, (URIforPersonPhoto(s)));
#        sys.stderr.write('fn ' + fn + '\n'); # @@@ debug
        #ni = NXImage.
#        imgRep = image.representations().objectAtIndex_(0)
#        data = imgRep.representationUsingType_properties_(NSPNGFileType, null);

        tempFile = open(tempFileName, 'w')
        a = array.array('B');
        for i in range(l):   # kludge @@ make space
            a.append(0)
        image.getBytes_length_(a, l)
        # sys.stderr.write('length of image:' + `len(a)` + '\n'); # @@@ debug
        a.tofile(tempFile);
        tempFile.close();

        tempFile = open(tempFileName, 'r')
        try:
            pi = Image.open(tempFile);
        except IOError:
            sys.stderr.write("*** Failed to open temp image file. Corrupt? So %s not written.\n" % fn)
        else:
            imageFile = open(fn, 'w');
            pi.save(imageFile);


def renderPropertyAndValue(s, p):
    v = s.valueForProperty_(p)
    if v is None: return ''
    return '%s %s;\n' %(translatePredicate(p), renderValue(p, v));

def renderValue(p, a, lab = None):

    if 'NSDictionary' in `type(a)`:
        sv = "["
        if lab:
            sv += ' a %s;\n' % cleanLabel(lab);
        keys = a.allKeys();
        for key in keys:
            x =  a.valueForKey_(key)
            if x is not None:
                sv += "    %s %s;\n" % (translatePredicate(key), enquote(x))
            # print "x.count()", x.count()
        sv += "]"
        return sv

    if (lab):  # All other types must built bnode
        return '[ a %s; vcard:value %s]' % (cleanLabel(lab), renderValue(p, a, None))

    if type(a) is objc.pyobjc_unicode:
        scheme = targetURIscheme(p);
        u = unicode(a);
        if scheme is not None:
            u = u.replace(" ", "") # beware of spaces in telephone numbers etc
            if scheme == 'tel:':
                u = u.replace('(', '-').replace(')', '-').replace('--', '-')
            if scheme == 'urn:uuid': # like B6DD6A45-DF5B-4859-81A0-EFE29E4613D2:ABPerson
                return '<%s%s>' % (scheme, unicode(a).split(':')[0])
            if scheme == 'mailto:':
                closer = u.rfind('>')   # clean up email like "J Blogs <blogs@acme.com>"
                if closer > 0:
                    opener = u.find('<')
                    if opener >= 0:
                        u = u[opener+1 : closer]
            return '<%s%s>' % (scheme, u)

        return  enquote(u);

    if type(a) is objc._pythonify.OC_PythonInt:
        return unicode(int(a));

    elif '__NSTaggedDate' in `type(a)` or '__NSDate' in `type(a)`:
        d = unicode(a);  # Looks like "2014-08-14 17:18:36 +0000"
        return '"%sT%s%s"^^xsd:dateTime' % (d[0:10], d[11:19], d[20:25]) # Missing tag info?

    elif 'NSDateComponents' in `type(a)`:
        u = unicode(a)
#        sys.stderr.write('@@@NSDateComponents - %s: unicode "%s"; python "%s"\n' % (type(a), u,`a`))
#        sys.stderr.write('  year "%s"\n' % (a.valueForKey_('year')))
#        sys.stderr.write('  month "%s"\n' % (a.valueForKey_('month')))
#        sys.stderr.write('  day "%s"\n' % (a.valueForKey_('day')))
        sv =  '"%04d-%02d-%02d"^^xsd:date' % (a.valueForKey_('year'), a.valueForKey_('month'), a.valueForKey_('day'))
        sys.stderr.write('  NSDateComponents Check Result: %s\n' % (sv))
        return  sv;


    elif type(a) is AddressBook.ABMultiValueCoreDataWrapper:
        sv = ''
        for i in range(a.count()):
            v = (a.valueAtIndex_(i))
            label = (a.labelAtIndex_(i));
            sv += renderValue(p, v, label);
            if i < a.count() - 1:
                sv += ',\n';
#            sv += '\n';
        return sv

    else:
        sys.stderr.write( 'Error unknown type - give up - %s.\n' % type(a) + `a`)
        sys.exit(1);

def fileNameFromURI(root, uri):
    return (root + documentPart(uri)).encode('utf-8');

def writeOutFile(group, uri, root, tail):
    # sys.stderr.write('uri '+`uri` + '\n')
    filename = fileNameFromURI(root, uri);
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise "Can't make directory " + os.path.dirname(filename)
    opf = open(filename, 'w')
    op = codecs.getwriter('utf-8')(opf)
    op.write(prefixes());
    op.write('<#%s>\n' % localPart(uri));
    op.write(tail);
    op.write('\n');  # just to be sure
    op.close();
    opf.close();

def writeOutSummaryFile(book, root, bookTitle):

    #////////////////////  List of all people just name and email
    uri = 'people.ttl';
    # sys.stderr.write('uri '+`uri` + '\n')
    filename = fileNameFromURI(root, uri);
    opf = open(filename, 'w')
    op = codecs.getwriter('utf-8')(opf)
    op.write(prefixes());

    abList = book.people()
    op.write("# people: %i\n" % len(abList));
    entries = []
    for person in abList:
        entries.append( '<%s> vcard:inAddressBook <index.ttl#this>;\n' % URIforPerson(person) + renderNameAndEmail(person));
    entries.sort(); # maintain stability of file under small changes
    op.write('\n'.join(entries) + '\n\n');  # just to be sure
    op.close();
    opf.close();

    #//////////////////////  List of groups
    uri = 'groups.ttl';
    sys.stderr.write('uri '+`uri` + '\n')
    filename = fileNameFromURI(root, uri);
    opf = open(filename, 'w')
    op = codecs.getwriter('utf-8')(opf)
    op.write(prefixes());
    op.write("# groups: %i\n" % len(book.groups()));
    entries = []
    for group in book.groups():
        entries.append( '<%s> is vcard:includesGroup of <index.ttl#this>;\n' % URIforGroup(group)  + renderGroupName(group) );
    entries.sort()
    op.write('\n'.join(entries) + '\n');  # just to be sure
    op.close();
    opf.close();

    #//////////////////////// Master book file
    uri = 'index.ttl';
    sys.stderr.write('uri '+`uri` + '\n')
    filename = fileNameFromURI(root, uri);
    opf = open(filename, 'w')
    op = codecs.getwriter('utf-8')(opf)
    op.write(prefixes());
    op.write('<#this> a vcard:AddressBook;\n'); # @@ squatting
    if bookTitle is not None:
        op.write('    vcard:fn """%s"""; \n' % bookTitle);
    op.write('    vcard:nameEmailIndex <people.ttl>; \n'); # @@ squatting
    op.write('    vcard:groupIndex <groups.ttl>. \n\n') # @@ squatting
    op.write('\n');  # just to be sure
    op.close();
    opf.close();





##############


def usage():
  """Displays the command line syntax information for the application."""
  print """Example usage:

    Extract my business card:

	python2.7 readAddressBook.py --me >  me.n3

    Make a tree of linked data pf the whole address book:

        pythpn2.7 readAddressBook.py --all ---distribute=

Arguments:
	-h, --help		Show this help.
        -m   --me               Dump just my own bsuiness card
        -g,  --groups           convert the groups
        -p,  --people           convert the cards
        -s,  --summary          Create linked summary files {book,groups,people}.ttl
	-a, --all		same as --people --groups --summary
	-d x, --distribute=x	Use x as the prefix for a file tree to be writtn.
                                Blank   (--distribute= )means this local directory

If you distribute the data, many files wil be made in a tree, linking to each other
Files (though not directories) will be created where necessary."

TODO
    optionally push the data into a LDP server using HTTP PUT
"""


def main(argv):
    """The main function for the application."""
    global globalUseFOAF
    gotNS = False
    doAllPeople = False
    doMe = False
    doGroups = False
    doSummary = False;
    doDistribute = False
    distributeRoot = None
    doImages = True
    bookTitle = None;
    try:
          opts, args = getopt.getopt(argv, "apmngsfe:hd:t:i:r",
            ["all", "people", "me", "noImages", "summary", "groups", "foaf", "exclude=", "help", "distribute=", "title=", "include=", "relationships"])
    except getopt.GetoptError:
          usage()
          sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-d", "--distribute"):
            doDistribute = True
            distributeRoot = arg
        elif opt in ("-t", "--title"):
            bookTitle = arg
        elif opt in ("-e", "--exclude"):
            global globalExcFile
            globalExcFile = arg
        elif opt in ("-n", "--noImages"):
            doImages = False
        elif opt in ("-p", "--people"):
            doAllPeople = True
        elif opt in ("-a", "--all"):
            doSummary = True
            doAllPeople = True
            doGroups = True
        elif opt in ("-g", "--groups"):
            doGroups = True
        elif opt in ("-s", "--summary"):
            doSummary = True
        elif opt in ("-m", "--me"):
            doMe = True
        elif opt in ("-d", "--foaf"):
            globalUseFOAF = True
        elif opt in ("-i", "--include"):
            global globalIncFile
            globalIncFile = arg
        elif opt in ("-r", "--relationships"):
            global globalRels
            globalRels = True

# WE need PIL to process images because we prefer to convert the MAC-native TIFF
# format for images to the web-happier PNG format.
# http://pillow.readthedocs.io/en/3.1.x/reference/Image.html

    if doImages:
        import PIL
        from PIL import Image

    # Get the shared address book.
    book = AddressBook.ABAddressBook.sharedAddressBook()

    if not book:
        print """ERROR can't access address book: """ + `book`
        print """Check in the System Preferences Security & Privacy pane,
        in the Privcay tab, in the Contacts section, that you have allowed Terminal App
        access to your contacts."""
        sys.exit(1)


    # Find out the 'me' entry.
    me = book.me()

    if not me:
        print """You haven't marked an entry as yourself."""
        sys.exit(1)



    # For doing the whole address book:
    # abList = book.people()
    # print book.groups()

    if doSummary:
        writeOutSummaryFile(book, distributeRoot, bookTitle);


    if doGroups:
        # print book.groups();
        for group in book.groups():
            if doDistribute:
                writeOutFile(group, URIforGroup(group),
                            distributeRoot, renderOneGroup(group));
            else:
                print prefixes();
                print '<%s>\n' % URIforGroup(group);
                print renderOneGroup(group);

    if doAllPeople:
        abList = book.people()
        print "# people: %i" % len(abList);
        if doDistribute:
            for person in abList:
                writeOutFile(person, URIforPerson(person),
                            distributeRoot, renderOnePerson(person));
                if doImages:
                    writeOutImage(person, distributeRoot);
        else:
            print prefixes();
            for person in abList:
                print '<%s> ' % URIforPerson(person) + renderOnePerson(person);

    elif doMe:
        print "# my webid: ", getWebid(me)
        if doDistribute:
            writeOutFile(me, URIforPerson(me),
                        distributeRoot, renderOnePerson(me));
            writeOutImage(me, distributeRoot);
        else:
            print prefixes();
            print '<#me> = <%s>;\n' % URIforPerson(me)  + renderOnePerson(me);


# Do the normal main/arguments processing.
if __name__ == "__main__":
    # Output UTF-8.
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
    main(sys.argv[1:])

#ends
