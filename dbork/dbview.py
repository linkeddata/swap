#!/bin/env python
"""
dbview -- view an SQL DB thru RDF glasses.

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



def testDBView(fp, host, port, user, passwd):
    import notation3
    
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
    
def test():
    import sys
    from string import atoi
    
    host, port, user, passwd = sys.argv[1:5]
    
    testDBView(sys.stdout, host, atoi(port), user, passwd)
    
if __name__ == '__main__':
    test()


