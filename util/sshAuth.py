"""
access to ssh-agent from python

$Id$
see log at end

REFERENCES
  ssh-agent man page
  http://www.openbsd.org/cgi-bin/man.cgi?query=ssh-agent&sektion=1

  ssh-agent source code
  http://www.openbsd.org/cgi-bin/cvsweb/src/usr.bin/ssh/ssh-agent.c?rev=1.111&content-type=text/x-cvsweb-markup

  browsing doesn't work well with (this style) of C code;
  grabbed source ala apt-get source ssh
  then built an etags TAGS table and explored with emacs M-. and M-*

  esp authfd.c
  
"""

SSH_AUTH_SOCK = "SSH_AUTH_SOCK"

# from authfd.h
SSH_AGENT_FAILURE = 5
SSH2_AGENTC_SIGN_REQUEST = 13
SSH2_AGENT_SIGN_RESPONSE = 14
SSH2_AGENT_FAILURE = 30
SSH_COM_AGENT2_FAILURE = 102


# http://www.python.org/doc/current/lib/modindex.html
import os, socket, struct

def test(data):
    keyd = open("/home/connolly/.ssh/authorized_keys").readline()
    progress("key data:", keyd)
    key = key_read(keyd)
    ap = os.getenv(SSH_AUTH_SOCK)
    progress("path to ssh agent's unix socket:", ap)
    as = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    as.connect(ap)
    progress("connected")
    progress("requesting signature of:", data)
    sig = ssh_agent_sign(as, key, data)
    progress("signature:", sig)

class RSAKey:
    def __init__(self, e, n):
	self._e = e
	self._n = n
	
    def to_blob(self):
	return packString("ssh-rsa") + \
	       packBignum(self._e) + \
	       packBignum(self._n)


class AgentFailed(IOError):
    pass
class ProtocolError(IOError):
    pass


def ssh_agent_sign(auth, key, data):
    """ conversion of ssh_agent_sign from authfd.c

    return code is used to pass back sig rather than exception status
    """
    
    kpack = packString(key.to_blob())
    dpack = packString(data)
    fpack = struct.pack(">I", 0) # flags
    buf = chr(SSH2_AGENTC_SIGN_REQUEST) + kpack + dpack + fpack

    msg = request_reply(auth, buf)
    ty = ord(msg[0])
    progress("reply type", ty)
    if ty == SSH_AGENT_FAILURE or ty == SSH_COM_AGENT2_FAILURE or \
       ty == SSH2_AGENT_FAILURE:
	raise AgentFailed, ty
    if ty != SSH2_AGENT_SIGN_RESPONSE:
	raise ProtocolError, ("expected", SSH2_AGENT_SIGN_RESPONSE, "got", ty)
    (len,) = struct.unpack(">I", msg[:4])
    return msg[4:4+len]


def request_reply(auth, buf):
    progress("about to write request length", len(buf))
    atomicio_w(auth, struct.pack(">I" , len(buf)))
    progress("about to write request data")
    atomicio_w(auth, buf)

    ln = 4
    rx = ''
    while ln > 0:
	progress("about to read reply length")
	r = auth.recv(ln)
	rx += r
	ln -= len(r)
    (ln,) = struct.unpack(">I", rx)
    if ln > 256 * 1024: raise IOError, ("response size too big", ln)
    rx = ''
    while ln > 0:
	progress("reading reply data; bytes to go:", ln)
	r = auth.recv(ln)
	rx += r
	ln -= len(r)
    return rx


def atomicio_w(sock, buf):
    dx = 0
    while 1:
	sent = sock.send(buf[dx:])
	if dx + sent >= len(buf): break
	dx += sent

import binascii

def key_read(cpp):
    """from key.c
    """
    tn, uu, other = cpp.split()
    progress("key_read:", tn, uu, other)
    if tn != "ssh-rsa": raise RuntimeError, "not implemented"

    blob = binascii.a2b_base64(uu)
    keytn, blob = getString(blob)
    if keytn != "ssh-rsa": raise RuntimeError, "not implemented"
    (e, blob) = getBignum(blob)
    (n, blob) = getBignum(blob)
    progress("read key: %x %x" % (e, n))
    return RSAKey(e, n)

def getString(buf):
    (ln, ) = struct.unpack(">I", buf[:4])
    s = buf[4:4+ln]
    return s, buf[4+ln:]
    
def packString(s):
    """ala buffer_put_cstring"""
    return struct.pack(">I", len(s)) + s

def getBignum(buf):
    """
    >>> getBignum(packBignum(20) + "abc")
    (20, 'abc')
    """
    
    (ln,) = struct.unpack(">I", buf[:4])
    progress("bignum bytes", ln)
    bin = buf[4:4+ln]
    x = 0
    for byte in bin:
	x = x * 256 + ord(byte)
	progress("getBignum: value so far: %x" %x)
    return x, buf[4+ln:]

def packBignum(n):
    """buffer_put_bignum2 SSH2 format

    """

    if n<0: raise RuntimeError, "packing negative numbers not implemented"
    bs = ''
    while n > 0:
	n, b = divmod(n, 256)
	bs = chr(b) + bs
    return packString(bs)

def progress(*args):
    import sys
    for a in args:
	sys.stderr.write("%s " % a)
    sys.stderr.write("\n")

def _test():
    import doctest, sshAuth
    doctest.testmod(sshAuth)


if __name__ == '__main__':
    _test()
    test("data to sign")

# $Log$
# Revision 1.2  2003-09-13 23:08:51  connolly
# woohoo! got a signature back!
#
# Revision 1.1  2003/09/13 22:54:52  connolly
# works well enough to not kill ssh-agent. loses with AgentFailed(5), though
#
