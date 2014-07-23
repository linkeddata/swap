#!/usr/bin/python
""" pfproxy.py -- a proof generating authentication proxy

based on
# Mediator proxy
# Itamar Shtull-Trauring <python@itamarst.org>
# http://itamarst.org
# Based off of Neil's Ad Munching HTTP Proxy Server
# Released under the GPL (http://www.gnu.org/copyleft/gpl.html)

"""

__version__ = "$Revision$ $Date$"

import time #hmm... not sure I want logging like that...
import urlparse, socket 
import SocketServer

from swap import llyn, diag
from swap.query import think, applyRules
from swap.why import explainFormula,  \
     BecauseOfExperience, BecauseOfCommandLine, becauseSubexpression, Premise


ServerBase = SocketServer.ThreadingTCPServer

class ProxyServer(ServerBase):
    def __init__(self, port):
        log('Starting proxy on port %d\n' % port, 1)
        ServerBase.__init__(self, ('', port), ProxyHandler)
        self._engine = ReinEngine()

    def process_request(self, request, client_address):
        return ServerBase.process_request(self, request, client_address)

Protocol = 'HTTP/1.0'

class ProxyHandler(SocketServer.StreamRequestHandler):
    def handle(self, retry = None):
        """handle one request from the browser"""
        if retry: host, port, request = retry
        else: host, port, request = self.read_request()
        srfile, swfile = self.connect(host, port)
        log('sending request to server %s "%s"\n' % (host, `request`), 2)
        self.send_request(swfile, request)
        try:
            self.handle_response(srfile)
        except IOError:
            pass # browser closed connection?
        log('finished request\n', 2)

    def read_request(self):
        """read request to find host and port and make new request"""
        request = self.rfile.readline()
        sys.stdout.write('%s - %s - %s' % (
                                self.client_address[0], 
                                time.ctime(time.time()),
                                request))
        try:
            method, url, protocol = request.split()
        except:
            self.error(400, "Can't parse request")
        if not url:
            self.error(400, "Empty URL")

        self._addr = url

        if method not in ['GET', 'HEAD', 'POST']: #@@ why not PUT?
            self.error(501, "Unknown request method (%s)" % method)
        # split url into site and path
        scheme, netloc, path, params, query, fragment = urlparse.urlparse(url)
        if scheme.lower() != 'http':
            self.error(501, "Unknown request scheme (%s)" % scheme)
        # find port number
        if ':' in netloc:
            host, port = netloc.split(':')
            port = int(port)
        else:
            host = netloc
            port = 80
        path = urlparse.urlunparse(('', '', path, params, query, fragment))
        # read headers
        headers = self.read_headers(self.rfile)
        if method == 'POST' and not headers.has_key('content-length'):
            self.error(400, "Missing Content-Length for POST method")
        length = int(headers.get('content-length', 0))
        # read content if any
        content = self.rfile.read(length)
        log('content = %s\n' % `content`, 2)
        # build new request
        try_del(headers, 'accept-encoding')
        try_del(headers, 'proxy-connection')

        self._req = (host, port, method, path, headers, content)
        request = '%s %s %s\r\n%s\r\n%s' % (method, path, Protocol,
                                            self.join_headers(headers),
                                            content)
        return host, port, request

    def connect(self, host, port):
        try:
            addr = socket.gethostbyname(host)
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.connect((addr, port))
        except socket.error, err:
            self.error(200, 'Error connecting to "%s" (%s)' % (host, err))
        return server.makefile('rb'), server.makefile('wb')

    def read_headers(self, input):
        headers = {}
        name = ''
        while 1:
            line = input.readline()
            if line == '\r\n' or line == '\n':
                break
            if line[0] in ' \t':
                # continued header
                headers[name] = headers[name] + '\r\n ' + line.strip()
            else:
                i = line.find(':')
                assert(i != -1)
                name = line[:i].lower()
                if headers.has_key(name):
                    # merge value
                    headers[name] = headers[name] + ', ' + line.strip()
                else:
                    headers[name] = line[i+1:].strip()
        return headers

    def join_headers(self, headers):
        data = []
        for name, value in headers.items():
            data.append('%s: %s\r\n' % (name, value))
        return ''.join(data)

    def send_request(self, server, request):
        try:
            server.write(request)
            server.flush()
        except socket.error, err:
            self.error(500, 'Error sending data to "%s" (%s)' % ('@@host', err))

    def handle_response(self, server):
        log('reading server response\n', 2)
        response = server.readline()
        log('response = %s\n' % response, 2)
        version, status, comment = response.strip().split(None, 2)


        log('reading response headers\n', 2)
        shead = self.read_headers(server)

        # hmm... policy header... squatting? registered?
        if status == '401' and shead.has_key('policy'):
            host, port, method, path, headers, content = self._req
            if not headers.has_key('x-cred'):
                self.discard_body(server)

                policy = shead['policy']
                #@@proof = self.server._engine.findProof(self._addr,
                #policy,
                #'judy-passwd') #@@
                proof = '@@big-hairy-proof'

                headers['x-cred'] = proof

                request = '%s %s %s\r\n%s\r\n%s' % \
                          (method, path, Protocol,
                           self.join_headers(headers),
                           content)
                self.handle(retry = (host, port, request))
                return

        self.wfile.write('%s %s %s\r\n' % (Protocol, status, comment))

        typ = shead.get('content-type', 'unknown')
        log('writing headers to client: %s\n' % shead, 3)
        self.wfile.write(self.join_headers(shead))
        self.wfile.write('\r\n')
        log('encoding %s\n' % typ, 2)
        if 0:
            pass #was: munch
        else:
            # read by blocks
            log('transfering raw data\n', 2)
            while 1:
                data = server.read(4096)
                log('data = %s\n' % `data`, 5)
                if not data:
                    break
                self.wfile.write(data)
        self.wfile.flush()

    def discard_body(self, server):
        while 1:
            data = server.read(4096)
            log('data = %s\n' % `data`, 5)
            if not data:
                break

    def finish(self):
        import select
        try:
            self.connection.setblocking(0)
            r, w, e = select.select([self.rfile], [self.wfile], [], 0)
            if r and w:
                self.wfile.write(self.rfile.read())
            SocketServer.StreamRequestHandler.finish(self)
        except IOError:
            pass

    def error(self, code, body):
        import BaseHTTPServer
        response = BaseHTTPServer.BaseHTTPRequestHandler.responses[code][0]
        self.wfile.write("%s %s %s\r\n" % (Protocol, code, response))
        self.wfile.write("Server: PAW Proxy\r\n")
        self.wfile.write("Content-type: text/html\r\n")
        self.wfile.write("\r\n")
        self.wfile.write('<html><head>\n<title>%d %s</title>\n</head>\n'
                '<body>\n%s\n</body>\n</html>' % (code, response, body))
        self.wfile.flush()
        self.wfile.close()
        self.rfile.close()
        raise SystemExit

