#!/usr/bin/python2.7
# MIT License.  (c)timbl, Richard Newman
#
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


import AddressBook, objc
import sha
import sys, codecs
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
};

MacIgnore = [ AddressBook.kABBirthdayComponentsProperty ]

nameParts = [
    AddressBook.kABTitleProperty,
    AddressBook.kABFirstNameProperty,
    AddressBook.kABLastNameProperty,
    AddressBook.kABMiddleNameProperty,
    AddressBook.kABSuffixProperty ];

def prefixes():
  """Spit out the RDF etc. at the start of a FOAF file.
removed: 
@prefix contact: <http://www.w3.org/2000/10/swap/pim/contact#>.
@prefix airport: <http://www.daml.org/2001/10/html/airport-ont#>. 
@prefix pos: <http://www.w3.org/2003/01/geo/wgs84_pos#>.
# @prefix trust: <http://trust.mindswap.org/on/trust.owl#>.
@prefix owl: <http://www.w3.org/2002/07/owl#>.
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>.
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
@prefix foaf: <http://xmlns.com/foaf/0.1/>.
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

def foafSuffix():
  """Tail end of a FOAF file."""
  return "# ends."

def foafEmptyTag(tagName, rel, value):
  """Returns the appropriate empty tag."""
  return '<foaf:%s %s="%s" />'%(tagName, rel, value)

def foafPO(tagName, value):
  """Returns the appropriate namespace-prefixed tag combo for the given values."""
  return '  foaf:%s %s; '%(tagName, enquote(value))

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
    return unicode('Person/%s.ttl#this' % (uuid(person)[-12:]))
#    return unicode('Person/%s.ttl#this' % (uuid(person)))
#    return 'People/%s/%s/%s' % (itemUID[0],itemUID[1],itemUID[2:]), 
    
def URIforGroup(group):
#    return 'Groups/%s.ttl#this' % uuid(group)
    name = unicode(group.valueForKey_('GroupName')).replace(' ', '_');
    return 'Group/%s.ttl#this' % name

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
    members = group.members();
    print "# Members - ", members.count();
    for i in range(members.count()):
        item = members[i];
        assert 'Person' in `type(item)`   # This is an assumption we make at the moment @@
        itemUID = item.valueForKey_(AddressBook.kABUIDProperty); 
        sv += 'vcard:hasMember <%s>; # %s\n' % (URIforPerson(item), fullName(item));
    if sv[-2:] == ';\n': return sv[:-2] + '.\n'
    return sv + '.\n';

def renderOnePerson(s):
    # sys.stderr.write(uuid(s)+ '\n'); # @@@ debug 
    
    sv = ' a vcard:Individual; vcard:fn %s;\n' % enquote(fullName(s));
    sv += renderComplexName(s);
    for p in defaultPersonProperties + defaultRecordCreationProperties:
        if p not in MacIgnore + nameParts:
            sv +=  renderPropertyAndValue(s, p);
    if sv[-2:] == ';\n': return sv[:-2] + '.\n'
    return sv + '.\n';


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
        return 'Error unknown type - give up - %s: ' % type(a) + `a`

def writeOutFile(group, uri, root, tail):
    filename = (root + documentPart(uri)).encode('utf-8');
    opf = open(filename, 'w')
    op = codecs.getwriter('utf-8')(opf)
    op.write(prefixes());
    op.write('<#%s>\n' % localPart(uri));
    op.write(tail);
    op.write('\n');  # just to be sure
    op.close();
    opf.close();


##############


def usage():
  """Displays the usage information for the application."""
  print """Usage:
	python2.7 readAddressBook.py [args] >  ab.n3

Arguments:
	-h, --help		Show this help.
        -m   --me               Dump just my own bsuiness card 
	-a, --all		Use all people in the address book
        -g,  --groups           Dump the groups
	-d x, --distribute=x	Use x as the prefix for a file tree to be writtn.

If you distribute the data, many files wil be made in a tree, linking to each other
Files (though not directories) will be created where necessary."""


def main(argv):
    """The main function for the application."""
    global globalUseFOAF
    gotNS = False
    doAllPeople = False
    doMe = False
    doGroups = False
    doDistribute = False
    distributeRoot = None               
    try:
          opts, args = getopt.getopt(argv, "amgfe:hd:i:r", ["all", "me", "groups", "foaf", "exclude=", "help", "distribute=", "include=", "relationships"])
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
        elif opt in ("-e", "--exclude"):
            global globalExcFile
            globalExcFile = arg
        elif opt in ("-a", "--all"):
            doAllPeople = True
        elif opt in ("-g", "--groups"):
            doGroups = True
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


    # Get the shared address book.
    book = AddressBook.ABAddressBook.sharedAddressBook()

    # Find out the 'me' entry.
    me = book.me()

    if not me:
        print """You haven't marked an entry as yourself."""
        sys.exit(1)
        
    
    
    # For doing the whole address book:
    # abList = book.people()
    # print book.groups()

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
        else:
            print prefixes();
            for person in abList:
                print '<%s> ' % URIforPerson(person) + renderOnePerson(person);

    elif doMe:
        if doDistribute:
            writeOutFile(me, URIforPerson(me),
                        distributeRoot, renderOnePerson(me));
        else:
            print prefixes();
            print '<#me> = <%s>;\n' % URIforPerson(me)  + renderOnePerson(me);
        
    elif False:
    # For doing only the FOAF group:

        abResults = book.recordsMatchingSearchElement_(AddressBook.ABGroup.searchElementForProperty_label_key_value_comparison_('GroupName', 0, 0, 'FOAF', AddressBook.kABPrefixMatchCaseInsensitive))

        if abResults.count() == 0:
            print """Error: do you have a 'FOAF' group defined?"""
            sys.exit(2);

        # Make a list of the members to process.
        abList = abResults[0].members()

        # Generate the FOAF document.
      
        # Make sure I'm in the 'good' list.
        globalIDList[me.valueForProperty_('UID')] = me.valueForProperty_('First') + me.valueForProperty_('Last')
        print "%s" % generateFOAFDocumentForPeople(me, abList)

# Do the normal main/arguments processing.
if __name__ == "__main__":
    # Output UTF-8.
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)
    main(sys.argv[1:])

#ends

