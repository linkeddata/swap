"""KIFSink.py -- a KIF sink for swap/cwm

Share and Enjoy. Open Source license:
Copyright (c) 2001 W3C (MIT, INRIA, Keio)
http://www.w3.org/Consortium/Legal/copyright-software-19980720
$Id$
see log at end

References

  Knowledge Interchange Format
  draft proposed American National Standard (dpANS)
  NCITS.T2/98-004
  http://logic.stanford.edu/kif/dpans.html
  Thu, 25 Jun 1998 22:31:37 GMT
"""

__version__="$Id$"

from string import rfind, split
import re

from ConstTerm import Symbol, StringLiteral


class Sink(object):
    def __init__(self, write):
        self._write = write
        self.prefixes = {}

    def bind(self, pfx, ns):
        w = self._write
        self.prefixes[ns] = pfx
        w('(prefix-kludge "%s" "%s")\n' % (pfx, ns))
        
    def startDoc(self):
        self._map = {} # scopes to (ex, uv, conj) tuples
        self._ancestors = []
        self._root = None # root scope

    def makeComment(self, text):
        for l in split(text, "\n"):
            self._write(";; %s\n" % l)

    def newFormula(self):
        """make a new formula

        Hmm... accept a 'which doc did I come from?' arg?
        """
        f =  Formula()
        if not self._root: self._root = f
        return f

    

    def endDoc(self):
        self._root.write(self._write, self.prefixes)



def writeTerm(w, t, prefixes, vmap, level):
    DEBUG("writing term", t, " at level", level)
    if isinstance(t, Variable):
        n, vl = vmap[t]

        # escape to where the variable is bound
        unquote = level - vl
        if unquote: w(", " * unquote)
        w("%s " % n)
    elif isinstance(t, Symbol):
        w("%s " % withPrefix(t, prefixes))
    elif isinstance(t, Formula):
        w("^ ")
        t.write(w, prefixes, vmap, level + 1)
    elif isinstance(t, StringLiteral):
        lit = re.sub(r'[\"\\]', _escchar, t) # escape newlines? hmm...
        w('"%s"' % lit)
    else:
        raise RuntimeError, "term not implemented: " + str(t)
        

def withPrefix(i, prefixes):
    sep = rfind(i, "#")
    if sep < 0:
        sep = rfind(i, "/")
    if sep >= 0:
        ns, ln = i[:sep+1], i[sep+1:]
        pfx = prefixes.get(ns, None)
        #print "split <%s> before <%s>. pfx: %s" % (i, ln, pfx)
        if pfx is not None:
            return "%s:%s" % (pfx, ln) # ala common lisp package syntax?
    return uri2word(i)


class Formula(object):
    def __init__(self):
        self._ex = []
        self._uv = []
        self._conj = []

    def add(self, p, s, o):
        self._conj.append((p, s, o))

    def mkVar(self, hint, universal = 0):
        v = Variable(hint)
        if universal: self._uv.append(v)
        else: self._ex.append(v)
        return v

    def write(self, w, prefixes, outer={}, level=1):
        ex, uv, conj = self._ex, self._uv, self._conj

        vmap = _moreVarNames(outer, ex + uv, level)

        ind = "  " * level

        if ex:
            w("%s(exists (" % ind)
            for v in ex:
                w("%s " % v.name())
            w(")\n")

        if uv:
            w("%s (forall (" % ind)
            for v in uv:
                w("%s " % v.name())
            w(")\n")

        if len(conj)>1: w("%s  (and\n" % ind)
        for p, s, o in conj:
            w("%s   (holds " % ind)
            writeTerm(w, p, prefixes, vmap, level)
            writeTerm(w, s, prefixes, vmap, level)
            writeTerm(w, o, prefixes, vmap, level)
            w(")\n")
        if len(conj)>1: w("%s  )\n" % ind)

        if uv: w("%s )\n" % ind)
        if ex:w("%s)\n" % ind)
        

class Variable(object):
    _i = 1
    
    def __init__(self, name):
        #@@TODO: make sure this is a good KIF name,
        Variable._i += 1
        self._name = '?%s%s' % (name, Variable._i)

    def name(self):
        return self._name


def uri2word(i):
    # special ::= " | # | ' | ( | ) | , | \ | ^ | ` | :
    return re.sub(r'[\"\#\'\(\)\,\\\^\`\:]', _escchar, i)

def _escchar(matchobj):
    return "\\%s" % matchobj.group(0)
    
def _moreVarNames(outermap, vars, level):
    """Build a mapping from variables to (n, l) pairs
    where n is a KIF variable name and l is the depth of
    the scope where the variable is declared/bound.

    Take care to clash with names already chosen in outermap."""

    m = {}; m.update(outermap)

    for v in vars:
        vname = v.name()
        m[v] = (vname, level)
    return m


def DEBUG(*args):
    import sys
    for a in args:
        sys.stderr.write("%s " % (a,))
    sys.stderr.write("\n")
    


# $Log$
# Revision 1.10  2002-08-13 07:55:15  connolly
# playing with a new parser/sink interface
#
# Revision 1.9  2002/08/07 16:01:23  connolly
# working on datatypes
#
# Revision 1.8  2002/06/21 16:04:02  connolly
# implemented list handling
#
# Revision 1.7  2001/11/27 00:51:59  connolly
# gotta keep popping...
#
# Revision 1.6  2001/11/26 23:53:55  connolly
# fixed bug with scopes nested more than one deep
#
# Revision 1.5  2001/09/19 18:47:57  connolly
# factored RDFSink.py out of notation3.py
#
# introduced SYMBOL to replace notation3.RESOURCE
# introduced forSomeSym, forAllSym to replace N3_forSome_URI, N3_forAll_URI
#
# Revision 1.4  2001/09/11 19:24:22  connolly
# fixed string quoting
# escape just specials in words
# added Open Source license details, log at end
#
