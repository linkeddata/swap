

// breadcrumbs:
// http://developer.mozilla.org/en/docs/Rhino_documentation
// http://www.mozilla.org/rhino/ScriptingJava.html
// http://www.exampledepot.com/egs/java.io/ReadLinesFromFile.html
// http://developer.mozilla.org/en/docs/Rhino_Shell#arguments

// load("/devel/dig/2005/ajar/ajaw/lib0.js");

load("/devel/dig/2005/ajar/ajaw/js/log.js");
load("/devel/dig/2005/ajar/ajaw/js/uri.js");
load("/devel/dig/2005/ajar/ajaw/js/rdf/term.js");
load("/devel/dig/2005/ajar/ajaw/js/rdf/match.js");
load("/devel/dig/2005/ajar/ajaw/js/rdf/identity.js");
load("/devel/dig/2005/ajar/ajaw/js/rdf/remote.js");
load("/devel/dig/2005/ajar/ajaw/js/rdf/rdfparser.js");
load("n3parser.js");  // @@ Note local copy
load("/devel/dig/2005/ajar/ajaw/js/rdf/query.js");
load("/devel/dig/2005/ajar/ajaw/js/rdf/sources.js");
load("/devel/dig/2005/ajar/ajaw/js/rdf/sparql.js");

kb = new RDFIndexedFormula();


testn3 = function(uri) {
    print('# Parsing '+uri)
    localURI = uri;
    if (uri.slice(0,5) == 'http:') {
        localURI ='http://localhost/' + uri.slice(7)
    }
    buf = readUrl(localURI);   // @@ offline
    print('# '+ buf.length+' bytes');
    var p = SinkParser(kb, kb, uri, uri, null, null, "", null)
    try {
	p.loadBuf(buf)

    } catch(e) {
	var msg = ("Error trying to parse " + uri
	    + ' as Notation3:\n' + e)
	print(msg)
        java.lang.System.exit(1)  // Error
    }
  
    
        str = ''+kb
    str = str.slice(1,-1)  // remove {}
    print ('#Result:\n' + str)
    java.lang.System.exit(0)
    
}

// print("Arguments <"+arguments+">"+arguments.length)

testn3(arguments[0]);
