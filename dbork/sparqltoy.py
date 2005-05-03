"""sparqltoy.py -- a toy SPARQL parser, just for testing
"""

__version__ = "$Id$"

def parse(s):
    """parse some sparql

    >>> parse('PREFIX dc:      <http://purl.org/dc/elements/1.1/> SELECT ?book ?title WHERE { ?book dc:title ?title }')
    ({'dc:': 'http://purl.org/dc/elements/1.1/'}, ['book', 'title'], '{ ?book dc:title ?title }')
    """

    ns = {}
    while 1:
        s = s.strip()
        k, s = s.split(None, 1)
        k = k.lower()
        if k == 'prefix':
            pfx, s = s.split(None, 1)
            utrm, s = s.split(None, 1)
            ns[pfx] = utrm[1:-1] # remove <> around <foo>
        elif k == 'select':
            vars = []
            while 1:
                s = s.strip()
                if s[0] == '{':
                    return ns, vars, s
                else:
                    k, s = s.split(None, 1)
                    if k.lower() == 'where': continue
                    vars.append(k[1:]) # ?foo becomes foo


def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    import sys
    if '--test' in sys.argv:
        _test()


# $Log$
# Revision 1.1  2005-05-03 22:08:40  connolly
# one test working
#
