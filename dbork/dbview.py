#!/bin/env python
"""
dbview -- view an SQL DB thru RDF glasses.

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
  - show tables, describe _table_ ==> RDF schema.
  
REFERENCES

  Python Database API v2.0
  http://www.python.org/topics/database/DatabaseAPI-2.0.html

SEE ALSO

earlier dev notes, links, ...
 http://ilrt.org/discovery/chatlogs/rdfig/2002-02-27#T18-29-01
 http://rdfig.xmlhack.com/2002/02/27/2002-02-27.html#1014821419.001175
"""

__version__ = "$Id$" #@@consult python style guide


from string import join, split

import MySQLdb # MySQL for Python
               # http://sourceforge.net/projects/mysql-python
               # any Python Database API-happy implementation will do.

import RDFSink
import notation3 # @@move RDF/XML writer out of notation3

import BaseHTTPServer
import cgi # for URL-encoded query parsing




class DBViewServer(BaseHTTPServer.HTTPServer):
    """Export an SQL database, read-only, into HTTP/RDF.

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
    QPath = '/dbq'
    UIPath = '/ui'
    
    def do_GET(self):
        s = self.server

        #DEBUG "which get?", self.path, s._home + s._dbName + self.UIPath
        
        pui = s._home + s._dbName + self.UIPath
        pq = s._home + s._dbName + self.QPath
        
        if self.path == pui: self.getUI()
        elif self.path[:len(pq)+1] == pq + '?': self.getView()
        else:
            self.send_error(404, 'path not understood')

            
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

        s = self.server
        dbaddr = s._home + s._dbName
        
        sink = notation3.ToRDF(self.wfile, dbaddr)

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

    return 'select %s from %s where %s;' % (join(fldnames, ','),
                                            join(tables, ','),
                                            cond)

    

def askdb(db, dbaddr, sink, fields, tables, keys, joins, condextra):
    """ask a query of a database; return an RDF formula.

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

    fmla = something(None, None, 'F')
    c = db.cursor()

    q = asSQL(fields, tables, keys, joins, condextra)
    
    c.execute(q)

    # using table names as namespace names seems to be aesthetic...
    for n in tables:
        sink.bind(n, (RDFSink.SYMBOL, "%s/%s#" % (dbaddr, n)))


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
                        uri = "%s/%s/%s" % (dbaddr, tbl, kv)
                except KeyError:
                    # no, no key supplied for this class/table
                    pass

                if uri: subj = (RDFSink.SYMBOL, uri)
                else:   subj = something(sink, fmla, tbl)

                # remember this for joins...
                things[ti] = subj
                
                # subj rdf:type _tableClass_.
                sink.makeStatement((fmla,
                                    (RDFSink.SYMBOL, notation3.RDF_type_URI),
                                    subj,
                                    (RDFSink.SYMBOL, "%s/%s" % (dbaddr, tbl))
                                    ))


                for fld in fields[ti]:
                    cell = row[col]
                    # @@our mysql implementation happens to use iso8859-1
                    ol = (RDFSink.LITERAL, str(cell).decode('iso8859-1'))

                    # ok... now we have subj, pred and obj...
                    prop = (RDFSink.SYMBOL, "%s/%s#%s" % (dbaddr, tbl, fld))
                    sink.makeStatement((fmla, prop, subj, ol))

                    col = col + 1

                # now relate it to other things...
                for j in range(ti):
                    if joins[ti][j] and things[j]:
                        prop = (RDFSink.SYMBOL, "%s/%s#%s" %
                                (dbaddr, tables[ti], joins[ti][j]))
                        sink.makeStatement((fmla, prop, subj, things[j]))
                        

g=0
def something(sink, scope=None, hint='gensym'):
    global g
    g=g+1
    term = (RDFSink.SYMBOL, '#%s%s' % (hint, g))
    #if scope: sink.makeStatement((scope,
    #(RDFSink.SYMBOL, RDFSink.forSomeSym),
    #scope, term))
    return term




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

    print "as SQL:", asSQL(fields, tables, keys, joins, cond)
    
    sink = notation3.ToRDF(sys.stdout, 'stdout:')

    db=MySQLdb.connect(host=host, port=port,
                       user=user, passwd=passwd,
                       db='administration')

    dbaddr='http://example/administration'
    
    askdb(db, dbaddr, sink,
          fields, tables, keys, joins, cond)

    sink.endDoc()


if __name__ == '__main__':
    testSvc()
    #testUI()
    #testQ()


# $Log$
# Revision 1.9  2002-03-06 05:41:32  connolly
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
