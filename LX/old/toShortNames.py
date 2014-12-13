#!/usr/local/bin/python
"""
Change any strings like '<http://foo#bar>' into foo_bar,
for certain pre-defined values of "http://foo" and "foo".

Should perhaps do it for other values, too?

$Id$
"""

import sys, string, re

# this should obvious just use a table!

globalTable = {
    "http://www.w3.org/2002/05/positive-triples/pt1":  "pt1_",
    "http://www.w3.org/2002/05/positive-triples/v2": "pt_",
    "http://www.w3.org/2000/01/rdf-schema": "rdfs_",
    "http://www.daml.org/2001/03/daml+oil": "daml_",
    "http://www.w3.org/2002/05/rx/v1":  "rx_",
    "http://www.w3.org/1999/02/22-rdf-syntax-ns": "rdf_",
    "http://www.w3.org/2002/08/LX/RDF/v2": "lx_",
    }

urirefPattern = re.compile(r"\'\<([^#>]*)\#([^>]*)\>\'")
nsCount = 0

def repl(match, table):
    global nsCount
    prefix = match.group(1)
    remainder = match.group(2)
    #print "MATCH:", prefix, remainder
    try:
        return table[prefix] + remainder
    except KeyError:
        table[prefix] = "ns"+str(nsCount)+"_"
        nsCount = nsCount+1
        return table[prefix] + remainder
    
def trans(line, table=globalTable):
    return urirefPattern.sub(lambda m: repl(m, table), line)

if __name__ == "__main__":
    line = sys.stdin.readline()
    while line:
        line = trans(line)
        print line,
        line = sys.stdin.readline()

