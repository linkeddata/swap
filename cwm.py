#!/usr/bin/python
"""
$Id$

Closed World Machine

(also, in Wales, a valley  - topologiclly a partially closed world perhaps?)

This is an application which knows a certian amount of stuff and can manipulate it.
It uses llyn, a (forward chaining) query engine, not an (backward chaining) inference engine:
that is, it will apply all rules it can but won't figure out which ones to apply to prove something. 


License
-------
Cwm: http://www.w3.org/2000/10/swap/doc/cwm.html

Copyright (c) 2000-2004 World Wide Web Consortium, (Massachusetts 
Institute of Technology, European Research Consortium for Informatics 
and Mathematics, Keio University). All Rights Reserved. This work is 
distributed under the W3C Software License [1] in the hope that it 
will be useful, but WITHOUT ANY WARRANTY; without even the implied 
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

[1] http://www.w3.org/Consortium/Legal/2002/copyright-software-20021231

"""


import string
import diag

from why import FormulaReason
from diag import verbosity, setVerbosity, progress, tracking, setTracking
from uripath import join
from webAccess import urlopenForRDF, load   # http://www.w3.org/2000/10/swap/

# import re
# import StringIO

import notation3    	# N3 parsers and generators
import toXML 		#  RDF generator

from why import BecauseOfCommandLine
from query import think, applyRules, testIncludes
from update import patch

import uripath
import sys

# from llyn import RDFStore  # A store with query functiuonality
import llyn
import LX
import LX.kb
import LX.engine
import LX.language
import LX.engine.llynInterface
import RDFSink

cvsRevision = "$Revision$"



    
            

#################################################  Command line

# Reoved from help:
# --reify       Replace the statements in the store with statements describing them. 
# --flat        Reify only nested subexpressions (not top level) so that no {} remain.

    
def doCommand():
        """Command line RDF/N3 tool
        
 <command> <options> <steps> [--with <more args> ]

options:
 
--pipe        Don't store, just pipe out *

steps, in order left to right:

--rdf         Input & Output ** in RDF/XML insead of n3 from now on
--n3          Input & Output in N3 from now on. (Default)
--rdf=flags   Input & Output ** in RDF and set given RDF flags
--n3=flags    Input & Output in N3 and set N3 flags
--ntriples    Input & Output in NTriples (equiv --n3=uspartan -bySubject -quiet)
--language=x  Input & Output in "x" (rdf, n3, etc)  --rdf same as: --language=rdf
--languageOptions=y     --n3=sp same as:  --language=n3 --languageOptions=sp
--ugly        Store input and regurgitate, data only, fastest *
--bySubject   Store input and regurgitate in subject order *
--no          No output *
              (default is to store and pretty print with anonymous nodes) *
--base=<uri>  Set the base URI. Input or output is done as though theis were the document URI.
--closure=flags  Control automatic lookup of identifiers (see below)
<uri>         Load document. URI may be relative to current directory.

--apply=foo   Read rules from foo, apply to store, adding conclusions to store
--patch=foo   Read patches from foo, applying insertions and deletions to store
--filter=foo  Read rules from foo, apply to store, REPLACING store with conclusions
--rules       Apply rules in store to store, adding conclusions to store
--think       as -rules but continue until no more rule matches (or forever!)
--engine=otter use otter (in your $PATH) instead of llyn for linking, etc
--why         Replace the store with an explanation of its contents
--mode=flags  Set modus operandi for inference (see below)
--flatten     turn formulas into triples using LX vocabulary
--unflatten   turn described-as-true LX sentences into formulas
--think=foo   as -apply=foo but continue until no more rule matches (or forever!)
--purge       Remove from store any triple involving anything in class log:Chaff
--data	      Remove all except plain RDF triples (formulae, forAll, etc)
--strings     Dump :s to stdout ordered by :k whereever { :k log:outputString :s }
--crypto      Enable processing of crypto builtin functions. Requires python crypto.
--help        print this message
--revision    print CVS revision numbers of major modules
--chatty=50   Verbose debugging output of questionable use, range 0-99

finally:

--with        Pass any further arguments to the N3 store as os:argv values
 

            * mutually exclusive
            ** doesn't work for complex cases :-/
Examples:
  cwm --rdf foo.rdf --n3 --pipe     Convert from rdf/xml to rdf/n3
  cwm foo.n3 bar.n3 --think         Combine data and find all deductions
  cwm foo.n3 --flat --n3=spart

Mode flags affect inference extedning to the web:
 r   Needed to enable any remote stuff.
 a   When reading schema, also load rules pointed to by schema (requires r, s)
 E   Errors loading schemas of definitive documents are ignored
 m   Schemas and definitive documents laoded are merged into the meta knowledge
     (otherwise they are consulted independently)
 s   Read the schema for any predicate in a query.
 u   Generate unique ids using a run-specific

Closure flags are set to cause the working formula to be automatically exapnded to
the closure under the operation of looking up:

 s   the subject of a statement added
 p   the predicate of a statement added
 o   the object of a statement added
 t   the object of an rdf:type statement added
 i   any owl:imports documents
 r   any doc:rules documents
 
 e   Smush together any nodes which are = (owl:sameAs)

See http://www.w3.org/2000/10/swap/doc/cwm  for more documentation.
"""
        
        import time
        import sys
        import myStore

        # These would just be attributes if this were an object
        global _store
        global workingContext
        global lxkb
        option_need_rdf_sometime = 0  # If we don't need it, don't import it
                               # (to save errors where parsers don't exist)
        
        option_pipe = 0     # Don't store, just pipe though
        option_inputs = []
        option_reify = 0    # Flag: reify on output  (process?)
        option_flat = 0    # Flag: reify on output  (process?)
	option_crypto = 0  # Flag: make cryptographic algorithms available
	setTracking(0)
        option_outURI = None
        option_outputStyle = "-best"
        _gotInput = 0     #  Do we not need to take input from stdin?
        option_meta = 0
        option_flags = { "rdf":"", "n3":"", "think":"" }    # Random flags affecting parsing/output
        option_quiet = 0
        option_with = None  # Command line arguments made available to N3 processing
        option_engine = "llyn"
        
        _step = 0           # Step number used for metadata
        _genid = 0

        hostname = "localhost" # @@@@@@@@@@@ Get real one
        
        # The base URI for this process - the Web equiv of cwd
	_baseURI = uripath.base()
	
        option_format = "n3"      # set the default format
        option_first_format = None
        
        _outURI = _baseURI
        option_baseURI = _baseURI     # To start with - then tracks running base
	
	#  First pass on command line			  			- - - - - - - P A S S  1
	
        for argnum in range(1,len(sys.argv)):  # Command line options after script name
            arg = sys.argv[argnum]
            if arg.startswith("--"): arg = arg[1:]   # Chop posix-style double dash to one
