#!/usr/bin/env python
"""

    By sandro@w3.org....  Nothing else did this at the time.  With
    python 2.3 gnu-style getopt probably has this basic functionality
    (allowing filenames to be mixed with arguments, cwm-style),
    although not nearly as easy-to-use (introspective) an interface.
    
"""
import sys
import inspect
import re

class Error(RuntimeError):
   pass

class ArgHandler:
    """A replacement for getopt which supports interleaving
    flags with other arguments and is very simple to use.

         from ArgHandler import ArgHandler;

         class MyArgHandler(ArgHandler):

             def handle__H__hello(self):
                 print "Hello, World!"

             def handle__xx(self, foo, baz=3, buz=4):
                 spiff=5
                 print "Hello, World!"

         if __name__ == "__main__":
             a = MyArgHandler(revision="$Id$")
             a.run()

     Special hack to support things like --filter=f where
     we have an optional parameter in the midst of extra arguments.
       ...  in1 in2 --filter in3 --filter=f1 in4 ...
     if the option contains a "=" it must match a method name
     with EQ appended  ( handle__x__y__filterEQ__z ) which
     must take exactly one argument.   So filter and filterEQ may
     be different options.   It's safe to add an EQ version to any
     option which takes only one parameter

     Should we issue a warning when a non-option parameter occurs
     next after a = option, saying that it makes the = significant
     which might confuse some people?

    """

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
        
    def handle__h__help__helpEQ(self, whichOption=None):
        """Output summary of options, or details on a particular option.

        If the optional parameter is present, it should name an option for
        additional information is requested.  (Omit the "-" or "--" from
        the option so that it looks like a parameter to --help instead of
        looking like another option!)

        Example:   foo --help help
        """

        if whichOption is None:
            lines = [ ]
            width = [0, 0, 0, 0, 0]
            for member in inspect.getmembers(self):
                if member[0].startswith("handle__"):
                    line = self.genHelpEntry(member)
                    #print line
                    for i in range(0, len(line)):
                        width[i] = max(width[i], len(line[i]))
                    lines.append(line)
            lines.sort(lambda x,y: cmp(x[3], y[3]))
            lines.insert(0, ("===========", "=====", "==========="))
            lines.insert(0, ("Option Name", "Param", "Description"))
                

            for line in lines:
               s1 = "%-*s  %-*s  " % (width[0], line[0],
                                      width[1], line[1])
               s2 = line[2]
               s = wrap(s1+s2,79)
               print re.sub('\\n', "\n"+" "*len(s1), s)
                
        else:
           member = self.findMember(whichOption)
           if member is None: return
           line = self.genHelpEntry(member, long=1)
           print "Option: ", line[0]
           print "Arguments: ", line[1]
           print "Description: ", wrap(line[2], 79)

    def handle__V__version(self):
        """Output version information.

        (It would be nice if this gave the versions of all the
        modules, too, and was more automatic given python version
        conventions.)"""
        print self.version

    def handleNoArgs(self):
        raise Error, "no options or parameters specified."

    def run(self):

        self.current_argument_index = 1

        try:
            if len(self.argv) == 1:
                self.handleNoArgs()
            while 1:
                try:
                    arg = self.peekThis()
                except IndexError:
                    return 0
                self.handleArg(arg)
                self.advance()
        except Error, e:
            print e
            print "Try --help for more information."
            return 1
           
    def handleArg(self, arg):
       option = None
       if arg.startswith("--"):
          option = arg[2:]
       else:
          if arg.startswith("-"):
            option = arg[1:]
          else:
             self.handleExtraArgument(arg)
             return

       option = re.sub("-", "_", option)
       try:
          (left, right) = option.split("=", 2)
       except ValueError:
          member = self.findMember(option)
          args = self.buildArgs(member)
          apply(member[1], args)
          return

       member = self.findMember(left+"EQ")
       apply(member[1], [right])

    def handleExtraArgument(self, arg):
       raise Error, "Extra argument: \"%s\"" % arg
    
    def findMember(self, arg):
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
           raise Error, "unknown argument: \"%s\"" % arg
        if len(matches) == 1:
            return last_match
        if len(matches) > 4:
           raise Error, ("ambiguous option might be: \"%s\"..." %
                       '", "'.join(matches[0:3]))
        if len(matches) > 1:
           raise Error, ("ambiguous option might be: \"%s\"" %
                       '", "'.join(matches))

    def buildArgs(self, member):
       """Call getNext as long as it's not a flag to fill in the
       argument list.   If we run out, fill in with defaults if
       possible."""
       f = member[1].im_func
       argcount = f.func_code.co_argcount
       if f.func_code.co_flags & 4 :
          raise Error, "handlers may not have variable arg lists"
       defaults = f.func_defaults or ()

       i = 1   # skip "self"
       args = []
       name = self.peekThis()
       while i < argcount:

          next = self.getNextNonFlag()
          if next is None:
             indexIntoDefaults = i + len(defaults) - argcount
             if indexIntoDefaults >= 0:      #defaultable
                next = defaults[indexIntoDefaults]
             else:
                raise Error, "not enough arguments to option \""+name+"\""
          args.append(next)
          i+=1
       return args
               

    def genHelpEntry(self, member, long=0):

        names = member[0].split("__")[1:]
        names = map(lambda x: re.sub("_", "-", x), names)
        names = map(lambda x: re.sub("EQ$", "=", x), names)
        # primary sort key = case insensitive version, 
        # secondary is case sensitive
        sortKey = names[0].lower() + " " + names[0]
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
            raise Error, "handlers may not have variable arg lists"
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
                docs = re.sub('(?m)^        ', "", f.__doc__)
            else:
                doc = f.__doc__.split("\n\n", 2)
                docs = doc[0]
        docs = re.sub("\\s*$", "", docs)
        return (optdesc, parmdesc, docs, sortKey)

    def peekThis(self):
        return self.argv[self.current_argument_index]

    def peekNext(self):
        return self.argv[self.current_argument_index + 1]

    def getNext(self):
        self.advance();
        return self.peekThis()

    def getNextNonFlag(self):
       try:
          if self.peekNext().startswith("-"):
             return None
          else:
             return self.getNext()
       except IndexError:
          return None

    def advance(self):
        self.current_argument_index += 1

       

