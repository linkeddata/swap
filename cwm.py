#!/usr/bin/python
"""

$Id$

Closed World Machine

(also, in Wales, a valley  - topologiclly a partially closed world perhaps?)

This is an application which knows a certian amount of stuff and can manipulate it.
It uses llyn, a (forward chaining) query engine, not an (backward chaining) inference engine:
that is, it will apply all rules it can but won't figure out which ones to apply to prove something. 


http://www.w3.org/DesignIssues/Notation3
Date: 2000/07/17 21:46:13  

Agenda:
=======


 - Use conventional python command line parsing
 
 - get rid of other globals (DWC 30Aug2001)
 

"""

"""emacs got confused by long string above@@"""


import string
import urlparse
import thing
from llyn import compareURI

# import re
# import StringIO

#import urllib # for log:content
import md5, binascii  # for building md5 URIs
urlparse.uses_fragment.append("md5") #@@kludge/patch
urlparse.uses_relative.append("md5") #@@kludge/patch

import notation3    # N3 parsers and generators, and RDF generator

from RDFSink import FORMULA, LITERAL, ANONYMOUS, VARIABLE, SYMBOL, Logic_NS

# from llyn import RDFStore  # A store with query functiuonality
import llyn

from thing import progress

cvsRevision = "$Revision$"


######################################################### Tests  
  
def test():
    import sys
    testString = []
    
    t0 = """bind x: <http://example.org/x-ns/> .
	    bind dc: <http://purl.org/dc/elements/1.1/> ."""

    t1="""[ >- x:firstname -> "Ora" ] >- dc:wrote ->
    [ >- dc:title -> "Moby Dick" ] .
     bind default <http://example.org/default>.
     <uriPath> :localProp defaultedName .
     
"""
    t2="""
[ >- x:type -> x:Receipt;
  >- x:number -> "5382183";
  >- x:for -> [ >- x:USD -> "2690" ];
  >- x:instrument -> [ >- x:type -> x:visa ] ]

>- x:inReplyTo ->

[ >- x:type -> x:jobOrder;
  >- x:number -> "025709";
 >- x:from ->

 [
  >- x:homePage -> <http://www.topnotchheatingandair.com/>;
  >- x:est -> "1974";
  >- x:address -> [ >- x:street -> "23754 W. 82nd Terr.";
      >- x:city -> "Lenexa";
      >- x:state -> "KS";
      >- x:zip -> "66227"];
  >- x:phoneMain -> <tel:+1-913-441-8900>;
  >- x:fax -> <tel:+1-913-441-8118>;
  >- x:mailbox -> <mailto:info@topnotchheatingandair.com> ]
].    

<http://www.davelennox.com/residential/furnaces/re_furnaces_content_body_elite90gas.asp>
 >- x:describes -> [ >- x:type -> x:furnace;
 >- x:brand -> "Lennox";
 >- x:model -> "G26Q3-75"
 ].
"""
    t3="""
bind pp: <http://example.org/payPalStuff?>.
bind default <http://example.org/payPalStuff?>.

<> a pp:Check; pp:payee :tim; pp:amount "$10.00";
  dc:author :dan; dc:date "2000/10/7" ;
  is pp:part of [ a pp:Transaction; = :t1 ] .
"""

# Janet's chart:
    t4="""
bind q: <http://example.org/>.
bind m: <>.
bind n: <http://example.org/base/>.
bind : <http://void-prefix.example.org/>.
bind w3c: <http://www.w3.org/2000/10/org>.

<#QA> :includes 
 [  = w3c:internal ; :includes <#TAB> , <#interoperability> ,
     <#validation> , w3c:wai , <#i18n> , <#translation> ,
     <#readability_elegance>, w3c:feedback_accountability ],
 [ = <#conformance>;
     :includes <#products>, <#content>, <#services> ],
 [ = <#support>; :includes
     <#tools>, <#tutorials>, <#workshops>, <#books_materails>,
     <#certification> ] .

<#internal> q:supports <#conformance> .  
<#support> q:supports <#conformance> .

"""

    t5 = """

bind u: <http://www.example.org/utilities>
bind default <>

:assumption = { :fred u:knows :john .
                :john u:knows :mary .} .

:conclusion = { :fred u:knows :mary . } .

"""
    thisURI = "file:notation3.py"

    testString.append(  t0 + t1 + t2 + t3 + t4 )
