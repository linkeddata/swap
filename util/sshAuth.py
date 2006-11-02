"""
access to ssh-agent from python

------
Well, after going at this for a while, I think I actually
need ssh-agent to do decryption; I was thinking that's
the same as signature, but I think it's not.

see http://dev.w3.org/cvsweb/2001/palmagent/credstore.py for
using PGP and seahorse-agent via DBus
------

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
SSH2_AGENTC_REQUEST_IDENTITIES = 11
SSH2_AGENT_IDENTITIES_ANSWER = 12
SSH2_AGENTC_SIGN_REQUEST = 13
SSH2_AGENT_SIGN_RESPONSE = 14
SSH2_AGENT_FAILURE = 30
SSH_COM_AGENT2_FAILURE = 102


# http://www.python.org/doc/current/lib/modindex.html
import os, socket, struct

def main():
    import sys
    data = sys.argv[1]
    
    keyd = open("/home/connolly/.ssh/authorized_keys").readline()
    key = key_read(keyd)

    ap = os.getenv(SSH_AUTH_SOCK)
    as = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    as.connect(ap)

    progress("getting identities...")
    msg = request_reply(as, chr(SSH2_AGENTC_REQUEST_IDENTITIES))
    progress("identities reply length:", len(msg))
    progress("identities reply type:", ord(msg[0]))
    if ord(msg[0]) == SSH2_AGENT_IDENTITIES_ANSWER:
        keys = []
        qty, msg = getInt(msg[1:])
        for i in range(qty):
            k, msg = getString(msg)
            keys.append(k)
        progress("identities:", len(keys))
    else:
        progress("huh?", ord(msg[0]))

    progress("requesting signature of:", data)
    sig = ssh_agent_sign(as, key, data)

    keytn, sig = getString(sig)
    signum, sig = getBignum(sig)
    if keytn <> "ssh-rsa": raise ProtocolError, ("unexpected key type", keytn)
    assert sig == ''
    progress("signature:", keytn, `signum`)

    #hmm... this doesn't work.
    # reading http://www.faqs.org/rfcs/rfc2437.html
    #  RFC 2437 - PKCS #1: RSA Cryptography Specifications Version 2.0
    if 1:
	# http://www.amk.ca/python/writing/pycrypt/pycrypt.html
	# and debian python23-crypto package
	from Crypto.PublicKey import RSA
	from Crypto.Hash import SHA
	k = RSA.construct((key._n, key._e))
	dh = SHA.new(data).digest()
	progress("hash length: ", len(dh))
	result = k.verify(dh, (signum,))
	progress("result:", result)

def pycryptest():
    from Crypto.PublicKey import RSA
    from Crypto.Hash import SHA
    from Crypto.Util.randpool import RandomPool
    r = RandomPool()
    k = RSA.generate(1024, r.get_bytes)
    progress("pycryptest key:", `(k.n, k.e)`)
    data = "abcdefg"
    
    dh = SHA.new(data).digest()
    sig = k.sign(dh, None)
    progress("pycryptest signature:", `sig`)
    result = k.verify(dh, sig)
    progress("pycryptest result:", result)
    

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
    if ty == SSH_AGENT_FAILURE or ty == SSH_COM_AGENT2_FAILURE or \
       ty == SSH2_AGENT_FAILURE:
	raise AgentFailed, ty
    if ty != SSH2_AGENT_SIGN_RESPONSE:
	raise ProtocolError, ("expected", SSH2_AGENT_SIGN_RESPONSE, "got", ty)
    (ln,) = struct.unpack(">I", msg[1:5])
    assert(len(msg) == 1+4+ln)
    return msg[5:]


def request_reply(auth, buf):
    auth.send(struct.pack(">I" , len(buf)) + buf)

    rx = read_all(auth, 4)
    (ln,) = struct.unpack(">I", rx)
    reply = read_all(auth, ln)
    progress("reply size:", len(reply))
    return reply

def read_all(auth, ln):
    progress("read_all:", ln)
    rx = ''
    while ln > 0:
	r = auth.recv(ln)
        if not r:
            raise IOError, "lost ssh-agent"
        progress("rxd:", len(r))
	rx += r
	ln -= len(r)
    return rx

import binascii

def key_read(cpp):
    """from key.c
    """
    tn, uu, other = cpp.split()
    if tn != "ssh-rsa": raise RuntimeError, "not implemented"

    blob = binascii.a2b_base64(uu)
    keytn, blob = getString(blob)
    if keytn != "ssh-rsa": raise RuntimeError, "not implemented"
    (e, blob) = getBignum(blob)
    (n, blob) = getBignum(blob)
    progress("read key: e=0x%x n=0x%x" % (e, n))
    return RSAKey(e, n)

def getString(buf):
    (ln, ) = struct.unpack(">I", buf[:4])
    s = buf[4:4+ln]
    return s, buf[4+ln:]
    
def getInt(buf):
    (i, ) = struct.unpack(">I", buf[:4])
    return i, buf[4:]
    
def packString(s):
    """ala buffer_put_cstring"""
    return struct.pack(">I", len(s)) + s

def getBignum(buf):
    """
    >>> getBignum(packBignum(20L) + "abc")
    (20L, 'abc')
    """

    (ln,) = struct.unpack(">I", buf[:4])
    bin = buf[4:4+ln]
    progress("getBignum bytes:", ln)
    x = 0L
    for byte in bin:
	#@@progress("byte: %02x" % ord(byte))
	x = (x << 8) + ord(byte)
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
    #_test()
    #pycryptest()
    main()

# $Log$
# Revision 1.6  2006-11-02 05:27:25  connolly
# end-of-life in favor of credstore
#
# Revision 1.5  2004/06/10 12:44:58  connolly
# more diagnostics. 16 Sep 2004
#
# Revision 1.4  2003/09/16 04:36:24  connolly
# trying to play with python crypto toolkit
#
# Revision 1.3  2003/09/13 23:18:03  connolly
# decoded signature a bit
#
# Revision 1.2  2003/09/13 23:08:51  connolly
# woohoo! got a signature back!
#
# Revision 1.1  2003/09/13 22:54:52  connolly
# works well enough to not kill ssh-agent. loses with AgentFailed(5), though
#
