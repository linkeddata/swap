"""n3absyn.py -- exploring Notation3 (N3) abstract syntax

Part 1: convert to lisp-ish JSON structure
Part 2: generate lisp s-expression from JSON structure
Part 3: generate XML from JSON structure, following RIF design sketches
Part 4: generate MathML from JSON structure

So far, we handle just the N3-rules subset of N3;
we deal with:
  { ... } => { ... }
but not other occurrences of {}.


References:

 ACL 2 seminar at U.T. Austin: Toward proof exchange in the Semantic Web
 Submitted by connolly on Sat, 2006-09-16
 http://dig.csail.mit.edu/breadcrumbs/node/160

 [RIF] Extensible Design: Horn semantics and syntax actions completed
 Boley, Harold (Thursday, 14 September)
 http://lists.w3.org/Archives/Public/public-rif-wg/2006Sep/thread.html#msg35

 N3 Syntax and Semantics
  a sketch by Dan Connolly
 http://dig.csail.mit.edu/2006/Papers/TPLP/n3absyn.html

 Notation 3 Logic
  a draft by TimBL and others
 http://www.w3.org/DesignIssues/N3Logic




MathML musings...

 import functions and operators from MathML rather than XPath/XQuery? (valueTesting)
 02 Jun 2005
 http://lists.w3.org/Archives/Public/public-rdf-dawg/2005AprJun/0304
  -> http://www.w3.org/2001/sw/DataAccess/mathml-rules.xml

 inference rule markup?
 12 Feb 2001
 http://lists.w3.org/Archives/Public/spec-prod/2001JanMar/0024.html

 Note HELM seems to be still going...
   http://helm.cs.unibo.it/software/index.html

 inference rule markup in W3C specs?
 11 Apr 2002
 http://lists.w3.org/Archives/Public/www-math/2002Apr/0044.html

"""

__version__ = '$Id$'

import sys

from swap import uripath, llyn, formula, term


def main(argv):
    """Usage: n3absyn.py foo.n3 --pprint | --lisp | --rif | --mathml
    --pprint to print the JSON structure using python's pretty printer
    --lisp to print a lisp s-expression for use with ACL2
    --rif for Rule Interchange Format (RIF)
    --mathml for MathML
    """
    path = argv[1]

    addr = uripath.join(uripath.base(), path)
    kb = llyn.RDFStore()
    f = kb.load(addr)

    j = json_formula(f)

    if '--pprint' in argv:
        import pprint
        pprint.pprint(j)
    elif '--lisp' in argv:
        for s in lisp_form(j):
            sys.stdout.write(s)
    elif '--rif' in argv:
        for s in xml_form(j):
            sys.stdout.write(s)
    elif '--mathml' in argv:
        for s in mathml_form(j):
            sys.stdout.write(s)


def json_formula(fmla, vars={}):
    """reduce a swap.formula.Formula to a JSON structure,
    i.e. strings, ints, lists, and dictionaries
    """
    varnames = {}
    varnames.update(vars)
    
    # find distinct names for each variable
    for v in fmla.existentials() | fmla.universals():
        try:
            vn = v.uri
            if '#' in vn: vn = vn.split('#')[1]
        except AttributeError:
            vn = "g%d" % v.serial


        i = 0
        while vn in varnames.values():
            i += 1
            vn = vn + `i`
        varnames[v] = vn

    parts = [] # conjuncts
    for s in fmla: # iterate over statements. hmm.

        # this is the N3rules subset, for now...
        # when we get n3-quote figured out, we can take this special-case out.
        if s.predicate().uriref() == 'http://www.w3.org/2000/10/swap/log#implies':
            
            parts.append(['implies',
                          json_formula(s.subject(), varnames), #@@
                          json_formula(s.object(), varnames)])
        else:
            parts.append(['holds',
                          json_term(s.predicate(), varnames),
                          json_term(s.subject(), varnames),
                          json_term(s.object(), varnames)])

    if len(parts) == 1:
        ret = parts[0]
    else:
        ret = ['and'] + parts
    if fmla.universals():
        ret = ['forall', [varnames[v] for v in fmla.universals()],
               ret]
    if fmla.existentials():
        ret = ['exists', [varnames[v] for v in fmla.existentials()],
               ret]
    return ret


