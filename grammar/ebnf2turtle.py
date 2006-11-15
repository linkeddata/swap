"""
bnf2turtle -- write a turtle version of an EBNF grammar
=======================================================

:Author: `Dan Connolly`_
:Version: $Revision$ of $Date$
:Copyright: `W3C Open Source License`_ Share and enjoy.

.. _Dan Connolly: http://www.w3.org/People/Connolly/
.. _W3C Open Source License: http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231

Usage
-----

Invoke a la::

  python bnf2turtle.py foo.bnf pfx uri >foo.ttl

where foo.bnf is full of lines like::

  [1] document ::= prolog element Misc*

as per the `XML formal grammar notation`_. The output is `Turtle`_ -
Terse RDF Triple Language::

  :document rdfs:label "document"; rdf:value "1";
   rdfs:comment "[1] document ::= prolog element Misc*";
    g:seq (
      :prolog
      :element
      [ g:star
        :Misc
       ]
     )
  .


.. _XML formal grammar notation: http://www.w3.org/TR/2004/REC-xml11-20040204/#sec-notation
.. _Turtle: http://www.dajobe.org/2004/01/turtle/


Motivation
----------

Many specifications include grammars that look formal but are not
actually checked, by machine, against test data sets. Debugging the
grammar in the XML specification has been a long, tedious manual
process. Only when the loop is closed between a fully formal grammar
and a large test data set can we be confident that we have an accurate
specification of a language [#]_.


The grammar in the `N3 design note`_ has evolved based on the original
manual transcription into a python recursive-descent parser and
subsequent development of test cases. Rather than maintain the grammar
and the parser independently, our goal_ is to formalize the language
syntax sufficiently to replace the manual implementation with one
derived mechanically from the specification.


.. [#] and even then, only the syntax of the language.
.. _N3 design note: http://www.w3.org/DesignIssues/Notation3

Related Work
------------

Sean Palmer's `n3p announcement`_ demonstrated the feasibility of the
approach, though that work did not cover some aspects of N3.

In development of the `SPARQL specification`_, Eric Prud'hommeaux
developed Yacker_, which converts EBNF syntax to perl and C and C++
yacc grammars. It includes an interactive facility for checking
strings against the resulting grammars.
Yosi Scharf used it in `cwm Release 1.1.0rc1`_, which includes
a SPAQRL parser that is *almost* completely mechanically generated.

The N3/turtle output from yacker is lower level than the EBNF notation
from the XML specification; it has the ?, +, and * operators compiled
down to pure context-free rules, obscuring the grammar
structure. Since that transformation is straightforwardly expressed in
semantic web rules (see bnf-rules.n3_), it seems best to keep the RDF
expression of the grammar in terms of the higher level EBNF
constructs.

.. _goal: http://www.w3.org/2002/02/mid/1086902566.21030.1479.camel@dirk;list=public-cwm-bugs
.. _n3p announcement: http://lists.w3.org/Archives/Public/public-cwm-talk/2004OctDec/0029.html
.. _Yacker: http://www.w3.org/1999/02/26-modules/User/Yacker
.. _SPARQL specification: http://www.w3.org/TR/rdf-sparql-query/
.. _Cwm Release 1.1.0rc1: http://lists.w3.org/Archives/Public/public-cwm-announce/2005JulSep/0000.html
.. _bnf-rules.n3: http://www.w3.org/2000/10/swap/grammar/bnf-rules.n3

Open Issues and Future Work
---------------------------

The yacker output also has the terminals compiled to elaborate regular
expressions. The best strategy for dealing with lexical tokens is not
yet clear. Many tokens in SPARQL are case insensitive; this is not yet
captured formally.

The schema for the EBNF vocabulary used here (``g:seq``, ``g:alt``, ...)
is not yet published; it should be aligned with `swap/grammar/bnf`_
and the bnf2html.n3_ rules (and/or the style of linked XHTML grammar
in the SPARQL and XML specificiations).

It would be interesting to corroborate the claim in the SPARQL spec
that the grammar is LL(1) with a mechanical proof based on N3 rules.

.. _swap/grammar/bnf: http://www.w3.org/2000/10/swap/grammar/bnf
.. _bnf2html.n3: http://www.w3.org/2000/10/swap/grammar/bnf2html.n3  



Background
----------

The `N3 Primer`_ by Tim Berners-Lee introduces RDF and the Semantic
web using N3, a teaching and scribbling language. Turtle is a subset
of N3 that maps directly to (and from) the standard XML syntax for
RDF.



.. _N3 Primer: _http://www.w3.org/2000/10/swap/Primer.html




Colophon
--------

This document is written in ReStructuredText_. The examples
in the docstrings below are executable doctest_ unit tests.
Check them a la::

  python bnf2turtle.py --test


.. _ReStructuredText: http://docutils.sourceforge.net/docs/user/rst/quickstart.html
.. _doctest: http://www.python.org/doc/lib/module-doctest.html

"""

