import rdfn3_yapps
import notation3

import sys

class Parser:
    def __init__(self, sink, baseURI):
        self._sink = sink
        self._baseURI = baseURI

    def feed(self, text):
        p = rdfn3_yapps.Parser(rdfn3_yapps.scanner(text),
                               self._sink, self._baseURI)
        f = getattr(p, 'document')
        f() #raises SyntaxError, etc.


def test(text):
    gen = notation3.ToN3(sys.stdout.write)
    p = Parser(gen, 'http://example.org/2001/stuff/doc23')
    gen.startDoc()
    p.feed(text)
    gen.endDoc()

def testKIF(text, addr):
    import KIFSink
    gen = KIFSink.Sink(sys.stdout.write)
    p = Parser(gen, addr)
    gen.startDoc()
    p.feed(text)
    gen.endDoc()

if __name__ == '__main__':
    import os
    testKIF(sys.stdin.read(), 'file:%s/STDIN' % (os.getcwd(),))