# borrowed from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/148061
# by Mike Brown, version 1.4, 2002/12/20
# modified to add "prefix"

def wrap(text, width):
   """
   A word-wrap function that preserves existing line breaks
   and most spaces in the text. Expects that existing line
   breaks are posix newlines (\n).
   """
   return reduce(lambda line, word, width=width: '%s%s%s' %
                 (line,
                  ' \n'[(len(line[line.rfind('\n')+1:])
                         + len(word.split('\n',1)[0]
                               ) >= width)],
                  word),
                 text.split(' ')
                 )    
           
################################################################

if __name__ == "__main__":
    import doctest, sys
    doctest.testmod(sys.modules[__name__])

# $Log$
# Revision 1.8  2003-08-01 15:32:28  sandro
# added name and comment at top
#
# Revision 1.7  2003/04/03 04:51:49  sandro
# fairly stable in skeletal state
#
# Revision 1.6  2003/04/02 20:55:20  sandro
# remove a debugging print
#
# Revision 1.5  2003/04/02 20:42:56  sandro
# pretty up help a bit
#
# Revision 1.4  2003/04/02 19:52:33  sandro
# a bit of docs
#
# Revision 1.3  2003/04/02 19:43:41  sandro
# nearly all works
#
# Revision 1.2  2003/04/02 18:06:13  sandro
# short documentation works
#
# Revision 1.1  2003/04/02 17:44:47  sandro
# a spectacular peice of dogwash
#
