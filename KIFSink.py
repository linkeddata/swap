"""KIFSink.n3 -- a KIF sink for cwm

"""
__version__="$Id$"

from string import rfind

import notation3 #@@ better name for the KB parse/sink interface?

class Sink(notation3.RDFSink):
    def __init__(self, write):
        notation3.RDFSink.__init__(self)
        self._write = write

    def bind(self, pfx, nspr):
        notation3.RDFSink.bind(self, pfx, nspr)

        x, ns = nspr
        w = self._write
        w('(prefix "%s" "%s")\n' % (pfx, ns))
        
    def startDoc(self):
        self._ex = []
        self._uv = []
        self._conj = []
        self._map = {} # scopes to (ex, uv, conj) tuples
        self._parents = {} # scopes to parent scopes
        self._root = None # root scope
        self._scope = None # current scope
        self._depth = None # scope depth

    def makeStatement(self, cpso):
        c, p, s, o = cpso

        if self._scope <> c[1]:
            self._setScope(c[1])

        if s == (notation3.FORMULA, self._scope):
            if p[1] == notation3.N3_forSome_URI:
                if o[0] is notation3.RESOURCE:
                    self._ex.append(o[1])
                return
            elif p[1] == notation3.N3_forAll_URI:
                self._uv.append(o[1])
                return

        self._conj.append((p, s, o)) #@@pairs?


    def _setScope(self, c):
        if self._root is None:
            self._root = self._scope = c
            self._parent = None
            self._ex, self._uv, self._conj = [], [], []
        else:
            self._map[self._scope] = (self._ex, self._uv, self._conj)

            if c == self._parent: # popping out of a scope
                self._parent = self._parents[self._scope]
                euc = self._map[c]
                self._ex, self._uv, self._conj = euc
            else: # pushing into a new scope
                self._parent = self._scope
                self._parents[c] = self._scope # GC cycle?
                self._ex, self._uv, self._conj = [], [], []
            self._scope = c


    def endDoc(self):
        self._map[self._scope] = (self._ex, self._uv, self._conj)
        self._writeScope(self._root)


    def _writeScope(self, scope, outer={}, level=1):
        ex, uv, conj = self._map[scope]
        w = self._write

        vmap = _moreVarNames(outer, ex + uv, level)

        ind = "  " * level

        if ex:
            w("%s(exists (" % ind)
            for v in ex:
                w("%s " % vmap[v][0])
            w(")\n")

        if uv:
            w("%s (forall (" % ind)
            for v in uv:
                w("%s " % vmap[v][0])
            w(")\n")

        if len(conj)>1: w("%s  (and\n" % ind)
        for p, s, o in conj:
            w("%s   (" % ind)
            self._writeTerm(p, vmap, level)
            self._writeTerm(s, vmap, level)
            self._writeTerm(o, vmap, level)
            w(")\n")
        if len(conj)>1: w("%s  )\n" % ind)

        if uv: w("%s )\n" % ind)
        if ex:w("%s)\n" % ind)
        
    def _writeTerm(self, t, vmap, level):
        w = self._write
        if t[0] is notation3.RESOURCE:
            nvl = vmap.get(t[1], None)

            if nvl:
                n, vl = nvl
                # escape to where the variable is bound
                unquote = level - vl
                if unquote: w(", " * unquote)
                w("%s " % n)
            else:
                w("%s " % self.withPrefix(t))
        elif t[0] is notation3.FORMULA:
            w("^ ")
            self._writeScope(t[1], vmap, level + 1)
        elif t[0] is notation3.LITERAL:
            w('"%s"' % t[1]) #@@ quoting
        else:
            raise RuntimeError, "not implemented"
        
    def withPrefix(self, pair):
        i = pair[1]
        sep = rfind(i, "#")
        if sep >= 0:
            ns, ln = i[:sep+1], i[sep+1:]
            pfx = self.prefixes.get((pair[0], ns), None)
            #print "split <%s> before <%s>. pfx: %s" % (i, ln, pfx)
            if pfx is not None:
                return "%s__%s" % (pfx, ln) #hmm... kludge?
        return i

def _moreVarNames(outermap, uris, level):
    """Build a mapping from URIs to (n, l) pairs
    where n is a KIF variable name and l is the depth of
    the scope where the variable is declared/bound.

    Take care to clash with names already chosen in outermap."""

    m = {}; m.update(outermap)

    for i in uris:
        for sepchar in '#/?:': # one of these has to occur in any full URI...
            sep = rfind(i, sepchar)
            if sep >= 0:
                vname = '?%s' % i[sep+1:]
                while vname in m.values():
                    vname = vname + "x"
                m[i] = (vname, level)
                break
    return m

