"""Reporting progress...

util, not LX?

"""
__version__ = "$Revision$"
# $Id$

from sys import stderr
import time
from html import xstr

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
        self.write((self.indent*self.level) + string)

    def begin(self, string=""):
        self.write((self.indent*self.level) + "/  " + string)
        self.level += 1

    def end(self, string=""):
        self.level -= 1
        self.write((self.indent*self.level) + "\\  " + string)

    def write(self, string):
        self.stream.write(string+"\n")
        self.stream.flush()

class nullReporter:
    def __init__(self, stream=stderr):
        pass

    def msg(self, string):
        pass

    def begin(self, string=""):
        pass
    
    def end(self, string=""):
        pass

theNullReporter = nullReporter()

class timingPrintReporter(printReporter):

   # Alas, I can't really do doctests on this, because the
   # timing results keep changing...
   
   def __init__(self, stream=stderr):
       printReporter.__init__(self, stream)
       self.t0 = []

   def begin(self, string=""):
       printReporter.begin(self, string)
       self.t0.append(time.time())
       assert(len(self.t0) == self.level)

   def end(self, string=""):
       tmsg = " (took  %fs)" % (time.time() - self.t0.pop())
       printReporter.end(self, string + tmsg)
       assert(len(self.t0) == self.level)
    

class timingHTMLReporter(timingPrintReporter):

   #def __init__(self, stream=stderr):
   #   timingPrintReporter.__init__(self, stream)

   def write(self, string):
        self.stream.write("<p class=\"reporter\">")
        self.stream.write(xstr(string))
        self.stream.write("</p>\n")
        self.stream.flush()

if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])


# $Log$
# Revision 1.4  2003-09-17 18:10:43  sandro
# redid html, with quoting; added flush()
#
# Revision 1.3  2003/09/17 16:12:10  sandro
# added HTML reporter
#
# Revision 1.2  2003/09/16 17:49:35  sandro
# fixed bug in timing
#
# Revision 1.1  2003/09/16 16:50:30  sandro
# first draft, passes tests
#