def json_term(t, varmap):
    """reduce a swap.term to a JSON structure,
    i.e. strings, ints, lists, and dictionaries
    """
    if t in varmap:
        return {'var': varmap[t]}
    elif isinstance(t, term.Literal):
        if t.datatype:
            dt = t.datatype.uriref()
            if dt in(DT.integer,
                     DT.nonNegativeInteger):
                return int(t.string)
            if dt == DT.double:
                return float(t.string)
            return ['data', [dt], t.string]
        else:
            return t.string

    elif isinstance(t, term.LabelledNode): # ugh.
        return [t.uriref()]

    # hmm... are lists part of the N3 abstract syntax?
    elif isinstance(t, term.List):
        return ['list'] + [json_term(i, varmap) for i in t]
    elif isinstance(t, formula.Formula):
        return ['n3-quote', json_formula(t, varmap)]
    else:
        raise RuntimeError, "huh? + %s %s" % (t, t.__class__)

def lisp_form(f):
    """generate an s-expression from a formula JSON structure.
    """

    # integer
    if type(f) is type(1):
        yield "%d " % f

    elif type(f) is type(1.1):
        yield "%f " % f

    # string
    elif type(f) in (type(''), type(u'')):
        if "\\" in f or '"' in f:
            raise RuntimeError, 'commonlisp string quoting TODO: %s' % f
        # @@ hmm... non-ascii chars?
        yield '"%s" ' % f

    # variable
    elif type(f) is type({}):
        yield f['var']
        yield ' '

    # compound forms
    elif type(f) is type([]):
        head = f[0]

        # URI, i.e. a 0-ary function symbol
        if ':' in head:
            if '|' in head:
                raise RuntimeError, "quoting | in symbols not yet implemented"
            yield '(URI::|%s|' % head
            assert(len(f) == 1)
            rest = []

        # function symbols
        #@@ interaction of n3-quote with variables needs work.
        elif head in ('holds', 'list', 'data', 'n3-quote'):
            yield '('
            yield head
            yield ' '
            rest = f[1:]

        # connectives
        elif head in ('and', 'implies'):
            yield '('
            yield head
            yield ' '
            rest = f[1:]

        # quantifiers
        elif head in ('exists', 'forall'):
            yield '('
            yield head
            yield ' ('
            for v in f[1]:
                yield v
                yield ' '
            yield ')\n'
            rest = f[2:]

        else:
            raise RuntimeError, 'unimplemented list head: %s' % head
        
        for clause in rest:
            for s in lisp_form(clause):
                yield s
        yield ')\n'

    else:
        raise RuntimeError, 'unimplemented syntactic type: %s %s' % (f, type(f))

    
from xml.sax.saxutils import escape

def xml_form(f):
    """generate XML version of JSON formula f
    see http://www.w3.org/2005/rules/wg/wiki/CORE
    and http://www.w3.org/2005/rules/wg/wiki/B.1_Horn_Rules
    """

    
    # integer
    if type(f) is type(1):
        #@@ I'm making up type; I don't see it in the draft
        yield '<Data type="%s">%d</Data>\n' % (DT.integer, f)

    elif type(f) is type(1.1):
        yield '<Data type="%s">%f</Data>\n' % (DT.double, f)

    # string
    elif type(f) in (type(''), type(u'')):
        yield '<Data>'
        yield escape(f)
        yield '</Data>\n'


    # variable
    elif type(f) is type({}):
        yield "<Var>%s</Var>\n" % f['var']

    # compound forms
    elif type(f) is type([]):
        head = f[0]

        # URI, i.e. a 0-ary function symbol
        if ':' in head:
            assert(len(f) == 1)
            yield '<Ind iri="'
            yield escape(head)
            yield '"/>\n'

        # data
        elif head == 'data':
            assert(len(f) == 3)
            yield '<Data type="%s">' % f[1][0]
            yield escape(f[2])
            yield "</Data>"
            rest = f[1:]

        elif head == 'n3-quote':
            raise RuntimeError, 'n3-quote not yet implemented'

        # list function symbol
        elif head == 'list':
            yield "<Expr><Fun>list</Fun>\n"
            for part in f[1:]:
                for s in xml_form(part):
                    yield s
            yield "</Expr>\n"

        # Atomic formula
        elif head == 'holds':
            yield "<Atom><Rel>holds</Rel>\n"
            for part in f[1:]:
                for s in xml_form(part):
                    yield s
            yield "</Atom>\n"
            
        # connectives
        elif head in ('and', 'implies'):
            tagname = {'and': 'And',
                       'implies': 'Implies'}[head]
            yield "<%s>\n" % tagname
            for part in f[1:]:
                for s in xml_form(part):
                    yield s
            yield "</%s>\n" % tagname
            
        # quantifiers
        elif head == 'exists':
            yield "<Exists>\n"
            for v in f[1]:
                yield "<Var>%s</Var>" % v
            yield '\n'
            for part in f[2:]:
                for s in xml_form(part):
                    yield s
            yield "</Exists>\n"

        elif head == 'forall':
            #@@hmm... treat other vars as implicitly universally quanitified?
            #@@how to assert that we're at the top level?
            for part in f[2:]:
                for s in xml_form(part):
                    yield s

        else:
            raise RuntimeError, 'unimplemented list head: %s' % head
        
    else:
        raise RuntimeError, 'unimplemented syntactic type: %s %s' % (f, type(f))


