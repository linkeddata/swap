#!/bin/env python
"""
dbview -- view an SQL DB thru RDF glasses.

Share and Enjoy. Open Source license:
Copyright (c) 2001 W3C (MIT, INRIA, Keio)
http://www.w3.org/Consortium/Legal/copyright-software-19980720

hmm... RDF/SQL mapping issue: consider:

  select person.name, phone.room from persons,phones
     where phone.owner=person.id;

we can look at persons, phones as RDF Classes...
name as a property whose domain is person,
and room as a property whose domain is phone.
then... what's the subject of the resulting properties?

i.e.
  { ?phone :room ?r; :owner [ is :id of ?who ]. ?who :name ?n}
    log:implies { [ :room ?r; :owner [:name ?n]]}.

that's the way the SQL query should work, but how do I know where to
put the []'s in the implies, when converting an SQL rule to an N3
rule? Hmm... make the id disappear in the RDF level?


  { ?phone :room ?r; :owner [ is :id of ?who ]. ?who :name ?n}
    log:implies { [ :col1 ?r; :col2 ?n].
                  :col1 sqlmap:cameFrom :name; sqlmap:tables (:person :phone).
                  :col2 sqlmap:
                }.


earlier dev notes, links, ...
 http://ilrt.org/discovery/chatlogs/rdfig/2002-02-27#T18-29-01
 http://rdfig.xmlhack.com/2002/02/27/2002-02-27.html#1014821419.001175
"""

__version__ = "$Id$" #@@consult python style guide


from string import join

import MySQLdb # MySQL for Python
               # http://sourceforge.net/projects/mysql-python
               #
               # implements...
               #  Python Database API v2.0
               #  http://www.python.org/topics/database/DatabaseAPI-2.0.html


import RDFSink
import notation3 # move RDF/XML writer out of notation3

import BaseHTTPServer


class DBViewServer(BaseHTTPServer.HTTPServer):
    def __init__(self, addr, handlerClass, db, base):
        BaseHTTPServer.HTTPServer.__init__(self, addr, handlerClass)
        
        self._db = db
        self._base = base
        

class DBViewHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.getRoot()
        else:
            self.getView()
            
    def getRoot(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        self.wfile.write("""
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head><title>RDF query interface@@</title></head>
        <body>
        <p>Query:</p>
        <form action='/dbview'>
        <input name="q"/>
        </form>
        </body>""")

        
    def getView(self):
        self.send_response(200, "@@not sure you're winning yet, actually")
        self.send_header("Content-type", "application/rdf+xml") #@@ cf. RDF Core "what mime type to use for RDF?" issue...
        self.end_headers()

        addr = self.server._base + self.path
        
        sink = notation3.ToRDF(self.wfile, addr)

        ns = addr + '#' #@@hmm...
        sink.bind('db', (RDFSink.SYMBOL, ns))

        #@@hardcoded
        fields = ('email', 'given', 'family', 'city', 'state', 'country', 'URL', 'last')
        tables = ('users', 'techplenary2002')
        condition = 'users.id=techplenary2002.id'
        
        askdb(self.server._db, ns, sink, fields, tables, condition)




g=0
def something(sink, scope=None, hint='gensym'):
    global g
    g=g+1
    term = (RDFSink.SYMBOL, '#%s%s' % (hint, g))
    #if scope: sink.makeStatement((scope,
    #(RDFSink.SYMBOL, RDFSink.forSomeSym),
    #scope, term))
    return term


def askdb(db, ns, sink, fields, tables, condition):
    scope = something(None, None, 'scope')
    c = db.cursor()
    q='select %s from %s where %s;' % (join(fields, ','), join(tables, ','), condition)
    c.execute(q)

    while 1:
	row=c.fetchone()
	if not row:
            break
	subj = something(sink, scope, 'ans')
        sink.startAnonymousNode(subj)
	col = 0
	for cell in row:
            # our mysql implementation happens to use iso8859-1
            ol = cell.decode('iso8859-1')
            
	    tup = (scope,
                   (RDFSink.SYMBOL, "%s%s" % (ns, fields[col])),
                   subj, (RDFSink.LITERAL, ol))
            sink.makeStatement(tup)
	    col = col + 1
        sink.endAnonymousNode()


def testSvc():
    import sys

    host, port, user, passwd, httpPort = sys.argv[1:6]
    port = int(port)
    
    db=MySQLdb.connect(host=host, port=port,
                       user=user, passwd=passwd,
                       db='administration') #@@

    hostPort = ('', int(httpPort))
    base = "http://127.0.0.1:%s" % httpPort
    httpd = DBViewServer(hostPort, DBViewHandler, db, base)

    print "Serving HTTP on port", httpPort, "..."
    httpd.serve_forever()




def testDBView(fp, host, port, user, passwd):
    #sink = notation3.ToN3(fp.write, 'stdout:')
    sink = notation3.ToRDF(fp, 'stdout:')
    db=MySQLdb.connect(host=host, port=port,
                       user=user, passwd=passwd,
                       db='administration')

    ns='http://example/w3c-admin-db#'
    sink.bind('admin', (RDFSink.SYMBOL, ns))
    askdb(db, ns, sink,
          ('email', 'given', 'family', 'city', 'state', 'country', 'URL', 'last'),
          ('users', 'techplenary2002'),
          'users.id=techplenary2002.id')
    sink.endDoc()




def testCLI():
    import sys
    from string import atoi
    
    host, port, user, passwd = sys.argv[1:5]

    testDBView(sys.stdout, host, atoi(port), user, passwd)
    
if __name__ == '__main__':
    #testCLI()
    testSvc()
    

# $Log$
# Revision 1.5  2002-03-05 22:04:18  connolly
# HTTP interface starting to work...
#
