// Things we need to define to make converted pythn code work in js
// environment of tabulator

var RDFSink_forSomeSym = "http://www.w3.org/2000/10/swap/log#forSome";
var RDFSink_forAllSym = "http://www.w3.org/2000/10/swap/log#forAll";


//  pyjs seems to reference runtime library which I didn't find

pyjslib_Tuple = function(theList) { return theList };

pyjslib_List = function(theList) { return theList };

pyjslib_Dict = function(listOfPairs) {
    if (listOfPairs.length > 0)
	throw "missing.js: oops nnonempty dict not imp";
    return [];
}

pyjslib_len = function(s) { return s.length }

pyjslib_slice = function(str, i, j) {
    if ((typeof j == 'undefined') || (j ==null)) return str.slice(i);
    return str.slice(i, j) // @ exactly the same spec?
}
StopIteration = Error('dummy error stop iteration')

pyjslib_Iterator = function(theList) {
    this.last = 0;
    this.li = theList;
    this.next = function() {
	if (this.last == this.li.length) throw StopIteration;
	return this.li[this.last++];
    }
    return this;
}

ord = function(str) {
    return str.charCodeAt(0)
}

string_find = function(str, s) {
    return str.indexOf(s)
}

assertFudge = function(condition, desc) {
    if (condition) return;
    if (desc) throw "python Assertion failed: "+desc;
    throw "(python) Assertion failed.";  
}

uripath_join = function(base, given) {
    return Util.uri.join(given, base)  // sad but true
}

var diag_tracking = 0;
var diag_chatty_flag = 0;
diag_progress = function(str) { tabulator.log.debug(str); }

// why_BecauseOfData = function(doc, reason) { return doc };


RDF_type_URI = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type";
DAML_sameAs_URI = "http://www.w3.org/2002/07/owl#sameAs";

function SyntaxError(details) {
    return new __SyntaxError(details);
}

function __SyntaxError(details) {
    this.details = details
}

