"""

Try to make a nice HTML page for this KB

"""
__version__ = "$Revision$"
# $Id$


import LX

#class Serializer(LX.language.abstract.Serializer):

class Serializer:

    def __init__(self):
        # LX.language.abstract.Serializer.__init__(self)
        pass
    
    def serialize(self, kb):
        print "kb"
        
defaultSerializer = Serializer()

def serialize(x):
    return defaultSerializer.serialize(x)

def test():
    s = Serializer()
    
if __name__ =='__main__':
    test()

# $Log: otter.p
    

# $Log$
# Revision 1.1  2003-01-29 06:09:18  sandro
# Major shift in style of LX towards using expr.py.  Added some access
# to otter, via --check.  Works as described in
# http://lists.w3.org/Archives/Public/www-archive/2003Jan/0024
# I don't like this UI; I imagine something more like --engine=otter
# --think, and --language=otter (instead of --otterDump).
# No tests for any of this.
#
#