__version__ = "$Id$"

import re

def main(argv):
    data, pfx, lang, ns = argv[1:]
    toTurtle(file(data), pfx, ns, lang)
        

def toTurtle(lines, pfx, ns, lang):
    """print a turtle version of the lines of a BNF file
    """
    
    started = False
    token = False
    for r in eachRule(lines):
        if r.strip() == '@terminals': token = True
        else:
            num, sym, expr = ruleParts(r)
            if not started:
                startTurtle(pfx, ns, lang, sym)
                started = True
            # all caps symbols are tokens
            if re.match("[A-Z_]+$", sym): token = True
            asTurtle(num, sym, expr, token, r)


def eachRule(lines):
    """turn an iterator over lines into an iterator over rule strings.

    a line that starts with [ and a digit or @ starts a new rule
    """
    
    r = ''
    for l in lines:
        l = l.strip()
        if l.startswith("/*"): continue # whole-line comments only
        if re.match(r"^\[\d\w*\]", l) or l.startswith('@'):
            if r: yield r
            r = l
        else:
            if r: r += ' '
            r += l
    if r: yield r


def ruleParts(r):
    """parse a rule into a rule number, a symbol, and an expression

    >>> ruleParts("[2]     Prolog    ::=           BaseDecl? PrefixDecl*")
    ('2', 'Prolog', (',', [('?', ('id', 'BaseDecl')), ('*', ('id', 'PrefixDecl'))]))

    """
    
    assert r.find(']') > 0
    num, r = r.split(']', 1)
    num = num[1:]
    rhs, r = r.split('::=', 1)
    rhs = rhs.strip()
    return (num, rhs, ebnf(r)[0])


def ebnf(s):
    """parse a string into an expression tree and a remaining string

    >>> ebnf("a b c")
    ((',', [('id', 'a'), ('id', 'b'), ('id', 'c')]), '')

    >>> ebnf("a? b+ c*")
    ((',', [('?', ('id', 'a')), ('+', ('id', 'b')), ('*', ('id', 'c'))]), '')

    >>> ebnf(" | x xlist")
    (('|', [(',', []), (',', [('id', 'x'), ('id', 'xlist')])]), '')

    >>> ebnf("a | (b - c)")
    (('|', [('id', 'a'), ('-', [('id', 'b'), ('id', 'c')])]), '')

    >>> ebnf("a b | c d")
    (('|', [(',', [('id', 'a'), ('id', 'b')]), (',', [('id', 'c'), ('id', 'd')])]), '')
    
    >>> ebnf("a | b | c")
    (('|', [('id', 'a'), ('id', 'b'), ('id', 'c')]), '')
    
    >>> ebnf("a) b c")
    (('id', 'a'), ' b c')
    
    >>> ebnf("BaseDecl? PrefixDecl*")
    ((',', [('?', ('id', 'BaseDecl')), ('*', ('id', 'PrefixDecl'))]), '')

    >>> ebnf("NCCHAR1 | '-' | [0-9] | #x00B7 | [#x0300-#x036F] | [#x203F-#x2040]")
    (('|', [('id', 'NCCHAR1'), ("'", '-'), ('[', '0-9'), ('#', '#x00B7'), ('[', '#x0300-#x036F'), ('[', '#x203F-#x2040')]), '')
    """

    # " help emacs

    e, s = alt(s)
    if s:
        t, ss = token(s)
        if t[0] == ')':
            return e, ss
    return e, s


