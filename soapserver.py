#!/usr/local/bin/python
"""

Offer plwm services via SOAP.

"""

from SOAPpy import SOAP
import sys
import maitred
import plwm

kbname = sys.argv[1]

# load kbname

... run

# save kbname


class MyRequestHandler(SOAP.SOAPRequestHandler):

    def do_GET(self):
        #print dir(self)
        print self.headers
        # look at "Accept: " lines and if they want html, then
        # redirect them to semwalker?   Nah.....
        self.send_response(200)
        self.send_header("Content-type", "application/rdf+xml")
        self.end_headers()
        self.wfile.write("<!-- Run semwalker to look at this! -->")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.send_header("X-Random-Message", "I love you!")
        self.end_headers()



server = SOAP.SOAPServer(("localhost", 0), MyRequestHandler)
port = server.socket.getsockname()[1]
print '# waiting at port', port
server.registerFunction(query)
server.registerFunction(queryAbout)

maitred.readyAtPort(port)
server.serve_forever()
