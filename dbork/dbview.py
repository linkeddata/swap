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


from string import join, split

import MySQLdb # MySQL for Python
               # http://sourceforge.net/projects/mysql-python
               #
               # implements...
               #  Python Database API v2.0
               #  http://www.python.org/topics/database/DatabaseAPI-2.0.html


import RDFSink
import notation3 # move RDF/XML writer out of notation3

import BaseHTTPServer
import cgi # for URL-encoded query parsing

class DBViewServer(BaseHTTPServer.HTTPServer):
    def __init__(self, addr, handlerClass, db, home, dbName):
        BaseHTTPServer.HTTPServer.__init__(self, addr, handlerClass)
        
        self._db = db
        self._home = home
        self._dbName = dbName
        self._base = 'http://%s:%s%s%s' % (addr[0], addr[1], home, dbName)

class DBViewHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    QPath = '/dbq'
    UIPath = '/ui'
    
    def do_GET(self):
        s = self.server

        #DEBUG "which get?", self.path, s._home + s._dbName + self.UIPath
        
        if self.path == s._home + s._dbName + self.UIPath:
            self.getUI()
        else:
            self.getView()

            
    def getUI(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        self.wfile.write("""
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head><title>RDF query interface@@</title></head>
        <body>""")

        queryUI(self.wfile.write,
                4, #@@ more tables?
                self.server._home + self.server._dbName + self.QPath,
                self.server._dbName)

        self.wfile.write("""
        <address>Dan C@@ $Revision$ $Date$</address>
        </body></html>
        """)


    def getView(self):
        self.send_response(200, "@@not sure you're winning yet, actually")
        self.send_header("Content-type", "application/rdf+xml") #@@ cf. RDF Core "what mime type to use for RDF?" issue...
        self.end_headers()

        dbaddr = self.server._base + self.path
        
        sink = notation3.ToRDF(self.wfile, dbaddr)

        #@@hardcoded
        fields = ('email', 'given', 'family', 'city', 'state', 'country', 'URL', 'last')
        tables = ('users', 'techplenary2002')
        condition = 'users.id=techplenary2002.id'
        
        askdb(self.server._db, dbaddr, sink, fields, tables, condition)




g=0
def something(sink, scope=None, hint='gensym'):
    global g
    g=g+1
    term = (RDFSink.SYMBOL, '#%s%s' % (hint, g))
    #if scope: sink.makeStatement((scope,
    #(RDFSink.SYMBOL, RDFSink.forSomeSym),
    #scope, term))
    return term


def askdb(db, dbaddr, sink, fields, tables, condition):
    scope = something(None, None, 'scope')
    c = db.cursor()
    q='select %s from %s where %s;' % (join(fields, ','), join(tables, ','), condition)
    c.execute(q)


    # we assume table names are also
    # XML names (e.g. no colons) and
    # URI path segments (e.g. no non-ascii chars)
    for n in tables:
        sink.bind(n, (RDFSink.SYMBOL, "%s/%s#" % (dbaddr, n)))


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
                   (RDFSink.SYMBOL,
                    "%s/%s#%s" % (dbaddr,
                                  tables[0], #@@right table
                                  fields[col])),
                   subj, (RDFSink.LITERAL, ol))
            sink.makeStatement(tup)
	    col = col + 1
        sink.endAnonymousNode()


def asSQL(fields, tables, joins, condextra):
    fldnames = [ "%s.%s" % (f[0], f[1]) for f in fields ]

    cond = ''
    if joins:
        joinexprs = [ "%s.%s = %s.%s" % (j[0][0], j[0][1], j[1][0], j[1][1])
                      for j in joins ]
        cond = join(joinexprs, ' AND ')
    if condextra:
        if cond:
            cond = cond + ' AND ' + condextra
        else:
            cond = condextra

    return 'select %s from %s where %s;' % (join(fldnames, ','),
                                            join(tables, ','),
                                            cond)

    
