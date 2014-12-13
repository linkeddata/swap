"""sparqltoy.py -- a toy SPARQL parser, just for testing

converts (a little bit of) SPARQL to N3QL
http://www.w3.org/DesignIssues/N3QL
  v 1.66 2004/07/03 13:33:38
"""


class Usage(Exception):
    """
    python sparqltoy.py --test
    or
    python sparqltoy.py portnum
    """
    
    def __str__(self):
        return self.__doc__


__version__ = "$Id$"

from swap import llyn, notation3
from swap.query import applyQueries
from swap.webAccess import load
from swap import toXML

def selectParts(s):
    """break down SPARQL select into variables, ns bindings, and rule head

    >>> selectParts('PREFIX dc:      <http://purl.org/dc/elements/1.1/> SELECT ?book ?title WHERE { ?book dc:title ?title }')
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


def constructParts(s):
    """break down SPARQL construct ns bindings, antecedent, and conclusion

    >>> constructParts('PREFIX dc:      <http://purl.org/dc/elements/1.1/> CONSTRUCT { ?book <data:title> ?title } WHERE { ?book dc:title ?title }')
    ({'dc': 'http://purl.org/dc/elements/1.1/'}, '{ ?book dc:title ?title }', '{ ?book <data:title> ?title }')

    """

    ns = {}
    while 1:
        #@@ factor out prefix stuff
        s = s.strip()
        k, s = s.split(None, 1)
        k = k.lower()
        if k == 'prefix':
            pfx, s = s.split(None, 1)
            utrm, s = s.split(None, 1)
            ns[pfx[:-1]] = utrm[1:-1] # remove <> around <foo> and : from dc:
        elif k == 'construct':
            s = s.strip()
            if s[0] == '{':
                conc, s = s.split("}", 1)
                conc += "}"
                s = s.strip()
                k, s = s.split(None, 1)
                if k.lower() == 'where':
                    return ns, s, conc
                else:
                    raise ValueError, "expecting 'where'; found " + s
            else:
                raise ValueError, "expecting '{'; found " + s
        else:
            raise ValueError, "expecting 'construct'; found " + s
            

def mkSelectFormula(vars, ns, ant, kb=None):
    """make a llyn Formula for an N3QL query
    vars - a list of variable names ("?foo", "?bar")
    ns - a dictionary of namespace bindings {"dc": "http://..."}
    ant - an antecedent "{ ?book dc:title ?title }"
    """

    if kb is None: kb = llyn.RDFStore()
    
    n3p = notation3.SinkParser(kb, baseURI="file:/")

    pfxDecls = ''
    for p, u in ns.items():
        pfxDecls += ("@prefix %s: <%s>.\n" % (p, u))

    r = pfxDecls + "<> <http://www.w3.org/2004/ql#where> " + ant + ("\n ; <http://www.w3.org/2004/ql#select> { (%s) a <#Answer> }." % (" ".join(vars)))
    return n3p.loadBuf(r).close()


def mkConstructFormula(ns, ant, conc, kb=None):
    """make a llyn Formula for an N3QL query
    ns - a dictionary of namespace bindings {"dc": "http://..."}
    ant - an antecedent "{ ?book dc:title ?title }"
    conc - a conclusion
    """

    if kb is None: kb = llyn.RDFStore()
    
    n3p = notation3.SinkParser(kb, baseURI="file:/")

    pfxDecls = ''
    for p, u in ns.items():
        pfxDecls += ("@prefix %s: <%s>.\n" % (p, u))

    r = pfxDecls + "[] <http://www.w3.org/2004/ql#where> " + ant + \
        "\n ; <http://www.w3.org/2004/ql#select> " + conc + "."
    return n3p.loadBuf(r).close()


def queryTriples(s):
    """@@hmm...

    >>> queryTriples('PREFIX dc:      <http://purl.org/dc/elements/1.1/> SELECT ?book ?title WHERE { ?book dc:title ?title }').size()
    2
    """
    vars, ns, ant = selectParts(s)
    f = mkSelectFormula(vars, ns, ant)
    #print f.universals(), "@@vars"
    #for rule in mkQueryFormula(vars, ns, ant): # should be just one
    #    for st in rule.subject():
    #        print st.subject(), "@@subj"
    #        print st.predicate(), "@@pred"
    #        print st.object(), "@@obj"
    return f

######
import BaseHTTPServer
import cgi # for URL-encoded query parsing

RDF_MediaType = "application/rdf+xml"
XML_MediaType = 'text/xml; charset="utf-8"'

class SparqlServer(BaseHTTPServer.HTTPServer):
    """export toy SPARQL service interface, for generating HTTP traces
    """

    def __init__(self, addr, handlerClass):
        BaseHTTPServer.HTTPServer.__init__(self, addr, handlerClass)

        self._kb = llyn.RDFStore()


class SparqleHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    QPath = '/sq?'

    def do_GET(self):
        s = self.server
        if self.path[:len(self.QPath)] == self.QPath:
            rest = self.path[len(self.QPath):]
            self.doQ()
        else:
            self.notFound()

    def doQ(self):
        s = self.server
        kb = s._kb
        
        path, qs = self.path.split('?')
        form = cgi.parse_qs(qs)
        try:
            sparql = form['query'][0]
        except KeyError:
            self.send_response(400)
            self.send_header("Content-type", "text/plain")
            self.wfile.write("no query param")
            return

        print "@@got query:", sparql

        dataSet = kb.newFormula()
        try:
            ds = form['default-graph-uri']
        except:
            pass
        else:
            for d in ds:
                load(kb, d, openFormula = dataSet)
                print "@@loaded", d, "; size=", dataSet.size()

        ns, ant, conc = constructParts(sparql) #@@ assume construct
        qf = mkConstructFormula(ns, ant, conc, kb)
        print "@@query:", qf.n3String()
        
        results = kb.newFormula()
        applyQueries(dataSet, qf, results)
        results.canonicalize()

        self.send_response(200, "result graph follows")
        self.send_header("Content-type", RDF_MediaType)
        self.end_headers()

        sink = toXML.ToRDF(self.wfile, "bogus:@@")
        kb.dumpNested(results, sink)


    def notFound(self):
        s = self.server
        
        self.send_response(404)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("""
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head><title>SparqlHandler: 404: Not Found</title></head>
        <body>
        <h1>Not Found</h1>

        <p>try: @@something else</p>
            
        <p>cf <a href="http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.5">10.4.5 404 Not Found from the HTTP specification.</a></p>
        """)

def main(argv):
    try:
        port = argv[1]
        port = int(port)
    except:
        raise Usage

    hostPort = ('127.0.0.1', int(port))
    httpd = SparqlServer(hostPort, SparqleHandler)

    print "sparqltoy %s\nserving on port %s ..." % (__version__, port)
    httpd.serve_forever()


##########

def _test():
    import doctest
    doctest.testmod()


if __name__ == '__main__':
    import sys
    if '--test' in sys.argv:
        _test()
    else:
        main(sys.argv)


# $Log$
# Revision 1.6  2005-05-05 22:08:07  connolly
# - implemented construct, with RDF/XML output
# - implemented default-graph-uri param (mouthful!)
# - finished constructParts; got the order right
# - added some else/exceptions to construct parsing code
# - startup msg includes version
#
# Revision 1.5  2005/05/05 21:21:45  connolly
# - starting HTTP interface
# - mkQueryFormula takes a kb rather than making one
# - parse a bit of CONSTRUCT as well as SELECT
# - start using N3QL rather than dbview
# - Usage exception doc
# - import swap.llyn rather than just llyn
#
# Revision 1.4  2005/05/04 23:01:00  connolly
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
