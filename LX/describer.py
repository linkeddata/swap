"""Support classes for Describers (which convert native knowledge into
LX sentences).

"""
__version__ = "$Revision$"
# $Id$

import LX

class DescriptionFailed(Exception):
    pass

class ListDescriber:
    "A describer of python sequences using rdf:first/rest/nil"

    def describe(self, object, ladder):
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
            
        ladder.kb.add(LX.Triple(term, LX.rdfns.first,
                                ladder.describer.describe(first, ladder)))
        ladder.kb.add(LX.Triple(term, LX.rdfns.rest,
                                ladder.describer.describe(rest, ladder)))
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
            print ladder.tracePrefix, "describe a",  type(object), object.__class__
            print ladder.tracePrefix, "value:",  `object`[0:80]
        ##tries = []
        for describer in self.describers:
            dname = describer.__class__.__name__
            try:
                if ladder.has("trace"):
                    print ladder.tracePrefix, dname, "trying..."
                result = describer.describe(object, ladder)
                if result:
                    if ladder.has("trace"):
                        print ladder.tracePrefix, dname, "worked!"
                    return result
            except DescriptionFailed, msg:
                if ladder.has("trace"):
                    print ladder.tracePrefix, dname, "failed", msg
                ##tries.append( (describer,msg), )
        # Ugh!  We failed!   Now try to explain this....
        # (skip most of this unless at depth 0?)
        # ... or just prepend "!  " to ever line in child messages!
        # and don't pay attention to depth
        ##nl = "\n|" + " " * (ladder.depth * 4)
        ##msg = ("\n" + ("="*60) + nl + self.__class__.__name__ +
        ##       " failed at depth " + str(ladder.depth))
        ##msg = msg + nl + "Object is 
        ##msg = msg + nl + "Value is %s " % (`object`[0:60] )
        ##msg = msg + nl + "Describers and their Errors:: "
        ##for (d, m) in tries:
        ##    msg = msg + nl + " " + d.__class__.__name__ + ":" + str(m)
        ##msg = msg + "\n"
        raise DescriptionFailed, "Try turning tracing on"


# $Log$
# Revision 1.2  2002-08-29 16:39:55  sandro
# fixed various early typos and ommissions; working on logic bug which is manifesting in description loops
#
# Revision 1.1  2002/08/29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

 