# I think there's a simpler idiom using .pop()
def try_del(dict, key):
    try:
        del dict[key]
    except KeyError:
        pass

RDF = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
REIN = 'http://dig.csail.mit.edu/2005/09/rein/network#'
ACCESS = 'http://dig.csail.mit.edu/2005/09/rein/examples/http-access#'
SESSION = 'http://redfoot.net/2005/session#'

n3Flags = "B"  # Make proofs easier to check

class ReinEngine(object):
    def __init__(self):
        assert(diag.tracking)
        s = llyn.RDFStore()
        log('loading rein/engine.n3\n')
        ar = 'http://groups.csail.mit.edu/dig/2005/09/rein/bengine.n3'
        rules = s.load(ar,
	    why = BecauseOfCommandLine("REIN bengine.n3@@"),
	    flags=n3Flags)
        af = 'http://groups.csail.mit.edu/dig/2005/09/rein/bfilter.n3'
        filter = s.load(af,
	    why = BecauseOfCommandLine("REIN bfilter.n3@@"),
	    flags=n3Flags)
        self._rules = rules
        self._filter = filter
        self._store = s

    def findProof(self, addr, policy, secret):
        """
        we're building this... hmm... just use n3 parser?
        
        { [] a rein:Request;
        rein:requester [ session:secret "judy-passwd"; session:id rein:test ];
        rein:access http:can-get;
        rein:resource <http://demo.policyawareweb.org/images/group.jpg>;
        rdfs:comment "Judy makes a request for
        http://demo.policyawareweb.org/images/group.jpg which was taken during
        AnnualMeeting which Judy attended. This is a valid request.".
        } a rein:RequestFormula.

        hmm... think with rules?
        """

        rsn = Premise("got it from an HTTP request@@")
        f = self._store.newFormula()
        g = self._store.newFormula()
        self._store.copyFormula(self._rules, g, why=rsn)

        req = f.newBlankNode()
        sym = f.newSymbol
        sub = becauseSubexpression
        f.add(req, sym(RDF + 'type'), sym(REIN + 'Request'), why=sub)
        who = f.newBlankNode() # don't see why newExistential doesn't work
        f.add(who, sym(SESSION + 'secret'), secret, why=sub)
        f.add(who, sym(SESSION + 'id'), sym(REIN + 'test'), why=sub) #@@huh?
        f.add(req, sym(REIN + 'requester'), who, why=sub)        
        f.add(req, sym(REIN + 'access'), sym(ACCESS + 'can-get'), why=sub)
        f.add(req, sym(REIN + 'resource'), sym(addr), why=sub)
        f = f.close()

        g.add(sym(addr), sym(REIN + 'policy'), sym(policy), why=rsn)

        g.add(f, sym(RDF + 'type'), sym(REIN + 'RequestFormula'), why=rsn)
        log('rules with request: %s. ready to think...\n' % g, 3)
        think(g)
        g = g.close()
        log('think done: %s\n' % `g`, 3)

        log('filtering...\n', 3)
        h = self._store.newFormula()
        applyRules(g, self._filter, h)
        h = h.close()
        log('filter done: %s\n' % h, 3)

        log('Expressing proof as a graph...\n', 3)
	diag.chatty_flag = 70
        pf = explainFormula(h)
	diag.chatty_flag = 10
        log('Done, %i top-level statements.\n' % len(pf), 3)
        return pf


DEBUG_LEVEL = 4
def log(s, level=1):
    if level <= DEBUG_LEVEL:
        sys.stderr.write(s)

PORT = 8000
def _test():
    ProxyServer(PORT).serve_forever()

def _testRein():
    diag.tracking = 1
    diag.setTracking(1)
    e = ReinEngine()
    log("made an engine\n")
    pf = e.findProof('http://demo.policyawareweb.org/images/award.jpg',
                     'http://groups.csail.mit.edu/dig/2005/09/rein/examples/troop42-policy.n3',
                     'judy-passwd')
    log("Found poof. Serializing...")
    print pf.n3String()
    log("Done.\n")
    
if __name__ == '__main__':
    import sys
    if '--test' in sys.argv:
        _test()
    elif '--test-rein' in sys.argv:
        _testRein()
    else:
        raise RuntimeError, "no main yet; use --test"