def askdb2(db, dbaddr, sink, fields, tables, keys, joins, condextra):
    fmla = something(None, None, 'F')
    c = db.cursor()

    fields = list(fields) # odd... tuples don't do index()

    q = asSQL(fields, tables, joins, condextra)
    
    c.execute(q)


    # we assume table names are also
    # XML names (e.g. no colons) and
    # URI path segments (e.g. no non-ascii chars)
    for n in tables:
        sink.bind(n, (RDFSink.SYMBOL, "%s/%s#" % (dbaddr, n)))


    while 1:
	row=c.fetchone()
	if not row:
            break

        things = {}

	#@@subj = something(sink, fmla, 'ans')
        #sink.startAnonymousNode(subj)

	col = 0
	for cell in row:
            # @@our mysql implementation happens to use iso8859-1
            ol = (RDFSink.LITERAL, str(cell).decode('iso8859-1'))

            tbl, fld = fields[col]

            # figure out the subject of this cell-statement...
            # all the property-fields from the same table-class
            # share a subject... do we already have it...?
            try:
                subj = things[tbl]
            except KeyError:
                # no... make up something in this table/class.
                # do we know a unique name for it?
                # i.e. ... is the table/class keyed?

                uri = None
                try:
                    kn = keys[tbl]

                    # yes...
                    # does this query return the key value?
                    try:
                        kc = fields.index((tbl, kn))
                    except ValueError:
                        # no...
                        pass
                    else:
                        kv = row[kc]
                        uri = "%s/%s/%s" % (dbaddr, tbl, kv)
                except KeyError:
                    # no, no key supplied for this class/table
                    pass

                if uri: subj = (RDFSink.SYMBOL, uri)
                else:   subj = something(sink, fmla, tbl)

                # subj rdf:type _tableClass_.
                sink.makeStatement((fmla,
                                    (RDFSink.SYMBOL, notation3.RDF_type_URI),
                                    subj,
                                    (RDFSink.SYMBOL, "%s/%s" % (dbaddr, tbl))
                                    ))

                things[tbl] = subj

            # ok... now we know what the relevant subject is...
	    prop = (RDFSink.SYMBOL, "%s/%s#%s" % (dbaddr, tbl, fld))
            sink.makeStatement((fmla, prop, subj, ol))

	    col = col + 1


###############
# Forms UI

def queryUI(write, n, qpath, dbName):
    write("<div><form action='%s'><table>\n" % qpath)
    write("<caption>Query %s database</caption>\n" % dbName)

    # table head:
    # Tbl Name Fields Key =Key 1 =Key2 ...
    write("<tr><th>Tbl</th><th>Name</th><th>Fields</th><th>Key</th>")
    for k in range(1, n):
        write("<th>= Key %s</th>" % k)
    write("</tr>\n")
    
    for k in range(1, n+1):
        write("<tr><th>%s</th>" % k)
        write("<td><input name='name%s'/></td>" % k)
        write("<td><input name='fields%s'/></td>" % k)
        write("<td><input name='key%s'/></td>" % k)
        for j in range(1, k):
            write("<td><input name='kj%s_%s'/></td>" % (k, j))
        write("</tr>\n")
    write("</table>\n")
    write("<p>other condition: <input name='condition'/></p>\n")
    write("<p><input type=submit value='Get Results'/></p>\n")
    write("</form></div>\n")
        


