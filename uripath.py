#!/bin/env python
"""
Uniform Resource Identifier (URI) manipulation,
above the access layer

cf.

* URI API design [was: URI Test Suite] Dan Connolly (Sun, Aug 12 2001)
http://lists.w3.org/Archives/Public/uri/2001Aug/0021.html

http://www.w3.org/DesignIssues/Model.html

http://www.ietf.org/rfc/rfc2396.txt

The name of this module and the functions are somewhat
arbitrary; they hark to other parts of the python
library; e.g. uripath.join() is somewhat like os.path.join().

"""

__version__ = "$Id$"

from string import find, rfind, index


def splitFrag(uriref):
    """split a URI reference between the fragment and the rest.

    Punctuation is thrown away.
    
    e.g. splitFrag("abc#def") = ("abc", "def")
    and splitFrag("abcdef") = ("abcdef", None)
    """
    i = rfind(uriref, "#")
    if i>= 0: return uriref[:i], uriref[i+1:]
    else: return uriref, None

def splitFragP(uriref, punct=0):
    """split a URI reference before the fragment

    Punctuation is kept.
    
    e.g. splitFrag("abc#def") = ("abc", "#def")
    and splitFrag("abcdef") = ("abcdef", "")
    """
    i = rfind(uriref, "#")
    if i>= 0: return uriref[:i], uriref[i:]
    else: return uriref, ''


def join(here, there):
    """join an absolute URI and URI reference

    here must be an absolute URI.
    there must be a URI reference

    Raise ValueError if there uses relative path
    syntax but here has no hierarchical path.
    """

    assert(find(here, "#") < 0) # caller must splitFrag

    slashl = find(there, '/')
    colonl = find(there, ':')

    # join(base, 'foo:/') -- absolute
    if colonl >= 0 and (slashl < 0 or colonl < slashl):
        return there

    bcolonl = find(here, ':')
    assert(bcolonl >= 0) # else it's not absolute

    # join('mid:foo@example', '../foo') bzzt
    if here[bcolonl+1:bcolonl+3] <> '//':
        raise ValueError, here

    bpath = find(here, '/', bcolonl+3)

    # join('http://xyz', 'foo')
    if bpath < 0:
        bpath = len(here)
        here = here + '/'

    # join('http://xyz/', '//abc') => 'http://abc'
    if there[:2] == '//':
        return here[:bcolonl+1] + there

    # join('http://xyz/', '/abc') => 'http://xyz/abc'
    if there[:1] == '/':
        return here[:bpath] + there

    slashr = rfind(here, '/')

    path, frag = splitFragP(there)
    if not path: return here + frag
    
    while 1:
        if path[:2] == './':
            path = path[2:]
        if path == '.':
            path = ''
        elif path[:3] == '../' or path == '..':
            path = path[3:]
            i = rfind(here, '/', bpath, slashr)
            if i >= 0:
                here = here[:i+1]
                slashr = i
        else:
            break

    return here[:slashr+1] + path + frag


def refTo(src, dest):
    """compute a path from one URI to another

    both src and dest are absolute URI references
    """

    scolon = index(src, ':')
    dcolon = index(dest, ':')

    # refTo("foo:xyz", "bar:abc") => "bar:abc"
    if src[scolon+1:scolon+3] == '//' and \
       src[:scolon+3] <> dest[:dcolon+3]: return dest


    src, dummy = splitFrag(src)
    
    # http://example/x/y/z - http://example/x/abc = ../abc
    slashr = rfind(src, '/', scolon+3)
    dots = ''
    while slashr > scolon:
        if src[:slashr] == dest[:slashr]:
            return dots + dest[slashr+1:]

        i = rfind(src, '/', scolon+3, slashr)
        if i >= i: slashr = i
        else: break

        if dots: dots = '../' + dots
        else: dots = '../'

    return dest