def alt(s):
    """parse alt

    >>> alt("a | b | c")
    (('|', [('id', 'a'), ('id', 'b'), ('id', 'c')]), '')

    """

    args = []
    while s:
        e, s = seq(s)
        if not e:
            if args: break
            e = (',', []) # empty sequence
        args.append(e)
        if s:
            t, ss = token(s)
            if not t[0] == '|': break
            s = ss
    if len(args) > 1:
        return ('|', args), s
    else:
        return e, s


def seq(s):
    """parse seq

    >>> seq("a b c")
    ((',', [('id', 'a'), ('id', 'b'), ('id', 'c')]), '')

    >>> seq("a b? c")
    ((',', [('id', 'a'), ('?', ('id', 'b')), ('id', 'c')]), '')

    """

    args = []
    while s:
        e, ss = diff(s)
        if e:
            args.append(e)
            s = ss
        else: break
    if len(args) > 1:
        return (',', args), s
    elif len(args) == 1:
        return args[0], s
    else:
        return None, s


def diff(s):
    """parse diff

    >>> diff("a - b")
    (('-', [('id', 'a'), ('id', 'b')]), '')

    """

    e1, s = postfix(s)
    if e1:
        if s:
            t, ss = token(s)
            if t[0] == '-':
                s = ss
                e2, s = primary(s)
                if e2:
                    return ('-', [e1, e2]), s
                else:
                    raise SyntaxError
            
    return e1, s


def postfix(s):
    """parse postfix

    >>> postfix("a b c")
    (('id', 'a'), ' b c')

    >>> postfix("a? b c")
    (('?', ('id', 'a')), ' b c')
    """

    e, s = primary(s)
    if not e: return None, s

    if s:
        t, ss = token(s)
        if t[0] in '?*+':
            return (t[0], e), ss
        
    return e, s

def primary(s):
    """parse primary

    >>> primary("a b c")
    (('id', 'a'), ' b c')
    """

    t, s = token(s)
    if t[0] == 'id' or t[0] == "'" or t[0] == '[' or t[0] == '#':
        return t, s

    elif t[0] is '(':
        e, s = ebnf(s)
        return e, s

    else:
        return None, s


def token(s):
    """parse one token; return the token and the remaining string

    A token is represented as a tuple whose 1st item gives the type;
    some types have additional info in the tuple.
    
    >>> token("'abc' def")
    (("'", 'abc'), ' def')

    >>> token("[0-9]")
    (('[', '0-9'), '')
    >>> token("#x00B7")
    (('#', '#x00B7'), '')
    >>> token ("[#x0300-#x036F]")
    (('[', '#x0300-#x036F'), '')
    >>> token("[^<>'{}|^`]-[#x00-#x20]")
    (('[', "^<>'{}|^`"), '-[#x00-#x20]')
    """
    # '" help emacs

    s = s.strip()
    if s.startswith("'"):
        l, s = s[1:].split("'", 1)
        return ("'", l), s
    elif s.startswith('"'):
        l, s = s[1:].split('"', 1)
        return ("'", l), s
    elif s.startswith("["):
        l, s = s[1:].split("]", 1)
        return ("[", l), s
    elif s.startswith("#"):
        i = re.match("\w+", s[1:]).end(0) + 1
        return (('#', s[:i]), s[i:])
    elif s[0].isalpha():
        i = re.match("\w+", s).end(0)
        return (('id', s[:i]), s[i:])
    elif s.startswith("@"):
        i = re.match("\w+", s[1:]).end(0) + 1
        return (('@', s[1:i]), s[i:])
    elif s[0] in '(?)*+|-':
        return ((s[0],) , s[1:])
    else:
        raise ValueError, "unrecognized token: %s" % s


