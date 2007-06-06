""" SPARQL Client Query for cwm architecture

"""

QL_NS = "http://www.w3.org/2004/ql#"
from sparql2cwm import SPARQL_NS

#from set_importer import Set, ImmutableSet


#from OrderedSequence import merge, intersection, minus, indentString

import diag
from diag import chatty_flag, tracking, progress

def SparqlQuery(query, items, serviceURI):
    """Perform remote query as client on remote store.
	See $SWAP/query.py
    """
    diag.chatty_flag = 99    # @@@@@@
    if diag.chatty_flag > 0:
	progress("SPARQL Query on service %s,\n\tvariables: %s;\n\texistentials: %s" %
			    (serviceURI, query.variables, query.existentials))
	for item in items:
	    progress("\tSparql query line: %s" % (`item`))
    
    s = query.n3String()
    progress("QUERY IS ", s)
    raise NotImplementedError()

    queryString = "CONSTRUCT { %s } WHERE { %s }" % (constructions, patterns )

    return nbs   # No bindings for testing


# ends

from xml.sax import make_parser
from xml.sax.saxutils import handler, quoteattr, escape
from xml.sax.handler import ErrorHandler

def parseSparqlResults(store, resultString):
    parser = make_parser()
    # Workaround for bug in expatreader.py. Needed when
    # expatreader is trying to guess a prefix.
    parser.start_namespace_decl("xml", "http://www.w3.org/XML/1998/namespace")
    parser.setFeature(handler.feature_namespaces, 1)
    sparqlResults = SparqlResultsHandler(store)
    parser.setContentHandler(sparqlResults)
    parser.setErrorHandler(ErrorHandler())
    sparqlResults.setDocumentLocator(parser)
    parser.feed(resultString)
    return sparqlResults.results


RESULTS_NS = 'http://www.w3.org/2005/sparql-results#'

class BadSyntax(SyntaxError):
    pass

class SparqlResultsHandler(handler.ContentHandler):

    states = ('sparql', 'start', 'head', 'var', 'afterHead', 'results', 'result', 'binding')
    
    def __init__(self, store):
        self.store = store


    def setDocumentLocator(self, locator):
        self.locator = locator

    def onError(self, explanation):
        documentLocation = "%s:line:%s, column:%s" % (self.locator.getSystemId(),
                            self.locator.getLineNumber(), self.locator.getColumnNumber())
        raise BadSyntax(explanation + '\n' + documentLocation)

    def startDocument(self):
        progress('starting document')
        self.state = 'start'

    def endDocument(self):
        progress('ending document')
        raise NotImplementedError

    def startElementNS(self, name, qname, attrs):
        (ns, lname) = name
        if ns != RESULTS_NS:
            self.onError('The tag %s does not belong anywhere!' % (ns + lname))
        try:
            processor = self.tagStateStartHandlers[(self.state, lname)]
        except KeyError:
            self.onError("The tag %s does not belong here\nI'm in state %s" % (ns + lname, self.state))
        processor(self, attrs)

    def endElementNS(self, name, qname):
        (ns, lname) = name
        processor = self.tagEndHandlers[lname]
        processor(self)

    def characters(self, content):
        self.text = content

    def startSparql(self, attrs):
        self.state = 'sparql'
    def sparqlHead(self, attrs):
        self.state = 'head'
    def variable(self, attrs):
        self.state = 'var'
        progress('I need to declare %s' % dict(attrs))
    def results(self, attrs):
        self.state = 'results'
        self.results = []
    def result(self, attrs):
        self.state = 'result'
        self.result = {}
    def binding(self, attrs):
        try:
            self.varName = attrs[(None, 'name')]
        except KeyError:
            self.error('We need a name')
        self.state = 'binding'
    def uri(self, attrs):
        self.state = 'uri'
    def bnode(self, attrs):
        self.state = 'bnode'
    def literal(self, attrs):
        self.state = 'literal'
        progress('The attrs are %s' % dict(attrs))
        self.dt = attrs.get((None, 'datatype'), None)
        if self.dt is not None:
            self.dt = self.store.newSymbol(self.dt)
        self.lang = attrs.get(('http://www.w3.org/XML/1998/namespace', 'lang'), None)
    
    

    tagStateStartHandlers = \
                     {('start', 'sparql'): startSparql,
                      ('sparql', 'head'): sparqlHead,
                      ('head', 'variable'): variable,
                      ('afterHead', 'results'): results,
                      ('results', 'result'): result,
                      ('result', 'binding'): binding,
                      ('binding', 'uri'): uri,
                      ('binding', 'bnode'): bnode,
                      ('binding', 'literal'): literal}

    def endHead(self):
        self.state = 'afterHead'
    def endVar(self):
        self.state = 'head'
    def endResults(self):
        self.state = 'sparql'
    def endResult(self):
        self.results.append(self.result)
        self.state = 'results'
    def endBinding(self):
        self.result[self.varName] = self.val
        self.state = 'result'
    def endLiteral(self):
        self.state = 'endBinding'
        self.val = self.store.newLiteral(self.text, self.dt, self.lang)
    def endUri(self):
        self.state = 'endBinding'
        self.val = self.store.newSymbol(self.text)
    def endBnode(self):
        self.state = 'endBinding'
        self.val = self.store.newSymbol(self.text)
    
    tagEndHandlers = \
                        {'sparql': lambda x: None,
                         'head': endHead,
                         'variable': endVar,
                         'results': endResults,
                         'result': endResult,
                         'binding': endBinding,
                         'literal': endLiteral,
                         'uri': endUri,
                         'bnode': endBnode}

    

    
