"""sparqltoy.py -- a toy SPARQL parser, just for testing
"""

__version__ = "$Id$"

def queryParts(s):
    """break down SPARQL select into variables, ns bindings, and rule head

    >>> queryParts('PREFIX dc:      <http://purl.org/dc/elements/1.1/> SELECT ?book ?title WHERE { ?book dc:title ?title }')
    (['?book', '?title'], {'dc': 'http://purl.org/dc/elements/1.1/'}, '{ ?book dc:title ?title }')
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
                    return (vars, ns, s)
                else:
                    k, s = s.split(None, 1)
                    if k.lower() == 'where': continue
                    vars.append(k)


def mkQueryFormula(vars, ns, ant):
    """make a llyn formula from
    vars - a list of variable names ("?foo", "?bar")
    ns - a dictionary of namespace bindings {"dc": "http://..."}
    ant - an antecedent "{ ?book dc:title ?title }"
    """
    
    import llyn, notation3
    kb = llyn.RDFStore()
    n3p = notation3.SinkParser(kb, baseURI="file:/")

    pfxDecls = ''
    for p, u in ns.items():
        pfxDecls += ("@prefix %s: <%s>.\n" % (p, u))

    r = pfxDecls + ant + ("\n => { (%s) a <#Answer> }." % (" ".join(vars)))
    return n3p.loadBuf(r).close()


def queryTriples(s):
    """@@hmm...

    >>> queryTriples('PREFIX dc:      <http://purl.org/dc/elements/1.1/> SELECT ?book ?title WHERE { ?book dc:title ?title }').size()
    1
    """
    vars, ns, ant = queryParts(s)
    f = mkQueryFormula(vars, ns, ant)
    #print f.universals(), "@@vars"
    #for rule in mkQueryFormula(vars, ns, ant): # should be just one
    #    for st in rule.subject():
    #        print st.subject(), "@@subj"
    #        print st.predicate(), "@@pred"
    #        print st.object(), "@@obj"
    return f


def _test():
    import doctest
    doctest.testmod()


class Usage(Exception):
    pass


if __name__ == '__main__':
    import sys
    if '--test' in sys.argv:
        _test()
    else:
        raise Usage

# $Log$
# Revision 1.4  2005-05-04 23:01:00  connolly
# made a sparql query into an N3 formula
#
# Revision 1.3  2005/05/03 22:16:48  connolly
# handle prefixes differently
#
# Revision 1.2  2005/05/03 22:10:34  connolly
# knock colon off prefix
#
# Revision 1.1  2005/05/03 22:08:40  connolly
# one test working
#
