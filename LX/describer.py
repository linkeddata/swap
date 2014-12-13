"""Support classes for Describers (which convert native knowledge into
LX sentences).

"""
__version__ = "$Revision$"
# $Id$

import LX

class DescriptionFailed(Exception):
    pass

class ListDescriber:
    """A describer of python sequences using rdf:first/rest/nil

    """

    def describe(self, object, ladder):

        # for now, let's be strict about it
        if object.__class__ is not [].__class__:
            raise DescriptionFailed, 'not strictly a list'

        # here' a more general approach
        try:
            length = len(object)
            first = object[0]
            rest = object[1:]
        except AttributeError:
            raise DescriptionFailed, 'not a list -- has no __len__'
        except TypeError:
            raise DescriptionFailed, 'not a list -- has no __getitem__'
        except IndexError:
            if ladder.has("term"):
                raise RuntimeError, "FLAG GORE" + str(ladder.__dict__)
                raise (DescriptionFailed,
                       'Cannot describe empty list with a given term')
                # ... unless we use daml:equivalentTo, or some such
            else:
                return LX.rdfns.nil

        if ladder.has("term"):
            term = ladder.term
        else:
            term = ladder.kb.newExistential()
            
        ladder.kb.add(term, LX.rdfns.first,
                      ladder.describer.describe(first, ladder))
        ladder.kb.add(term, LX.rdfns.rest,
                      ladder.describer.describe(rest, ladder))
        return term

class CombinedDescriber:

    def __init__(self, describers):
        self.describers = describers[:]

    def describe(self, object, ladder):
        ladder = ladder.setIfMissing("describer", self)
        if ladder.has("trace"):
            ladder = ladder.setIfMissing("depth", 0)
            ladder = ladder.set("depth", ladder.depth+1)
            ladder = ladder.setIfMissing("tracePrefix", "")
            ladder = ladder.set("tracePrefix", ladder.tracePrefix+"|  ")
            print ladder.tracePrefix, "/", "describe a",  type(object), object.__class__
            print ladder.tracePrefix, "value:",  `object`[0:80]
        for describer in self.describers:
            dname = describer.__class__.__name__
            try:
                if ladder.has("trace"):
                    print ladder.tracePrefix, dname, "trying..."
                result = describer.describe(object, ladder)
                if result is not None:
                    if ladder.has("trace"):
                        print ladder.tracePrefix, "\\", dname, "worked!"
                    return result
                else:
                    if ladder.has("trace"):
                        print ladder.tracePrefix, dname, "failed returning None"
                    # return result
            except DescriptionFailed, msg:
                if ladder.has("trace"):
                    print ladder.tracePrefix, dname, "failed", msg
                continue
            if ladder.has("trace"):
                print ladder.tracePrefix, dname, "did something odd!"
        if ladder.has("trace"):
            print ladder.tracePrefix, "*** All failed, punt back up stack"
            msg = "All available describers failed"
        else:
            msg = "Try turning on tracing"
        raise DescriptionFailed, msg


def _test():
    import doctest, describer
    return doctest.testmod(describer) 

if __name__ == "__main__": _test()

# $Log$
# Revision 1.5  2003-01-29 06:09:18  sandro
# Major shift in style of LX towards using expr.py.  Added some access
# to otter, via --check.  Works as described in
# http://lists.w3.org/Archives/Public/www-archive/2003Jan/0024
# I don't like this UI; I imagine something more like --engine=otter
# --think, and --language=otter (instead of --otterDump).
# No tests for any of this.
#
# Revision 1.4  2002/10/03 16:13:02  sandro
# some minor changes to LX-formula stuff, but it's still broken in ways
# that don't show up on the regression test.
#
# mostly: moved llyn-LX conversion stuff out of llyn.py, into
# LX.engine.llynInterface.py
#
# Revision 1.3  2002/08/29 17:10:38  sandro
# fixed description bug; flatten runs and may even be correct
#
# Revision 1.2  2002/08/29 16:39:55  sandro
# fixed various early typos and ommissions; working on logic bug which is manifesting in description loops
#
# Revision 1.1  2002/08/29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

 
