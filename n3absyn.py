"""n3absyn.py -- exploring Notation3 (N3) abstract syntax

Part 1: convert to lisp-ish JSON structure
Part 2: generate ACL2 lisp s-expression from JSON structure
        in progress: IKL s-expressions
Part 3: generate XML from JSON structure, following RIF design sketches
Part 4: generate MathML from JSON structure

So far, we handle just the N3-rules subset of N3;
we deal with:
  { ... } => { ... }
but not other occurrences of {}.


References:

 AI: A Modern Approach by Stuart Russell and Peter Norvig
 AIMA Python file: logic.py Jul 18, 2005
 http://aima.cs.berkeley.edu/python/logic.html

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
    elif '--ikl' in argv:
        for s in ikl_sentence(j, []):
            sys.stdout.write(s)
    elif '--rif' in argv:
        for s in xml_form(j):
            sys.stdout.write(s)
    elif '--mathml' in argv:
        for s in mathml_top():
            sys.stdout.write(s)
        for s in mathml_form(j):
            sys.stdout.write(s)
    elif '--defns' in argv:
        # split top-level N3 constructs
        assert(j[0]) == 'forall'
        assert(j[2][0]) == 'and'

        for s in mathml_top():
            sys.stdout.write(s)

        sys.stdout.write('<html xmlns="http://www.w3.org/1999/xhtml">\n')
        sys.stdout.write('<head><title>defns</title></head>\n')
        sys.stdout.write('<body>\n')
        sys.stdout.write("<ul>\n")
        for expr in j[2][1:]:
            sys.stdout.write("<li>\n")
            for s in mathml_form(expr):
                sys.stdout.write(s)
            sys.stdout.write("</li>\n")
        sys.stdout.write("</ul>\n")
        sys.stdout.write("</body>\n")
        sys.stdout.write("</html>\n")
            


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
            try:
                vn = "g%d" % v.serial
            except AttributeError:
                vn = v.fragid


        i = 0
        while vn in list(varnames.values()):
            i += 1
            vn = vn + repr(i)
        varnames[v] = vn

    parts = [] # conjuncts
    for s in fmla: # iterate over statements. hmm.

        # this is the N3rules subset, for now...
        # when we get n3-quote figured out, we can take this special-case out.
        if s.predicate().uriref() == 'http://www.w3.org/2000/10/swap/log#implies':
            
            parts.append({'op': 'implies',
                          'parts': [json_formula(s.subject(), varnames), #@@
                                   json_formula(s.object(), varnames)]
                          })
        else:
            parts.append({'op': 'holds',
                          'parts': [json_term(s.predicate(), varnames),
                                   json_term(s.subject(), varnames),
                                   json_term(s.object(), varnames)]})

    if len(parts) == 1:
        ret = parts[0]
    else:
        ret = {'op': 'and', 'parts': parts}
    if fmla.universals():
        ret = {'Q': 'forall',
               'Vars': [varnames[v] for v in fmla.universals()],
               'f': ret}
    if fmla.existentials():
        ret = {'Q':'exists',
               'Vars': [varnames[v] for v in fmla.existentials()],
               'f': ret}
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
            return {'op': 'data', 'parts': [{'op': dt}, t.string]}
        else:
            return t.string

    elif isinstance(t, term.LabelledNode): # ugh.
        return {'op': t.uriref()}

    # hmm... are lists part of the N3 abstract syntax?
    elif isinstance(t, term.List):
        return [json_term(i, varmap) for i in t]
    elif isinstance(t, term.N3Set):
        return {'op': 'n3-set', 'parts': [json_term(i, varmap) for i in t]}
    elif isinstance(t, formula.Formula):
        return {'op': 'n3-quote', 'parts': [json_formula(t, varmap)]}
    else:
        raise RuntimeError("huh? + %s %s" % (t, t.__class__))

def lisp_form(f):
    """generate an s-expression from a formula JSON structure.
    """

    # integer
    if type(f) is type(1):
        yield "%d " % f

    elif type(f) is type(1.1):
        yield "%f " % f

    # string
    elif type(f) in (type(''), type('')):
        if "\\" in f or '"' in f:
            raise RuntimeError('commonlisp string quoting TODO: %s' % f)
        # @@ hmm... non-ascii chars?
        yield '"%s" ' % f

    # list
    elif type(f) is type([]):
        yield '(list '
        for expr in f:
            for s in lisp_form(expr):
                yield s
        yield ')\n'


    elif type(f) is type({}):
        # variable
        if 'var' in f:
            yield f['var'] #@@ quoting?
            yield ' '
            return

        elif 'op' in f:
            head = f['op']

            # URI, i.e. a 0-ary function symbol
            if ':' in head:
                if '|' in head:
                    raise RuntimeError("quoting | in symbols not yet implemented")
                yield '(URI::|%s|' % head
                rest = f.get('parts', [])
                assert(len(rest) == 0)

            # function symbols
            #@@ interaction of n3-quote with variables needs work.
            elif head in ('holds', 'data', 'n3-quote'):
                yield '('
                yield head
                yield ' '
                rest = f['parts']

            # connectives
            elif head in ('and', 'implies'):
                yield '('
                yield head
                yield ' '
                rest = f['parts']

        # quantifiers
        elif 'Q' in f:
            head = f['Q']
            yield '('
            yield head
            yield ' ('
            for v in f['Vars']:
                yield v
                yield ' '
            yield ')\n'
            rest = [f['f']]

        else:
            raise RuntimeError('unimplemented list head: %s' % head)
        
        for expr in rest:
            for s in lisp_form(expr):
                yield s
        yield ')\n'

    else:
        raise RuntimeError('unimplemented syntactic type: %s %s' % (f, type(f)))

    
def ikl_sentence(f, subscripts):
    """generate an IKL s-expression from a formula JSON structure.

    IKL Specification Document
    Pat Hayes, IHMC & Chris Menzel, TAMU
    On behalf of the IKRIS Interoperability Group
    rev July 20 2006
    http://www.ihmc.us/users/phayes/IKL/SPEC/SPEC.html
    """

    if 'op' in f:
        head = f['op']

        if head == 'holds':
            yield '('
            yield head
            yield ' '
            for t in f['parts']:
                for s in ikl_term(t, subscripts):
                    yield s
            yield ')\n'
            return

        # connectives
        elif head in ('and', 'implies'):
            if head == 'implies': head = 'if'
            yield '('
            yield head
            yield ' '
            rest = f['parts']

    # quantifiers
    elif 'Q' in f:
        head = f['Q']
        yield '('
        yield head
        yield ' ('
        for v in f['Vars']:
            yield v
            yield ' '
        yield ')\n'
        rest = [f['f']]

    else:
        raise RuntimeError('unimplemented IKL sentence head: %s' % head)

    for expr in rest:
        for s in ikl_sentence(expr, subscripts):
            yield s
    yield ')\n'

    
def ikl_term(f, subscripts):
    """generate an IKL term s-expression from a formula JSON structure.

    """

    # integer
    if type(f) is type(1):
        yield "%d " % f

    elif type(f) is type(1.1):
        #@@refactor ikl_data()?
        yield "(xsd:double %f)" % f #@@long uri form

    # string
    elif type(f) in (type(''), type('')):
        if "\\" in f or '"' in f:
            raise RuntimeError('string quoting TODO: %s' % f)
        if subscripts:
            yield "('%s' " % f # string
            sub = subscripts[0]
            s2 = subscripts[1:]
            if s2:
                for s in ikl_term(sub, s2):
                    yield s
                yield ") "
            else:
                yield "%s) " % sub
        else:
            yield "'%s' " % f

    # list
    elif type(f) is type([]):
        yield '(list '
        for expr in f:
            for s in ikl_term(expr, subscripts):
                yield s
        yield ')\n'


    elif type(f) is type({}):
        # variable.
        if 'var' in f:
            yield f['var'] #@@ quoting?
            yield ' '
            return

        elif 'op' in f:
            head = f['op']

            # URI, i.e. a 0-ary function symbol
            if ':' in head:
                if '"' in head:
                    raise RuntimeError("quoting \" in IKL names not yet implemented")
                if subscripts:
                    for s in ikl_term(head, subscripts):
                        yield s
                else:
                    yield '"%s" ' % head
                rest = f.get('parts', [])
                assert(len(rest) == 0)
                return

            # function symbols
            # data
            elif head == 'data':
                ty, lit = f['args']
                yield '("%s" \'%s\') ' % (ty['op'], lit) #@@ escaping
                return

            elif head == 'n3-set':
                yield '(n3-set '
                rest = f['parts']

            elif head == 'n3-quote':
                yield '(that '
                for s in ikl_sentence(f['parts'][0],
                                      ['c%d' % id(f)] + subscripts):
                    yield s
                yield ') '
                return

        else:
            raise RuntimeError('unimplemented IKL term head: %s' % head)
        
        for expr in rest:
            for s in ikl_term(expr):
                yield s
        yield ')\n'

    else:
        raise RuntimeError('unimplemented syntactic type: %s %s' % (f, type(f)))

    
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
    elif type(f) in (type(''), type('')):
        yield '<Data>'
        yield escape(f)
        yield '</Data>\n'


    # list function symbol
    elif type(f) is type([]):
        yield "<Expr><Fun>list</Fun>\n"
        for part in f:
            for s in xml_form(part):
                yield s
        yield "</Expr>\n"

    elif type(f) is type({}):
        # variable
        if 'var' in f:
            yield "<Var>%s</Var>\n" % f['var']

        elif 'op' in f:
            head = f['op']

            # URI, i.e. a 0-ary function symbol
            if ':' in head:
                assert(len(f.get('args', [])) == 0)
                yield '<Ind iri="'
                yield escape(head)
                yield '"/>\n'

            # data
            elif head == 'data':
                ty, lit = f['args']
                yield '<Data type="%s">' % ty['op']
                yield escape(lit)
                yield "</Data>"

            elif head == 'n3-quote':
                raise RuntimeError('n3-quote not yet implemented')

            # Atomic formula
            elif head == 'holds':
                yield "<Atom><Rel>holds</Rel>\n"
                for part in f.get('parts', []):
                    for s in xml_form(part):
                        yield s
                yield "</Atom>\n"

            # connectives
            elif head in ('and', 'implies'):
                tagname = {'and': 'And',
                           'implies': 'Implies'}[head]
                yield "<%s>\n" % tagname
                for part in f.get('parts', []):
                    for s in xml_form(part):
                        yield s
                yield "</%s>\n" % tagname

        # quantifiers
        elif 'Q' in f:
            tagname = {'exists': 'Exists',
                       'forall': 'Forall', #@@
                       }[f['Q']]

            if tagname == 'Forall':
                #@@hmm... treat other vars as implicitly universally quanitified?
                #@@how to assert that we're at the top level?
                for s in xml_form(f['f']):
                    yield s
            else:
                yield "<%s>\n" % tagname
                for v in f['Vars']:
                    yield "<Var>%s</Var>" % v
                yield '\n'
                for s in xml_form(f['f']):
                    yield s
                yield "</%s>\n" % tagname

        else:
            raise RuntimeError('unimplemented list head: %s' % head)
        
    else:
        raise RuntimeError('unimplemented syntactic type: %s %s' % (f, type(f)))


def mathml_top():
    yield '<?xml version="1.0" ?>'
    # hmm... local or global link?
    #yield '<?xml-stylesheet type="text/xsl" href="http://www.w3.org/Math/XSL/mathml.xsl"?>\n'
    yield '<?xml-stylesheet type="text/xsl" href="mathml.xsl"?>\n'

def mathml_form(f):
    """generate MathML version of JSON formula
    """


    yield '<math xmlns="http://www.w3.org/1998/Math/MathML">\n'
    for s in mathml_fmla(f):
        yield s
    yield "</math>\n"
    
def mathml_fmla(f):
    """generate MathML version of JSON formula
    """
    if type(f) is type([]):
        yield "<list>\n"
        for part in f:
            for s in mathml_fmla(part):
                yield s
        yield "</list>\n"
    elif type(f) is type({}):
        if 'Q' in f:
            q = f['Q']
            yield "<apply>\n" \
                  "<%s/>\n" % q
            for v in f['Vars']:
                # per 5 Using definitionURL for Bound Variable Identification.
                # http://www.w3.org/TR/mathml-bvar/#proposal
                yield '<bvar><ci id="%s">%s</ci></bvar>\n' % (v, v)
                
            for s in mathml_fmla(f['f']):
                yield s
            yield "</apply>\n"

        elif 'op' in f:
            head = f['op']

            if head == 'holds':

                # Not only are we not using a holds predicate,
                # but we're going classes as unary predicates.
                if f['parts'][0]['op'] == RDF.type:
                    args = [f['parts'][2], f['parts'][1]]
                else: args = f['parts']

                yield "<apply>\n"
                for part in args:
                    for s in mathml_fmla(part):
                        yield s
                yield "</apply>\n"
            elif ':' in head:
                assert(len(f.get('parts', [])) == 0)
                u = f['op']
                try:
                    ln = u.split("#")[1]
                except IndexError:
                    ln = u
                yield '<csymbol definitionURL="'
                yield escape(u)
                yield '" encoding="RDF"><mi>'
                yield escape(ln)
                yield '</mi></csymbol>\n'
            else:
                #hmm... n3-quote...
                yield "<apply><%s/>\n" % head
                for part in f.get('parts', []):
                    for s in mathml_fmla(part):
                        yield s
                yield "</apply>\n"

        # variable
        elif 'var' in f:
            v = f['var']
            yield '<ci definitionURL="#%s">%s</ci>\n' % (v, v)

    # integer
    elif type(f) is type(1):
        yield '<cn type="integer">%d</cn>\n' % f

    elif type(f) is type(1.1):
        yield '<cn type="rational">%f</cn>\n' % f

    # string
    elif type(f) in (type(''), type('')):
        yield '<ms>'
        yield escape(f)
        yield '</ms>\n'


    else:
        raise RuntimeError('unimplemented syntactic type: %s %s' % (f, type(f)))

class Namespace(object):
    def __init__(self, nsname):
        self._ns = nsname
    def __getattr__(self, ln):
        return self._ns + ln

DT = Namespace('http://www.w3.org/2001/XMLSchema#')
RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')


if __name__ == '__main__':
    main(sys.argv)