##########
# turtle generation
#

def startTurtle(pfx, ns, lang, start):
    print "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>."
    print "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>."
    print "@prefix %s: <%s>." % (pfx, ns)
    print "@prefix : <%s>." % ns
    print "@prefix re: <http://www.w3.org/2000/10/swap/grammar/regex#>."
    print "@prefix g: <http://www.w3.org/2000/10/swap/grammar/ebnf#>."
    print
    print ":%s rdfs:isDefinedBy <>; g:start :%s." % (lang, start)
    
def asTurtle(num, sym, expr, isToken, orig):
    print
    print ':%s rdfs:label "%s"; rdf:value "%s";' % (sym, sym, num)
    print ' rdfs:comment "%s";' % esc(orig.strip())

    if isToken: pfx = 're'
    else: pfx = 'g'

    ttlExpr(expr, pfx, indent='  ', obj=0)
    print "."


def ttlExpr(expr, pfx, indent, obj=1):
    op, args = expr

    if obj:
        bra = "[ "
        ket = " ]"
    else:
        bra = ket = ''

    if op == ',':
        print indent + bra + "%s:seq (" % pfx
        for a in args:
            ttlExpr(a, pfx, indent + '  ')
        print indent + " )" + ket

    elif op == '|':
        print indent + bra + "%s:alt (" % pfx
        for a in args:
            ttlExpr(a, pfx, indent + '  ')
        print indent + " )" + ket

    elif op == '-':
        print indent + bra + "%s:diff (" % pfx
        for a in args:
            ttlExpr(a, pfx, indent + '  ')
        print indent + " )" + ket

    elif op == '?':
        print indent + bra + "%s:opt " % pfx
        ttlExpr(args, pfx, indent + '  ')
        if ket: print indent + ket

    elif op == '+':
        print indent + bra + "%s:plus " % pfx
        ttlExpr(args, pfx, indent + '  ')
        if ket: print indent + ket

    elif op == '*':
        print indent + bra + "%s:star " % pfx
        ttlExpr(args, pfx, indent + '  ')
        if ket: print indent + ket

    elif op == 'id':
        if obj:
            print "%s:%s" % (indent, args)
        else:
            print "%sg:seq ( :%s )" % (indent, args)
    elif op == "'":
        print '%s"%s"' %(indent, esc(args))
    elif op == "[":
        print '%s%s re:matches "[%s]" %s' % (indent, bra, cclass(args), ket)
    elif op == "#":
        assert not('"' in args)
        print r'%s%s re:matches "[%s]" %s' % (indent, bra, cclass(args), ket)
    else:
        raise RuntimeError, op


def cclass(txt):
    r"""turn an XML BNF character class into an N3 literal for that
    character class (less the outer quote marks)
    
    >>> cclass("^<>'{}|^`")
    "^<>'{}|^`"
    >>> cclass("#x0300-#x036F")
    '\\u0300-\\u036F'
    >>> cclass("#xC0-#xD6")
    '\\u00C0-\\u00D6'
    >>> cclass("#x370-#x37D")
    '\\u0370-\\u037D'

    as in: ECHAR ::= '\' [tbnrf\"']
    >>> cclass("tbnrf\\\"'")
    'tbnrf\\\\\\"\''


    >>> cclass("^#x22#x5C#x0A#x0D")
    '^\\u0022\\\\\\u005C\\u000A\\u000D'
    """
    # '" help out emacs

    hexpat = re.compile("#x[0-9a-zA-Z]+")
    ret = ''
    txt=esc(txt)
    while 1:
        m = hexpat.search(txt)
        if not m:
            return ret + txt
        ret += txt[:m.start(0)]
        hx = m.group(0)[2:]
        if len(hx) < 6: hx = ("0000" + hx)[-4:]
        elif len(hx) < 10: hx = ("0000" + hx)[-8:]

        # This is just about hopelessly ugly
        if unichr(int(hx, 16)) in "\\[]": ret += '\\\\'

        if len(hx) == 4: ret += r"\u" + hx
        elif len(hx) == 8: ret += r"\U" + hx
        else:
            raise ValueError, "#x must preceede 1 to 8 hex digits"
        txt = txt[m.end(0):]


