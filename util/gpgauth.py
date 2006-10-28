
# libgcrypt was kinda nifty, but I'm not sure how to get to it from python
# file:///usr/share/doc/libgcrypt11-doc/html/gcrypt_10.html#SEC51

# seahorse-daemon looks promising...
#
# http://dbus.freedesktop.org/doc/dbus-tutorial.html#python-invoking-methods
# http://dbus.freedesktop.org/doc/dbus-tutorial.html
# http://live.gnome.org/Seahorse/DBus

#         dbus-send --dest='org.freedesktop.ExampleName            \
#                   /org/freedesktop/sample/object/name              \
#                   org.freedesktop.ExampleInterface.ExampleMethod   \
#                  int32:47 string:'hello world' double:65.32

import dbus

#signal sender=:1.31 -> dest=(null destination) path=/org/gnome/seahorse/keys/openpgp; interface=org.gnome.seahorse.Keys; member=KeyAdded
#   string "openpgp:3715751B2926A6D3"

bus = dbus.SessionBus()
proxy = bus.get_object('org.gnome.seahorse', '/org/gnome/seahorse/keys/openpgp')
i = dbus.Interface(proxy, 'org.freedesktop.DBus.Introspectable')
print i.Introspect()
c = dbus.Interface(proxy, 'org.gnome.seahorse.Keys')

keys = c.ListKeys()
conkeys = c.MatchKeys(["6E52C29E"], 0)
print "connolly keys", conkeys
mykey = conkeys[0][0]
proxy2 = bus.get_object('org.gnome.seahorse', '/org/gnome/seahorse/crypto')
i = dbus.Interface(proxy2, 'org.freedesktop.DBus.Introspectable')
print i.Introspect()
c = dbus.Interface(proxy2, 'org.gnome.seahorse.CryptoService')
print c.EncryptText([mykey], mykey,
                    0, "hello world")


import sys
sys.exit(0)

###############
import popen2

# gnupg2.info.gz from
# Filename: pool/main/g/gnupg2/gnupg2_1.9.20-2+b1_i386.deb
# Size: 773760
# SHA1: 7719cdb1280e1f9637e3580d1285a17acce4209e

def test():
    o, i = popen2.popen2("gpg-connect-agent")
    i.write("PKDECRYPT\r\n")
    ln = o.readline()
    print "@@return:", ln
    if ln.startswith("INQUIRE CIPHERTEXT"):
        (n, e) = (123, 345)
        i.write("D (enc-val rsa (n %d)\r\n (e %d))\r\n" % (n, e))
        i.write("END\r\n")
        while 1:
            ln = o.readline()
            if not ln:
                raise IOError, "lost agent"
            print "@@return:", ln
            if ln[:2] == "OK":
                break

if __name__ == '__main__':
    test()