def mathml_form(f):
    """generate MathML version of JSON formula
    """


    yield '<?xml-stylesheet type="text/xsl" href="http://www.w3.org/Math/XSL/mathml.xsl"?>\n'
    yield '<math xmlns="http://www.w3.org/1998/Math/MathML">\n'
    for s in mathml_fmla(f):
        yield s
    yield "</math>\n"
    
def mathml_fmla(f):
    """generate MathML version of JSON formula
    """
    if type(f) is type([]):
        head = f[0]
        
        if head in ('forall', 'exists'):
            yield "<apply>\n" \
                  "<%s/>\n" % head
            for v in f[1]:
                # per 5 Using definitionURL for Bound Variable Identification.
                # http://www.w3.org/TR/mathml-bvar/#proposal
                yield '<bvar><ci id="%s">%s</ci></bvar>\n' % (v, v)
                
            assert(len(f) == 3)
            for s in mathml_fmla(f[2]):
                yield s
            yield "</apply>\n"

        elif head in ('and', 'implies'):
            yield "<apply><%s/>\n" % head
            for part in f[1:]:
                for s in mathml_fmla(part):
                    yield s
            yield "</apply>\n"

        elif head == 'holds':
            yield "<apply><ci>holds</ci>\n" #@@hmm...
            for part in f[1:]:
                for s in mathml_fmla(part):
                    yield s
            yield "</apply>\n"
        elif ':' in head:
            assert(len(f) == 1)
            u = f[0]
            try:
                ln = u.split("#")[1]
            except IndexError:
                ln = u
            yield '<csymbol definitionURL="'
            yield escape(u)
            yield '" encoding="RDF"><mi>'
            yield escape(ln)
            yield '</mi></csymbol>\n'

        # list function symbol
        elif head == 'list':
            yield "<apply><list/>\n"
            for part in f[1:]:
                for s in mathml_fmla(part):
                    yield s
            yield "</apply>\n"

        else:
            raise RuntimeError, 'unimplemented list head: %s' % head

    # variable
    elif type(f) is type({}):
        v = f['var']
        yield '<ci definitionURL="#%s">%s</ci>\n' % (v, v)

    # integer
    elif type(f) is type(1):
        yield '<cn type="integer">%d</cn>\n' % f

    elif type(f) is type(1.1):
        yield '<cn type="rational">%f</cn>\n' % f

    # string
    elif type(f) in (type(''), type(u'')):
        yield '<ms>'
        yield escape(f)
        yield '</ms>\n'


    else:
        raise RuntimeError, 'unimplemented syntactic type: %s %s' % (f, type(f))

class Namespace(object):
    def __init__(self, nsname):
        self._ns = nsname
    def __getattr__(self, ln):
        return self._ns + ln

DT = Namespace('http://www.w3.org/2001/XMLSchema#')


if __name__ == '__main__':
    main(sys.argv)

