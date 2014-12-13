#!/usr/bin/python
"""
Mail callback service -- public-key notarized email callback

$Id$

see change log at end

"""

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import cgi
import smtplib
import Cookie # http://www.python.org/doc/current/lib/module-Cookie.html
import random


TopPage = """
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Mail Callback Playgound</title></head>
<body>
<h1>@@</h1>

<p>Try <a href="/sekret">the sekret page</a>.</p>

</body>
</html>

"""


CRED_KEY="crk"
PORT=8000

class MailCallbackIdea(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.wfile.write(TopPage)
        elif self.path.startswith("/cbAnswer?"):
            self.cbAnswer()
        elif self.path == "/sekret":
            nonces = self.server.nonces
            #print "request headers:", self.headers.headers
            for h in self.headers.headers:
                if h.startswith("Cookie:"):
                    #print "cookie header:", h
                    s = h.split(None, 1)[1].strip()
                    c = Cookie.SimpleCookie(s)
                    #print "nonces:", nonces
                    if c.has_key(CRED_KEY):
                        #print "cred:", c[CRED_KEY].value
                        if c[CRED_KEY].value in nonces:
                            self.textReply("ok! you're in!")
                            return None

            self.authChallenge()
            return None
        else:
            self.send_error(404, "unrecognized path: %s" % (self.path,))
            return None


    def do_POST(self):
        if self.path == '/callback': self.doCallBack()
        else:
            self.send_error(404, "unrecognized path: %s" % (self.path,))
            return None


    def doCallBack(self):
        qty = int(self.headers.getheader('Content-Length'))
        body = self.rfile.read(qty)
        print "@@body:", body
        for k, addr in cgi.parse_qsl(body):
            if k == "mboxAddr": #@@ hard coded
                n = self.mkNonce(addr)
                sendPointer(addr, "email address verification",
                            "http://127.0.0.1:8000/cbAnswer?k=%s" % (n,) )
                self.textReply("Sent msg to <%s>. Check your mail." % (addr,))
                return None
        self.send_error(400, "missing field values")


    def cbAnswer(self):
        query = self.path.split('?', 1)[1]
        nonces = self.server.nonces
        for k, v in cgi.parse_qsl(query):
            if k == 'k':
                if v in nonces:
                    mbox = self.server.challenges[v]
                    self.textReply("key matches for mailbox: %s" % (mbox,))
                    return None
                    #@@now on to secret?
        self.textReply("key %s does not match any fresh nonces." % (k,))

        
    def textReply(self, txt):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(txt)
        

    def mkNonce(self, val):
        nonce = str(random.randint(1, 9999))

        #@@ access to .server isn't documented
        self.server.nonces.append(nonce)
        self.server.challenges[nonce] = val

        #print "new nonce:", self.server.nonces
        return nonce


    def authChallenge(self):
        code = 403
        self.send_response(code)
        self.send_header("Content-Type", "text/html")
        self.send_header('Connection', 'close')
        self.end_headers()

        if self.command != 'HEAD' and code >= 200 and code not in (204, 304):
            self.wfile.write(open("mailCbHelper.html").read())

    def dead_code(self):
        #@@set cookie
        nonce = self.mkNonce('abc')
        fv = fmtCookieField(CRED_KEY, nonce)
        #print "sending cookie header field:", fv
        self.send_header("Set-Cookie", fv)
        

def sendPointer(mbox, subj, url):
    host, port, me = '127.0.0.1', 5000, 'connolly+mailcbtest@w3.org'
    server = smtplib.SMTP(host, port)
    msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\nTo continue, see <%s>" % (me, mbox, subj, url)
    server.sendmail(me, mbox, msg)
    server.quit()

    
def fmtCookieField(n, v):
    """
    >>> fmtCookieField("cred", "42")
    ' cred=42; Domain=127.0.0.1; Path=/;'
    """
    
    c = Cookie.SimpleCookie()
    c[n] = v
    c[n]["path"] = "/"
    c[n]["domain"] = "127.0.0.1"
    return c.output(None, "")


def run(server_class=HTTPServer,
        handler_class=MailCallbackIdea):
    server_address = ('', PORT)
    httpd = server_class(server_address, handler_class)
    random.seed()
    httpd.nonces = []
    httpd.challenges = {}
    httpd.serve_forever()


def _test():
    import doctest, mailCbSvc
    doctest.testmod(mailCbSvc)

if __name__ == '__main__':
    import sys
    if sys.argv[1:] and sys.argv[1] == '--test': _test()
    else: run()


# $Log$
# Revision 1.1  2004-01-26 06:12:00  connolly
# email callback working; cookie stuff was working but is now dead code
#
