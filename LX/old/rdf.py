#
# Some quick-hack RDF/n3 stuff
#
#  $Id$

import re, os, string

def uuid():
    s = os.popen('uuidgen -t');
    u = s.readline()
    s.close()
    return u[:-1]

def escape(s):
    result = ""
    for c in s:
        if   c == "\\":  c = "\\\\"
        elif c == "\|":  c = "\\\""
        elif c == "\n":  c = "\\n"
        elif c == "\r":  c = "\\r"
        elif c == "\t":  c = "\\t"
        # @@@ elif outside ascii?
        result = result + c
    return result

def hideApostrophe(s):
    result = ""
    for c in s:
        if   c == "'" or c == "%":  c = "%02x" % ord(x)
        result = result + c
    return result

def unescapeChar(m):
    c = m.group(0)
    # print "Looking at a '"+c+"'"
    if c == "\\\\": return "\\"
    if c == "\\\"": return "\""
    if c == "\\n": return "\n"
    if c == "\\r": return "\r"
    if c == "\\t": return "\t"
    return c

def unescape(s):
    return re.sub(r'\\.', unescapeChar, s)

def n3NameGen(scope):
    val = scope.get("__next", 0)
    while 1:
        name = "_:g%d" % val
        val = val + 1
        if not scope.has_key(name): break
    scope["__next"] = val
    return name

def prologNameGen(scope):
    val = scope.get("__next", 0)
    while 1:
        name = "g%d" % val
        val = val + 1
        if not scope.has_key(name): break
    scope["__next"] = val
    return name
        
class Ident:
    "An RDF (Semantic Web) Identifier"
    def __init__(self):
        self.uri = None
        self.stringValue = None
    def setURI(self, uri):
        "constrain it to identify just that thing"
        assert self.stringValue == None
        assert self.uri == None or self.uri == uri
        self.uri = uri
        return self
    def setStringValue(self, s):
        assert self.stringValue == None or self.stringValue == s
        assert self.uri == None
        self.stringValue=s
        return self
    def skolemize(self):
        assert self.stringValue == None
        assert self.uri == None
        global genidCount
        global runID
        self.uri = "urn:uuid:" + str(runID) + ":" + str(genidCount)
        return self
    def getURI(self):
        return self.uri
    def getStringValue(self):
        return self.stringValue
    def getN3(self, scope):
        if self.stringValue != None:
            return "\"" + escape(self.stringValue) + "\""
        if self.uri != None:
            return "<" + self.uri + ">"
        lr = repr(self)
        if scope.has_key(lr):
            return scope[lr]
        else:
            name = n3NameGen(scope)
            scope[lr] = name
            scope[name] = self
            return name
    def getProlog(self, scope):
        if self.stringValue != None:
            return "\"" + escape(self.stringValue) + "\""
        if self.uri != None:
            return "'<" + self.uri + ">'"
        lr = repr(self)
        if scope.has_key(lr):
            return scope[lr]
        else:
            name = prologNameGen(scope)
            scope[lr] = name
            scope[name] = self
            return name
    def getOtter(self, scope):
        if self.stringValue != None:
            return "'\"" + hideApostrophe(self.stringValue) + "\"'"
        if self.uri != None:
            return "'<" + self.uri + ">'"
        lr = repr(self)
        if scope.has_key(lr):
            return scope[lr]
        else:
            name = prologNameGen(scope)
            scope[lr] = name
            scope[name] = self
            return name

n3uripat = re.compile(r'^\<([^ <>{}]*)\>$')
n3bnodepat = re.compile(r'^_:(.*)$')
n3strpat = re.compile(r'^"(.*)"$')
# ntriple = re.compile(

def getFromN3(term, scope):
    global n3uripat, n3bnodepat, n3strpat
    m = n3uripat.match(term)
    if m:
        i = Ident()
        i.setURI(m.group(1))
        return i;
    m = n3strpat.match(term)
    if m:
        i = Ident()
        i.setStringValue(unescape(m.group(1)))
        return i;
    m = n3bnodepat.match(term)
    if m:
        k = m.group(0)
        if scope.has_key(k): return scope[k]
        i = Ident()
        scope[k] = i;
        scope[i] = k;
        return i
    raise RuntimeError, "Can't parse N3 Term: %s" % term

def read(filename):
    global genidCount
    global runID
    genidCount = 0
    runID = uuid()
    s = os.popen("rdfdump --quiet -o ntriples file:"+filename)
    mapping = { }
    result = []
    while 1:
        line = s.readline()
        if not line: break
        parts = string.split(line[:-3], ' ', 2)
        transparts = map(lambda x: getFromN3(x, mapping), parts);
        result.append(transparts)
    return result

def asNTriples(triples, scope=None):
    if scope == None: scope = {}
    result = ""
    for triple in triples:
        result = result + ( "%s %s %s .\n" % (
                            triple[0].getN3(scope),
                            triple[1].getN3(scope),
                            triple[2].getN3(scope)
                            ) )
    return result

def asProlog(triples, scope=None):
    if scope == None: scope = {}
    result = ""
    for triple in triples:
        result = result + ( "rdf(%s, %s, %s).\n" % (
                            triple[0].getProlog(scope),
                            triple[1].getProlog(scope),
                            triple[2].getProlog(scope)
                            ) )
    return result

def asOtter(triples, scope=None):
    if scope == None: scope = {}
    result = ""
    for triple in triples:
        result = result + ( "rdf(%s, %s, %s).\n" % (
                            triple[0].getOtter(scope),
                            triple[1].getOtter(scope),
                            triple[2].getOtter(scope)
                            ) )
    return result


def test():
    rdf.read("test/abc.rdf")

type = Ident()
type.setURI('http://www.w3.org/1999/02/22-rdf-syntax-ns#type')

rdfns = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
first  = Ident().setURI(rdfns+'first')
rest   = Ident().setURI(rdfns+'rest')
nil    = Ident().setURI(rdfns+'nil')

if __name__ == "__main__":
    test()
