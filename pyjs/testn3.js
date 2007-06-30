

// breadcrumbs:
// http://developer.mozilla.org/en/docs/Rhino_documentation
// http://www.mozilla.org/rhino/ScriptingJava.html
// http://www.exampledepot.com/egs/java.io/ReadLinesFromFile.html
// http://developer.mozilla.org/en/docs/Rhino_Shell#arguments

load("/devel/dig/2005/ajar/ajaw/lib0.js");

kb = new RDFIndexedFormula();


testn3 = function(uri) {
    print('Parsing '+uri)
    buf = readUrl(uri);
    print(buf.length+' bytes');
    var p = SinkParser(kb, kb, uri, uri, null, null, "", null)
    try {
	p.loadBuf(buf)

    } catch(e) {
	var msg = ("Error trying to parse " + uri
	    + ' as Notation3:\n' + e)
	print(msg)
    }
    
    print ('\nResult:\n' + kb)
    
}

print("Arguments <"+arguments+">"+arguments.length)

testn3(arguments[0]);
