#!/usr/bin/env python
"""
Wrap notation3.py as plwm components.   Could go into notation3.py
but I don't want to muck with that right now.

"""

import pluggable
import notation3
import sys

class Parser(pluggable.Parser):

    def __init__(self, sink=None, host=None, copyFrom=None):
        if copyFrom is not None:
            self.sink = copyFrom.sink
            self.host = copyFrom.host
        if sink is not None: self.sink = sink
        if host is not None: self.host = host

    def setSink(self, sink):
        self.sink = sink
        
    def parse(self, stream, host=None):
        #
        # make a new SinkParser each time, because it seems
        # to want to know thisDoc at creation time....
        #
        # @@ what is the difference between SinkParser.thisDoc and
        # SinkParser.baseURI?
        #
        # host is not used yet
        #
        uri = stream.info().uri
        print "Using sink", self.sink
        self.sink.dumpPrefixes(sys.stdout)
        p = notation3.SinkParser(self.sink, uri)
        result = p.loadStream(stream)
        self.sink.top = result    #  possible approach....   We need
        # some way to work around context problem....

class Serializer(pluggable.Serializer, notation3.ToN3):

    def __init__(self, stream, flags):
        apply(notation3.ToN3.__init__, [self, stream.write],
              {"flags": flags})
        

#      r=notation3.SinkParser(notation3.ToN3(sys.stdout.write,
#                                            base='file:output'), 
#                                      thisURI,'http://example.org/base/',)

#                  print notation3.ToN3.flagDocumentation

 
#            _outSink = notation3.ToN3(sys.stdout.write, base=option_baseURI,
#                             quiet=option_quiet, flags=option_flags["n3"])


# needs to move out to PumpNested or something, so we can
# select the different options.   And how long can we
# cheat and do the real work in llyn?   Maybe check to see
# if the store can do it....
class Pump(pluggable.Pump):

    def pump(self, store, ser):
        store.dumpNested(store.top, ser)

    
