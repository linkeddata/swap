""" rdfx2kif.py -- connect RDF/xml parser with KIF generator

Share and Enjoy. Open Source license:
Copyright (c) 2001 W3C (MIT, INRIA, Keio)
http://www.w3.org/Consortium/Legal/copyright-software-19980720
$Id$
see log at end

References

  @@RDF 1.0 spec
  @@SAX
  
  Knowledge Interchange Format
  draft proposed American National Standard (dpANS)
  NCITS.T2/98-004
  http://logic.stanford.edu/kif/dpans.html
  Thu, 25 Jun 1998 22:31:37 GMT
"""

import os, sys

from . import KIFSink
from . import sax2rdf
from . import xml2rdf # if you want the older RDF parser that doesn't require python2

def convert(text, addr, outFp):
    gen = KIFSink.Sink(outFp)
    p = sax2rdf.RDFXMLParser(gen, addr)
    gen.startDoc()
    p.feed(text)
    gen.endDoc()

    
if __name__ == '__main__':
    convert(sys.stdin.read(),
            'file:%s/STDIN' % (os.getcwd(),),
            sys.stdout.write)
    

#$Log$
#Revision 1.3  2001-11-13 23:24:49  connolly
#back to modern RDF parser...
#
#Revision 1.2  2001/09/19 18:47:57  connolly
#factored RDFSink.py out of notation3.py
#
#introduced SYMBOL to replace notation3.RESOURCE
#introduced forSomeSym, forAllSym to replace N3_forSome_URI, N3_forAll_URI
#
#Revision 1.1  2001/09/11 16:30:57  connolly
#for sharing with dmiles
#
