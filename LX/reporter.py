"""Reporting progress...

util, not LX?

"""
__version__ = "$Revision$"
# $Id$

from sys import stderr
import time

class printReporter:
    """
    Provides a simple indirection for giving status messages, with nesting.

    See timingPrintReporter for timed output.

    >>> import reporter, sys
    >>> pr = printReporter(sys.stdout)
    >>> pr.msg("Hello")
    Hello
    >>> def x():
    ...    pr.begin("Thinking about politics")
    ...    pr.msg("Politics is wonderful")
    ...    pr.msg("Politics is scarey")
    ...    pr.begin("Being scared")
    ...    pr.msg("where can I hide today?")
    ...    pr.end("I'm not scared any more")
    ...    pr.end("-")        # or nothing, but that breaks doctest
    ...    pr.msg("la la la")
    >>> x()
    /  Thinking about politics
    .  Politics is wonderful
    .  Politics is scarey
    .  /  Being scared
    .  .  where can I hide today?
    .  \  I'm not scared any more
    \  -
    la la la



    """
    def __init__(self, stream=stderr):
        self.stream=stream
        self.level = 0
        self.indent = ".  "
        self.t0 = []

    def msg(self, string):
        print >>self.stream, (self.indent*self.level) + string

    def begin(self, string=""):
        print >>self.stream, (self.indent*self.level) + "/  " + string
        self.level += 1
        self.t0.append(time.time())

    def end(self, string=""):
        self.level -= 1
        print >>self.stream, (self.indent*self.level) + "\\  " + string


class nullReporter:
    def __init__(self, stream=stderr):
        pass

    def msg(self, string):
        pass

    def begin(self, string=""):
        pass
    
    def end(self, string=""):
        pass

class timingPrintReporter(printReporter):

   def __init__(self, stream=stderr):
       printReporter.__init__(self, stream)
       self.t0 = []

   def begin(self, string=""):
       printReporter.begin(self, string)
       self.t0.append(time.time())

   def end(self, string=""):
       tmsg = " (after %fs)" % (time.time() - self.t0.pop())
       printReporter.begin(self, string + tmsg)
    

if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])


# $Log$
# Revision 1.1  2003-09-16 16:50:30  sandro
# first draft, passes tests
#