def parseQuery(qs):
    """Parse url-encoded SQL query string

    return fields, tables, keys, keyJoins, condition
       (ala: select fields from tables where keyJoins and condition)
    where fields is a list of (tableName, fieldName) pairs,
      tables is a list of table names
      keys is a dictionary that maps tables to given primary key fields
      and keyJoins is a list of ((tn, fn), (tn, fn)) pairs.
    
    qs is an URL-encoded query string, ala the form above"""


    form = cgi.parse_qs(qs)

    try:
        condition = form['condition'][0]
    except KeyError:
        condition = None
        
    i = 1

    tables = []
    fields = []
    keys = {}
    
    while 1:
        nameN = 'name%s' % i
        if not form.has_key(nameN): break

        tname = form[nameN][0]
        tables.append(tname)
        
        try:
            fieldsI = split(form['fields%s' % i][0], ',')
        except KeyError:
            pass
        else:
            for f in fieldsI:
                fields.append((tname, f))

        try:
            key = form['key%s' % i][0]
        except:
            pass
        else:
            keys[tname] = key

        i = i + 1

    keyJoins = []
    for i in range(1, len(tables)+1):
        for j in range(1, i):
            kjN = 'kj%s_%s' % (i, j)
            try:
                f = form[kjN][0]
            except KeyError:
                pass
            else:
                keyJoins.append(((tables[i-1], f),
                                 (tables[j-1], keys[tables[j-1]]) ))

    return fields, tables, keys, keyJoins, condition


#################
# Test harness...

def testSvc():
    import sys

    host, port, user, passwd, httpHost, httpPort = sys.argv[1:7]
    port = int(port)

    dbName = 'administration' #@@
    db=MySQLdb.connect(host=host, port=port,
                       user=user, passwd=passwd,
                       db=dbName)

    hostPort = (httpHost, int(httpPort))
    httpd = DBViewServer(hostPort, DBViewHandler, db, '/', dbName)

    print "base:", httpd._base
    print "Serving HTTP on port", httpPort, "..."
    httpd.serve_forever()




def testDBView(fp, host, port, user, passwd):
    #sink = notation3.ToN3(fp.write, 'stdout:')
    sink = notation3.ToRDF(fp, 'stdout:')
    db=MySQLdb.connect(host=host, port=port,
                       user=user, passwd=passwd,
                       db='administration')

    dbaddr='http://example/w3c-admin-db'
    askdb(db, dbaddr, sink,
          ('email', 'given', 'family', 'city', 'state', 'country', 'URL', 'last'),
          ('users', 'techplenary2002'),
          'users.id=techplenary2002.id')
    sink.endDoc()




def testCLI():
    import sys
    from string import atoi
    
    host, port, user, passwd = sys.argv[1:5]

    testDBView(sys.stdout, host, atoi(port), user, passwd)


def testUI():
    import sys
    queryUI(sys.stdout.write, 3, '/', "niftydb")


def testQ():
    import sys
    
    host, port, user, passwd = sys.argv[1:5]
    port = int(port)
    
    path='/administration/dbq?name1=users&fields1=family%2Cemail%2Ccity%2Cid&key1=id&name2=techplenary2002&fields2=plenary%2Cmeal_choice&key2=&kj2_1=id&name3=&fields3=&key3=&kj3_1=&kj3_2=&name4=&fields4=&key4=&kj4_1=&kj4_2=&kj4_3='

    path, fields = split(path, '?')
    print "CGI parse:", cgi.parse_qs(fields)
    
    fields, tables, keys, joins, cond = parseQuery(fields)
    print "SQL parse:", fields, tables, keys, joins, cond

    print "as SQL:", asSQL(fields, tables, joins, cond)
    
    sink = notation3.ToRDF(sys.stdout, 'stdout:')

    db=MySQLdb.connect(host=host, port=port,
                       user=user, passwd=passwd,
                       db='administration')

    dbaddr='http://example/administration'
    
    askdb2(db, dbaddr, sink,
           fields, tables, keys, joins, cond)

    sink.endDoc()


if __name__ == '__main__':
    #testCLI()
    #testSvc()
    #testUI()
    testQ()
    
# $Log$
# Revision 1.8  2002-03-06 03:44:05  connolly
# the multi-table case is starting to work...
# I haven't captured the joined relationships yet...
# I'm thinking about turning the fields structure inside out...
#
# Revision 1.7  2002/03/06 00:03:16  connolly
# starting to work out the forms UI...
#
# Revision 1.6  2002/03/05 22:16:24  connolly
# per-table namespace of columns starting to work...
#
# Revision 1.5  2002/03/05 22:04:18  connolly
# HTTP interface starting to work...
#