#            _equals = string.find(arg, "=")
            _lhs = ""
            _rhs = ""
            try:
                [_lhs,_rhs]=arg.split('=',1)
		try:
		    _uri = join(option_baseURI, _rhs)
		except ValueError:
		    _uri = _rhs
            except ValueError: pass
            if arg == "-ugly": option_outputStyle = arg
            elif _lhs == "-base": option_baseURI = _uri
            elif arg == "-rdf":
                option_format = "rdf"
		if option_first_format == None: option_first_format = option_format 
                option_need_rdf_sometime = 1
            elif _lhs == "-rdf":
                option_format = "rdf"
		if option_first_format == None: option_first_format = option_format 
                option_flags["rdf"] = _rhs
                option_need_rdf_sometime = 1
            elif arg == "-n3":
		option_format = "n3"
		if option_first_format == None: option_first_format = option_format 
            elif _lhs == "-n3":
                option_format = "n3"
		if option_first_format == None: option_first_format = option_format 
                option_flags["n3"] = _rhs
            elif _lhs == "-mode":
                option_flags["think"] = _rhs
            elif _lhs == "-closure":
		pass
            elif _lhs == "-language":
                option_format = _rhs
                if option_first_format == None: option_first_format = option_format
            elif _lhs == "-languageOptions":
                option_flags[option_format] = _rhs
            elif arg == "-quiet": option_quiet = 1
            elif arg == "-pipe": option_pipe = 1
            elif arg == "-crypto": option_crypto = 1
            elif arg == "-why":
		diag.tracking=1
		diag.setTracking(1)
            elif arg == "-track":
		diag.tracking=1
		diag.setTracking(1)
            elif arg == "-bySubject": option_outputStyle = arg
            elif arg == "-no": option_outputStyle = "-no"
            elif arg == "-strings": option_outputStyle = "-no"
            elif arg == "-triples" or arg == "-ntriples":
                option_format = "n3"
                option_flags["n3"] = "uspartan"
                option_outputStyle = "-bySubject"
                option_quiet = 1
            elif _lhs == "-outURI": option_outURI = _uri
            elif _lhs == "-chatty":
                setVerbosity(int(_rhs))
            elif arg[:7] == "-apply=": pass
            elif arg[:7] == "-patch=": pass
            elif arg == "-reify": option_reify = 1
            elif arg == "-flat": option_flat = 1
            elif arg == "-help":
                print doCommand.__doc__
                print notation3.ToN3.flagDocumentation
                print toXML.ToRDF.flagDocumentation
		try:
		    import sax2rdf      # RDF1.0 syntax parser to N3 RDF stream
		    print sax2rdf.RDFXMLParser.flagDocumentation
		except:
		    pass
                return
            elif arg == "-revision":
                progress( "cwm=",cvsRevision, "llyn=", llyn.cvsRevision)
                return
            elif arg == "-with":
                option_with = sys.argv[argnum+1:] # The rest of the args are passed to n3
                break
            elif arg[0] == "-": pass  # Other option
            else :
                option_inputs.append(join(option_baseURI, arg))
                _gotInput = _gotInput + 1  # input filename
            

        # Between passes, prepare for processing
        setVerbosity(0)

        #  Base defauts
        if option_baseURI == _baseURI:  # Base not specified explicitly - special case
            if _outURI == _baseURI:      # Output name not specified either
                if _gotInput == 1:  # But input file *is*, 
                    _outURI = option_inputs[0]        # Just output to same URI
                    option_baseURI = _outURI          # using that as base.

        #  Fix the output sink
        if option_format == "rdf":
            _outSink = toXML.ToRDF(sys.stdout, _outURI, base=option_baseURI, 						flags=option_flags["rdf"])
        elif option_format == "n3":
            _outSink = notation3.ToN3(sys.stdout.write, base=option_baseURI,
                                      quiet=option_quiet, flags=option_flags["n3"])
        elif option_format == "trace":
            _outSink = RDFSink.TracingRDFSink(_outURI, base=option_baseURI,
			flags=option_flags.get("trace",""))
            if option_pipe:
                # this is really what a parser wants to dump to
                _outSink.backing = llyn.RDFStore( _outURI+"#_g",
		    argv=option_with, crypto=option_crypto) 
            else:
                # this is really what a store wants to dump to 
                _outSink.backing = notation3.ToN3(sys.stdout.write, base=option_baseURI,
                                                  quiet=option_quiet, flags=option_flags["n3"])

                #  hm.  why does TimBL use sys.stdout.write, above?  performance at the                
        else:
            myflags = option_flags.get(option_format, "")
            _outSink = LX.language.getSerializer(language=option_format,
                                                 stream=sys.stdout,
                                                 flags=myflags)

        version = "$Id$"
        if not option_quiet and option_outputStyle != "-no":
            _outSink.makeComment("Processed by " + version[1:-1]) # Strip $ to disarm
            _outSink.makeComment("    using base " + option_baseURI)
        #if option_reify: _outSink = notation3.Reifier(_outSink, _outURI+ "#_formula")
        if option_flat: _outSink = notation3.Reifier(_outSink, _outURI+ "#_formula", flat=1)

        if option_pipe:
            _store = _outSink
        else:
	    if "u" in option_flags["think"]:
		_store = llyn.RDFStore(argv=option_with, crypto=option_crypto)
	    else:
		_store = llyn.RDFStore( _outURI+"#_g", argv=option_with, crypto=option_crypto)
	    myStore.setStore(_store)

        lxkb = LX.kb.KB()      # set up a parallel store for LX-based operations

	becauseCwm = None
	if diag.tracking:
	    proof = FormulaReason(workingContext)
	    becauseCwm = BecauseOfCommandLine(sys.argv[0]) 
	    # @@ add user, host, pid, date time? Privacy!

	workingContext = None
        if  _gotInput: 
	    workingContext = _store.newFormula(option_inputs [0]+"#_work")
	else: # default input
            if option_first_format is None: option_first_format = option_format
	    ContentType={ "rdf": "application/xml+rdf", "n3":
				"application/n3" }[option_first_format]
	    workingContext = _store.load(
#			    asIfFrom = join(_baseURI, ".stdin"),
			    asIfFrom = _baseURI,
			    contentType = ContentType,
			    flags = option_flags[option_first_format],
			    remember = 0,
			    why = becauseCwm)
	    workingContext.reopen()





        #  Take commands from command line: Second Pass on command line:    - - - - - - - P A S S 2

        option_format = "n3"      # Use RDF/n3 rather than RDF/XML 
        option_flags = { "rdf":"", "n3":"", "think": "" } 
        option_quiet = 0
        _outURI = _baseURI
        option_baseURI = _baseURI     # To start with
        for arg in sys.argv[1:]:  # Command line options after script name
            if arg.startswith("--"): arg = arg[1:]   # Chop posix-style double dash to one
            _equals = string.find(arg, "=")
            _lhs = ""
            _rhs = ""
            if _equals >=0:
                _lhs = arg[:_equals]
                _rhs = arg[_equals+1:]
	    try:
                _uri = join(option_baseURI, _rhs)
	    except ValueError:
		_uri =_rhs
            if arg[0] != "-":
                _inputURI = join(option_baseURI, arg)
                assert ':' in _inputURI
		ContentType={ "rdf": "application/xml+rdf", "n3":
				"application/n3" }[option_format]

		if not option_pipe: workingContext.reopen()
		load(_store, _inputURI,
			    openFormula=workingContext,
			    contentType =ContentType,
			    flags=option_flags[option_format])

                _gotInput = 1

            elif arg == "-help":
                pass  # shouldn't happen
            elif arg == "-revision":
                pass
            elif _lhs == "-base":
                option_baseURI = _uri
                if verbosity() > 10: progress("Base now "+option_baseURI)

            elif arg == "-ugly":
                option_outputStyle = arg            

            elif arg == "-crypto": pass
            elif arg == "-pipe": pass
            elif _lhs == "-outURI": option_outURI = _uri

            elif arg == "-rdf": option_format = "rdf"
            elif _lhs == "-rdf":
                option_format = "rdf"
                option_flags["rdf"] = _rhs
            elif _lhs == "-mode":
                option_flags["think"] = _rhs
            elif _lhs == "-closure":
		workingContext.setClosureMode(_rhs)
            elif arg == "-n3": option_format = "n3"
            elif _lhs == "-n3":
                option_format = "n3"
                option_flags["n3"] = _rhs
            elif _lhs == "-language":
                option_format = _rhs
                if option_first_format == None: option_first_format = option_format
            elif _lhs == "-languageOptions":
                option_flags[option_format] = _lhs
            elif arg == "-quiet" : option_quiet = 1            
            elif _lhs == "-chatty": setVerbosity(int(_rhs))
	    elif arg[:7] == "-track=":
		diag.tracking = int(_rhs)
		
            elif option_pipe: ############## End of pipable options
                print "# Command line error: %s illegal option with -pipe", arg
                break

            elif arg == "-triples" or arg == "-ntriples":
                option_format = "n3"
                option_flags["n3"] = "spartan"
                option_outputStyle = "-bySubject"
                option_quiet = 1

            elif arg == "-bySubject":
                option_outputStyle = arg            

            elif arg[:7] == "-apply=":
		workingContext = workingContext.canonicalize()
                need(_store); touch(_store)
                filterContext = _store.load(_uri)
		workingContext.reopen()
                applyRules(workingContext, filterContext);

            elif arg[:7] == "-patch=":
		workingContext = workingContext.canonicalize()
                need(_store); touch(_store)
                filterContext = _store.load(_uri)
		workingContext.reopen()
                patch(workingContext, filterContext);

            elif _lhs == "-filter":
		workingContext = workingContext.canonicalize()
		if tracking: 
		    r = BecauseOfCommandLine(sys.argv[0]) # @@ add user, host, pid, date time? Privacy!
		else:
		    r = None
                need(_store); touch(_store)
                filterContext = _store.load(_uri, why=r)
		_newContext = _store.newFormula()
		if diag.tracking: proof = FormulaReason(_newContext)
                applyRules(workingContext, filterContext, _newContext)
		workingContext.close()
                workingContext = _newContext

            elif arg == "-why":
                need(_store); touch(_store)
		workingContext.close()
		workingContext = workingContext.collector.explanation()

            elif arg == "-dump":
                need(_store); touch(_store)
		workingContext = workingContext.canonicalize()
		progress("\nDump of working formula:\n" + workingContext.debugString())
		
            elif arg == "-purge":
                need(_store); touch(_store)
		workingContext.reopen()
                _store.purge(workingContext)
		
            elif arg == "-purge-rules" or arg == "-data":
                need(_store); touch(_store)
		workingContext.reopen()
                _store.purgeExceptData(workingContext)

            elif arg == "-rules":
                need(_store); touch(_store)
		workingContext.reopen()
                applyRules(workingContext, workingContext)

            elif arg[:7] == "-think=":
                need(_store); touch(_store)
                filterContext = _store.load(_uri)
                if verbosity() > 4: progress( "Input rules to --think from " + _uri)
		workingContext.reopen()
                think(workingContext, filterContext, mode=option_flags["think"]);

            elif _lhs == "-engine":
                option_engine = _rhs
                
            elif arg == "-think":
                if option_engine=="llyn":
                    need(_store); touch(_store)
                    think(workingContext, mode=option_flags["think"])
                else:
                    need(lxkb);
                    LX.engine.think(engine=option_engine, kb=lxkb)
                    touch(lxkb)

            elif arg == "-lxkbdump":  # just for debugging
                need(lxkb)
                print lxkb

            elif arg == "-lxfdump":   # just for debugging
                need(lxkb)
                print lxkb.asFormula()

            elif _lhs == "-prove":

                # code copied from -filter without really being understood  -sdh
                _tmpstore = llyn.RDFStore( _outURI+"#_g", metaURI=_metaURI, argv=option_with, crypto=option_crypto)

                tmpContext = _tmpstore.newFormula(_uri+ "#_formula")
                _newURI = join(_baseURI, "_w_"+`_genid`)  # Intermediate
                _genid = _genid + 1
                _newContext = _tmpstore.newFormula(_newURI+ "#_formula")
                _tmpstore.loadURI(_uri)

                targetkb = LX.kb.KB()
                LX.engine.llynInterface.toLX(_tmpstore, _newContext, kb=targetkb, kbMode=1)
                print targetkb

            elif arg == "-flatten":
                need(lxkb); touch(lxkb)
                lxkb.reifyAsTrueNonRDF()
                
            elif arg == "-reify":
                need(lxkb); touch(lxkb)
                lxkb.reifyAsTrue()

            elif arg == "-dereify":
                need(lxkb); touch(lxkb)
                lxkb.dereifyTrue()

            elif arg == "-size":
                progress("Size: %i statements in store, %i in working formula."
		    %(_store.size, workingContext.size()))

            elif arg == "-strings":  # suppress output
                need(_store)
                workingContext.outputStrings() 
                option_outputStyle = "-no"
                
            elif arg == "-no":  # suppress output
                option_outputStyle = arg
                
            elif arg[:8] == "-outURI=": pass
            elif arg == "-with": break
            else:
                progress( "cwm: Unknown option: " + arg)
                sys.exit(-1)



        # Squirt it out if not piped

        if not option_pipe:
            # we're really checking two things:
            #   (1) does the sink really want to take control, being given
            #       the kb, not just the triples one at a time, and
            #   (2) does it use lxkb or llyn ?
            if hasattr(_outSink, "serializeKB"):
                need(lxkb)
                _outSink.serializeKB(lxkb)
            else:
                need(_store)
                if verbosity()>5: progress("Begining output.")
                if option_outputStyle == "-ugly":
		    workingContext = workingContext.close()
                    _store.dumpChronological(workingContext, _outSink)
                elif option_outputStyle == "-bySubject":
		    workingContext = workingContext.close()
                    _store.dumpBySubject(workingContext, _outSink)
                elif option_outputStyle == "-no":
                    pass
                else:  # "-best"
		    workingContext = workingContext.close()
		    assert workingContext.canonical != None
                    _store.dumpNested(workingContext, _outSink)

# These could well be methods using instance variables instead of
# functions using globals.

def touch(object):
    """Indicate that this object has been modified; for use by need()"""
    object.touched = 1

def need(object):
    """Update the given repository object from the other one if the
    other one has been changed since they were last synchronized.
    If both have been touched, raise an error.
    """ 
    if hasattr(_store, "touched"):
        if hasattr(lxkb, "touched"):
            raise RuntimeError, "Both _store and lxkb were touched"
        else:
            if object is lxkb:
                #print "# copying _store to lxkb"
                lxkb.clear()
                LX.engine.llynInterface.toLX(_store, workingContext, kb=lxkb,
                                             kbMode=1)
                del(_store.touched)
            else:
                pass   # lxkb is out of date, but not needed yet
    else:
        if hasattr(lxkb, "touched"):
            if object is _store:
                #print "# copying lxkb to _store"
		workingContext.reopen()
                _store.deleteFormula(workingContext)   ##@@@@ very slow
                LX.engine.llynInterface.addLXKB(_store, workingContext, lxkb)
                del(lxkb.touched)
            else:
                pass  # _store is out of date, but not needed yet
        else:
            pass   # neither was touched, nothing to do!


############################################################ Main program
    
if __name__ == '__main__':
    import os
    doCommand()