def esc(st):
    r"""turn a string into an N3 string literal for that string,
    without the outer quote marks.

    >>> esc(r'abc')
    'abc'

    >>> esc(r'[^"\\]')
    '[^\\"\\\\\\\\]'

    """
    
    if not ('"' in st or '\\' in st): return st
    s = ''
    for c in st:
        if c == '"' or c == '\\':
            s += '\\'
        s += c
    return s


def _test():
    import doctest
    doctest.testmod()

    
if __name__ == '__main__':
    import sys
    if '--test' in sys.argv: _test()
    else: main(sys.argv)

# $Log$
# Revision 1.11  2006-11-15 19:59:25  connolly
# change rep to plus, eps to empty
#
# Revision 1.10  2006/06/21 00:53:31  connolly
# added a special case for #x5c (\) in rehex/cclass
#
# Revision 1.9  2006/06/20 23:26:29  connolly
# regex escaping details. ugh!
#
# Revision 1.8  2006/06/20 21:12:05  connolly
# change terminal, nonterminal from classes to relationships to languages
# add command-line arg for name of language
# move :matches from EBNF to regex ns
#
# Revision 1.7  2006/06/20 08:21:52  connolly
# strip trailing space from rdfs:comment
#
# Revision 1.6  2006/06/20 08:18:39  connolly
# more line-splitting fixes
#
# Revision 1.5  2006/06/20 05:59:10  connolly
# properly escape #xNN notation in regex's
# join lines with a space to avoid merging tokens
#
# Revision 1.4  2006/06/20 04:57:16  connolly
# all caps symbol signals a switch to terminals
#
# Revision 1.3  2006/06/20 04:43:10  connolly
# be more discriminating about breaking lines in order to handle
# Andy's turtle.html bnf
#
# Revision 1.2  2006/06/17 05:27:41  connolly
# use separate namespaces for g:seq and re:seq
# move --test arg check out of main
#
# Revision 1.1  2006/06/16 15:35:28  connolly
# move bnf2turtle here; make a real EBNF ontology and use it
#
# Revision 1.14  2006/06/10 05:24:26  connolly
# handle empty alternative (at start of production, at least)
# handle /* */ comments (whole-line only)
# change unrecognized token from RuntimeError to ValueError
#
# Revision 1.13  2006/02/10 06:02:05  connolly
# updated doctest: rule labels are numerals, not ints
#
# Revision 1.12  2006/02/10 05:57:42  connolly
# document --test flag
#
# Revision 1.11  2006/02/10 05:56:23  connolly
# citing sources and such done-ish. rst sorta working
#
# Revision 1.10  2006/02/10 02:51:35  connolly
# added a license
# moved main to top
# started citing sources, trying to use rst; losing
#
# Revision 1.9  2006/02/09 23:19:14  connolly
# handle a ::= b rules
# RDF housekeeping: comment, label, namespaces
#
# Revision 1.8  2006/02/09 22:51:49  connolly
# include original rules as comments
# indentation tweaks
#
# Revision 1.7  2006/02/09 22:32:08  connolly
# fixed bug in diff
#
# Revision 1.6  2006/02/09 22:29:38  connolly
# precedence parsing unit tests pass
#
# Revision 1.5  2006/02/09 21:29:39  connolly
# docstrings with unit tests
#
# Revision 1.4  2006/02/09 21:02:07  connolly
# generates ttl that cwm parses
#
# Revision 1.3  2006/02/09 20:45:43  connolly
# walking and generating indented turtle sorta works;
# some high level turtle syntax errors to work out
#
# Revision 1.2  2006/02/09 19:23:03  connolly
# seems to be parsed
#
# Revision 1.1  2006/02/09 18:46:20  connolly
# seems to tokenize ok
#