#    testString.append(  t5 )

#    p=notation3.SinkParser(RDFSink(),'http://example.org/base/', 'file:notation3.py',
#		     'data:#')

    r=notation3.SinkParser(notation3.ToN3(sys.stdout.write, base='file:output'),
                  thisURI,'http://example.org/base/',)
    r.startDoc()
    
    progress( "=== test stringing: ===== STARTS\n " + t0 + "\n========= ENDS\n")
    r.feed(t0)

    progress( "=== test stringing: ===== STARTS\n " + t1 + "\n========= ENDS\n")
    r.feed(t1)

    progress( "=== test stringing: ===== STARTS\n " + t2 + "\n========= ENDS\n")
    r.feed(t2)

    progress( "=== test stringing: ===== STARTS\n " + t3 + "\n========= ENDS\n")
    r.feed(t3)

    r.endDoc()

    progress( "----------------------- Test store:")

    store = llyn.RDFStore()

    thisDoc = store.internURI(thisURI)    # Store used interned forms of URIs
    thisContext = store.intern((FORMULA, thisURI+ "#_formula"))    # @@@ Store used interned forms of URIs

    # (sink,  thisDoc,  baseURI, bindings)
    p = notation3.SinkParser(store,  thisURI, 'http://example.org/base/')
    p.startDoc()
    p.feed(testString[0])
    p.endDoc()

    progress( "\n\n------------------ dumping chronologically:")

    store.dumpChronological(thisContext, notation3.ToN3(sys.stdout.write, base=thisURI))

    progress( "\n\n---------------- dumping in subject order:")

    store.dumpBySubject(thisContext, notation3.ToN3(sys.stdout.write, base=thisURI))

    progress( "\n\n---------------- dumping nested:")

    store.dumpNested(thisContext, notation3.ToN3(sys.stdout.write, base=thisURI))

    progress( "Regression test **********************************************")

    
    testString.append(reformat(testString[-1], thisURI))

    if testString[-1] == testString[-2]:
        progress( "\nRegression Test succeeded FIRST TIME- WEIRD!!!!??!!!!!\n")
        return
    
    testString.append(reformat(testString[-1], thisURI))

    if testString[-1] == testString[-2]:
        progress( "\nRegression Test succeeded SECOND time!!!!!!!!!\n")
    else:
        progress( "Regression Test Failure: ===================== LEVEL 1:")
        progress( testString[1])
        progress( "Regression Test Failure: ===================== LEVEL 2:")
        progress( testString[2])
        progress( "\n============================================= END")

    testString.append(reformat(testString[-1], thisURI))
    if testString[-1] == testString[-2]:
        progress( "\nRegression Test succeeded THIRD TIME. This is not exciting.\n")

    
                
def reformat(str, thisURI):
    if 0:
        progress( "Regression Test: ===================== INPUT:")
        progress( str)
        progress( "================= ENDs")
    buffer=StringIO.StringIO()
    r=notation3.SinkParser(notation3.ToN3(buffer.write, base=thisURI), thisURI)
    r.startDoc()
    r.feed(str)
    r.endDoc()

    return buffer.getvalue()    # Do we need to explicitly close it or will it be GCd?
    


##############################################  String output




    
            

#################################################  Command line
    