def test():
    cases = (("foo:xyz", "bar:abc", "bar:abc"),
             ('http://example/x/y/z', 'http://example/x/abc', '../abc'),
             ('http://example2/x/y/z', 'http://example/x/abc', 'http://example/x/abc'),
             ('http://ex/x/y/z', 'http://ex/r', '../../r'),
             ('http://ex/x/y', 'http://ex/x/q/r', 'q/r'),
             ('http://ex/x/y', 'http://ex/x/q/r#s', 'q/r#s'),
             ('http://ex/x/y', 'http://ex/x/q/r#s/t', 'q/r#s/t'),
             ('http://ex/x/y', 'ftp://ex/x/q/r', 'ftp://ex/x/q/r'),
             ('http://ex/x/y', 'http://ex/x/y', 'y'),
             ('http://ex/x/y/', 'http://ex/x/y/', ''),
             ('http://ex/x/y/', 'http://ex/x/y/z/', 'z/'),
             )

    for inp1, inp2, exp in cases:
        print "refTo input", inp1, " -> ", inp2
        act = refTo(inp1, inp2)
        print "result:", act, " =?= ", exp
        assert act == exp
        assert join(inp1, act) == inp2
        print "pass"
        
    cases = (
        ("abc#def", "abc", "def"),
        ("abc", "abc", None),
        ("#def", "", "def"),
        ("", "", None),
        ("abc#de:f", "abc", "de:f"),
        ("abc#de?f", "abc", "de?f"),
        ("abc#de/f", "abc", "de/f"),
        )
    for inp, exp1, exp2 in cases:
        print "splitFrag input", inp
        act1, act2 = splitFrag(inp)
        assert act1 == exp1 and act2 == exp2
        print "pass"
        

    base = 'http://a/b/c/d;p?q'

    # C.1.  Normal Examples

    normalExamples = (
        (base, 'g:h', 'g:h'),
        (base, 'g', 'http://a/b/c/g'),
        (base, './g', 'http://a/b/c/g'),
        (base, 'g/', 'http://a/b/c/g/'),
        (base, '/g', 'http://a/g'),
        (base, '//g', 'http://g'),
        (base, '?y', 'http://a/b/c/?y'), #@@wow... really?
        (base, 'g?y', 'http://a/b/c/g?y'),
        (base, '#s', 'http://a/b/c/d;p?q#s'), #@@ was: (current document)#s
        (base, 'g#s', 'http://a/b/c/g#s'),
        (base, 'g?y#s', 'http://a/b/c/g?y#s'),
        (base, ';x', 'http://a/b/c/;x'),
        (base, 'g;x', 'http://a/b/c/g;x'),
        (base, 'g;x?y#s', 'http://a/b/c/g;x?y#s'),
        (base, '.', 'http://a/b/c/'),
        (base, './', 'http://a/b/c/'),
        (base, '..', 'http://a/b/'),
        (base, '../', 'http://a/b/'),
        (base, '../g', 'http://a/b/g'),
        (base, '../..', 'http://a/'),
        (base, '../../', 'http://a/'),
        (base, '../../g', 'http://a/g')
        )

    otherExamples = (
        (base, '', base),
        (base, '../../../g', 'http://a/g'), #@@disagree with RFC2396
        (base, '../../../../g', 'http://a/g'), #@@disagree with RFC2396
        (base, '/./g', 'http://a/./g'),
        (base, '/../g', 'http://a/../g'),
        (base, 'g.', 'http://a/b/c/g.'),
        (base, '.g', 'http://a/b/c/.g'),
        (base, 'g..', 'http://a/b/c/g..'),
        (base, '..g', 'http://a/b/c/..g'),

        (base, './../g', 'http://a/b/g'),
        (base, './g/.', 'http://a/b/c/g/.'), #@@hmmm...
        (base, 'g/./h', 'http://a/b/c/g/./h'), #@@hmm...
        (base, 'g/../h', 'http://a/b/c/g/../h'),
        (base, 'g;x=1/./y', 'http://a/b/c/g;x=1/./y'), #@@hmmm...
        (base, 'g;x=1/../y', 'http://a/b/c/g;x=1/../y'),  #@@hmmm...

        (base, 'g?y/./x', 'http://a/b/c/g?y/./x'),
        (base, 'g?y/../x', 'http://a/b/c/g?y/../x'),
        (base, 'g#s/./x', 'http://a/b/c/g#s/./x'),
        (base, 'g#s/../x', 'http://a/b/c/g#s/../x')
        )

    moreExamples = (
        ('mid:foo@example', '../foo', None),
        )

    for b, inp, exp in normalExamples + otherExamples + moreExamples:
        print "sum input", b, " + ", inp
        try:
            act = join(b, inp)
        except ValueError:
            act = None
        print "sum output" , act
        assert act == exp
        print "pass"
        



if __name__ == '__main__':
    test()


# $Log$
# Revision 1.1  2002-02-19 22:52:42  connolly
# renamed uritools.py to uripath.py
#
# Revision 1.2  2002/02/18 07:33:51  connolly
# pathTo seems to work
#
