#!/bin/env python
"""
dbview -- view an SQL DB thru RDF glasses.

dev notes, links, ...
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
    if scope: sink.makeStatement(scope, RDFSink.forSomeSym, scope, term)
    return term


def bind(pfx, ns):
    print "@prefix %s: <%s>.\n" % (pfx, ns)


def askdb(db, ns, sink, fields, tables, condition):
    scope = something(None, None, 'scope')
    c = db.cursor()
    q='select %s from %s where %s;' % (join(fields, ','), join(tables, ','), condition)
    c.execute(q)

    while 1:
	row=c.fetchone()
	if not row: break
	subj = something(sink, scope, 'ans')
	col = 0
	for ol in row:
	    sink.makeStatement(None,
                               (RDFSink.SYMBOL, "%s%s" % (ns, fields[col])),
                               subj, ol)
	    col = col + 1
    

def testDBView(fp, host, port, user, passwd):
    import notation3
    
    sink = notation3.ToN3(fp, 'stdout:')
    db=MySQLdb.connect(host=host, port=port,
                       user=user, passwd=passwd,
                       db='administration')

    ns='http://example/w3c-admin-db#'
    sink.bind('admin', ns)
    askdb(db, ns, sink,
          ('family', 'city'),
          ('users', 'techplenary2002'),
          'users.id=techplenary2002.id')

def test():
    import sys
    from string import atoi
    
    host, port, user, passwd = sys.argv[1:5]
    
    testDBView(sys.stdout, host, atoi(port), user, passwd)
    
if __name__ == '__main__':
    test()