def doCommand():
        """Command line RDF/N3 tool
        
 <command> <options> <inputURIs>
 
--pipe      Don't store, just pipe out *

--rdf       Input & Output ** in RDF M&S 1.0 insead of n3 from now on
--n3        Input & Output in N3 from now on
--rdf=flags Input & Output ** in RDF and set given RDF flags
--n3=flags  Input & Output in N3 and set N3 flags
--ntriples  Input & Output in NTriples (equiv --n3=spart -bySubject -quiet)
--ugly      Store input and regurgitate *
--bySubject Store input and regurgitate in subject order *
--no        No output *
            (default is to store and pretty print with anonymous nodes) *
--strings   Dump :s to stdout ordered by :k whereever { :k log:outputString :s }
--apply=foo Read rules from foo, apply to store, adding conclusions to store
--filter=foo Read rules from foo, apply to store, REPLACING store with conclusions
--rules     Apply rules in store to store, adding conclusions to store
--think     as -rules but continue until no more rule matches (or forever!)
--think=foo as -apply=foo but continue until no more rule matches (or forever!)
--reify     Replace the statements in the store with statements describing them.
--flat      Reify only nested subexpressions (not top level) so that no {} remain.
--help      print this message
--revision  print CVS revision numbers of major modules
--chatty=50 Verbose output of questionable use, range 0-99
--with      Pass any further arguments to the N3 store as os:argv values
 

            * mutually exclusive
            ** doesn't work for complex cases :-/
Examples:
  cwm --rdf foo.rdf --n3 --pipe     Convert from rdf/xml to rdf/n3
  cwm foo.n3 bar.n3 --think         Combine data and find all deductions
  cwm foo.n3 --flat --n3=spart

See http://www.w3.org/2000/10/swap/doc/cwm  for more documentation.

"""
        
#        import urllib
        import time
        import sys
        global sax2rdf
        import thing
#        from thing import chatty
#        import sax2rdf

        option_need_rdf_sometime = 0  # If we don't need it, don't import it
                               # (to save errors where parsers don't exist)
        
        option_pipe = 0     # Don't store, just pipe though
        option_inputs = []
        option_test = 0     # Do simple self-test
        option_reify = 0    # Flag: reify on output  (process?)
        option_flat = 0    # Flag: reify on output  (process?)
        option_outURI = None
        option_outputStyle = "-best"
        _gotInput = 0     #  Do we not need to take input from stdin?
        option_meta = 0
        option_rdf_flags = ""  # Random flags affecting parsing/output
        option_n3_flags = ""  # Random flags affecting parsing/output
        option_quiet = 0
        option_with = None  # Command line arguments made available to N3 processing

        _step = 0           # Step number used for metadata
        _genid = 0

        hostname = "localhost" # @@@@@@@@@@@ Get real one
        
        # The base URI for this process - the Web equiv of cwd
#	_baseURI = "file://" + hostname + os.getcwd() + "/"
	_baseURI = "file:" + fixslash(os.getcwd()) + "/"
	
        option_format = "n3"      # Use RDF rather than XML
        option_first_format = None
        
        _outURI = _baseURI
        option_baseURI = _baseURI     # To start with - then tracks running base
        for argnum in range(1,len(sys.argv)):  # Command line options after script name
            arg = sys.argv[argnum]
            if arg.startswith("--"): arg = arg[1:]   # Chop posix-style double dash to one
            _equals = string.find(arg, "=")
            _lhs = ""
            _rhs = ""
            if _equals >=0:
                _lhs = arg[:_equals]
                _rhs = arg[_equals+1:]
                _uri = urlparse.urljoin(option_baseURI, _rhs) # Make abs from relative
            if arg == "-test":
                option_test = 1
                _gotInput = 1
            elif arg == "-ugly": option_outputStyle = arg
            elif _lhs == "-base": option_baseURI = _uri
            elif arg == "-rdf":
                option_format = "rdf"
                option_need_rdf_sometime = 1
            elif _lhs == "-rdf":
                option_format = "rdf"
                option_rdf_flags = _rhs
                option_need_rdf_sometime = 1
            elif arg == "-n3": option_format = "n3"
            elif _lhs == "-n3":
                option_format = "n3"
                option_n3_flags = _rhs
            elif arg == "-quiet": option_quiet = 1
            elif arg == "-pipe": option_pipe = 1
            elif arg == "-bySubject": option_outputStyle = arg
            elif arg == "-no": option_outputStyle = "-no"
            elif arg == "-strings": option_outputStyle = "-no"
            elif arg == "-triples" or arg == "-ntriples":
                option_format = "n3"
                option_n3_flags = "spart"
                option_outputStyle = "-bySubject"
                option_quiet = 1
            elif _lhs == "-outURI": option_outURI = _uri
            elif _lhs == "-chatty":
                thing.setVerbosity(int(_rhs))
            elif arg[:7] == "-apply=": pass
            elif arg == "-reify": option_reify = 1
            elif arg == "-flat": option_flat = 1
            elif arg == "-help":
                print doCommand.__doc__
                print notation3.ToN3.flagDocumentation
                print notation3.ToRDF.flagDocumentation
                return
            elif arg == "-revision":
                progress( "cwm=",cvsRevision, "llyn=", llyn.cvsRevision)
                return
            elif arg == "-with":
                option_with = sys.argv[argnum+1:] # The rest of the args are passed to n3
                break
            elif arg[0] == "-": pass  # Other option
            else :
                option_inputs.append(urlparse.urljoin(option_baseURI,arg))
                _gotInput = _gotInput + 1  # input filename
            

        # This is conditional as it is not available on all platforms,
        # needs C and Python to compile xpat.
        if option_need_rdf_sometime:
            import sax2rdf      # RDF1.0 syntax parser to N3 RDF stream

