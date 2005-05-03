"""sparqltoy.py -- a toy SPARQL parser, just for testing
"""

__version__ = "$Id$"

def parse(s):
    """parse some sparql

    >>> parse('PREFIX dc:      <http://purl.org/dc/elements/1.1/> SELECT ?book ?title WHERE { ?book dc:title ?title }')
    (['?book', '?title'], '@prefix dc <http://purl.org/dc/elements/1.1/>.\\n?book dc:title ?title.')

    """

    ns = {}
    while 1:
        s = s.strip()
        k, s = s.split(None, 1)
        k = k.lower()
        if k == 'prefix':
            pfx, s = s.split(None, 1)
            utrm, s = s.split(None, 1)
            ns[pfx[:-1]] = utrm[1:-1] # remove <> around <foo> and : from dc:
        elif k == 'select':
            vars = []
            while 1:
                s = s.strip()
                if s[0] == '{':
                    pfxDecls = ''
                    for p, u in ns.items():
                        pfxDecls += ("@prefix %s <%s>.\n" % (p, u))
                    s = s[1:-1].strip()
                    return vars, (pfxDecls + s + '.') # remove outer {}
                else:
                    k, s = s.split(None, 1)
                    if k.lower() == 'where': continue
                    vars.append(k)


def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    import sys
    if '--test' in sys.argv:
        _test()


# $Log$
# Revision 1.3  2005-05-03 22:16:48  connolly
# handle prefixes differently
#
# Revision 1.2  2005/05/03 22:10:34  connolly
# knock colon off prefix
#
# Revision 1.1  2005/05/03 22:08:40  connolly
# one test working
#
