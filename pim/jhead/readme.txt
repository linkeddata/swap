Compiling:

    Windows:

    Make sure visual C is on your path (I use version 6, but it shouldn't 
    matter much).
    Run the batch file make.bat

    Linux & Unices:

    type 'make'.

Portability:

    Although I have never done so myself, people tell me it compiles
    under platforms as diverse as such as Mac OS-X, or NetBSD on Mac68k.
    Jhead doesn't care about the endian-ness of your CPU, and should not
    have problems with processors that do not handle unaligned data,
    such as ARM or Alpha.  The main portability problem is the use 
    of C++ stype '//' comments.  This is intentional, and won't change.

    Jhead has also made its way into the ports tree of NetBSD and FreeBSD,
    as well as Debian "unstable".  So if you are using one of these, you
    might already have jhead.  Note that I have never used any of these
    platforms myself.
   

Liscence:

    Jhead is public domain software - that is, you can do whatever you want
    with it, and include it software that is licensesed under the GNU or the 
    BSD license, or whatever other licence you chose, including proprietary
    closed source licenses.

    If you do integrate the code into some software of yours, I'd appreciate
    knowing about it though. You can e-mail me at mwandel(at)sentex.net

Matthias Wandel