# Between passes, prepare for processing
        thing.setVerbosity(0)
#  Base defauts

        if option_baseURI == _baseURI:  # Base not specified explicitly - special case
            if _outURI == _baseURI:      # Output name not specified either
                if _gotInput == 1 and not option_test:  # But input file *is*, 
                    _outURI = option_inputs[0]        # Just output to same URI
                    option_baseURI = _outURI          # using that as base.

#  Fix the output sink
        
        if option_format == "rdf":
            _outSink = notation3.ToRDF(sys.stdout, _outURI, base=option_baseURI, flags=option_rdf_flags)
        else:
            _outSink = notation3.ToN3(sys.stdout.write, base=option_baseURI,
                                      quiet=option_quiet, flags=option_n3_flags)
        version = "$Id$"
        if not option_quiet and option_outputStyle != "-no":
            _outSink.makeComment("Processed by " + version[1:-1]) # Strip $ to disarm
            _outSink.makeComment("    using base " + option_baseURI)
        if option_reify: _outSink = notation3.Reifier(_outSink, _outURI+ "#_formula")
        if option_flat: _outSink = notation3.Reifier(_outSink, _outURI+ "#_formula", flat=1)


        if option_pipe:
            _store = _outSink
            workingContextURI = None
        else:
            _metaURI = urlparse.urljoin(option_baseURI, "RUN/") + `time.time()`  # Reserrved URI @@
            _store = llyn.RDFStore( _outURI+"#_gs", metaURI=_metaURI, argv=option_with)
            workingContextURI = _outURI+ "#0_work"
            workingContext = _store.intern((FORMULA, workingContextURI))   #@@@ Hack - use metadata
#  Metadata context - storing information about what we are doing

            _store.reset(_metaURI+"#_experience")     # Absolutely need this for remembering URIs loaded
            history = None
	

        if not _gotInput: #@@@@@@@@@@ default input
            _inputURI = _baseURI # Make abs from relative
            p = notation3.SinkParser(_store,  _inputURI, formulaURI=workingContextURI)
            p.load("")
            del(p)
            if not option_pipe:
                inputContext = _store.intern((FORMULA, _inputURI+ "#_formula"))
                history = inputContext


#  Take commands from command line: Second Pass on command line:

        option_format = "n3"      # Use RDF rather than XML
        option_rdf_flags = ""
        option_n3_flags = ""
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
                _uri = urlparse.urljoin(option_baseURI, _rhs) # Make abs from relative
                
            if arg[0] != "-":
                _inputURI = urlparse.urljoin(option_baseURI, arg) # Make abs from relative
                if option_format == "rdf" :
                    p = sax2rdf.RDFXMLParser(_store, _inputURI, formulaURI=workingContextURI)
                else: p = notation3.SinkParser(_store,  _inputURI, formulaURI=workingContextURI)
                if not option_pipe: workingContext.reopen()
                p.load(_inputURI)
                del(p)
                if not option_pipe:
                    inputContext = _store.intern((FORMULA, _inputURI+ "#_formula"))
                    _step  = _step + 1
                    s = _metaURI + `_step`  #@@ leading 0s to make them sort?
