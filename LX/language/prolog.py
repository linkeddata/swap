"""


"""
__version__ = "$Revision$"
# $Id$


import LX
import LX.language.abstract

class Serializer(LX.language.abstract.Serializer):

    opTable = {
        # This table come from the otter user manual (not on web)
        LX.OR:        [ 790, "xfy", "; " ],
        LX.AND:       [ 780, "xfy", ", " ],
        }

def test():
    t1 = LX.Term([1])
    t2 = LX.Term([2])
    t3 = LX.Term([3])
    t4 = LX.Term([4])
    s = Serializer()
    print s.serialize((t1 & t2) | t3)
    print s.serialize(t1 & (t2 | t3))
    print s.serialize(t1 & (t2 | t3) | t4)
    print s.serialize(t1 & (t2 | t3 | t4))
    print s.serialize([(t1 & t2) | t3, t1 & (t2 | t3)])
    
if __name__ =='__main__':
    test()

# $Log$
# Revision 1.1  2002-08-29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#
