#!/usr/bin/python 
"""
Cryptographic Built-Ins for CWM/Llyn

Since TimBL has dared me to start this on more-than-one occasions...

cf. http://www.w3.org/2000/10/swap/cwm.py
"""

__author__ = 'Sean B. Palmer'
__cvsid__ = '$Id$'
__version__ = '$Revision$'

import sys, string, re, urllib, md5, sha, binascii
import thing, notation3

# ToDo: RSA. This should be an option, because you don't want to require 
# OpenSSL just to have CWM run properly...
# from Crypto.Hash import MD5
# from Crypto.PublicKey import RSA

from thing import *

LITERAL_URI_prefix = 'data:application/n3,'
DAML_LISTS = notation3.DAML_LISTS

RDF_type_URI = notation3.RDF_type_URI
DAML_equivalentTo_URI = notation3.DAML_equivalentTo_URI

CRYPTO_NS_URI = 'http://www.w3.org/2000/10/swap/crypto#'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# C R Y P T O G R A H P I C   B U I L T - I N s
#
# At the moment, we only have built-ins that can gague the hash values of 
# strings. It may be cool to have built ins that can give the hash value 
# of the content of a work, too, although you can do that with log:content.
#
#   Light Built-in classes

#  Hash Constructors - light built-ins

class BI_md5(LightBuiltIn, Function):
    def evaluateObject(self, store, context, subj, subj_py): 
        m = md5.new(subj_py).digest() 
        return store._fromPython(binascii.hexlify(m))

class BI_sha(LightBuiltIn, Function):
    def evaluateObject(self, store, context, subj, subj_py): 
        m = sha.new(subj_py).digest() 
        return store._fromPython(binascii.hexlify(m))

#  Register the string built-ins with the store

def register(store):
    str = store.internURI(CRYPTO_NS_URI[:-1])
    str.internFrag('md5', BI_md5)
    str.internFrag('sha', BI_sha)

if __name__=="__main__": 
   print string.strip(__doc__)