#                    if doMeta and history:
#                        _store.storeQuad((_store._experience, META_mergedWith, s, history))
#                        _store.storeQuad((_store._experience, META_source, s, inputContext))
#                        _store.storeQuad((_store._experience, META_run, s, run))
#                        history = s
#                    else:
                    history = inputContext
                _gotInput = 1

            elif arg == "-help":
                pass  # shouldn't happen
            elif arg == "-revision":
                pass
            elif arg == "-test": test()
            elif _lhs == "-base":
                option_baseURI = _uri
                progress("Base now "+option_baseURI)

            elif arg == "-ugly":
                option_outputStyle = arg            

            elif arg == "-pipe": pass
            elif _lhs == "-outURI": option_outURI = _uri

            elif arg == "-rdf": option_format = "rdf"
            elif _lhs == "-rdf":
                option_format = "rdf"
                option_rdf_flags = _rhs
            elif arg == "-n3": option_format = "n3"
            elif _lhs == "-n3":
                option_format = "n3"
                option_n3_flags = _rhs
            elif arg == "-quiet" : option_quiet = 1            
            elif _lhs == "-chatty": thing.setVerbosity(int(_rhs))

            elif arg == "-reify":
                pass

            elif arg == "-flat":  # reify only nested expressions, not top level
                pass

            elif option_pipe: ############## End of pipable options
                print "# Command line error: %s illegal option with -pipe", arg
                break

            elif arg == "-triples" or arg == "-ntriples":
                option_format = "n3"
                option_n3_flags = "spart"
                option_outputStyle = "-bySubject"
                option_quiet = 1

            elif arg == "-bySubject":
                option_outputStyle = arg            

            elif arg[:7] == "-apply=":
                filterContext = (_store.intern((FORMULA, _uri+ "#_formula")))
                if thing.verbosity() > 4: progress( "Input rules to --apply from " + _uri)
                _store.loadURI(_uri)
                _store.applyRules(workingContext, filterContext);

            elif _lhs == "-filter":
                filterContext = _store.intern((FORMULA, _uri+ "#_formula"))
                _newURI = urlparse.urljoin(_baseURI, "_w_"+`_genid`)  # Intermediate
                _genid = _genid + 1
                _newContext = _store.intern((FORMULA, _newURI+ "#_formula"))
                _store.loadURI(_uri)
                _store.applyRules(workingContext, filterContext, _newContext)
                workingContext = _newContext
                workingContextURI = _newURI


#                if doMeta:
#                    _step  = _step + 1
#                    s = _metaURI + `_step`  #@@ leading 0s to make them sort?
#                    _store.storeQuad(_store._experience, META_basis, s, history)
#                    _store.storeQuad(_store._experience, META_filter, s, inputContext)
#                    _store.storeQuad(_store._experience, META_run, s, run)
#                    history = s

            elif arg == "-purge":
                _store.purge(workingContext)

            elif arg == "-rules":
                _store.applyRules(workingContext, workingContext)

            elif arg[:7] == "-think=":
                filterContext = (_store.intern((FORMULA, _uri+ "#_formula")))
                if thing.verbosity() > 4: progress( "Input rules to --think from " + _uri)
                _store.loadURI(_uri)
                _store.think(workingContext, filterContext);
            elif arg == "-think":
                _store.think(workingContext)

            elif arg == "-size":
                progress("Size: %i statements in store, %i in working formula." %(_store.size, workingContext.size()))

            elif arg == "-strings":  # suppress output
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
            if thing.verbosity()>5: progress("Begining output.")
            if option_outputStyle == "-ugly":
                _store.dumpChronological(workingContext, _outSink)
            elif option_outputStyle == "-bySubject":
                _store.dumpBySubject(workingContext, _outSink)
            elif option_outputStyle == "-no":
                pass
            else:  # "-best"
                _store.dumpNested(workingContext, _outSink)

    
def fixslash(str):
    """ Fix windowslike filename to unixlike
    """
    s = str
    for i in range(len(s)):
        if s[i] == "\\": s = s[:i] + "/" + s[i+1:]
    if s[0] != "/" and s[1] == ":": s = s[2:]  # @@@ Hack when drive letter
    return s
        
############################################################ Main program
    
if __name__ == '__main__':
    import os
#    import urlparse
    doCommand()

