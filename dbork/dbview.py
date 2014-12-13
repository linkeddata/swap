#!/bin/env python
"""
dbview -- view an SQL DB thru RDF glasses.

  *** NOTE WELL ***
  As of May 2006, active development has moved to
  http://dig.csail.mit.edu/2006/dbview/dbview.py
  
an implementation of...

[SWDB]
 Relational Databases on the Semantic Web
 Id: RDB-RDF.html,v 1.17 2002/03/06 20:43:13 timbl
 http://www.w3.org/DesignIssues/RDB-RDF.html

Share and Enjoy. Open Source license:
Copyright (c) 2001 W3C (MIT, INRIA, Keio)
http://www.w3.org/Consortium/Legal/copyright-software-19980720

consider:

  select person.name, phone.room from persons,phones
     where phone.owner=person.id;

we can look at persons, phones as RDF Classes...
name as a property whose domain is person,
and room as a property whose domain is phone.
then... what's the subject of the stuff in the
result of the query?

What we really want is something like...
  { ?phone :room ?r;
           :owner ?who.
    ?who :name ?n}
    log:implies
    { [ :room ?r;
        :owner [:name ?n]]}.

but how do we know where to put the []'s in the implies, when
converting an SQL rule to an N3 rule?

The solution implemented here is to include primary key info in the
query, and to treat (database, table, primary key value)s as
URIs.

A query regards a number of tables in a database; for
each table, we're given
  - the table's name
  - the fields we want selected from the table (if any)
  - the table's primary key (if relevant)
  - the fields we want to join with other table's primary keys
  - an optional/supplimentary WHERE clause


TODO
  - show tables, describe _table_ ==> RDF schema. (in progress)
  
REFERENCES

  Python Database API v2.0
  http://www.python.org/topics/database/DatabaseAPI-2.0.html

  MySQL Reference Manual for version 4.0.2-alpha.
  generated on 7 March 2002
  http://www.mysql.com/documentation/mysql/bychapter/manual_toc.html

 
SEE ALSO

earlier dev notes, links, ...
 http://ilrt.org/discovery/chatlogs/rdfig/2002-02-27#T18-29-01
 http://rdfig.xmlhack.com/2002/02/27/2002-02-27.html#1014821419.001175
"""

__version__ = "$Id$" #@@consult python style guide


from string import join, split
import codecs

import MySQLdb # MySQL for Python
               # http://sourceforge.net/projects/mysql-python
               # any Python Database API-happy implementation will do.

from RDFSink import SYMBOL, LITERAL
import toXML # RDF/XML sink

import BaseHTTPServer
import cgi # for URL-encoded query parsing


RDF_MediaType = "text/xml" #@@ cf. RDF Core
                           #"what mime type to use for RDF?" issue...


class DBViewServer(BaseHTTPServer.HTTPServer):
    """Export an SQL database, read-only, into HTTP/RDF.

    @@integration with http://www.w3.org/DesignIssues/RDB-RDF.html
    in progress.
    
    databasename is
      'http://%s:%s%s%s' % (addr[0], addr[1], home, dbName)
    e.g.
      http://example:9003/dbview/inventory

    table names are, e.g.
      http://example:9003/dbview/inventory/products

    @@hmm... conflate the table-class name with an HTTP document?
    
    field names are, e.g.
      http://example:9003/dbview/inventory/products#description

    object names are, e.g.
      http://example:9003/dbview/inventory/products/1432
    where 1432 is the value of the primary key in the products table.
    """

    
    def __init__(self, addr, handlerClass, db, home, dbName):
        BaseHTTPServer.HTTPServer.__init__(self, addr, handlerClass)
        
        self._db = db
        self._home = home
        self._dbName = dbName
        self._base = 'http://%s:%s%s%s' % (addr[0], addr[1], home, dbName)


class DBViewHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    QPath = '/.dbq' # not an SQL name
    UIPath = '/.ui'
    
    def do_GET(self):
        s = self.server

        #DEBUG "which get?", self.path, s._home + s._dbName + self.UIPath

        dbdocpath = s._home + s._dbName

        if self.path[:len(dbdocpath)] == dbdocpath:
            rest = self.path[len(dbdocpath):]

            if rest == '':
                self.describeDB()
            elif rest == self.UIPath:
                self.getUI()
            elif rest[:len(self.QPath)+1] == self.QPath + '?':
                self.getView()
            elif rest[0] == '/':
                self.describeTable(rest[1:])
            else:
                self.notFound()
        else:
            self.notFound()

    def notFound(self):
        s = self.server
        pui = s._home + s._dbName + self.UIPath
        
        self.send_response(404)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("""
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head><title>DBViewHandler: 404: Not Found</title></head>
        <body>
        <h1>Not Found</h1>

        <p>try: <a href="%s">%s</a> database UI.</p>
            
        <p>cf <a href="http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.5">10.4.5 404 Not Found from the HTTP specification.</a></p>
        """ % (pui, s._dbName) )

            
    def getUI(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        self.wfile.write("""
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head><title>RDF query interface@@</title></head>
        <body>""")

        queryUI(self.wfile.write,
                6, #@@ more tables?
                self.server._home + self.server._dbName + self.QPath,
                self.server._dbName)

        self.wfile.write("""
        <p>@@TODO: link to form with more than 3 tables</p>
        """)

        self.wfile.write("""
        <h2>Descriptions/Schemas</h2>
        <p>database: <a href="../%s">%s</a>.</p>
        <p>tables:</p>
        <ul>
        """ % (self.server._dbName, self.server._dbName))
        
        for tbl in tableNames(self.server._db):
            self.wfile.write("<li><a href='%s'>%s</a></li>\n" % \
                                     (tbl, tbl))
        self.wfile.write("</ul>")

        self.wfile.write("""
        <address>Dan C@@ $Revision$ $Date$</address>
        </body></html>
        """)


    def describeDB(self):
        self.send_response(200, "@@not sure you're winning yet, actually")
        self.send_header("Content-type", RDF_MediaType)
        self.end_headers()

        s = self.server
        dbdocaddr = s._base
        
        sink = toXML.ToRDF(self.wfile, dbdocaddr)

        aboutDB(self.server._db, dbdocaddr, sink)

        sink.endDoc()


    def describeTable(self, tbl):
        self.send_response(200, "@@not sure you're winning yet, actually")
        self.send_header("Content-type", RDF_MediaType)
        self.end_headers()

        s = self.server
        dbdocaddr = s._base
        
        sink = toXML.ToRDF(self.wfile, dbdocaddr)

        aboutTable(self.server._db, dbdocaddr, sink, tbl)

        sink.endDoc()


    def getView(self):
        self.send_response(200, "@@not sure you're winning yet, actually")
        self.send_header("Content-type", RDF_MediaType)
        self.end_headers()

        s = self.server
        dbaddr = s._base
        
        sink = toXML.ToRDF(self.wfile, dbaddr)

        path, qs = split(self.path, '?')
        fields, tables, keys, joins, cond = parseQuery(qs)

        askdb(self.server._db, dbaddr, sink,
              fields, tables, keys, joins, cond)

        sink.endDoc()




def asSQL(fields, tables, keys, joins, condextra = ''):
    """format query as SQL.

    rougly: select fields from tables where keyJoins and condextra

    details:

      tables is a list of table names

      fields is a list of lists of fieldnames, one list per table

      keys is a dictionary that maps tables to given primary key fields

      and keyJoins is a list of lists... the bottom half
      of a matrix... keyJoins[i][j] is None or the
      name of a field in table i to join with the primary
      key of table j.
    
      condextra is an SQL expression
    """

    fldnames = []
    for ti in range(len(tables)):
        for f in fields[ti]:
            fldnames.append("%s.%s" % (tables[ti], f))

    cond = ''
    for i in range(len(tables)):
        for j in range(i):
            if joins[i][j]:
                jexpr = "%s.%s = %s.%s" % (tables[i], joins[i][j],
                                           tables[j], keys[tables[j]])
                if cond: cond = cond + ' AND '
                cond = cond + jexpr

    if condextra:
        if cond:
            cond = cond + ' AND ' + condextra
        else:
            cond = condextra

    q = 'select %s from %s' % (join(fldnames, ','), join(tables, ','))
    if cond: q = q + ' where ' + cond
    return q + ';'
    

def askdb(db, dbaddr, sink, fields, tables, keys, joins, condextra):
    """ask a query of a database; output results as RDF formula to sink.

    db is a python DB API database object
    dbaddr is a URI for the database (see DBViewServer above for details)
    sink is an RDF serializer (cf RDFSink module)
    fields/tables/keys/joins/condextra per asSQL above.

    note that fields really needs to be a list of lists, not
    a list of tuples, since tuples don't grok .index(). Odd.

    We assume table names are also
    XML names (e.g. no colons) and
    URI path segments (e.g. no non-ascii chars, no /?#).

    """

    fmla = something(sink, None, 'F')
    c = db.cursor()

    q = asSQL(fields, tables, keys, joins, condextra)
    
    c.execute(q)

    # using table names as namespace names seems to be aesthetic...
    for n in tables:
        sink.bind(n, "%s/%s#" % (dbaddr, n))
    # and suggest a prefix for the table classes...
    sink.bind('tables', "%s#" % (dbaddr,))


    while 1:
        row=c.fetchone()
        if not row:
            break

        things = [None] * len(tables)

        col = 0
        for ti in range(len(tables)):
            if fields[ti]:
                tbl = tables[ti]

                # figure out the subject of these cells...
                # all the property-fields from the same table-class
                # share a subject...
                # do we know a unique name for it?
                # i.e. ... is the table/class keyed?

                uri = None
                try:
                    kn = keys[tbl]

                    # yes...
                    # does this query return the key value?
                    try:
                        kc = fields[ti].index(kn)
                    except ValueError:
                        # no...
                        pass
                    else:
                        kv = row[col+kc]
                        uri = "%s/%s/%s#item" % (dbaddr, tbl, kv) # cf [SWDB]
                except KeyError:
                    # no, no key supplied for this class/table
                    pass

                if uri: subj = (SYMBOL, uri)
                else:   subj = something(sink, fmla, tbl)

                # remember this for joins...
                things[ti] = subj
                
                # subj rdf:type _tableClass_.
                sink.makeStatement((fmla,
                                    (SYMBOL, RDF.type),
                                    subj,
                                    (SYMBOL, "%s#%s" % (dbaddr, tbl))
                                    ))


                for fld in fields[ti]:
                    cell = row[col]
                    if cell is None: continue
                    
                    # @@our mysql implementation happens to use iso8859-1
                    ol = (LITERAL, latin1(str(cell)))

                    # ok... now we have subj, pred and obj...
                    prop = (SYMBOL, "%s/%s#%s" % (dbaddr, tbl, fld))
                    sink.makeStatement((fmla, prop, subj, ol))

                    col = col + 1

                # now relate it to other things...
                for j in range(ti):
                    if joins[ti][j] and things[j]:
                        prop = (SYMBOL, "%s/%s#%s" %
                                (dbaddr, tables[ti], joins[ti][j]))
                        sink.makeStatement((fmla, prop, subj, things[j]))

# cf
# 4.8 codecs -- Codec registry and base classes
# http://www.python.org/doc/2.1.2/lib/module-codecs.html
latin1_decode = codecs.lookup('iso8859-1')[1]
def latin1(bytes):
    return latin1_decode(bytes)[0]

g=0
def something(sink, scope=None, hint='gensym'):
    global g
    g=g+1
    term = (SYMBOL, '#%s%s' % (hint, g))
    #if scope: sink.makeStatement((scope,
    #(SYMBOL, RDFSink.forSomeSym),
    #scope, term))
    return term


class Namespace:
    """A collection of URIs witha common prefix.

    rape-and-pasted from 2000/04/maillog2rdf/mid_proxy.py
    
    ACK: AaronSw / #rdfig
    http://cvs.plexdev.org/viewcvs/viewcvs.cgi/plex/plex/plexrdf/rdfapi.py?rev=1.6&content-type=text/vnd.viewcvs-markup
    """
    def __init__(self, nsname): self.nsname = nsname
    def __getattr__(self, lname): return self.nsname + lname
    def __str__(self): return self.nsname
    def sym(self, lname): return self.nsname + lname

SwDB = Namespace("http://www.w3.org/2000/10/swap/db#")
  # in particular: db.n3,v 1.5 2002/03/06 23:12:00
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
RDF  = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")
DAML = Namespace("http://www.daml.org/2001/03/daml+oil#")


def aboutDB(db, dbdocaddr, sink):
    """describe a database into a sink.

    We have a need for arbitrary names that don't clash
    with table and column names. We chose names with '.'
    at the end (or beginning?), taking advantage of:

      You cannot use the `.' character in names because
      it is used to extend the format by which you can refer
      to columns.

      -- 6.1.2 Database, Table, Index, Column, and Alias Names
      http://www.mysql.com/documentation/mysql/bychapter/manual_Reference.html#Legal_names

    """

    fmla = something(sink, None, 'aboutDB')

    sink.bind('db', str(SwDB))
    sink.bind('rdfs', str(RDFS))
    sink.bind('rdf', str(RDF))

    dbaddr = "%s#.database" % dbdocaddr

    # <personell#.database> db:databaseSchema <personell>.
    sink.makeStatement((fmla,
                        (SYMBOL, SwDB.databaseSchema),
                        (SYMBOL, dbaddr),
                        (SYMBOL, dbdocaddr),
                        ))

    sink.makeStatement((fmla,
                        (SYMBOL, SwDB.formService),
                        (SYMBOL, dbdocaddr),
                        (SYMBOL, "%s%s" % (dbdocaddr, DBViewHandler.QPath)),
                        ))

    for tbl in tableNames(db):
        tblI = "%s#%s" % (dbdocaddr, tbl)
        tbldocI = "%s/%s" % (dbdocaddr, tbl)
        
        sink.makeStatement((fmla,
                            (SYMBOL, SwDB.table),
                            (SYMBOL, dbaddr),
                            (SYMBOL, tblI),
                            ))
        sink.makeStatement((fmla,
                            (SYMBOL, SwDB.tableSchema),
                            (SYMBOL, tblI),
                            (SYMBOL, tbldocI),
                            ))
        sink.makeStatement((fmla,
                            (SYMBOL, RDFS.label),
                            (SYMBOL, tblI),
                            (LITERAL, tbl)
                            ))


def tableNames(db):
    c = db.cursor()
    c.execute("show tables") # mysql-specific?
    # http://www.mysql.com/documentation/mysql/bychapter/manual_MySQL_Database_Administration.html#SHOW

    res = []
    
    while 1:
        row = c.fetchone()
        if not row: break

        res.append(row[0])

    return res


def aboutTable(db, dbaddr, sink, tbl):
    fmla = something(sink, None, 'aboutTable')

    sink.bind('db', str(SwDB))
    sink.bind('rdfs', str(RDFS))
    sink.bind('rdf', str(RDF))
    
    c = db.cursor()
    c.execute("show columns from %s" % tbl)
    while 1:
        row = c.fetchone()
        if not row: break

        colName, ty, nullable, isKey, dunno, dunno = row
        
        tblI = "%s#%s" % (dbaddr, tbl)
        colI = "%s/%s#%s" % (dbaddr, tbl, colName)
        
        sink.makeStatement((fmla,
                            (SYMBOL, SwDB.column),
                            (SYMBOL, tblI),
                            (SYMBOL, colI),
                            ))

        if isKey == 'PRI':
            sink.makeStatement((fmla,
                                (SYMBOL, SwDB.primaryKey),
                                (SYMBOL, tblI),
                                (SYMBOL, colI),
                                ))

        sink.makeStatement((fmla,
                            (SYMBOL, RDFS.domain),
                            (SYMBOL, colI),
                            (SYMBOL, tblI),
                            ))
        sink.makeStatement((fmla,
                            (SYMBOL, RDFS.label),
                            (SYMBOL, colI),
                            (LITERAL, colName)
                            ))

        # could expose nullable as DAML.minCardinality
        # could expose type as RDFS.range


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

    qs is an URL-encoded query string, ala the form above
    return fields, tables, keys, keyJoins, condition ala asSQL() above.
    """

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
            fields.append(())
        else:
            fields.append(fieldsI)

        try:
            key = form['key%s' % i][0]
        except:
            pass
        else:
            keys[tname] = key

        i = i + 1

    keyJoins = []
    for i in range(1, len(tables)+1):
        tjoins = []
        for j in range(1, i):
            kjN = 'kj%s_%s' % (i, j)
            try:
                f = form[kjN][0]
            except KeyError:
                tjoins.append(None)
            else:
                tjoins.append(f)
        keyJoins.append(tjoins)

    return fields, tables, keys, keyJoins, condition




###############################
# Test harness...

def testSvc():
    import sys

    host, port, user, passwd, httpHost, httpPort = sys.argv[2:8]
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


def testShow():
    import sys

    host, port, user, passwd = sys.argv[2:6]
    port = int(port)

    dbName = 'administration' #@@
    db=MySQLdb.connect(host=host, port=port,
                       user=user, passwd=passwd,
                       db=dbName)

    dbaddr = 'http://example/administration'
    sink = toXML.ToRDF(sys.stdout, dbaddr)

    aboutDB(db, dbaddr, sink)

    aboutTable(db, dbaddr, sink, 'users')

    sink.endDoc()
    

def testUI():
    import sys
    queryUI(sys.stdout.write, 3, '/', "niftydb")


def testSQL():
    cases = ('/administration/.dbq?name1=users&fields1=family%2Cemail%2Ccity%2Cid&key1=id&name2=techplenary2002&fields2=plenary%2Cmeal_choice&key2=&kj2_1=id&name3=&fields3=&key3=&kj3_1=&kj3_2=&name4=&fields4=&key4=&kj4_1=&kj4_2=&kj4_3=',

           '/manage/.dbq?name1=Resources&fields1=ResourceName%2CResourceID&key1=ResourceID&name2=Activities&fields2=ActivityName%2CActivityID&key2=ActivityID&kj2_1=ResourceID&name3=Assignments&fields3=Percent_of_person%2CAssignment_ID&key3=Assignment_ID&kj3_1=MyResourceID&kj3_2=MyActivityID&name4=&fields4=&key4=&kj4_1=&kj4_2=&kj4_3=&condition=',

           '/w3c/.dbq?name1=uris&fields1=uri&key1=id&name2=groupDetails&fields2=id%2Cname&key2=id&kj2_1=sub&name3=ids&fields3=&key3=id&kj3_1=&kj3_2=sponsor&name4=userDetails&fields4=id%2Cfamily%2Cgiven%2Cphone&key4=&kj4_1=emailUrisId&kj4_2=&kj4_3=id&name5=hierarchy&fields5=&key5=id&kj5_1=&kj5_2=&kj5_3=sub&kj5_4=&name6=&fields6=&key6=&kj6_1=&kj6_2=&kj6_3=&kj6_4=&kj6_5=&name7=&fields7=&key7=&kj7_1=&kj7_2=&kj7_3=&kj7_4=&kj7_5=&kj7_6=&condition=hierarchy.type%3D%27U%27+and+hierarchy.super%3D30310',

                      '/w3c/.dbq?name1=uris&fields1=uri&key1=id'
           )

    if sys.argv[2:]: cases = sys.argv[2:]
    
    for path in cases:
        path, fields = split(path, '?')
        print "CGI parse:", cgi.parse_qs(fields)
    
        fields, tables, keys, joins, cond = parseQuery(fields)
        print "SQL parse:", fields, tables, keys, joins, cond

        print "as SQL:", asSQL(fields, tables, keys, joins, cond)


def testQ():
    import sys
    
    host, port, user, passwd = sys.argv[2:6]
    port = int(port)
    
    path='/administration/.dbq?name1=users&fields1=family%2Cemail%2Ccity%2Cid&key1=id&name2=techplenary2002&fields2=plenary%2Cmeal_choice&key2=&kj2_1=id&name3=&fields3=&key3=&kj3_1=&kj3_2=&name4=&fields4=&key4=&kj4_1=&kj4_2=&kj4_3='
    
    path, fields = split(path, '?')
    print "CGI parse:", cgi.parse_qs(fields)
    
    fields, tables, keys, joins, cond = parseQuery(fields)
    print "SQL parse:", fields, tables, keys, joins, cond

    print "as SQL:", asSQL(fields, tables, keys, joins, cond)
    
    sink = toXML.ToRDF(sys.stdout, 'stdout:')

    db=MySQLdb.connect(host=host, port=port,
                       user=user, passwd=passwd,
                       db='administration')

    dbaddr = 'http://example/administration'
    
    askdb(db, dbaddr, sink,
          fields, tables, keys, joins, cond)

    sink.endDoc()



def main(argv):
    host, port, user, passwd, httpHost, httpPort, dbName = argv[1:8]
    port = int(port)

    db=MySQLdb.connect(host=host, port=port,
                       user=user, passwd=passwd,
                       db=dbName)

    hostPort = (httpHost, int(httpPort))
    httpd = DBViewServer(hostPort, DBViewHandler, db, '/', dbName)

    print "base:", httpd._base
    print "Serving database %s HTTP on port %s ..." % (dbName, httpPort)
    httpd.serve_forever()



if __name__ == '__main__':
    import sys

    if sys.argv[1] == '--testSvc': testSvc()
    elif sys.argv[1] == '--testShow': testShow()
    elif sys.argv[1] == '--testQ': testQ()
    elif sys.argv[1] == '--testUI': testUI()
    elif sys.argv[1] == '--testSQL': testSQL()
    else:
        main(sys.argv)



# $Log$
# Revision 1.21  2007-06-26 02:36:16  syosi
# fix tabs
#
# Revision 1.20  2006/05/18 19:53:54  connolly
# note development has moved
#
# Revision 1.19  2003/03/02 06:07:46  connolly
# updated per bind API change, XML serializer move to toXML module
#
# Revision 1.18  2002/03/16 06:14:53  connolly
# allow command-line test cases for --testSQL
#
# Revision 1.17  2002/03/16 05:59:43  connolly
# xml mime type more convenient; fixed buggy namespace bindings
#
# Revision 1.16  2002/03/08 06:45:24  connolly
# fixed bug with empty where clause
# added --testSQL
# handle NULL values by not asserting anything. Hmm...
#
# Revision 1.15  2002/03/08 00:11:36  connolly
# HTTP export of schemas working.
# UI fleshed out a bit.
#
# Revision 1.14  2002/03/07 23:25:01  connolly
# moved ui path to not conflict with table names
#
# Revision 1.13  2002/03/07 00:24:43  connolly
# stop conflating stuff, per designissues thingy.
# lightly tested...
#
# Revision 1.12  2002/03/06 17:24:39  connolly
# add pointer to msql doc for mysql-specific schema-interrogation stuff
#
# Revision 1.11  2002/03/06 17:20:18  timbl
# (timbl) Changed through Jigsaw.
#
# Revision 1.10  2002/03/06 06:37:32  connolly
# structure browsing is starting to work:
# listing tables in a database,
# listing columns in a table.
# Converting to RDF/RDFS works.
# SwDB namespace name needs deciding.
# HTTP export is TODO.
#
# Revision 1.9  2002/03/06 05:41:32  connolly
# OK! basic query interface, including joins,
# seems to work.
#
# Revision 1.8  2002/03/06 03:44:05  connolly
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
