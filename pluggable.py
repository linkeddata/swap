#!/usr/bin/env python
"""
Declare some basic pluggable interfaces.


Problems:
  we need at least three kinds of sinks:
      triples, quads, and fol

  how does the parser say which kind of sink it can write to?
  

"""

revision = '$Id$'

# Opener?
# Reader?
# Writer?

class NotOverridden(RuntimeError):
    pass

class Parser:
    """
    An active (client) object which reads from a stream and writes to
    a Store.  Our style is to consider the sink/store as an attribute
    of the Parser, set at creation time, and the stream to be parsed
    as a parameter to a parse/load function.   Why?  Well, that's what
    notation3.py and LX/languages/lbase.py both happen to do.

    We don't actually want a constructor here, though.
    """

    def setSink(self, sink):
        raise NotOverridden
    
    def parse(self, stream):
        """Parse the contents of the stream, adding statements to
        the sink (named elsewhere) as discovered.

        The stream should have an info() method for finding out
        metadata, as provided by urllib.urlopen(), but perhaps
        with extra features like the URI.
        """
        raise NotOverridden

class Serializer:
    """
    A passive (server) object which receives content like a Store but
    instead of keeping it, write it out to an output stream.

    is an RDFSink...
    """
    pass
    

class Store:
    """
    A passive repository for structured data.   See KB.
    """
    pass

class Engine:
    """
    A server (passive) object which works with a Store, potentially
    doing complex queries and inference.  See KB.

    Typically Engine functions will be tho
    """
    pass

class KB:
    """
    The combination of a Store and an Engine.  Sometimes it makes more
    sense to treat the pair as one unit; sometimes it makes to
    consider them separately.

    Could be seen as subclassing both Engine and Store, but
    its engine functions don't need to be passed the store.

    Optional parameter?   engine.setStore? 
    """
    pass


class Pump:
    """
    An active (client) object which queries a KB and sends the results
    to a Receiver (Store or Serializer).
    """
    def pump(self, store, serializer):
        raise NotOverridden

class Receiver:
    """
    Something to which you can send structured information.
    [ RDFSink ]
    """
    pass
