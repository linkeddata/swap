#!/bin/env python
"""
uri manipulation, above the access layer

http://www.w3.org/DesignIssues/Model.html

http://www.ietf.org/rfc/rfc2396.txt
"""

__version__ = "$Id$"

from string import find, rfind


def splitFrag(uriref, punct=0):
    i = rfind(uriref, "#")
    if punct:
        if i>= 0: return uriref[:i], uriref[i:]
        else: return uriref, ''
    else:
        if i>= 0: return uriref[:i], uriref[i+1:]
        else: return uriref, None



def pathJoin(here, there):
    """join an absolute URI and URI reference

    here must be an absolute URI.
    there must be a URI reference

    Raise ValueError if there uses relative path
    syntax but here has no hierarchical path.
    """

    assert(find(here, "#") < 0) # caller must splitFrag

    slashl = find(there, '/')
    colonl = find(there, ':')

    # pathJoin(base, 'foo:/') -- absolute
    if colonl >= 0 and (slashl < 0 or colonl < slashl):
        return there

    bcolonl = find(here, ':')
    assert(bcolonl >= 0) # else it's not absolute

    # pathJoin('mid:foo@example', '../foo') bzzt
    if here[bcolonl+1:bcolonl+3] <> '//':
        raise ValueError, here

    bpath = find(here, '/', bcolonl+3)

    # pathJoin('http://xyz', 'foo')
    if bpath < 0:
        bpath = len(here)
        here = here + '/'

    # pathJoin('http://xyz/', '//abc') => 'http://abc'
    if there[:2] == '//':
        return here[:bcolonl+1] + there

    # pathJoin('http://xyz/', '/abc') => 'http://xyz/abc'
    if there[:1] == '/':
        return here[:bpath] + there

    slashr = rfind(here, '/')

    path, frag = splitFrag(there, 1)
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




def test():
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
            act = pathJoin(b, inp)
        except ValueError:
            act = None
        print "sum output" , act
        assert act == exp
        print "pass"
        



if __name__ == '__main__':
    test()
