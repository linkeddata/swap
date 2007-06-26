#!/usr/bin/python
"""toLdif.py -- convert RDF to LDIF syntax

USAGE:
  python toLdif.py foo.rdf > foo.ldif
  python toLdif.py foo.n3 > foo.ldif
  python toLdif.py http://example/foo.rdf > foo.ldif

see also:
  RDF Calendar Workspace
  http://www.w3.org/2002/12/cal/
  http://www.w3.org/2002/12/cal/vcard-notes.html


Copyright (C) 2000-2004 World Wide Web Consortium, (Massachusetts
Institute of Technology, European Research Consortium for Informatics
and Mathematics, Keio University). All Rights Reserved. This work is
distributed under the W3C(R) Software License [1] in the hope that it
will be useful, but WITHOUT ANY WARRANTY; without even the implied
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

"""


__version__ = '$Id$'


from string import maketrans, translate
import sha, binascii, base64

from swap.myStore import Namespace, load, setStore # http://www.w3.org/2000/10/swap/
from swap import uripath
from swap.term import Symbol


#hmm... generate from schema?
# from fromIcal import iCalendarDefs # http://www.w3.org/2002/12/cal/ 


CRLF = chr(13) + chr(10)
WRAP = 76   # Chars per line

RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
ICAL = Namespace('http://www.w3.org/2002/12/cal/icaltzd#')
XMLSchema = Namespace('http://www.w3.org/2001/XMLSchema#')
LDIF_NS = 'http://www.w3.org/2007/ont/ldif#'
LDIF = Namespace(LDIF_NS)

######################

fields = [  # Examples in comments from zac.ldif
    'givenName', #: Zackery
    'sn',   #: Zephyr
    'cn',       #: Zackery Zephyr
    'mozillaNickname', #: testnick
    'mail', #: zac@example.com
    'mozillaSecondEmail',   #: zackery@example.org 
    'nsAIMid',  #: zaco
    'mozillaUseHtmlMail', #: false
#    'modifytimestamp', #: 0Z   -- not a property of the person
    'telephoneNumber', #: +1 202 250 2525
    'homePhone', #: +1 202 250 2526
    'fax',  #: +1 202 250 2527
    'pager',  #: +1 202 555 2525
    'mobile',  #: +1 202 555 2526
    'homeStreet',  #: 1 Zephyr Drive
    'mozillaHomeStreet2',  #: Apt 26
    'mozillaHomeLocalityName',  #: Zoaloc
    'mozillaHomeState',  #: MA
    'mozillaHomePostalCode',  #: 02999
    'mozillaHomeCountryName',  #: USA
    'street',  #: 1 Enterprise Way
    'mozillaWorkStreet2',  #: Suite 260
    'l',  #: Zoaloc Heights
    'st',  #: MA
    'postalCode',  #: 02998
    'c',  #: USA
    'title',  #: Chief Test dataset
    'department',  #: Testing
    'company',  #: Zacme Widgets
    'mozillaWorkUrl',  #: http://example.com/test/zac
    'mozillaHomeUrl',  #: http://zac.example.net/zac
    'mozillaCustom1',  #: custom1 value
    'mozillaCustom2',  #: custom2 value
    'mozillaCustom3',  #: custom3 value
    'mozillaCustom4',  #: custom4 value
    'description']  #: This is a n imaginary person ..
    
def wr(buf):
    return sys.stdout.write(buf)

def backslashEncode(val):
    text = val.encode('ascii') # Just check
    # @@TODO: wrap at 75 cols
    for c in ('\\'):  # cal: ('\\', ';', ',')
        text = text.replace(c, "\\"+c)
    text = text.replace('\n', "\\n")
    result = ""
    while text:
        result = result +  '\n ' + text[:WRAP]
        text = text[WRAP:]
    return result[2:]  # chop zeroth fold


def encodeLine(key, val):
    try:
        text = val.encode('ascii')
    except UnicodeEncodeError:
        text = base64.encodestring(val.encode('utf-8')) # Comes wrapped by \n
        while text[-1:] == '\n': text = text[:-1]
        text = text.replace('\n', '\n ')  # Proper folding
        return "%s:: %s\n" %(key, text)
    else:
        return "%s: %s\n" %(key, backslashEncode(text))


def extractLDIF(kb):
    progress('Found %i statements' % len(kb))
    cn = kb.newSymbol(LDIF_NS+'cn')
    sts = kb.statementsMatching( cn, None, None) # p s o
    progress('Found %i common names' % len(sts))
    wr("version: 1\n")  # Mandatory in sepc, not given by Tbird.
    emails = 0
    for st in sts:
        person = st.subject()
        name = st.object()
        email = kb.any(person, LDIF.mail)  # s p o
        if not email:
            progress ("No email for "+ name.value().encode('utf-8'))
            continue
        assert email.uriref().startswith("mailto:")
        emails += 1
        emailad = email.uriref()[7:]
        wr(encodeLine("dn", "cn=%s,mail=%s" %(name, emailad)))
#       wr( "dn: cn=%s,mail=%s\n" %(name, emailad))
        progress("  %s <%s>" % (name.value().encode('utf-8'), emailad)) 
        wr( """objectclass: top
objectclass: person
objectclass: organizationalPerson
objectclass: inetOrgPerson
objectclass: mozillaAbPersonAlpha
""") #
        for key in fields:
            pred = kb.newSymbol(LDIF_NS+key)
            obj = kb.any(person, pred)
            if obj:
                if isinstance(obj, Symbol):
                    uri = obj.uriref()
                    colon = uri.find(':')
                    assert colon > 0
                    if uri[:colon] in ['tel', 'mailto']:
                        val = uri[colon+1:]
                    else:
                        progress("eh? URI not tel or mailto", uri)
                else:
                    val = obj.value()
                wr(encodeLine(key, val))  # base64 if utf8
        wr('\n') # Blank line netween records
        progress('Total of %i emails' % emails)
            
#

######################

import sys, os

def usage():
    print __doc__


def main(args):
    if not args[1:]:
        usage()
        sys.exit(1)


    addr = uripath.join("file:" + os.getcwd() + "/", args[1])
    
    progress("loading...", addr)

    kb = load(addr)

    progress("exporting...")
    extractLDIF(kb)


def _test():
    import doctest
    doctest.testmod()

def progress(*args):
    for i in args:
        sys.stderr.write(str(i))
    sys.stderr.write("\n")


def debug(*args):
    for i in args:
        sys.stderr.write(str(i))
    sys.stderr.write("\n")


if __name__ == '__main__':
    if '--test' in sys.argv: _test()
    else: main(sys.argv)


