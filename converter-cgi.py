#! /usr/bin/python /devel/WWW/2000/10/swap/cwm.py
"""

$Id$

convert-cgi

An CGI server applet which provides a form for playing with N3 syntax,
allowing conversion from N3 to conventional RDF.

This is an application which knows a certian amount of stuff and can manipulate it.
It uses llyn, a (forward chaining) query engine, not an (backward chaining) inference engine:
that is, it will apply all rules it can but won't figure out which ones to apply to prove something. 


http://www.w3.org/DesignIssues/Notation3
Date: 2000/07/17 21:46:13  

Agenda:
=======


"""

import string
import urllib.parse
# import re
# import StringIO

#import urllib # for log:content
import md5, binascii  # for building md5 URIs
urllib.parse.uses_fragment.append("md5") #@@kludge/patch
urllib.parse.uses_relative.append("md5") #@@kludge/patch

from . import notation3    # N3 parsers and generators, and RDF generator

              
            
        
############################################################## Web service
# Author: DanC
#
import random
import time
import cgi
import sys
import io

def serveRequest(env):
    import random #for message identifiers. Hmm... should seed from request

    #sys.stderr = open("/tmp/connolly-notation3-log", "w")

    form = cgi.FieldStorage()

    if 'data' in form:
	try:
	    convert(form, env)
	except BadSyntax as e:
	    print("Status: 500 syntax error in input data")
	    print("Content-type: text/plain")
	    print()
	    print(e)
	    

	except:
	    import traceback

	    print("Status: 500 error in python script. traceback follows")
	    print("Content-type: text/plain")
	    print()
	    traceback.print_exc(sys.stdout)
	    
    else:
	showForm()

def convert(form, env):
    """ raises KeyError if the form data is missing required fields."""

    serviceDomain = 'w3.org' #@@ should compute this from env['SCRIPT_NAME']
         # or whatever; cf. CGI spec
    thisMessage = 'mid:t%s-r%f@%s' % (time.time(), random.random(), serviceDomain)

    data = form['data'].value

    if 'genspace' in form:
	genspace = form['genspace'].value
    else: genspace = thisMessage + '#_'

    if 'baseURI' in form:	baseURI = form['baseURI'].value
    elif 'HTTP_REFERER' in env: baseURI = env['HTTP_REFERER']
    else: baseURI = None

    # output is buffered so that we only send
    # 200 OK if all went well
    buf = io.StringIO()

    xlate = notation3.ToRDFParser(buf, baseURI, thisMessage, genspace)
    xlate.startDoc()
    xlate.feed(data)
    xlate.endDoc()

    print("Content-Type: text/xml")
    #hmm... other headers? last-modified?
    # handle if-modified-since? i.e. handle input by reference?
    print() # end of HTTP response headers
    print(buf.getvalue())

def showForm():
    print("""Content-Type: text/html

<html>
<title>Notation3 to RDF Service</title>
<body>

<form method="GET">
<textarea name="data" rows="4" cols="40">
bind dc: &lt;http://purl.org/dc/elements/1.1/&gt;
</textarea>
<input type="submit"/>
</form>

<div>
<h2>References</h2>
<ul>
<li><a href="http://www.w3.org/DesignIssues/Notation3">Notation 3</a></li>
<li><a href="http://www.python.org/doc/">python documentation</a></li>
<li><a href="http://www.w3.org/2000/01/sw/">Semantic Web Development</a></li>
</ul>
</div>

<address>
<a href="http://www.w3.org/People/Connolly/">Dan Connolly</a>
</address>

</body>
</html>
""")
        
############################################################ Main program
    
if __name__ == '__main__':
    import os
#    import urlparse
#    if os.environ.has_key('SCRIPT_NAME'):
    serveRequest(os.environ)
#    else:
#        doCommand()

