#!/usr/bin/env python

import sys
import inspect

class ArgHandler:
    """A replacement for getopt which supports interleaving
    flags with other arguments and is very simple to use."""

    def __init__(self, **attrs):
        """Accept arbitrary keyword arguments and just store
        them for later, so subclasses can have their own easily.

        We use:
           argv, to override sys.argv
           program, the program name
           uri, where people should go for more information
           version, version information
        """
        self.__dict__.update(attrs)
        self.__dict__.setdefault("argv", sys.argv)
        
    def handle__h__help(self, whichArg=None):
        """Output summary of options, or details on a particular option.

        More explanation here."""

        if whichArg is None:
            lines = [
                ("Option Name", "Param", "Description"),
                ("===========", "=====", "===========")
                ]
            width = [0, 0, 0, 0, 0]
            for member in inspect.getmembers(self):
                if member[0].startswith("handle__"):
                    line = self.genHelpEntry(member)
                    # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/148061
                    for i in range(0, len(line)):
                        width[i] = max(width[i], len(line[i]))
                    lines.append(line)
            for line in lines:
                print "%-*s  %-*s  %s" % (width[0], line[0],
                                      width[1], line[1],
                                      line[2])
        else:
           method = self.findMethod(whichArg)
           if method is None: return
           self.printHelpEntry(member, long=1)

    def handle__V__version(self):
        """Output version information.

        (It would be nice if this gave the versions of all the
        modules, too, and was more automatic given python version
        conventions.)"""
        print self.version

    def error(self, msg):
        print "Error:", msg
        
    def run(self):
        self.handle__h__help()
        return
        self.current_argument_index = 1
        while 1:
            try:
                arg = self.peekThis()
            except IndexError:
                return
            m = self.findMethod(arg)
            if m:
                # print m.__doc__
                #print "Arguments:", m.im_func.func_code.co_argcount
                #print "Var Args:", m.im_func.func_code.co_flags & 4
                #print "Argument List:", m.im_func.func_code.co_varnames
                #print "Def:", m.im_func.func_defaults
                #args = []
                # for each needed arg, do a getNextNonFlag
                #    if it fails, then fill it from the right default
                apply(m[1], ["foo"])
            else:
                return  # error
            self.advance()

    def findMethod(self, arg):
        matches=[]
        last_match=None
        for member in inspect.getmembers(self):
            if member[0].startswith("handle__"):
                parts = member[0].split("__")[1:]

                # exact match
                if arg in parts:
                    return member

                # leading substring match
                for part in parts:
                    if part.startswith(arg):
                        matches.append(part)
                        last_match = member

        if len(matches) == 0:
            self.error("unknown argument: \"%s\"" % arg)
        if len(matches) == 1:
            return last_match
        if len(matches) > 1:
            self.error("ambiguous argument, might be: \"%s\"..." %
                       '", "'.join(matches[0:3]))

    def buildArgs(self, member):
        pass

    def genHelpEntry(self, member, long=0):

        names = member[0].split("__")[1:]
        #print names, member
        f = member[1].im_func
        optdesc = ""
        for name in names:
            if len(name) == 1:
                optdesc += "-" + name + " "
            else:
                optdesc += "--" + name + " "
        optdesc = optdesc[:-1]

        parmdesc = ""
        argcount = f.func_code.co_argcount
        if f.func_code.co_flags & 4 :
            raise RuntimeError, "handlers may not have variable arg lists"
        defaults = f.func_defaults or ()
        argnames = f.func_code.co_varnames
        i = 1   # skip "self"
        #print "argcount", argcount
        #print "defaults", defaults
        while i < argcount:
            indexIntoDefaults = i + len(defaults) - argcount
            #print "index", i
            #print "indexIntoDefaults", indexIntoDefaults
            if indexIntoDefaults >= 0:
                parmdesc += "[" +  argnames[i]
                d = defaults[indexIntoDefaults]
                if d is not None:
                    parmdesc += "=" + str(d)
                parmdesc +=  "] "
            else:
                parmdesc +=  argnames[i] + " "
            i+=1

        if f.__doc__ is None:
            docs = "<undocumented>"
        else:
            if long:
                docs = f.__doc__
            else:
                doc = f.__doc__.split("\n\n", 2)
                docs = doc[0]

        return (optdesc, parmdesc, docs)

    def peekThis(self):
        return self.argv[self.current_argument_index]

    def peekNext(self):
        return self.argv[self.current_argument_index + 1]

    def getNext(self):
        self.advance();
        return self.peekThis()

    def advance(self):
        self.current_argument_index += 1

           
################################################################

if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])

# $Log$
# Revision 1.2  2003-04-02 18:06:13  sandro
# short documentation works
#
# Revision 1.1  2003/04/02 17:44:47  sandro
# a spectacular peice of dogwash
#
