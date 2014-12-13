// Javascript


Store = function() { return new __Store() };  // @@@
__Store = function() {
}
   
var kb = new RDFIndexedFormula();

function test_buf(str) {
//    var p = SinkParser(store, openFormula, thisDoc, baseURI, genPrefix, metaURI, flags, why)
    var p = SinkParser(kb, kb, "http://example.com/", null, null, null, "", null)
    p.loadBuf(str)
}