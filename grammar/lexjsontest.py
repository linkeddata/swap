import simplejson #http://cheeseshop.python.org/pypi/simplejson
import re

def main(argv):
    import sys

    fn = argv[1]
    data = file(fn).read()
    data = data.split("=", 1)[1] # SYNTAX_foo = ...
    it = simplejson.loads(data)

    #import pprint
    #print "Tokens:"
    #pprint.pprint(it['tokens'])
    #print
    
    s = Scanner(it['tokens'], )
    s.feed(sys.stdin.read())
    while 1:
        t, txt = s.next()
        if not t: break
        print t, txt

class Scanner(object):
    def __init__(self, tokens):
        patterns = [(None, re.compile("\s+")), # whitespace
                    (None, re.compile("#.*\r?\n")), # comments
                    ]
        for p, t, f in tokens:
            patterns.append((t, re.compile(p)))
        self._patterns = patterns
        self._in = ''
        self._idx = 0

    def feed(self, d):
        self._in += d

    def next(self):
        while 1:
            if self._idx >= len(self._in): return None, None

            besttok, beststr = None, None

            for t, regex in self._patterns:
                #print >>sys.stderr, "@@trying", t, self._in[self._idx:self._idx+30]
                m = regex.match(self._in[self._idx:])
                if m:
                    s = m.group(0)
                    if beststr is None or len(s) > len(beststr):
                        besttok = t
                        beststr = s
            if beststr:
                self._idx += len(beststr)
                if besttok:
                    return besttok, beststr
                # else whitespace/comment... try again
            else:
                raise SyntaxError, self._in[self._idx:self._idx+30]


def scanner(tokens, input):
    return yappsrt.Scanner([(t, p) for (p, t, dummy) in tokens],
                           ['\\s+', '#.*\\r?\\n'],
                           input)

if __name__ == '__main__':
    import sys
    main(sys.argv)
